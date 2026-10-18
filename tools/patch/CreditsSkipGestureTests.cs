using System;
using System.Collections.Generic;

// 只验证真实纯逻辑类，不启动Unity、片尾场景或任何存档入口。
public static class CreditsSkipGestureTests
{
    private static void Check(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
    private static void Progress(CreditsSkipGesture gesture, float expected)
    {
        Check(Math.Abs(gesture.Progress - expected) < 0.00001f, "长按进度不符");
    }
    private static CreditsSkipGesture Ready(double start)
    {
        var gesture = new CreditsSkipGesture();
        Check(!gesture.Tick(true, true, false, start), "松开不应触发");
        Check(!gesture.Tick(true, true, true, start), "首次按下不应触发");
        return gesture;
    }
    private static void InvalidTime(double invalid)
    {
        var gesture = Ready(10);
        gesture.Tick(true, true, true, 10.5);
        Check(!gesture.Tick(true, true, true, invalid), "无效时钟不应触发");
        Progress(gesture, 0);
        Check(!gesture.Tick(true, true, true, 20), "无效时钟后保持按住不能重新计时");
        Progress(gesture, 0);
        gesture.Tick(true, true, false, 21);
        gesture.Tick(true, true, true, 22);
        Check(gesture.Tick(true, true, true, 23), "释放后应允许新的有效手势");
    }
    private static Dictionary<string, Action> Cases()
    {
        return new Dictionary<string, Action> {
            { "short_press", delegate {
                var gesture = Ready(0);
                Check(!gesture.Tick(true, true, true, 0.2), "短按不应跳过");
                Check(!gesture.Tick(true, true, false, 0.3), "短按松开不应跳过");
                Progress(gesture, 0);
            } },
            { "one_second_boundary", delegate {
                Check(CreditsSkipGesture.HoldSeconds == 1.0, "长按门槛必须为1秒");
                var gesture = Ready(10);
                Check(!gesture.Tick(true, true, true, 10.999), "不足1秒不应触发");
                Check(gesture.Tick(true, true, true, 11), "满1秒应触发");
                Progress(gesture, 1);
            } },
            { "quarter_and_half_progress", delegate {
                var gesture = Ready(5);
                Check(!gesture.Tick(true, true, true, 5.25), "25%不应触发");
                Progress(gesture, 0.25f);
                Check(!gesture.Tick(true, true, true, 5.5), "50%不应触发");
                Progress(gesture, 0.5f);
            } },
            { "release_cancels_progress", delegate {
                var gesture = Ready(0);
                gesture.Tick(true, true, true, 0.75);
                Check(!gesture.Tick(true, true, false, 0.8), "松开应取消");
                Progress(gesture, 0);
                gesture.Tick(true, true, true, 0.9);
                Check(!gesture.Tick(true, true, true, 1.15), "新一轮不得继承上轮进度");
                Progress(gesture, 0.25f);
            } },
            { "held_on_entry_requires_release", delegate {
                var gesture = new CreditsSkipGesture();
                Check(!gesture.Tick(true, true, true, 0), "进场已按住不能开始");
                Check(!gesture.Tick(true, true, true, 10), "进场按住再久也不能触发");
                Progress(gesture, 0);
                gesture.Tick(true, true, false, 11);
                gesture.Tick(true, true, true, 12);
                Check(gesture.Tick(true, true, true, 13), "释放重按后应触发");
            } },
            { "focus_loss_cancels", delegate {
                var gesture = Ready(0);
                gesture.Tick(true, true, true, 0.5);
                Check(!gesture.Tick(true, false, true, 0.6), "失焦不能触发");
                Progress(gesture, 0);
                Check(!gesture.Tick(true, false, true, 500), "后台不能累计");
                Check(!gesture.Tick(true, true, true, 501), "恢复焦点且按住不能触发");
                Progress(gesture, 0);
            } },
            { "focus_return_requires_fresh_press", delegate {
                var gesture = Ready(0);
                gesture.Tick(true, false, false, 0.5);
                Check(!gesture.Tick(true, true, true, 2), "后台松开不能给前台手势上膛");
                gesture.Tick(true, true, false, 3);
                gesture.Tick(true, true, true, 4);
                Check(gesture.Tick(true, true, true, 5), "前台释放重按应触发");
            } },
            { "one_shot", delegate {
                var gesture = Ready(0);
                Check(gesture.Tick(true, true, true, 1), "首次长按应触发");
                Check(!gesture.Tick(true, true, true, 2), "保持按住不能重复触发");
                Check(!gesture.Tick(true, true, false, 3), "触发后松开不能再次触发");
                Check(!gesture.Tick(true, true, true, 5), "同一轮重新长按不能再次触发");
            } },
            { "reset_starts_new_round", delegate {
                var gesture = Ready(0);
                Check(gesture.Tick(true, true, true, 1), "第一轮应触发");
                gesture.Reset(); Progress(gesture, 0);
                Check(!gesture.Tick(true, true, true, 2), "重置后已按住仍须释放");
                gesture.Tick(true, true, false, 3);
                gesture.Tick(true, true, true, 4);
                Check(gesture.Tick(true, true, true, 5), "重置后新一轮应触发");
            } },
            { "clock_rollback_restarts", delegate {
                var gesture = Ready(10);
                gesture.Tick(true, true, true, 10.5);
                Check(!gesture.Tick(true, true, true, 9), "时钟回退不能触发");
                Progress(gesture, 0);
                Check(!gesture.Tick(true, true, true, 9.5), "回退后应重新累计");
                Progress(gesture, 0.5f);
                Check(gesture.Tick(true, true, true, 10), "回退后完整1秒应触发");
            } },
            { "clock_rollback_after_progress", delegate {
                var gesture = Ready(10);
                gesture.Tick(true, true, true, 10.5);
                Check(!gesture.Tick(true, true, true, 10.25), "进度内时钟回退不能触发");
                Progress(gesture, 0);
                Check(!gesture.Tick(true, true, true, 10.75), "回退后应重新累计而非继承旧起点");
                Progress(gesture, 0.5f);
                Check(gesture.Tick(true, true, true, 11.25), "回退后重新完整1秒应触发");
            } },
            { "subsecond_rounding_cannot_trigger", delegate {
                var gesture = Ready(0);
                Check(!gesture.Tick(true, true, true, 1.0 - 1e-9), "进度取float不能让不足1秒提前触发");
                Check(gesture.Tick(true, true, true, 1), "双精度满1秒才应触发");
            } },
            { "nan_time", delegate { InvalidTime(Double.NaN); } },
            { "positive_infinity", delegate { InvalidTime(Double.PositiveInfinity); } },
            { "negative_infinity", delegate { InvalidTime(Double.NegativeInfinity); } },
            { "negative_time", delegate { InvalidTime(-1); } },
            { "inactive_cancels", delegate {
                var gesture = Ready(0);
                gesture.Tick(true, true, true, 0.5);
                Check(!gesture.Tick(false, true, true, 0.75), "离开片尾不能触发");
                Progress(gesture, 0);
                Check(!gesture.Tick(true, true, true, 5), "重入片尾按住不能触发");
            } },
            { "inactive_cannot_arm", delegate {
                var gesture = new CreditsSkipGesture();
                Check(!gesture.Tick(false, true, false, 0), "片尾外松开不能上膛");
                Check(!gesture.Tick(false, true, true, 1), "片尾外长按不能触发");
                Check(!gesture.Tick(false, true, true, 10), "片尾外持续按住不能触发");
                Check(!gesture.Tick(true, true, true, 11), "片尾外输入不能传入片尾");
                Progress(gesture, 0);
            } },
            { "long_frame_clamps_progress", delegate {
                var gesture = Ready(1);
                Check(gesture.Tick(true, true, true, 100), "长帧超过门槛应触发一次");
                Progress(gesture, 1);
                Check(!gesture.Tick(true, true, true, 1000), "长帧之后不可重复");
            } },
            { "reset_clears_partial_hold", delegate {
                var gesture = Ready(0);
                gesture.Tick(true, true, true, 0.75);
                gesture.Reset(); Progress(gesture, 0);
                Check(!gesture.Tick(true, true, true, 1), "Reset不能继承部分长按");
                Check(!gesture.Tick(true, true, true, 2), "Reset后按住不能自动重新累计");
            } },
        };
    }
    public static int Main(string[] args)
    {
        try
        {
            // 故意失败仅用于验证异常走标准错误及退出码，不交给Windows错误报告。
            if (args.Length == 1 && args[0] == "--check-error-handler") throw new InvalidOperationException("测试终端错误处理");
            var cases = Cases();
            if (args.Length == 1)
            {
                Action test;
                if (!cases.TryGetValue(args[0], out test)) throw new ArgumentException("未知用例");
                test();
                Console.WriteLine("{\"pure_cases\":1,\"passed\":true}");
                return 0;
            }
            foreach (var test in cases.Values) test();
            Console.WriteLine("{\"pure_cases\":" + cases.Count + ",\"passed\":true}");
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine(error.GetType().Name + ": " + error.Message);
            return 1;
        }
    }
}
