using System;

// 复现原游戏 autoTileImages 的几何公式，保留70%重叠与方形墨迹片。
public static class SplotchTileGeometry
{
    public static int Count(float width, float height)
    {
        if (float.IsNaN(width) || float.IsInfinity(width) || float.IsNaN(height)
            || float.IsInfinity(height) || width <= 0 || height <= 0)
            throw new ArgumentOutOfRangeException("width", "背景尺寸必须为有限正数。");
        if (width <= height) return 1;
        float step = (1f - 0.7f) * height;
        return checked((int)Math.Ceiling((width - 0.7f * height) / step));
    }

    public static float Center(int index, int count, float height)
    {
        float step = (1f - 0.7f) * height;
        float span = count * step + 0.7f * height;
        return (height - span) / 2f + index * step;
    }
}
