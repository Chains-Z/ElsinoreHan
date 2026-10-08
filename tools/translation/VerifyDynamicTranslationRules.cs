using System;
using System.IO;
using System.Reflection;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;
using System.Linq.Expressions;

// 使用真实 XUnity Splitter 构造器验证格式模板及参数重排，不启动游戏。
public static class VerifyDynamicTranslationRules
{
    private static Dictionary<string, string> translations = new Dictionary<string, string>();
    private static int translatedParts;
    public static string TranslatePart(object info)
    {
        translatedParts++;
        string source = (string)info.GetType().GetProperty("UntranslatedText").GetValue(info, null);
        string target;
        return translations.TryGetValue(source, out target) ? target : null;
    }

    public static int Main(string[] args)
    {
        try { return Run(args); }
        catch (Exception error)
        {
            for (Exception current = error; current != null; current = current.InnerException)
                Console.Error.WriteLine(current.GetType().Name + ": " + current.Message);
            return 1;
        }
    }

    private static int Run(string[] args)
    {
        if (args.Length != 3) return 2;
        string plugin = Path.GetFullPath(args[0]);
        string folder = Path.GetDirectoryName(plugin);
        string managed = @"D:\SteamLibrary\steamapps\common\Elsinore\Elsinore_Data\Managed";
        string core = Path.GetFullPath(@"runtime\vendor\BepInEx5\BepInEx\core");
        string xunityCore = Path.GetFullPath(@"runtime\vendor\XUnity\BepInEx\core");
        AppDomain.CurrentDomain.AssemblyResolve += delegate(object sender, ResolveEventArgs request)
        {
            foreach (string directory in new string[] { folder, managed, core, xunityCore })
            {
                string dependency = Path.Combine(directory, new AssemblyName(request.Name).Name + ".dll");
                if (File.Exists(dependency)) return Assembly.LoadFrom(dependency);
            }
            return null;
        };
        Assembly assembly = Assembly.LoadFrom(plugin);
        MethodInfo decode = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.Utilities.TextHelper", true)
            .GetMethod("ReadTranslationLineAndDecode", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static);
        Type splitter = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.Parsing.RegexTranslationSplitter", true);
        JavaScriptSerializer serializer = new JavaScriptSerializer();
        serializer.MaxJsonLength = 16 * 1024 * 1024;
        object[] rules = serializer.DeserializeObject(File.ReadAllText(args[1])) as object[];
        foreach (object value in (object[])serializer.DeserializeObject(File.ReadAllText(args[2])))
        {
            Dictionary<string, object> row = (Dictionary<string, object>)value;
            translations[(string)row["source"]] = (string)row["target"];
        }
        Type parser = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.Parsing.ParserResult", true);
        Type origin = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.Parsing.ParserResultOrigin", true);
        MethodInfo consume = parser.GetMethod("GetTranslationFromParts");
        Type delegateType = consume.GetParameters()[0].ParameterType;
        ParameterExpression info = Expression.Parameter(delegateType.GetGenericArguments()[0], "info");
        Delegate callback = Expression.Lambda(delegateType,
            Expression.Call(typeof(VerifyDynamicTranslationRules).GetMethod("TranslatePart"), Expression.Convert(info, typeof(object))), info).Compile();
        foreach (object value in rules)
        {
            Dictionary<string, object> row = (Dictionary<string, object>)value;
            string[] line = (string[])decode.Invoke(null, new object[] { (string)row["encoded_line"] });
            object instance = Activator.CreateInstance(splitter, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance, null,
                new object[] { line[0], line[1] }, null);
            Regex regex = (Regex)splitter.GetProperty("CompiledRegex").GetValue(instance, null);
            string replacement = (string)splitter.GetProperty("Translation").GetValue(instance, null);
            if (replacement != (string)row["replacement"]) throw new Exception("模板替换文本改变");
            object[] parameters = new object[16];
            for (int i = 0; i < parameters.Length; i++) parameters[i] = "ARG" + i;
            string source = String.Format((string)row["source"], parameters);
            string expected = String.Format((string)row["target"], parameters);
            if (!regex.IsMatch(source) || regex.Replace(source, replacement) != expected)
                throw new Exception("真实动态模板不匹配或参数重排错误：" + row["id"]);
            bool ignored = (bool)row["preserve_args"];
            object[] expectedParts = new object[16];
            for (int i = 0; i < parameters.Length; i++)
            {
                string name = i % 2 == 0 ? "Ophelia" : "Bernardo";
                parameters[i] = ignored ? "ARG" + i : name;
                expectedParts[i] = ignored ? "ARG" + i : translations[name];
            }
            source = String.Format((string)row["source"], parameters);
            expected = String.Format((string)row["target"], expectedParts);
            object parsed = Activator.CreateInstance(parser, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance, null,
                new object[] { Enum.ToObject(origin, 0), source, replacement, false, false, false, false, regex, regex.Match(source) }, null);
            translatedParts = 0;
            if ((string)consume.Invoke(parsed, new object[] { callback }) != expected || (ignored && translatedParts != 0))
                throw new Exception("真实Splitter消费或按键保护失败：" + row["id"]);
        }
        Console.WriteLine("{\"actual_xunity_splitter_passed\":true,\"actual_parser_consumer_passed\":true,\"count\":" + rules.Length + "}");
        return 0;
    }
}
