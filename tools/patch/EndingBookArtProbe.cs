using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

// 导出真实UI纹理、字形网格与图层供离线软件合成检查；不是GPU截图。
public static class EndingBookArtProbe
{
    [Serializable] public class Vertex { public float x, y, u, v; }
    [Serializable] public class Picture
    {
        public string texture, raw_file;
        public int width, height, depth;
        public Vertex[] vertices;
        public int[] triangles;
    }
    [Serializable] public class Glyph
    {
        public string text, atlas;
        public int atlas_width, atlas_height, depth;
        public float[] color;
        public float threshold;
        public Vertex[] vertices;
    }
    [Serializable] public class Scene
    {
        public int width = 2048, height = 1400;
        public string state;
        public Picture[] pictures;
        public Glyph[] glyphs;
    }
    private const BindingFlags flags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
    private static Vertex Point(Image paper, Transform from, Vector3 position, Vector2 uv)
    {
        Vector3 local = paper.rectTransform.InverseTransformPoint(from.TransformPoint(position));
        Rect rect = paper.rectTransform.rect;
        return new Vertex { x = (local.x - rect.x) / rect.width * 2048, y = (rect.yMax - local.y) / rect.height * 1400, u = uv.x, v = uv.y };
    }
    private static Picture ImageData(Image image, Image paper)
    {
        var helper = new VertexHelper(); var mesh = new Mesh();
        try
        {
            typeof(Image).GetMethod("OnPopulateMesh", flags, null, new Type[] { typeof(VertexHelper) }, null).Invoke(image, new object[] { helper });
            helper.FillMesh(mesh);
            var points = new Vertex[mesh.vertexCount];
            for (int i = 0; i < points.Length; i++) points[i] = Point(paper, image.transform, mesh.vertices[i], mesh.uv[i]);
            return new Picture { texture = image.sprite.texture.name, width = image.sprite.texture.width, height = image.sprite.texture.height,
                depth = image.depth, vertices = points, triangles = mesh.triangles };
        }
        finally { helper.Dispose(); UnityEngine.Object.DestroyImmediate(mesh); }
    }
    public static void Dump(Component canvas, Image paper, string directory, string state)
    {
        Canvas.ForceUpdateCanvases();
        var images = new List<Picture>();
        var texts = new List<Glyph>();
        Type type = canvas.GetType();
        var current = ImageData(paper, paper);
        current.raw_file = paper.sprite.name == "UI_Book_BackGround2" ? "paper-source.rgba" : "paper-clean.rgba";
        images.Add(current);
        foreach (string field in new string[] { "icon", "Background" })
        {
            var image = (Image)type.GetField(field, flags).GetValue(canvas);
            if (image.gameObject.activeInHierarchy && image.sprite != null) images.Add(ImageData(image, paper));
        }
        foreach (TMP_Text text in canvas.GetComponentsInChildren<TMP_Text>())
        {
            if (!text.gameObject.activeInHierarchy || text.name == "Tooltip" || text.GetComponentInParent<Button>() != null) continue;
            text.ForceMeshUpdate();
            for (int index = 0; index < text.textInfo.characterCount; index++)
            {
                var ch = text.textInfo.characterInfo[index]; if (!ch.isVisible) continue;
                var atlas = ch.fontAsset.atlasTextures[0];
                string name = "book-atlas-" + atlas.GetInstanceID() + ".bin";
                if (!File.Exists(Path.Combine(directory, name))) File.WriteAllBytes(Path.Combine(directory, name), atlas.GetRawTextureData());
                var mesh = text.textInfo.meshInfo[ch.materialReferenceIndex];
                var points = new Vertex[4];
                for (int i = 0; i < 4; i++) points[i] = Point(paper, text.transform, mesh.vertices[ch.vertexIndex + i], mesh.uvs0[ch.vertexIndex + i]);
                Color32 tint = mesh.colors32[ch.vertexIndex];
                Material material = text.fontSharedMaterials[ch.materialReferenceIndex];
                float weight = material.GetFloat((ch.style & FontStyles.Bold) != 0 ? "_WeightBold" : "_WeightNormal") / 4f;
                float ratio = material.HasProperty("_ScaleRatioA") ? material.GetFloat("_ScaleRatioA") : 1;
                texts.Add(new Glyph { text = ch.character.ToString(), atlas = name, atlas_width = atlas.width, atlas_height = atlas.height,
                    depth = text.depth, color = new float[] { tint.r / 255f, tint.g / 255f, tint.b / 255f, tint.a / 255f },
                    threshold = 0.5f - (weight + material.GetFloat("_FaceDilate")) * ratio * 0.5f, vertices = points });
            }
        }
        var scene = new Scene { state = state, pictures = images.ToArray(), glyphs = texts.ToArray() };
        File.WriteAllText(Path.Combine(directory, "book-render-" + state + ".json"), ItalicGeometryProbe.Serialize(scene), new UTF8Encoding(false));
    }
}
