using System;
using System.IO;
using System.Reflection;
using System.Collections;
using System.Collections.Generic;
using System.Linq.Expressions;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;

// 离线调用真实词表缓存、富文本拆分及逆序首匹配规则，复现片段词条抢占。
// 不初始化Unity、不启动游戏、不访问存档；不冒充对话界面或F8验收。
public sealed class VerifyDialogueTokenCache
{
    private const BindingFlags Members = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance;
    private readonly object cache, rich, splitter;
    private readonly Type keyType;
    private readonly MethodInfo lookup, parseRich, parseSplitter, consume;
    private readonly Delegate callback;
    private int depth;

    private VerifyDialogueTokenCache(Assembly assembly, object[] rows, object[] rules, bool includeAlias)
    {
        Type cacheType = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.TextTranslationCache", true);
        cache = Activator.CreateInstance(cacheType, Members, null, new object[] { new DirectoryInfo(".") }, null);
        keyType = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.UntranslatedText", true);
        lookup = cacheType.GetMethod("TryGetTranslation", Members);
        MethodInfo add = cacheType.GetMethod("AddTranslation", Members);
        MethodInfo addToken = cacheType.GetMethod("AddTokenTranslation", Members);
        Type richType = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.Parsing.RichTextParser", true);
        rich = Activator.CreateInstance(richType, true);
        parseRich = richType.GetMethod("Parse", Members);
        var selected = new List<Dictionary<string, object>>();
        foreach (Dictionary<string, object> row in rows)
        {
            if (!includeAlias && (string)row["id"] == "dialogue-line-height-i-will") continue;
            selected.Add(row);
            add.Invoke(cache, new object[] { row["source"], row["target"], -1 });
        }
        // 与真实LoadTranslationFiles一致，从完整译文按顺序派生片段缓存。
        foreach (var row in selected)
        {
            object p = parseRich.Invoke(rich, new object[] { row["source"], -1 });
            object q = parseRich.Invoke(rich, new object[] { row["target"], -1 });
            if (p == null || q == null) continue;
            IList x = (IList)p.GetType().GetProperty("Arguments").GetValue(p, null);
            IList y = (IList)q.GetType().GetProperty("Arguments").GetValue(q, null);
            if (x.Count != y.Count) continue;
            foreach (object item in x)
            {
                object name = item.GetType().GetProperty("Key").GetValue(item, null);
                foreach (object other in y)
                    if (Equals(name, other.GetType().GetProperty("Key").GetValue(other, null)))
                        addToken.Invoke(cache, new object[] { Part(item), Part(other), -1 });
            }
        }
        Type ruleType = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.Parsing.RegexTranslationSplitter", true);
        IList splitters = (IList)cacheType.GetField("_splitterRegexes", Members).GetValue(cache);
        MethodInfo decode = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.Utilities.TextHelper", true)
            .GetMethod("ReadTranslationLineAndDecode", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);
        foreach (Dictionary<string, object> rule in rules)
        {
            string[] pair = (string[])decode.Invoke(null, new object[] { rule["encoded_line"] });
            splitters.Add(Activator.CreateInstance(ruleType, Members, null, new object[] { pair[0], pair[1] }, null));
        }
        Type splitterType = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.Parsing.RegexSplittingTextParser", true);
        splitter = Activator.CreateInstance(splitterType, true);
        parseSplitter = splitterType.GetMethod("Parse", Members);
        consume = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.Parsing.ParserResult", true).GetMethod("GetTranslationFromParts");
        Type delegateType = consume.GetParameters()[0].ParameterType;
        var argument = Expression.Parameter(delegateType.GetGenericArguments()[0], "info");
        callback = Expression.Lambda(delegateType, Expression.Call(Expression.Constant(this),
            GetType().GetMethod("TranslatePart"), Expression.Convert(argument, typeof(object))), argument).Compile();
    }

    private static string Part(object argument)
    {
        object info = argument.GetType().GetProperty("Info").GetValue(argument, null);
        return (string)info.GetType().GetProperty("UntranslatedText").GetValue(info, null);
    }

    private string Lookup(string source, bool token)
    {
        object key = Activator.CreateInstance(keyType, Members, null,
            new object[] { source, false, false, true, false, false }, null);
        var arguments = new object[] { key, !token, token, -1, null };
        return (bool)lookup.Invoke(cache, arguments) ? (string)arguments[4] : null;
    }

    public string TranslatePart(object info)
    {
        string source = (string)info.GetType().GetProperty("UntranslatedText").GetValue(info, null);
        return Lookup(source, true) ?? Resolve(source);
    }

    public string Resolve(string source)
    {
        string target = Lookup(source, false);
        if (target != null) return target;
        if (!Regex.IsMatch(Regex.Replace(source, "<[^>]*>", ""), "[A-Za-z]")) return source;
        if (depth >= 64) throw new InvalidOperationException("解析递归超过64层");
        depth++;
        try
        {
            object parsed = parseSplitter.Invoke(splitter, new object[] { source, -1, cache })
                ?? parseRich.Invoke(rich, new object[] { source, -1 });
            // 子项失败即失败，不能换下一条规则兜底。
            return parsed == null ? null : (string)consume.Invoke(parsed, new object[] { callback });
        }
        finally { depth--; }
    }

    public static int Main(string[] args)
    {
        Console.OutputEncoding = System.Text.Encoding.UTF8;
        try
        {
            string plugin = Path.GetFullPath(args[0]);
            string game = Path.GetFullPath("D:/SteamLibrary/steamapps/common/Elsinore/Elsinore_Data/Managed");
            AppDomain.CurrentDomain.AssemblyResolve += delegate(object sender, ResolveEventArgs request)
            {
                foreach (string folder in new string[] { Path.GetDirectoryName(plugin), game,
                    Path.GetFullPath("runtime/vendor/BepInEx5/BepInEx/core"), Path.GetFullPath("runtime/vendor/XUnity/BepInEx/core") })
                {
                    string path = Path.Combine(folder, new AssemblyName(request.Name).Name + ".dll");
                    if (File.Exists(path)) return Assembly.LoadFrom(path);
                }
                return null;
            };
            Assembly assembly = Assembly.LoadFrom(plugin);
            Type settings = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.Configuration.Settings", true);
            settings.GetField("HandleRichText", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic).SetValue(null, true);
            var serializer = new JavaScriptSerializer { MaxJsonLength = 64 * 1024 * 1024, RecursionLimit = 256 };
            object[] rows = (object[])serializer.DeserializeObject(File.ReadAllText(args[1]));
            object[] rules = (object[])serializer.DeserializeObject(File.ReadAllText(args[2]));
            object[] tests = (object[])serializer.DeserializeObject(File.ReadAllText(args[3]));
            var before = new VerifyDialogueTokenCache(assembly, rows, rules, false);
            var after = new VerifyDialogueTokenCache(assembly, rows, rules, true);
            int failures = 0;
            foreach (Dictionary<string, object> test in tests)
            {
                string source = (string)test["source"];
                string old = before.Resolve(source), current = after.Resolve(source);
                bool passed = old == (string)test["before"] && current == (string)test["target"];
                if (!passed) failures++;
                Console.WriteLine(serializer.Serialize(new { id = test["id"], before = old, actual = current, passed = passed }));
            }
            Console.WriteLine(serializer.Serialize(new { actual_xunity_token_cache_passed = failures == 0, count = tests.Length }));
            return failures == 0 ? 0 : 1;
        }
        catch (Exception error)
        {
            for (Exception current = error; current != null; current = current.InnerException)
                Console.Error.WriteLine(current.GetType().Name + ": " + current.Message);
            return 1;
        }
    }
}
