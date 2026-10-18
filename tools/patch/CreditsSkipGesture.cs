using System;

// 与Unity无关的长按判定；只接收片尾范围、焦点、Ctrl状态和单调时钟。
public sealed class CreditsSkipGesture
{
    public const double HoldSeconds = 1.0;
    private bool armed, pressed, triggered;
    private double started, lastNow;
    public float Progress { get; private set; }

    public void Reset()
    {
        armed = pressed = triggered = false;
        started = lastNow = 0;
        Progress = 0;
    }
    public bool Tick(bool active, bool focused, bool controlHeld, double now)
    {
        return Tick(active, focused, controlHeld, now, true);
    }
    public bool Tick(bool active, bool focused, bool controlHeld, double now, bool presentationReady)
    {
        if (triggered) return false;
        if (!active || !focused || Double.IsNaN(now) || Double.IsInfinity(now) || now < 0)
        {
            armed = pressed = false;
            Progress = 0;
            return false;
        }
        if (now < lastNow)
        {
            pressed = false;
            Progress = 0;
        }
        lastNow = now;
        if (!controlHeld)
        {
            armed = true;
            pressed = false;
            Progress = 0;
            return false;
        }
        // 片尾出现或重新获得焦点时已按住的Ctrl不算新的跳过手势。
        if (!armed) return false;
        // 可以记住加载期间新按下的Ctrl，但界面未就绪时不累计黑屏中的时间。
        if (!presentationReady)
        {
            pressed = false;
            Progress = 0;
            return false;
        }
        if (!pressed || now < started)
        {
            started = now;
            pressed = true;
            Progress = 0;
            return false;
        }
        Progress = (float)Math.Min(1.0, (now - started) / HoldSeconds);
        if (now - started < HoldSeconds) return false;
        triggered = true;
        return true;
    }
}
