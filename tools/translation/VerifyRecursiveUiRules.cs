using System;
using System.IO;
using System.Reflection;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;
using System.Linq.Expressions;

// 使用真实 XUnity Splitter 和 ParserResult 递归消费冻结 UI 用例，不启动游戏。
public static class VerifyRecursiveUiRules
{
    private sealed class Rule
    {
        public string Id;
        public object Splitter;
        public Regex Regex;
        public string Replacement;
    }

    private static readonly Dictionary<string, string> translations =
        new Dictionary<string, string>(StringComparer.Ordinal);
    private static readonly List<Rule> rules = new List<Rule>();
    private static readonly HashSet<string> activeSources = new HashSet<string>(StringComparer.Ordinal);
    private static readonly Regex english = new Regex("[A-Za-z]", RegexOptions.CultureInvariant);
    private static readonly Regex markup = new Regex("<[^>]*>", RegexOptions.CultureInvariant);
    private static Type parserType;
    private static Type originType;
    private static MethodInfo consume;
    private static Delegate callback;
    private static int depth;

    public static string TranslatePart(object info)
    {
        PropertyInfo property = info.GetType().GetProperty("UntranslatedText");
        if (property == null) throw new InvalidOperationException("真实 ParserResult 参数缺少 UntranslatedText");
        return Translate((string)property.GetValue(info, null));
    }

    private static string Translate(string source)
    {
        if (source == null) return null;
        string target;
        if (translations.TryGetValue(source, out target)) return target;
        if (translations.TryGetValue(source.Trim(), out target)) return target;
        // 富文本标记不构成待译英文；数字、标点、空白及已翻译的中文原样消费。
        if (!english.IsMatch(markup.Replace(source, String.Empty))) return source;
        if (depth >= 20) throw new InvalidOperationException("递归翻译深度超过20");
        if (!activeSources.Add(source)) throw new InvalidOperationException("递归翻译出现源文循环");
        depth++;
        try
        {
            for (int ruleIndex = rules.Count - 1; ruleIndex >= 0; ruleIndex--)
            {
                Rule rule = rules[ruleIndex];
                Match match = rule.Regex.Match(source);
                if (!match.Success) continue;
                object parsed = Activator.CreateInstance(parserType,
                    BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance, null,
                    new object[] { Enum.ToObject(originType, 0), source, rule.Replacement,
                        false, false, false, false, rule.Regex, match }, null);
                // _i 组由真实 ParserResult 忽略，回调不自行拼接或模拟受保护片段。
                string result = (string)consume.Invoke(parsed, new object[] { callback });
                if (result != null) return result;
            }
            // 未知英文不能以原样返回冒充消费成功。
            return null;
        }
        finally
        {
            depth--;
            activeSources.Remove(source);
        }
    }

    private static void ResolveDependencies(string plugin)
    {
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
    }

    private static object[] ReadRows(JavaScriptSerializer serializer, string filename)
    {
        object[] result = serializer.DeserializeObject(File.ReadAllText(filename)) as object[];
        if (result == null) throw new InvalidOperationException("输入文件必须是 JSON 数组：" + Path.GetFileName(filename));
        return result;
    }

    private static int Run(string[] args)
    {
        if (args.Length != 4)
        {
            Console.Error.WriteLine("参数：coreDLL dynamic-rules.json translations.json tests.json");
            return 2;
        }
        string plugin = Path.GetFullPath(args[0]);
        ResolveDependencies(plugin);
        Assembly assembly = Assembly.LoadFrom(plugin);
        MethodInfo decode = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.Utilities.TextHelper", true)
            .GetMethod("ReadTranslationLineAndDecode", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static);
        Type splitterType = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.Parsing.RegexTranslationSplitter", true);
        parserType = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.Parsing.ParserResult", true);
        originType = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.Parsing.ParserResultOrigin", true);
        consume = parserType.GetMethod("GetTranslationFromParts");
        if (decode == null || consume == null) throw new InvalidOperationException("真实 XUnity 解析入口缺失");
        Type delegateType = consume.GetParameters()[0].ParameterType;
        ParameterExpression info = Expression.Parameter(delegateType.GetGenericArguments()[0], "info");
        callback = Expression.Lambda(delegateType,
            Expression.Call(typeof(VerifyRecursiveUiRules).GetMethod("TranslatePart"),
                Expression.Convert(info, typeof(object))), info).Compile();
        JavaScriptSerializer serializer = new JavaScriptSerializer();
        serializer.MaxJsonLength = 64 * 1024 * 1024;
        serializer.RecursionLimit = 256;
        foreach (object value in ReadRows(serializer, args[2]))
        {
            Dictionary<string, object> row = (Dictionary<string, object>)value;
            string source = (string)row["source"];
            string target = (string)row["target"];
            string existing;
            if (translations.TryGetValue(source, out existing) && existing != target)
                throw new InvalidOperationException("冻结词表同一原文有不同译文");
            translations[source] = target;
        }
        foreach (object value in ReadRows(serializer, args[1]))
        {
            Dictionary<string, object> row = (Dictionary<string, object>)value;
            string[] line = (string[])decode.Invoke(null, new object[] { (string)row["encoded_line"] });
            if (line == null || line.Length != 2) throw new InvalidOperationException("动态规则无法由真实 XUnity 解码");
            object splitter = Activator.CreateInstance(splitterType,
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance, null,
                new object[] { line[0], line[1] }, null);
            string replacement = (string)splitterType.GetProperty("Translation").GetValue(splitter, null);
            object expected;
            if (row.TryGetValue("replacement", out expected) && replacement != (string)expected)
                throw new InvalidOperationException("真实 Splitter 替换文本与冻结规则不符：" + row["id"]);
            rules.Add(new Rule { Id = (string)row["id"], Splitter = splitter,
                Regex = (Regex)splitterType.GetProperty("CompiledRegex").GetValue(splitter, null),
                Replacement = replacement });
        }
        object[] tests = ReadRows(serializer, args[3]);
        if (tests.Length == 0) throw new InvalidOperationException("冻结递归消费用例为空");
        int failures = 0;
        foreach (object value in tests)
        {
            Dictionary<string, object> row = (Dictionary<string, object>)value;
            string actual = null;
            string error = null;
            try { actual = Translate((string)row["source"]); }
            catch (Exception exception)
            {
                Exception current = exception;
                while (current.InnerException != null) current = current.InnerException;
                error = current.GetType().Name + ": " + current.Message;
            }
            if (actual == (string)row["target"] && error == null) continue;
            failures++;
            Console.Error.WriteLine(serializer.Serialize(new Dictionary<string, object> {
                { "id", row["id"] }, { "actual", actual }, { "expected", row["target"] }, { "error", error } }));
        }
        Console.WriteLine("{\"actual_recursive_xunity_consumer_passed\":" +
            (failures == 0 ? "true" : "false") + ",\"count\":" + tests.Length + "}");
        return failures == 0 ? 0 : 1;
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
}
