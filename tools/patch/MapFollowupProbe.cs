using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

// 只供隔离后台探针调用：真实地图组件确认框与F8往返，不确认移动，不称物理输入E2E。
public static class MapFollowupProbe
{
    private const BindingFlags Instance = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance;

    private sealed class Context
    {
        public string Path;
        public StringBuilder Report = new StringBuilder();
        public float Deadline;
        public object Gui;
        public Component Map;
        public MonoBehaviour Toggle;
        public bool InitialMode;
        public bool Completed;
        public void Line(string value)
        {
            Report.AppendLine(value);
            File.WriteAllText(Path, Report.ToString(), new UTF8Encoding(false));
        }
    }

    public static IEnumerator Capture(string outputDirectory)
    {
        Directory.CreateDirectory(outputDirectory);
        var context = new Context { Path = System.IO.Path.Combine(outputDirectory, "map-followup.tsv"),
                                    Deadline = Time.realtimeSinceStartup + 10f };
        context.Line("SCHEMA\t1");
        context.Line("SCOPE\t" + Enc("真实地图按钮、确认框和共享F8组件路径；只点否，不验证物理键盘或实际移动"));
        var routines = new Stack<IEnumerator>();
        routines.Push(CaptureCore(context));
        try
        {
            while (routines.Count > 0)
            {
                bool more = false;
                object current = null;
                Exception failure = null;
                try
                {
                    if (Time.realtimeSinceStartup >= context.Deadline)
                        throw new TimeoutException("地图组件采集超过10秒");
                    more = routines.Peek().MoveNext();
                    if (more) current = routines.Peek().Current;
                }
                catch (Exception error) { failure = error; }
                if (failure != null)
                {
                    context.Line("FAILURE\t" + Enc(failure.ToString()));
                    break;
                }
                if (!more) { routines.Pop(); continue; }
                var child = current as IEnumerator;
                if (child != null) { routines.Push(child); continue; }
                yield return current;
            }
        }
        finally
        {
            // 故障也沿真实否按钮关闭确认框；不调用确认/移动入口。
            try
            {
                if (context.Map != null && DialogOpen(context)) Cancel(context, "cleanup");
                if (context.Toggle != null) SetMode(context, context.InitialMode);
            }
            catch (Exception error)
            {
                context.Completed = false;
                context.Line("FAILURE\t" + Enc("地图清理失败：" + error));
            }
            context.Line("STATUS\t" + (context.Completed ? "COLLECTED" : "FAILED"));
        }
    }

