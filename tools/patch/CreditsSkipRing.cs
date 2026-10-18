using UnityEngine;
using UnityEngine.UI;

// 使用原生UI网格绘制圆环，不读取或替换游戏图片。
public sealed class CreditsSkipRing : MaskableGraphic
{
    private float progress;
    public float Progress
    {
        get { return progress; }
        set { float next = Mathf.Clamp01(value); if (next != progress) { progress = next; SetVerticesDirty(); } }
    }
    protected override void OnPopulateMesh(VertexHelper mesh)
    {
        mesh.Clear();
        if (progress <= 0) return;
        Rect rect = rectTransform.rect;
        Vector2 center = rect.center;
        float outer = Mathf.Min(rect.width, rect.height) * 0.5f;
        float inner = outer * 0.78f;
        int segments = Mathf.Max(1, Mathf.CeilToInt(64 * progress));
        for (int i = 0; i <= segments; i++)
        {
            float angle = Mathf.PI * 0.5f - 2 * Mathf.PI * progress * i / segments;
            var direction = new Vector2(Mathf.Cos(angle), Mathf.Sin(angle));
            mesh.AddVert(center + direction * outer, color, Vector2.zero);
            mesh.AddVert(center + direction * inner, color, Vector2.zero);
            if (i == 0) continue;
            int a = (i - 1) * 2;
            mesh.AddTriangle(a, a + 1, a + 2); mesh.AddTriangle(a + 2, a + 1, a + 3);
        }
    }
}
