using System;
using System.Collections;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;

// 只调用已编译探针的反射选择与纯托管序列化；绝不创建Unity组件或调用引擎API。
public static class CreditsSkipProbeTests
{
    private static string[] dependencyDirectories;
    private static Assembly Resolve(object sender, ResolveEventArgs args)
    {
        string filename = new AssemblyName(args.Name).Name + ".dll";
        foreach (string directory in dependencyDirectories)
        {
            string path = Path.Combine(directory, filename);
            if (File.Exists(path)) return Assembly.LoadFrom(path);
        }
        return null;
    }
    private static void Check(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
    private static object New(Assembly assembly, string name)
    {
        return Activator.CreateInstance(assembly.GetType("CreditsSkipProbe+" + name, true));
    }
    private static void Set(object instance, string name, object value)
    {
        instance.GetType().GetField(name).SetValue(instance, value);
    }
    private static void Add(object report, string name, object row)
    {
        ((IList)report.GetType().GetField(name).GetValue(report)).Add(row);
    }
    private static int Run(string[] args)
    {
        if (args.Length == 1 && args[0] == "--check-error-handler") throw new InvalidOperationException("测试CLI异常收口");
        if (args.Length != 3) throw new ArgumentException("需要项目目录、游戏Managed目录和测试模式");
        string root = Path.GetFullPath(args[0]);
        dependencyDirectories = new string[] {
            Path.GetFullPath(args[1]), Path.Combine(root, "runtime/build"),
            Path.Combine(root, "runtime/vendor/BepInEx5/BepInEx/core"),
            Path.Combine(root, "runtime/vendor/XUnity/BepInEx/plugins/XUnity.AutoTranslator"),
            Path.Combine(root, "runtime/vendor/XUnity/BepInEx/plugins/XUnity.Common")
        };
        AppDomain.CurrentDomain.AssemblyResolve += Resolve;
        Assembly probe = Assembly.LoadFrom(Path.Combine(root, "runtime/build/ElsinoreHan.RuntimeProbe.dll"));
        Type type = probe.GetType("CreditsSkipProbe", true);
        if (args[2] == "metadata")
        {
            Assembly plugin = Assembly.LoadFrom(Path.Combine(root, "runtime/build/ElsinoreHan.TranslationToggle.dll"));
            Type ring = plugin.GetType("CreditsSkipRing", true);
            BindingFlags flags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
            bool oldAmbiguous = false;
            try { ring.GetMethod("OnPopulateMesh", flags); }
            catch (AmbiguousMatchException) { oldAmbiguous = true; }
            MethodInfo method = (MethodInfo)type.GetMethod("PopulateMeshMethod").Invoke(null, new object[] { ring });
            Check(method != null, "精确网格入口缺失");
            ParameterInfo[] parameters = method.GetParameters();
            Check(method.Name == "OnPopulateMesh" && method.ReturnType == typeof(void) && method.DeclaringType == ring,
                "返回的方法不是正式圆环自身的void重载");
            Check(parameters.Length == 1 && parameters[0].ParameterType.FullName == "UnityEngine.UI.VertexHelper",
                "必须选择VertexHelper参数，不可选旧Mesh重载");
            int exactDefinitions = 0, overloads = 0;
            foreach (MethodInfo candidate in ring.GetMethods(flags))
            {
                if (candidate.Name != "OnPopulateMesh") continue;
                overloads++;
                var candidateParameters = candidate.GetParameters();
                if (candidateParameters.Length == 1 && candidateParameters[0].ParameterType == parameters[0].ParameterType)
                    exactDefinitions++;
            }
            Check(oldAmbiguous && overloads >= 2 && exactDefinitions == 1, "真实Unity重载前置状态不符");
            Console.WriteLine(new JavaScriptSerializer().Serialize(new {
                ambiguous_without_signature = oldAmbiguous, overloads = overloads,
                exact_definitions = exactDefinitions, declaring_type = method.DeclaringType.FullName,
                parameter_type = parameters[0].ParameterType.FullName, return_type = method.ReturnType.FullName,
                probe_assembly = probe.Location, plugin_assembly = plugin.Location
            }));
            return 0;
        }
        if (args[2] != "report" && args[2] != "empty-report") throw new ArgumentException("未知测试模式");
        // 法语文化使用小数逗号，证明正式序列化函数仍输出JSON合法的小数点。
        Thread.CurrentThread.CurrentCulture = CultureInfo.GetCultureInfo("fr-FR");
        object report = New(probe, "Report");
        if (args[2] == "report")
        {
            Set(report, "passed", true);
            Set(report, "scene", "credits\n\"引号\"\\路径\t末尾\r\n\u0001");
            Set(report, "label_screen_corners", new float[] { 1.25f, 2.5f });
            object check = New(probe, "CheckRow");
            Set(check, "name", "检查\"名称");
            Set(check, "detail", "第一行\n第二行\t\\\"\u0001");
            Set(check, "passed", true); Add(report, "checks", check);
            object ring = New(probe, "RingRow");
            Set(ring, "state", "quarter"); Set(ring, "progress", 0.25f);
            Set(ring, "minimum_alpha", 1f); Set(ring, "maximum_radius", 18f);
            Set(ring, "vertices", 34); Set(ring, "triangles", 32); Set(ring, "white", true);
            Add(report, "rings", ring);
            object glyph = New(probe, "GlyphRow");
            Set(glyph, "character", "长"); Set(glyph, "font", "ElsinoreHan Sans SDF");
            Set(glyph, "atlas", "atlas\\\"中文"); Set(glyph, "material", 1);
            Set(glyph, "atlas_width", 4096); Set(glyph, "atlas_height", 4096);
            Set(glyph, "visible", true); Set(glyph, "white", true); Add(report, "glyphs", glyph);
        }
        string json = (string)type.GetMethod("SerializeReport").Invoke(null, new object[] { report });
        Console.WriteLine(json);
        return 0;
    }
    public static int Main(string[] args)
    {
        try
        {
            Console.OutputEncoding = new UTF8Encoding(false);
            return Run(args);
        }
        catch (Exception error)
        {
            // 不把异常交给Windows错误报告或即时调试器，全部通过终端及退出码返回。
            Console.Error.WriteLine(error.GetType().Name + ": " + error.ToString());
            return 1;
        }
    }
}
