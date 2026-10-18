using System;
using System.Globalization;
using System.Reflection;

// 离线加载真实插件中的纯手势类，比较已安装旧版与候选；不启动Unity或读取存档。
public static class CreditsStallRegressionTests
{
    public static int Main(string[] args)
    {
        try
        {
            if (args.Length != 2 || (args[1] != "baseline" && args[1] != "candidate"))
                throw new ArgumentException("需要插件路径及baseline/candidate");
            Type type = Assembly.LoadFrom(args[0]).GetType("CreditsSkipGesture", true);
            object gesture = Activator.CreateInstance(type);
            MethodInfo tick = type.GetMethod("Tick", new Type[] { typeof(bool), typeof(bool), typeof(bool), typeof(double), typeof(bool) });
            PropertyInfo progress = type.GetProperty("Progress");
            Func<bool, double, bool> sample = (held, now) => (bool)tick.Invoke(gesture, new object[] { true, true, held, now, true });
            sample(false, 0); sample(true, 0);
            for (int frame = 1; frame <= 16; frame++)
                if (sample(true, frame / 32.0)) throw new InvalidOperationException("半圈之前提前完成");
            float half = (float)progress.GetValue(gesture, null);
            if (Math.Abs(half - 0.5f) > 0.00001f) throw new InvalidOperationException("没有正常增长到半圈");
            bool completed = sample(true, 2.5);
            float after = (float)progress.GetValue(gesture, null);
            if (args[1] == "baseline")
            {
                if (!completed || after != 1) throw new InvalidOperationException("旧版未复现2秒间隔后直接补满");
            }
            else
            {
                if (completed || Math.Abs(after - 0.6f) > 0.00001f)
                    throw new InvalidOperationException("新版卡顿后仍直接补满，或单次推进未限制");
                for (int frame = 1; frame <= 12; frame++)
                    if (sample(true, 2.5 + frame / 32.0)) throw new InvalidOperationException("恢复后未走完剩余进度就完成");
                if (!sample(true, 2.5 + 13 / 32.0)) throw new InvalidOperationException("恢复正常采样后无法完成");
            }
            Console.WriteLine("{\"passed\":true,\"mode\":\"" + args[1] + "\",\"half_progress\":0.5,\"sample_gap_seconds\":2,\"post_gap_progress\":"
                + after.ToString("R", CultureInfo.InvariantCulture) + ",\"completed_at_gap\":" + (completed ? "true" : "false") + "}");
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine(error.GetType().Name + ": " + error.Message);
            return 1;
        }
    }
}
