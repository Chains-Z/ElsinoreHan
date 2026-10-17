using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using HarmonyLib;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

// 从玩家自己的原始书页重建去字纹理；新增文字与正文共享层级，受原翻页图遮挡。
public sealed class EndingBookLabels : MonoBehaviour
{
    public const int PaperWidth = 2048, PaperHeight = 1400;
    public const long PaperStreamOffset = 371948484;
    public const string PaperStreamSha256 = "7bd5234ad6cf2d6b3dfaa78b8a140c506f1ad4f9e435f6c75810188fafdc35fb";
    public const int UnlockWidth = 916, UnlockHeight = 1252;
    public const long UnlockStreamOffset = 95762528;
    public const string UnlockStreamSha256 = "4f29559662c2813ad68de49fbe63ecfea23d03d9ce48e9f74fc4b0c2d95c667b";
    private static readonly List<EndingBookLabels> instances = new List<EndingBookLabels>();
    private static readonly BindingFlags fields = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
    private static bool translated = true;
    private GameObject layer;
    private Image book;
    private GameObject content;
    private TMP_Text template;
    private TMP_Text first, second;
    private bool failed;
    private int width = PaperWidth, height = PaperHeight;
    private float firstTop = 288.5f, secondTop = 505.5f;
    public Sprite OriginalSprite { get; private set; }
    public Sprite CleanSprite { get; private set; }
    public int RepairMaskCount { get; private set; }
    public float ReconstructionResidual { get; private set; }

