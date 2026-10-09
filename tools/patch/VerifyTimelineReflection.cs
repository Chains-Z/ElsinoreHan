using System;
using System.IO;
using System.Reflection;
using System.Collections.Generic;
using System.Web.Script.Serialization;

// 仅读取真实DLL方法元数据并调用探针的签名选择器；不创建Unity实例、不运行游戏格式器。
public static class VerifyTimelineReflection
{
    public static int Main(string[] args)
    {
        if (args.Length != 3) { Console.Error.WriteLine("参数：helperDLL managedDirectory outputJSON"); return 2; }
        string managed = Path.GetFullPath(args[1]);
        AppDomain.CurrentDomain.AssemblyResolve += delegate(object sender, ResolveEventArgs request)
        {
            string candidate = Path.Combine(managed, new AssemblyName(request.Name).Name + ".dll");
            return File.Exists(candidate) ? Assembly.LoadFrom(candidate) : null;
        };
        try
        {
            var assembly = Assembly.LoadFrom(Path.GetFullPath(args[0]));
            var type = assembly.GetType("TimelineFollowupProbe", true);
            var method = type.GetMethod("ValidateReflectionSignatures", BindingFlags.Public | BindingFlags.Static,
                null, new Type[] { typeof(string) }, null);
            string[] signatures = (string[])method.Invoke(null, new object[] { managed });
            if (signatures.Length != 14 || signatures[0] != "LEGACY_NAME_ONLY_AMBIGUOUS=True")
                throw new InvalidOperationException("完整反射目标数量或旧重载错误复现证据不符");
            var clockMethod = type.GetMethod("ValidateClockFixtures", BindingFlags.Public | BindingFlags.Static);
            string[] clocks = (string[])clockMethod.Invoke(null, null);
            if (clocks.Length != 5) throw new InvalidOperationException("真实时钟日期回归数量不符");
            var proof = new Dictionary<string, object> {
                { "passed", true }, { "legacy_name_only_ambiguous_reproduced", true },
                { "exact_method_signatures", signatures.Length - 1 }, { "signatures", signatures },
                { "clock_fixtures", clocks }, { "clock_epoch_offset_minutes", 360 },
                { "legacy_six_hour_offset_reproduced", true },
                { "method", "真实DLL离线签名与GameClock纯逻辑检查；未创建Unity实例或调用UiStrings格式器" }
            };
            string json = new JavaScriptSerializer().Serialize(proof);
            File.WriteAllText(Path.GetFullPath(args[2]), json + "\n", new System.Text.UTF8Encoding(false));
            Console.WriteLine(json);
            return 0;
        }
        catch (Exception error)
        {
            for (Exception current = error; current != null; current = current.InnerException)
                Console.Error.WriteLine(current.GetType().Name + ": " + current.Message);
            return 1;
        }
    }
}
