using System;
using System.Collections.Generic;
using System.IO;
using System.Linq.Expressions;
using System.Reflection;
using System.Text.RegularExpressions;

// 从文件词表和真实首匹配Splitter重建日志，拒绝把未知英文片段当作成功译文。
public sealed class StrictLogTranslation
{
    private const BindingFlags Members = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
    private readonly object translator, fileCache, parser;
    private readonly MethodInfo cacheKey, lookup, parse, consume, add;
    private readonly Delegate callback;
    private readonly Dictionary<string, string> memo = new Dictionary<string, string>(StringComparer.Ordinal);
    private readonly HashSet<string> active = new HashSet<string>(StringComparer.Ordinal);
    private int depth;

    public StrictLogTranslation(object translator)
    {
        this.translator = translator;
        Type cacheType = translator.GetType().GetField("TextCache", Members).FieldType;
        Type settings = cacheType.Assembly.GetType("XUnity.AutoTranslator.Plugin.Core.Configuration.Settings", true);
        string path = (string)settings.GetField("TranslationsPath", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static).GetValue(null);
        fileCache = Activator.CreateInstance(cacheType, Members, null, new object[] { new DirectoryInfo(path) }, null);
        cacheType.GetMethod("LoadTranslationFiles", Members).Invoke(fileCache, null);
        cacheKey = translator.GetType().GetMethod("GetCacheKey", Members, null, new Type[] { typeof(string), typeof(bool) }, null);
        lookup = cacheType.GetMethod("TryGetTranslation", Members);
        add = cacheType.GetMethod("AddTranslation", Members, null, new Type[] { typeof(string), typeof(string), typeof(int) }, null);
        Type parserType = cacheType.Assembly.GetType("XUnity.AutoTranslator.Plugin.Core.Parsing.RegexSplittingTextParser", true);
        parser = Activator.CreateInstance(parserType, true);
        parse = parserType.GetMethod("Parse", Members);
        Type result = cacheType.Assembly.GetType("XUnity.AutoTranslator.Plugin.Core.Parsing.ParserResult", true);
        consume = result.GetMethod("GetTranslationFromParts", Members);
        Type delegateType = consume.GetParameters()[0].ParameterType;
        var info = Expression.Parameter(delegateType.GetGenericArguments()[0], "info");
        callback = Expression.Lambda(delegateType, Expression.Call(Expression.Constant(this),
            GetType().GetMethod("TranslatePart"), Expression.Convert(info, typeof(object))), info).Compile();
    }

    public string TranslatePart(object info)
    {
        return Resolve((string)info.GetType().GetProperty("UntranslatedText").GetValue(info, null));
    }

    public string Resolve(string source)
    {
        if (source == null) return null;
        string target;
        if (memo.TryGetValue(source, out target)) return target;
        object key = cacheKey.Invoke(translator, new object[] { source, false });
        var arguments = new object[] { key, true, false, -1, null };
        if ((bool)lookup.Invoke(fileCache, arguments)) return memo[source] = (string)arguments[4];
        if (!Regex.IsMatch(Regex.Replace(source, "<[^>]*>", ""), "[A-Za-z]")) return source;
        if (depth >= 64 || !active.Add(source)) return null;
        depth++;
        try
        {
            // Parse内部只选逆序首个匹配；子项失败时不换规则兜底。
            object parsed = parse.Invoke(parser, new object[] { source, -1, fileCache });
            if (parsed == null) return null;
            target = (string)consume.Invoke(parsed, new object[] { callback });
            if (target != null) memo[source] = target;
            return target;
        }
        finally { depth--; active.Remove(source); }
    }

    public void Register(object liveCache, string source, string target)
    {
        // 仅覆盖此准确原文的内存项；不持久化，不修改游戏历史或组件收到的原文。
        add.Invoke(liveCache, new object[] { source, target, -1 });
    }
}
