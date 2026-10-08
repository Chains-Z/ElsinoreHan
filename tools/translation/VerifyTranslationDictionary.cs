using System;
using System.IO;
using System.Reflection;
using System.Collections.Generic;
using System.Web.Script.Serialization;

// 使用实际已安装版本的 XUnity 解析器核对词表，不启动或运行 Unity 游戏。
public static class VerifyTranslationDictionary
{
    public static int Main(string[] args)
    {
        if (args.Length != 3) return 2;
        string plugin = Path.GetFullPath(args[0]);
        string folder = Path.GetDirectoryName(plugin);
        AppDomain.CurrentDomain.AssemblyResolve += delegate(object sender, ResolveEventArgs request)
        {
            string dependency = Path.Combine(folder, new AssemblyName(request.Name).Name + ".dll");
            return File.Exists(dependency) ? Assembly.LoadFrom(dependency) : null;
        };
        Assembly assembly = Assembly.LoadFrom(plugin);
        Type helper = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.Utilities.TextHelper", true);
        MethodInfo decode = helper.GetMethod("ReadTranslationLineAndDecode", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static);
        JavaScriptSerializer serializer = new JavaScriptSerializer();
        serializer.MaxJsonLength = 32 * 1024 * 1024;
        object[] expected = serializer.DeserializeObject(File.ReadAllText(args[2])) as object[];
        string[] lines = File.ReadAllLines(args[1]);
        if (expected == null || lines.Length != expected.Length) throw new Exception("词表数量不符");
        for (int i = 0; i < lines.Length; i++)
        {
            string[] decoded = (string[])decode.Invoke(null, new object[] { lines[i] });
            Dictionary<string, object> row = (Dictionary<string, object>)expected[i];
            if (decoded == null || decoded.Length != 2 || decoded[0] != (string)row["source"] || decoded[1] != (string)row["target"])
                throw new Exception("实际 XUnity 解码不符：索引 " + i);
        }
        Console.WriteLine("{\"actual_xunity_parser_passed\":true,\"count\":" + lines.Length + "}");
        return 0;
    }
}