    private static IEnumerator CaptureCore(Context context)
    {
        if (!Application.isBatchMode || string.IsNullOrEmpty(Environment.GetEnvironmentVariable("ELSINOREHAN_PROBE_SAVE_PATH")))
            throw new InvalidOperationException("地图诊断要求后台模式和既有隔离存档保护");
        bool saveGuard = false, inputGuard = false;
        foreach (var component in Resources.FindObjectsOfTypeAll<MonoBehaviour>())
        {
            if (component == null || component.GetType().Name != "RuntimeProbe") continue;
            saveGuard = (bool)Field(component, "saveGuardActive");
            var input = component.GetType().GetField("physicalInputGuardActive", BindingFlags.NonPublic | BindingFlags.Static);
            inputGuard = input != null && (bool)input.GetValue(null);
        }
        context.Line("SAVE_GUARD_ACTIVE\t" + saveGuard);
        context.Line("PHYSICAL_INPUT_GUARD_ACTIVE\t" + inputGuard);
        if (!saveGuard || !inputGuard) throw new InvalidOperationException("地图诊断保护未建立");
        var tracker = ObjectTracker.Instance;
        if (tracker == null || tracker.Gui == null || tracker.Boss == null || !tracker.Boss.IsGameInitialized)
            throw new InvalidOperationException("当前真实游戏跟踪器未初始化");
        context.Gui = tracker.Gui;
        context.Map = (Component)Field(context.Gui, "mapCanvas");
        foreach (var component in Resources.FindObjectsOfTypeAll<MonoBehaviour>())
            if (component != null && component.GetType().Name == "TranslationToggle") { context.Toggle = component; break; }
        if (context.Toggle == null) throw new InvalidOperationException("真实F8共享插件不存在");
        context.InitialMode = Mode(context);
        yield return Wait(context, delegate { return !Transitioning(context) && Property(context.Gui, "ActiveModalControl") != null; }, 1.5f, "map.entry");
        var active = Property(context.Gui, "ActiveModalControl");
        var transitions = context.Gui.GetType().GetNestedType("UiTransitions", BindingFlags.Public | BindingFlags.NonPublic);
        var current = Activator.CreateInstance(transitions, Instance, null, new object[] { context.Gui, active }, null);
        transitions.GetMethod("ActivateMap").Invoke(current, null);
        context.Line("TRANSITION\tActivateMap\t" + Enc(active.GetType().Name));
        yield return Wait(context, delegate { return MapReady(context); }, 2f, "map.owner");
        context.Line("NAVIGATION\tmap\tTrue\tTrue");
        State(context, "before");
        var mapBase = Field(context.Map, "mapBase");
        bool hamletCaptured = false;
        var initialHamlet = FindHamlet(mapBase);
        if (initialHamlet != null)
        {
            yield return ProbeCase(context, "hamlet", "character", initialHamlet, (string)Field(initialHamlet, "tooltip"));
            hamletCaptured = true;
        }
        Component upper = FindRoom(mapBase, "Upper Hallway");
        bool descending = false;
        // 通过真实楼层按钮遍历；从当前层向上，到顶后向下，步数和总时限均有限。
        for (int step = 0; upper == null && step < 6; step++)
        {
            var button = Field(context.Map, descending ? "FloorDownButton" : "FloorUpButton") as Component;
            if (!Clickable(button))
            {
                if (descending) break;
                descending = true;
                button = Field(context.Map, "FloorDownButton") as Component;
                if (!Clickable(button)) break;
            }
            Click(context, "floor", button);
            yield return new WaitForSecondsRealtime(0.15f);
            yield return Wait(context, delegate { return MapReady(context); }, 0.6f, "map.floor");
            upper = FindRoom(mapBase, "Upper Hallway");
            if (!hamletCaptured)
            {
                var floorHamlet = FindHamlet(mapBase);
                if (floorHamlet != null && Time.realtimeSinceStartup + 1.3f < context.Deadline)
                {
                    yield return ProbeCase(context, "hamlet", "character", floorHamlet, (string)Field(floorHamlet, "tooltip"));
                    hamletCaptured = true;
                }
            }
        }
        if (upper != null) yield return ProbeCase(context, "upper-hallway", "room", upper, "Upper Hallway");
        else context.Line("UNAVAILABLE\tupper-hallway\t" + Enc("当前实际地图楼层没有可交互的Upper Hallway按钮"));
        var other = FindRoom(mapBase, null, "Upper Hallway");
        if (other != null && Time.realtimeSinceStartup + 1.3f < context.Deadline)
            yield return ProbeCase(context, "other-room", "room", other, RoomName(other));
        var hamlet = FindHamlet(mapBase);
        if (!hamletCaptured && hamlet != null && Time.realtimeSinceStartup + 1.3f < context.Deadline)
        {
            yield return ProbeCase(context, "hamlet", "character", hamlet, (string)Field(hamlet, "tooltip"));
            hamletCaptured = true;
        }
        if (!hamletCaptured) context.Line("UNAVAILABLE\thamlet\t" + Enc("已访问楼层没有可交互Hamlet图标，或采集剩余时限不足；不构造人物按钮"));
        State(context, "after");
        context.Completed = true;
    }

