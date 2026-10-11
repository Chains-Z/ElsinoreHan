using System;
using System.Reflection;
using HarmonyLib;
using UnityEngine;
using UnityEngine.UI;

// 原背景仅首次生成。只同步真实任务按钮的背景几何，不重跑Setup或增加交互监听。
public sealed class LeadSplotchLayout : MonoBehaviour
{
    private const BindingFlags Fields = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
    private static Type generatorType;
    private static FieldInfo imagesField;
    private static FieldInfo extrusionField;
    private static FieldInfo modeField;
    private Behaviour generator;
    private RectTransform rectangle;
    private Vector2 lastSize;
    private bool synchronized;

    public static void Apply(Harmony harmony)
    {
        foreach (Assembly assembly in AppDomain.CurrentDomain.GetAssemblies())
        {
            generatorType = assembly.GetType("Elsinore.Ui.SplotchGenerator", false);
            if (generatorType != null) break;
        }
        if (generatorType == null) throw new TypeLoadException("缺少游戏墨迹背景组件。");
        imagesField = generatorType.GetField("splotches", Fields);
        extrusionField = generatorType.GetField("splotchExtrusion", Fields);
        modeField = generatorType.GetField("mode", Fields);
        MethodInfo enable = generatorType.GetMethod("OnEnable", Fields);
        if (imagesField == null || extrusionField == null || modeField == null || enable == null)
            throw new MissingMemberException("游戏墨迹背景接口不兼容。");
        harmony.Patch(enable, postfix: new HarmonyMethod(typeof(LeadSplotchLayout).GetMethod("Attach")));
        foreach (UnityEngine.Object value in Resources.FindObjectsOfTypeAll(generatorType)) Attach(value as Behaviour);
    }

    public static void Attach(Behaviour __instance)
    {
        if (__instance == null || !__instance.gameObject.scene.IsValid()
            || Convert.ToInt32(modeField.GetValue(__instance)) != 2) return;
        bool lead = false;
        for (Transform parent = __instance.transform; parent != null; parent = parent.parent)
        {
            foreach (Component component in parent.GetComponents<Component>())
                if (component != null && component.GetType().FullName == "Elsinore.Ui.LeadItem") lead = true;
            if (lead) break;
        }
        if (!lead) return;
        var synchronizer = __instance.GetComponent<LeadSplotchLayout>();
        if (synchronizer == null) synchronizer = __instance.gameObject.AddComponent<LeadSplotchLayout>();
        synchronizer.generator = __instance;
        synchronizer.rectangle = __instance.transform as RectTransform;
    }

    private void LateUpdate()
    {
        if (generator == null || !generator.isActiveAndEnabled || rectangle == null) return;
        Vector2 size = rectangle.rect.size + (Vector2)extrusionField.GetValue(generator);
        if (synchronized && (size - lastSize).sqrMagnitude < 0.0001f) return;
        Image[] previous = imagesField.GetValue(generator) as Image[];
        // 等原Setup完成；不介入首次字体/墨迹初始化和颜色监听。
        if (previous == null || previous.Length == 0 || previous[0] == null || size.x <= 0 || size.y <= 0) return;
        int count = SplotchTileGeometry.Count(size.x, size.y);
        Image[] current = count == previous.Length ? previous : new Image[count];
        for (int index = 0; index < count; index++)
        {
            Image image = index < previous.Length ? previous[index]
                : UnityEngine.Object.Instantiate(previous[index % previous.Length], rectangle, false);
            current[index] = image;
            if (index >= previous.Length) image.transform.SetAsFirstSibling();
            image.rectTransform.sizeDelta = new Vector2(size.y, size.y);
            image.rectTransform.anchoredPosition = new Vector2(SplotchTileGeometry.Center(index, count, size.y), 0);
        }
        // 既有监听读取此数组；新增墨迹沿用当前颜色，之后仍由真实交互事件更新。
        imagesField.SetValue(generator, current);
        for (int index = count; index < previous.Length; index++)
        {
            previous[index].gameObject.SetActive(false);
            UnityEngine.Object.Destroy(previous[index].gameObject);
        }
        lastSize = size;
        synchronized = true;
    }
}
