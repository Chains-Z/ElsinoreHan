using System;
using System.Collections.Generic;

// 纯CPU解码本游戏DXT5书页，并只在英文笔画掩码内做邻域插值；不复制矩形纸块。
public static class BookPaperReconstruction
{
    public sealed class Result
    {
        public byte[] pixels;
        public int[] mask;
        public int iterations;
        public float residual;
    }

    private static uint Rgb565(int value)
    {
        int r = (value >> 11) & 31, g = (value >> 5) & 63, b = value & 31;
        return (uint)(((r << 3) | (r >> 2)) | (((g << 2) | (g >> 4)) << 8) | (((b << 3) | (b >> 2)) << 16));
    }
    private static uint Mix(uint a, uint b, int wa, int wb)
    {
        uint result = 0;
        for (int shift = 0; shift <= 16; shift += 8)
            result |= (uint)((((a >> shift) & 255) * wa + ((b >> shift) & 255) * wb) / 3) << shift;
        return result;
    }
    public static byte[] DecodeDxt5(byte[] blocks, int width, int height)
    {
        if (width < 4 || height < 4 || width % 4 != 0 || height % 4 != 0 || blocks.Length != width * height)
            throw new ArgumentException("DXT5书页尺寸或块长度不符");
        var pixels = new byte[checked(width * height * 4)];
        var alpha = new byte[8];
        int offset = 0;
        for (int by = 0; by < height; by += 4) for (int bx = 0; bx < width; bx += 4, offset += 16)
        {
            alpha[0] = blocks[offset]; alpha[1] = blocks[offset + 1];
            if (alpha[0] > alpha[1])
                for (int i = 2; i < 8; i++) alpha[i] = (byte)(((8 - i) * alpha[0] + (i - 1) * alpha[1]) / 7);
            else
            {
                for (int i = 2; i < 6; i++) alpha[i] = (byte)(((6 - i) * alpha[0] + (i - 1) * alpha[1]) / 5);
                alpha[6] = 0; alpha[7] = 255;
            }
            ulong ai = 0;
            for (int i = 0; i < 6; i++) ai |= (ulong)blocks[offset + 2 + i] << (8 * i);
            uint c0 = Rgb565(blocks[offset + 8] | blocks[offset + 9] << 8);
            uint c1 = Rgb565(blocks[offset + 10] | blocks[offset + 11] << 8);
            uint c2 = Mix(c0, c1, 2, 1), c3 = Mix(c0, c1, 1, 2);
            uint ci = (uint)(blocks[offset + 12] | blocks[offset + 13] << 8 | blocks[offset + 14] << 16 | blocks[offset + 15] << 24);
            for (int y = 0; y < 4; y++) for (int x = 0; x < 4; x++)
            {
                int selector = (int)(ci & 3); uint color = selector == 0 ? c0 : selector == 1 ? c1 : selector == 2 ? c2 : c3;
                int p = ((by + y) * width + bx + x) * 4;
                pixels[p] = (byte)color; pixels[p + 1] = (byte)(color >> 8); pixels[p + 2] = (byte)(color >> 16);
                pixels[p + 3] = alpha[(int)(ai & 7)]; ci >>= 2; ai >>= 3;
            }
        }
        return pixels;
    }

    public static Result Reconstruct(byte[] original, int width, int height)
    {
        bool spread = width == 2048 && height == 1400;
        bool unlock = width == 916 && height == 1252;
        if ((!spread && !unlock) || original.Length != width * height * 4)
            throw new ArgumentException("未核查的书页像素布局");
        var seeds = new HashSet<int>();
        // 原始完整纹理坐标，左上原点；不能使用Sprite裁剪后PNG的1322高度。
        int[][] regions = spread
            ? new int[][] { new int[] { 1350, 240, 1650, 334 }, new int[] { 1425, 458, 1555, 548 } }
            : new int[][] { new int[] { 345, 180, 605, 263 }, new int[] { 410, 398, 515, 480 } };
        foreach (var box in regions)
            for (int top = box[1]; top < box[3]; top++) for (int x = box[0]; x < box[2]; x++)
            {
                int p = (height - 1 - top) * width + x, at = p * 4;
                if (original[at + 3] == 255 && Math.Max(original[at], Math.Max(original[at + 1], original[at + 2])) < 150) seeds.Add(p);
            }
        if (seeds.Count < 2500 || seeds.Count > 5000) throw new InvalidOperationException("原书页英文笔画数量与来源不符");
        var mask = new HashSet<int>();
        foreach (int p in seeds)
            for (int dy = -2; dy <= 2; dy++) for (int dx = -2; dx <= 2; dx++) mask.Add(p + dy * width + dx);
        int[] indices = new int[mask.Count]; mask.CopyTo(indices); Array.Sort(indices);
        var lookup = new Dictionary<int, int>();
        for (int i = 0; i < indices.Length; i++) lookup.Add(indices[i], i);
        var values = new float[indices.Length * 3];
        for (int i = 0; i < indices.Length; i++) for (int channel = 0; channel < 3; channel++)
        {
            int p = indices[i], left = p, right = p;
            while (mask.Contains(left)) left--;
            while (mask.Contains(right)) right++;
            values[i * 3 + channel] = (original[left * 4 + channel] + original[right * 4 + channel]) * 0.5f;
        }
        var result = new Result { pixels = (byte[])original.Clone(), mask = indices };
        int[] offsets = { -1, 1, -width, width };
        for (int iteration = 0; iteration < 500; iteration++)
        {
            float residual = 0;
            for (int i = 0; i < indices.Length; i++) for (int channel = 0; channel < 3; channel++)
            {
                float sum = 0;
                foreach (int delta in offsets)
                {
                    int neighbor;
                    sum += lookup.TryGetValue(indices[i] + delta, out neighbor) ? values[neighbor * 3 + channel] : original[(indices[i] + delta) * 4 + channel];
                }
                float next = sum * 0.25f;
                residual = Math.Max(residual, Math.Abs(next - values[i * 3 + channel]));
                values[i * 3 + channel] = next;
            }
            result.iterations = iteration + 1; result.residual = residual;
            if (residual < 0.002f) break;
        }
        for (int i = 0; i < indices.Length; i++) for (int channel = 0; channel < 3; channel++)
            result.pixels[indices[i] * 4 + channel] = (byte)Math.Round(values[i * 3 + channel]);
        return result;
    }
}