    private static IEnumerator ProbeCase(Context context, string identifier, string kind, Component button, string parameter)
    {
        context.Line("CASE\t" + identifier + "\t" + kind + "\t" + Enc(parameter) + "\t" + Enc(TextPath(button.transform)));
        Click(context, identifier, button);
        yield return Wait(context, delegate { return ConfirmReady(context); }, 0.8f, identifier + ".dialog");
        var body = (TMP_Text)Field(context.Map, "confirmMoveText");
        string source = ((StringBuilder)Field(context.Map, "builder")).ToString();
        if (source != "Go to " + parameter + "?")
            throw new InvalidOperationException("真实地图回调参数或确认源不符：" + source);
        context.Line("SOURCE\t" + identifier + "\t" + Enc(source));
        string translation;
        bool found = Lookup(source, out translation);
        context.Line("API\t" + identifier + "\t" + found + "\t" + Enc(translation));
        string[] modes = { "translated", "original", "restored" };
        foreach (string mode in modes)
        {
            SetMode(context, mode != "original");
            yield return new WaitForSecondsRealtime(0.2f);
            bool active = ConfirmReady(context) && body.gameObject.activeInHierarchy;
            context.Line("SAMPLE\t" + identifier + "\t" + mode + "\t" + body.GetInstanceID()
                + "\t" + Enc(TextPath(body.transform)) + "\t" + Enc(((StringBuilder)Field(context.Map, "builder")).ToString())
                + "\t" + Enc(body.text ?? "") + "\t" + active + "\t" + Mode(context));
            if (!active) throw new InvalidOperationException("地图确认框在F8三态采集中失活：" + identifier + "/" + mode);
        }
        Cancel(context, identifier);
        yield return Wait(context, delegate { return !DialogOpen(context) && MapReady(context); }, 0.5f, identifier + ".cancel");
        // 等待游戏再处理一帧，避免只读取否按钮回调同帧的旧时间状态。
        yield return new WaitForSecondsRealtime(0.1f);
        context.Line("CANCEL\t" + identifier + "\t1\tTrue\tTrue");
    }

    private static IEnumerator Wait(Context context, Func<bool> ready, float seconds, string phase)
    {
        float until = Math.Min(context.Deadline, Time.realtimeSinceStartup + seconds);
        while (!ready())
        {
            if (Time.realtimeSinceStartup >= until) throw new TimeoutException("地图真实组件未就绪：" + phase);
            yield return null;
        }
    }

