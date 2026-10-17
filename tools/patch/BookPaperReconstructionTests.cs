using System;
using System.IO;

// 压缩格式与异常边界的纯逻辑回归；真实书页资源由Python消费者核验。
public static class BookPaperReconstructionTests
{
    private static void Check(bool result) { if (!result) throw new Exception("书页像素逻辑断言失败"); }
    public static int Main(string[] args)
    {
        if (args.Length >= 2)
        {
            bool unlock = args.Length == 3 && args[2] == "unlock";
            int width = unlock ? 916 : 2048, height = unlock ? 1252 : 1400;
            byte[] original = BookPaperReconstruction.DecodeDxt5(File.ReadAllBytes(args[0]), width, height);
            var result = BookPaperReconstruction.Reconstruct(original, width, height);
            File.WriteAllBytes(args[1] + "-source.rgba", original);
            File.WriteAllBytes(args[1] + "-clean.rgba", result.pixels);
            File.WriteAllLines(args[1] + "-mask.txt", Array.ConvertAll(result.mask, value => value.ToString()));
            Console.WriteLine("{\"mask\":" + result.mask.Length + ",\"iterations\":" + result.iterations + ",\"residual\":" + result.residual.ToString(System.Globalization.CultureInfo.InvariantCulture) + "}");
            return 0;
        }
        var block = new byte[16]; block[0] = 255; block[8] = 0; block[9] = 248;
        var red = BookPaperReconstruction.DecodeDxt5(block, 4, 4);
        for (int i = 0; i < 16; i++) Check(red[i * 4] == 255 && red[i * 4 + 1] == 0 && red[i * 4 + 2] == 0 && red[i * 4 + 3] == 255);
        block[0] = 0; block[1] = 255; block[2] = 7;
        Check(BookPaperReconstruction.DecodeDxt5(block, 4, 4)[3] == 255);
        block[0] = 255; block[1] = 0; block[2] = 2;
        Check(BookPaperReconstruction.DecodeDxt5(block, 4, 4)[3] == 218);
        bool rejected = false;
        try { BookPaperReconstruction.DecodeDxt5(new byte[15], 4, 4); } catch (ArgumentException) { rejected = true; }
        Check(rejected); rejected = false;
        try { BookPaperReconstruction.DecodeDxt5(block, 5, 4); } catch (ArgumentException) { rejected = true; }
        Check(rejected); rejected = false;
        try { BookPaperReconstruction.Reconstruct(new byte[4], 1, 1); } catch (ArgumentException) { rejected = true; }
        Check(rejected); rejected = false;
        try { BookPaperReconstruction.Reconstruct(new byte[2048 * 1400 * 4], 2048, 1400); } catch (InvalidOperationException) { rejected = true; }
        Check(rejected);
        rejected = false;
        try { BookPaperReconstruction.Reconstruct(new byte[916 * 1252 * 4], 916, 1252); } catch (InvalidOperationException) { rejected = true; }
        Check(rejected);
        Console.WriteLine("{\"pure_cases\":8,\"passed\":true}");
        return 0;
    }
}
