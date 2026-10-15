using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

// 背景上的两行英文没有文本控件；以原书页空白区域覆盖印字，另建可切换的斜体中文。
public sealed class EndingBookLabels : MonoBehaviour
{
    private static readonly List<EndingBookLabels> instances = new List<EndingBookLabels>();
    private static bool translated = true;
    private GameObject layer;
    private Image book;
    private GameObject content;
    private static readonly BindingFlags fields = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;

    public static void Apply(Harmony harmony)
    {
        Type type = AccessTools.TypeByName("Elsinore.Ui.EndingSelectUI");
        harmony.Patch(AccessTools.Method(type, "populate"), postfix: new HarmonyMethod(typeof(EndingBookLabels), "AfterPopulate"));
    }

    public static void SetTranslated(bool value)
    {
        translated = value;
        for (int index = instances.Count - 1; index >= 0; index--)
        {
            if (instances[index] == null) instances.RemoveAt(index);
            else instances[index].Refresh();
        }
    }

    public static void AfterPopulate(Component __instance)
    {
        var type = __instance.GetType();
        var image = (Image)type.GetField("book", fields).GetValue(__instance);
        if (image.sprite == null || image.sprite.name != "UI_Book_BackGround2") return;
        var labels = image.GetComponent<EndingBookLabels>();
        if (labels == null)
        {
            labels = image.gameObject.AddComponent<EndingBookLabels>();
            labels.book = image;
            labels.content = (GameObject)type.GetField("contentPanel", fields).GetValue(__instance);
            labels.Create((TMP_Text)type.GetField("sacrificeWhatText", fields).GetValue(__instance));
            instances.Add(labels);
        }
        labels.Refresh();
    }

    private void Create(TMP_Text template)
    {
        if (book.type != Image.Type.Simple || book.preserveAspect || book.sprite.packingRotation != SpritePackingRotation.None)
            throw new InvalidOperationException("命运书页的贴图映射与已核查资源不一致");
        layer = new GameObject("ElsinoreHanBookLabels", typeof(RectTransform));
        var rect = layer.GetComponent<RectTransform>();
        rect.SetParent(book.transform, false);
        rect.anchorMin = Vector2.zero; rect.anchorMax = Vector2.one;
        rect.offsetMin = Vector2.zero; rect.offsetMax = Vector2.zero;
        CreateRow("Sacrifice", new Rect(0.64f, 0.795f, 0.19f, 0.075f), new Rect(0.64f, 0.87f, 0.19f, 0.075f), template);
        CreateRow("for", new Rect(0.69f, 0.625f, 0.10f, 0.075f), new Rect(0.69f, 0.425f, 0.10f, 0.075f), template);
    }

    private void CreateRow(string source, Rect target, Rect sample, TMP_Text template)
    {
        var cover = new GameObject(source + "Cover", typeof(RectTransform), typeof(BookLabelCover));
        var rect = cover.GetComponent<RectTransform>();
        rect.SetParent(layer.transform, false);
        rect.anchorMin = new Vector2(target.xMin, target.yMin); rect.anchorMax = new Vector2(target.xMax, target.yMax);
        rect.offsetMin = Vector2.zero; rect.offsetMax = Vector2.zero;
        var graphic = cover.GetComponent<BookLabelCover>();
        graphic.raycastTarget = false;
        graphic.Configure(book.sprite, sample);
        var label = new GameObject(source + "Text", typeof(RectTransform), typeof(TextMeshProUGUI));
        var textRect = label.GetComponent<RectTransform>();
        textRect.SetParent(cover.transform, false);
        textRect.anchorMin = Vector2.zero; textRect.anchorMax = Vector2.one;
        // 中文字体行距大于印字区域；扩展不可见排版框，字形仍居中，不缩小字号。
        textRect.offsetMin = new Vector2(0, -template.fontSize * 0.25f);
        textRect.offsetMax = new Vector2(0, template.fontSize * 0.25f);
        var text = label.GetComponent<TextMeshProUGUI>();
        text.font = template.font;
        text.fontSize = template.fontSize;
        text.fontStyle = FontStyles.Normal;
        text.color = new Color(0.035f, 0.03f, 0.02f, 1);
        text.alignment = TextAlignmentOptions.Center;
        text.enableWordWrapping = false; text.raycastTarget = false;
        text.text = "<i>" + source + "</i>";
    }

    private void Refresh()
    {
        if (layer != null) layer.SetActive(translated && content != null && content.activeSelf && book.sprite != null && book.sprite.name == "UI_Book_BackGround2");
    }

    private void LateUpdate() { Refresh(); }
    private void OnDestroy() { instances.Remove(this); }
}

// 只采样原贴图无字区域；3像素羽化位于英文笔画以外，保留分隔线及纸面层次。
public sealed class BookLabelCover : MaskableGraphic
{
    private Sprite source;
    private Rect sample;
    public override Texture mainTexture { get { return source == null ? Texture2D.whiteTexture : source.texture; } }
    public void Configure(Sprite sprite, Rect area) { source = sprite; sample = area; SetAllDirty(); }

    protected override void OnPopulateMesh(VertexHelper mesh)
    {
        mesh.Clear();
        if (source == null) return;
        Rect rect = GetPixelAdjustedRect();
        Rect tex = source.textureRect;
        float[] xs = { 0, 3f / source.rect.width / (rectTransform.anchorMax.x - rectTransform.anchorMin.x), 1f - 3f / source.rect.width / (rectTransform.anchorMax.x - rectTransform.anchorMin.x), 1 };
        float[] ys = { 0, 3f / source.rect.height / (rectTransform.anchorMax.y - rectTransform.anchorMin.y), 1f - 3f / source.rect.height / (rectTransform.anchorMax.y - rectTransform.anchorMin.y), 1 };
        for (int y = 0; y < 4; y++) for (int x = 0; x < 4; x++)
        {
            var uv = new Vector2((tex.x + (sample.x + sample.width * xs[x]) * tex.width) / source.texture.width,
                                 (tex.y + (sample.y + sample.height * ys[y]) * tex.height) / source.texture.height);
            var tint = new Color(1, 1, 1, x == 0 || x == 3 || y == 0 || y == 3 ? 0 : 1);
            mesh.AddVert(new Vector3(rect.x + rect.width * xs[x], rect.y + rect.height * ys[y]), tint, uv);
        }
        for (int y = 0; y < 3; y++) for (int x = 0; x < 3; x++)
        {
            int a = y * 4 + x;
            mesh.AddTriangle(a, a + 4, a + 5); mesh.AddTriangle(a, a + 5, a + 1);
        }
    }
}