    private static bool Transitioning(Context context) { return (bool)Property(context.Gui, "IsTransitioning"); }
    private static bool MapReady(Context context)
    {
        return context.Map.gameObject.activeInHierarchy && !Transitioning(context)
            && ReferenceEquals(Property(context.Gui, "ActiveModalControl"), context.Map)
            && ReferenceEquals(Property(context.Gui, "CurrentlyActiveRootCanvas"), context.Map);
    }
    private static bool DialogOpen(Context context)
    {
        var dialog = Field(context.Map, "confirmMoveDialog") as Component;
        return dialog != null && dialog.gameObject.activeInHierarchy;
    }
    private static bool ConfirmReady(Context context)
    {
        var dialog = Field(context.Map, "confirmMoveDialog");
        return DialogOpen(context) && !Transitioning(context)
            && ReferenceEquals(Property(context.Gui, "CurrentlyActiveRootCanvas"), context.Map)
            && ReferenceEquals(Property(context.Gui, "ActiveModalControl"), dialog);
    }
    private static void Cancel(Context context, string phase)
    {
        var dialog = Field(context.Map, "confirmMoveDialog");
        var buttons = Field(dialog, "ActionButtons") as IList;
        if (buttons == null || buttons.Count != 2) throw new InvalidOperationException("真实地图是/否按钮结构不符");
        // MapUI.Awake按Yes、No顺序添加按钮；索引1唯一对应onCancelMove。
        Click(context, phase + ".no", buttons[1] as Component);
    }
    private static bool Clickable(Component button)
    {
        var selectable = button as Selectable;
        if (selectable == null || !button.gameObject.scene.IsValid() || !button.gameObject.scene.isLoaded
            || !button.gameObject.activeInHierarchy || !selectable.interactable) return false;
        var property = button.GetType().GetProperty("IsInteractable", Instance);
        return property == null || (bool)property.GetValue(button, null);
    }
    private static void Click(Context context, string phase, Component button)
    {
        if (!Clickable(button) || EventSystem.current == null) throw new InvalidOperationException("实际地图按钮不可交互：" + phase);
        var pointer = new PointerEventData(EventSystem.current) { button = PointerEventData.InputButton.Left };
        EventSystem.current.SetSelectedGameObject(button.gameObject);
        bool handled = ExecuteEvents.Execute(button.gameObject, pointer, ExecuteEvents.pointerClickHandler);
        context.Line("CLICK\t" + phase + "\t" + Enc(TextPath(button.transform)) + "\t" + handled);
        if (!handled) throw new InvalidOperationException("真实地图按钮未消费PointerClick：" + phase);
    }
    private static string RoomName(Component button)
    {
        var method = ObjectTracker.Instance.GetType().GetMethod("RoomMarker", Instance);
        var id = Activator.CreateInstance(method.GetParameters()[0].ParameterType, new object[] { button.name });
        var room = method.Invoke(ObjectTracker.Instance, new object[] { id });
        return (string)Field(room, "playerFacingName");
    }
    private static Component FindRoom(object mapBase, string desired, string excluded = null)
    {
        foreach (var value in (IEnumerable)Property(mapBase, "ActiveRoomButtons"))
        {
            var button = value as Component;
            if (!Clickable(button)) continue;
            string name = RoomName(button);
            if ((desired == null || name == desired) && name != excluded) return button;
        }
        return null;
    }
    private static Component FindHamlet(object mapBase)
    {
        var npcs = Field(mapBase, "npcs") as Array;
        var icons = Field(mapBase, "npcIcons") as Array;
        var active = Property(mapBase, "ActiveCharButtons") as IList;
        if (npcs == null || icons == null || active == null || npcs.Length != icons.Length) return null;
        for (int index = 0; index < npcs.Length; index++)
        {
            var button = icons.GetValue(index) as Component;
            var id = Property(npcs.GetValue(index), "Id");
            if ((string)Property(id, "Name") == "hamlet" && active.Contains(button) && Clickable(button)) return button;
        }
        return null;
    }
    private static void State(Context context, string moment)
    {
        var player = (Component)Property(ObjectTracker.Instance, "Player");
        var room = Property(player, "CurrentRoom");
        string roomId = (string)Property(Property(room, "Id"), "Name");
        var point = player.transform.position;
        context.Line("POSITION\t" + moment + "\t" + Enc(roomId) + "\t" + Number(point.x) + "\t" + Number(point.y) + "\t" + Number(point.z));
        var info = ObjectTracker.Instance.Info;
        var visible = Property(info, "VisibleTime");
        context.Line("CLOCK\t" + moment + "\t" + Convert.ToInt32(Property(info, "TimeMode"))
            + "\t" + Number(Convert.ToSingle(Property(visible, "MinutesFromEpochFloat"))));
    }
    private static bool Lookup(string source, out string translation)
    {
        Type api = null;
        foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
        {
            api = assembly.GetType("XUnity.AutoTranslator.Plugin.Core.AutoTranslator", false);
            if (api != null) break;
        }
        if (api == null) throw new InvalidOperationException("真实离线翻译缓存API不存在");
        var instance = api.GetProperty("Default").GetValue(null, null);
        var contract = api.Assembly.GetType("XUnity.AutoTranslator.Plugin.Core.ITranslator");
        var method = contract.GetMethod("TryTranslate", new Type[] { typeof(string), typeof(string).MakeByRefType() });
        var args = new object[] { source, null };
        bool found = (bool)method.Invoke(instance, args);
        translation = args[1] as string;
        return found;
    }
    private static bool Mode(Context context)
    {
        return (bool)context.Toggle.GetType().GetMethod("IsTranslatedMode", Instance).Invoke(context.Toggle, null);
    }
    private static void SetMode(Context context, bool translated)
    {
        var key = context.Toggle.GetType().GetMethod("HandleKey", Instance);
        if (Mode(context) != translated) key.Invoke(context.Toggle, new object[] { true });
        key.Invoke(context.Toggle, new object[] { false });
        if (Mode(context) != translated) throw new InvalidOperationException("真实共享F8模式没有切换成功");
    }
    private static object Field(object owner, string name)
    {
        if (owner == null) throw new InvalidOperationException("地图字段所属对象为空：" + name);
        var field = owner.GetType().GetField(name, Instance);
        if (field == null) throw new MissingFieldException(owner.GetType().FullName, name);
        return field.GetValue(owner);
    }
    private static object Property(object owner, string name)
    {
        if (owner == null) throw new InvalidOperationException("地图属性所属对象为空：" + name);
        var property = owner.GetType().GetProperty(name, Instance);
        if (property == null) throw new MissingMemberException(owner.GetType().FullName, name);
        return property.GetValue(owner, null);
    }
    private static string TextPath(Transform transform)
    {
        string path = transform.name;
        while (transform.parent != null) { transform = transform.parent; path = transform.name + "/" + path; }
        return path;
    }
    private static string Enc(string value) { return Convert.ToBase64String(Encoding.UTF8.GetBytes(value ?? "")); }
    private static string Number(float value) { return value.ToString("R", CultureInfo.InvariantCulture); }
}