    public static void Apply(Harmony harmony)
    {
        Type type = AccessTools.TypeByName("Elsinore.Ui.EndingSelectUI");
        harmony.Patch(AccessTools.Method(type, "populate"), postfix: new HarmonyMethod(typeof(EndingBookLabels), "AfterPopulate"));
        harmony.Patch(AccessTools.Method(AccessTools.TypeByName("Elsinore.Ui.GameOverUI"), "Activate"),
            postfix: new HarmonyMethod(typeof(EndingBookLabels), "AfterGameOver"));
    }
    public static void SetTranslated(bool value)
    {
        translated = value;
        for (int index = instances.Count - 1; index >= 0; index--)
            if (instances[index] == null) instances.RemoveAt(index); else instances[index].Refresh();
    }
    public static void AfterPopulate(Component __instance)
    {
        var type = __instance.GetType();
        var image = (Image)type.GetField("book", fields).GetValue(__instance);
        Attach(image, (GameObject)type.GetField("contentPanel", fields).GetValue(__instance),
            (TMP_Text)type.GetField("sacrificeWhatText", fields).GetValue(__instance), false);
    }
    public static void AfterGameOver(Component __instance)
    {
        var type = __instance.GetType();
        if (type.GetField("activeEnding", fields).GetValue(__instance) == null) return;
        var image = (Image)type.GetField("EndingUnlockTexture", fields).GetValue(__instance);
        var page = (Image)type.GetField("EndingUnlockPage", fields).GetValue(__instance);
        Attach(image, page.gameObject, (TMP_Text)type.GetField("EndingTitleWhat", fields).GetValue(__instance), true);
    }
    private static void Attach(Image image, GameObject content, TMP_Text template, bool unlock)
    {
        var labels = image.GetComponent<EndingBookLabels>();
        if (labels == null)
        {
            if (image.sprite == null || image.sprite.name != (unlock ? "UI_Book_Unlock" : "UI_Book_BackGround2")) return;
            labels = image.gameObject.AddComponent<EndingBookLabels>();
            labels.book = image;
            labels.content = content;
            labels.template = template;
            if (unlock)
            {
                labels.width = UnlockWidth; labels.height = UnlockHeight;
                labels.firstTop = 222f; labels.secondTop = 439f;
            }
            instances.Add(labels);
            try { labels.Create(); }
            catch (Exception error)
            {
                labels.failed = true;
                if (labels.layer != null) labels.layer.SetActive(false);
                Debug.LogWarning("命运书页重建失败，保留原始背景：" + error.GetType().Name);
            }
        }
        labels.Refresh();
    }
    public static byte[] ReadSourcePixels()
    {
        return ReadSourcePixels(false);
    }
    private static byte[] ReadSourcePixels(bool unlock)
    {
        int width = unlock ? UnlockWidth : PaperWidth, height = unlock ? UnlockHeight : PaperHeight;
        var blocks = new byte[width * height];
        string path = Path.Combine(Application.dataPath, "sharedassets1.assets.resS");
        using (var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read))
        {
            stream.Position = unlock ? UnlockStreamOffset : PaperStreamOffset;
            int count = 0;
            while (count < blocks.Length)
            {
                int got = stream.Read(blocks, count, blocks.Length - count);
                if (got == 0) throw new EndOfStreamException("书页原始像素块不完整");
                count += got;
            }
        }
        using (var hash = SHA256.Create())
            if (BitConverter.ToString(hash.ComputeHash(blocks)).Replace("-", "").ToLowerInvariant() != (unlock ? UnlockStreamSha256 : PaperStreamSha256))
                throw new InvalidDataException("书页原始像素哈希不符");
        return BookPaperReconstruction.DecodeDxt5(blocks, width, height);
    }
    private void Create()
    {
        OriginalSprite = book.sprite;
        if (book.type != Image.Type.Simple || book.preserveAspect || OriginalSprite.rect.width != width || OriginalSprite.rect.height != height)
            throw new InvalidOperationException("未核查的完整书页映射");
        var repair = BookPaperReconstruction.Reconstruct(ReadSourcePixels(width == UnlockWidth), width, height);
        RepairMaskCount = repair.mask.Length; ReconstructionResidual = repair.residual;
        var texture = new Texture2D(width, height, TextureFormat.RGBA32, false);
        texture.name = "ElsinoreHan Book Paper"; texture.hideFlags = HideFlags.DontSave;
        texture.filterMode = OriginalSprite.texture.filterMode; texture.wrapMode = TextureWrapMode.Clamp;
        texture.LoadRawTextureData(repair.pixels); texture.Apply(false, false);
        CleanSprite = Sprite.Create(texture, new Rect(0, 0, width, height), new Vector2(OriginalSprite.pivot.x / width, OriginalSprite.pivot.y / height),
            OriginalSprite.pixelsPerUnit, 0, SpriteMeshType.FullRect, OriginalSprite.border);
        CleanSprite.name = "ElsinoreHan Book Paper"; CleanSprite.hideFlags = HideFlags.DontSave;
        layer = new GameObject("ElsinoreHanBookLabels", typeof(RectTransform));
        var rect = layer.GetComponent<RectTransform>();
        rect.SetParent(template.transform.parent, false);
        rect.anchorMin = Vector2.zero; rect.anchorMax = Vector2.one;
        rect.offsetMin = Vector2.zero; rect.offsetMax = Vector2.zero;
        first = CreateText("Sacrifice"); second = CreateText("for");
        PositionLabels();
    }
    private TMP_Text CreateText(string source)
    {
        var label = new GameObject(source + "Text", typeof(RectTransform), typeof(TextMeshProUGUI));
        var rect = label.GetComponent<RectTransform>(); rect.SetParent(layer.transform, false);
        rect.anchorMin = rect.anchorMax = new Vector2(0.5f, 0.5f); rect.sizeDelta = new Vector2(600, 160);
        var text = label.GetComponent<TextMeshProUGUI>();
        text.font = template.font; text.fontSize = template.fontSize * 0.8f;
        text.fontStyle = FontStyles.Normal; text.color = template.color;
        text.alignment = TextAlignmentOptions.Center; text.enableWordWrapping = false; text.raycastTarget = false;
        text.text = "<i>" + source + "</i>";
        return text;
    }
    private void PositionLabels()
    {
        Rect paper = book.rectTransform.rect;
        // 两种入口各取完整纹理的行中心，列中心沿用各自的原生关键词。
        float column = book.rectTransform.InverseTransformPoint(template.transform.TransformPoint(Vector3.zero)).x;
        first.rectTransform.position = book.rectTransform.TransformPoint(new Vector3(column, paper.yMax - paper.height * (firstTop / height), 0));
        second.rectTransform.position = book.rectTransform.TransformPoint(new Vector3(column, paper.yMax - paper.height * (secondTop / height), 0));
    }
    private void Refresh()
    {
        if (failed || layer == null) return;
        bool visible = translated && content != null && content.activeSelf;
        var expected = visible ? CleanSprite : OriginalSprite;
        if (book.sprite != expected) book.sprite = expected;
        layer.SetActive(visible);
        PositionLabels();
    }
    private void LateUpdate() { Refresh(); }
    private void OnDestroy()
    {
        instances.Remove(this);
        if (CleanSprite != null) { var texture = CleanSprite.texture; Destroy(CleanSprite); Destroy(texture); }
        if (layer != null) Destroy(layer);
    }
}
