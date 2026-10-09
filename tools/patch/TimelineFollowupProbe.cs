using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

// 临时探针：真实按钮采样与资源格式器重放分别记账，不改进度或生成剧情事件。
public static class TimelineFollowupProbe
{
    private const BindingFlags Members = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static;
    private sealed class Session
    {
        public string Path;
        public float Deadline;
        public Component Timeline;
        public TMP_Text Text;
        public Action<bool> SetMode;
        public HashSet<string> Captured = new HashSet<string>();
        public HashSet<string> SeenDescriptions = new HashSet<string>();
        public int RealCount;
        public int InitialLoop;
        public string InitialSource;
        public string InitialKey;
        public void Write(params object[] fields)
        {
            var parts = new string[fields.Length];
            for (int index = 0; index < fields.Length; index++) parts[index] = Convert.ToString(fields[index], System.Globalization.CultureInfo.InvariantCulture);
            File.AppendAllText(Path, string.Join("\t", parts) + "\n", new UTF8Encoding(false));
        }
    }
    private static object Field(object owner, string name)
    {
        var field = owner.GetType().GetField(name, Members);
        if (field == null) throw new MissingFieldException(owner.GetType().FullName, name);
        return field.GetValue(owner);
    }
    private static object Property(object owner, string name)
    {
        var property = owner.GetType().GetProperty(name, Members);
        if (property == null) throw new MissingMemberException(owner.GetType().FullName, name);
        return property.GetValue(owner, null);
    }
    private static object Call(object owner, string name, params object[] args)
    {
        var types = new Type[args.Length];
        for (int index = 0; index < args.Length; index++)
        {
            if (args[index] == null) throw new ArgumentException("实例反射参数须明确类型，禁止用null推测签名");
            types[index] = args[index].GetType();
        }
        var method = ExactMethod(owner.GetType(), name, false, types);
        return method.Invoke(owner, args);
    }
    private static MethodInfo ExactMethod(Type owner, string name, bool isStatic, params Type[] parameters)
    {
        var flags = BindingFlags.Public | BindingFlags.NonPublic | (isStatic ? BindingFlags.Static : BindingFlags.Instance);
        var method = owner.GetMethod(name, flags, null, parameters, null);
        if (method == null || method.IsGenericMethodDefinition)
            throw new MissingMethodException(owner.FullName, name + "（准确非泛型参数签名）");
        return method;
    }
    private static Type GameType(string name)
    {
        return Type.GetType("Elsinore.Game." + name + ", Elsinore", true);
    }
    private static MethodInfo UiMethod(Type uiStrings, string name, params Type[] parameters)
    {
        return ExactMethod(uiStrings, name, true, parameters);
    }
    private static MethodInfo ListMethod(Type uiStrings)
    {
        MethodInfo found = null;
        foreach (var method in uiStrings.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static))
        {
            if (method.Name != "FormatList" || !method.IsGenericMethodDefinition || method.ReturnType != typeof(void)
                || method.GetGenericArguments().Length != 1) continue;
            var argument = method.GetGenericArguments()[0];
            var parameters = method.GetParameters();
            if (parameters.Length != 3 || parameters[0].ParameterType != typeof(StringBuilder)) continue;
            var function = parameters[1].ParameterType;
            var list = parameters[2].ParameterType;
            if (!function.IsGenericType || function.GetGenericTypeDefinition() != typeof(Func<,>)
                || function.GetGenericArguments()[0] != argument || function.GetGenericArguments()[1] != typeof(string)
                || !list.IsGenericType || list.GetGenericTypeDefinition().FullName != "System.Collections.Generic.IReadOnlyList`1"
                || list.GetGenericArguments()[0] != argument) continue;
            if (found != null) throw new AmbiguousMatchException("真实FormatList泛型签名不唯一");
            found = method;
        }
        if (found == null) throw new MissingMethodException(uiStrings.FullName, "FormatList<T>(StringBuilder,Func<T,string>,IReadOnlyList<T>)");
        return found;
    }
    // 离线仅读取真实程序集方法元数据，不创建Unity实例或调用游戏格式器。
    public static string[] ValidateReflectionSignatures(string managedDirectory)
    {
        var assembly = Assembly.LoadFrom(System.IO.Path.Combine(managedDirectory, "Assembly-CSharp.dll"));
        var ui = assembly.GetType("Elsinore.Ui.UiStrings", true);
        var timeline = assembly.GetType("Elsinore.Ui.TimelineUI", true);
        var clock = GameType("GameClock");
        var room = GameType("RoomId");
        var character = GameType("CharacterId");
        var state = GameType("GameState");
        var item = GameType("TimelineItem");
        var lookup = GameType("DataLookup");
        bool ambiguous = false;
        try { ui.GetMethod("FormatTimeString", Members); }
        catch (AmbiguousMatchException) { ambiguous = true; }
        if (!ambiguous) throw new InvalidOperationException("旧name-only调用未复现已知真实重载歧义");
        var methods = new MethodInfo[] {
            UiMethod(ui, "FormatTimeString", clock),
            UiMethod(ui, "FormatCharacterName", character),
            UiMethod(ui, "FormatRoomId", room),
            UiMethod(ui, "FormatLogEntryOpener", typeof(StringBuilder), clock, typeof(Nullable<>).MakeGenericType(room), typeof(bool)),
            UiMethod(ui, "FormatEvent", typeof(StringBuilder), GameType("ElsinoreEvent")),
            ListMethod(ui),
            UiMethod(ui, "SetLineHeight", typeof(StringBuilder)),
            UiMethod(ui, "AddParagraphBreakIfPriorContent", typeof(StringBuilder)),
            ExactMethod(timeline, "createEventContent", true, typeof(StringBuilder), typeof(StringBuilder), state, item),
            ExactMethod(timeline, "DeactivateEventInfoPopup", false, Type.EmptyTypes),
            ExactMethod(item, "IsInFuture", false, state),
            ExactMethod(item, "Details", false, state),
            ExactMethod(lookup, "Event", false, GameType("HEventId"))
        };
        if (methods[0].ReturnType != typeof(string) || clock.GetConstructor(new Type[] { typeof(float) }) == null)
            throw new InvalidOperationException("真实GameClock单参格式器或Single构造器契约不符");
        var closedList = methods[5].MakeGenericMethod(character);
        if (!closedList.GetParameters()[2].ParameterType.IsAssignableFrom(character.MakeArrayType()))
            throw new InvalidOperationException("真实CharacterId数组不能绑定FormatList的IReadOnlyList参数");
        var lines = new List<string>();
        lines.Add("LEGACY_NAME_ONLY_AMBIGUOUS=True");
        foreach (var method in methods) lines.Add(method.DeclaringType.FullName + "::" + method.ToString());
        return lines.ToArray();
    }
    private static string B64(string value) { return Convert.ToBase64String(Encoding.UTF8.GetBytes(value ?? "")); }
    private static string Hash(string value)
    {
        using (var sha = SHA256.Create()) return BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(value))).Replace("-", "").ToLowerInvariant();
    }
    private static bool Clickable(object value)
    {
        var button = value as Selectable;
        return button != null && button.gameObject.activeInHierarchy && button.interactable;
    }
    private static void Click(object value)
    {
        if (!Clickable(value)) throw new InvalidOperationException("时间线真实按钮不可点击");
        var component = (Component)value;
        ExecuteEvents.Execute(component.gameObject, new PointerEventData(EventSystem.current), ExecuteEvents.pointerEnterHandler);
        var click = Property(value, "OnClick") as Button.ButtonClickedEvent;
        if (click == null) throw new InvalidOperationException("时间线真实按钮缺少OnClick");
        click.Invoke();
    }
    private static string Clock()
    {
        var info = ObjectTracker.Instance.Info;
        if (Convert.ToInt32(Property(info, "TimeMode")) != 2) throw new InvalidOperationException("时间线采样必须保持真实暂停态");
        var clock = Property(info, "VisibleTime");
        return Convert.ToString(Property(clock, "MinutesFromEpochFloat"), System.Globalization.CultureInfo.InvariantCulture);
    }
    private static bool[] Ownership(Session session)
    {
        var gui = ObjectTracker.Instance.Gui;
        var popup = (Component)Field(session.Timeline, "EventInfoPopup");
        var modal = Property(gui, "ActiveModalControl");
        // 原ActiveModalControl会优先返回自己的详情DialogBox；仍须绑定当前Timeline画布。
        return new bool[] {
            session.Timeline.gameObject.scene.IsValid() && session.Timeline.gameObject.scene.isLoaded,
            session.Timeline.gameObject.activeInHierarchy,
            session.Text.gameObject.activeInHierarchy,
            session.Text.transform.IsChildOf(session.Timeline.transform),
            ReferenceEquals(Property(gui, "CurrentlyActiveRootCanvas"), session.Timeline)
                || ReferenceEquals(Property(gui, "CurrentlyActiveOverlayCanvas"), session.Timeline),
            ReferenceEquals(modal, session.Timeline),
            ReferenceEquals(modal, popup),
            popup.gameObject.activeInHierarchy,
            session.Text.transform.IsChildOf(popup.transform)
        };
    }
    private static bool AcceptedOwner(bool[] parts)
    {
        return parts[0] && parts[1] && parts[2] && parts[3] && parts[4]
            && (parts[5] || (parts[6] && parts[7] && parts[8]));
    }
    private static bool Owns(Session session)
    {
        return AcceptedOwner(Ownership(session));
    }
    private static bool OwnerEvidence(Session session, string kind, string id, string mode)
    {
        var parts = Ownership(session);
        bool accepted = AcceptedOwner(parts);
        session.Write("OWNER", kind, id, mode, parts[0], parts[1], parts[2], parts[3], parts[4],
            parts[5], parts[6], parts[7], parts[8], accepted);
        return accepted;
    }
    private static string Description(object evt)
    {
        var option = Property(evt, "Description");
        return option == null ? "An event occurs." : (string)Property(option, "Value");
    }
    private static string Room(object evt, Type uiStrings)
    {
        var primary = Property(evt, "PrimaryRoom");
        return primary == null ? "" : (string)UiMethod(uiStrings, "FormatRoomId", GameType("RoomId")).Invoke(null, new object[] { primary });
    }
    private static string Name(object cid, Type uiStrings)
    {
        return (string)UiMethod(uiStrings, "FormatCharacterName", GameType("CharacterId")).Invoke(null, new object[] { cid });
    }
    private static void Skipped(Session session, object item, object eventId, bool attended, bool future,
        string description, string reason, string error, string detailsOrigin)
    {
        var scenes = new List<string>();
        foreach (var scene in (IEnumerable)Property(item, "Scenes")) scenes.Add((string)Property(scene, "Name"));
        session.Write("SKIP", Field(session.Timeline, "loopToShow"), B64((string)Property(item, "Key")),
            (string)Property(eventId, "Name"), attended, future, B64(description), Hash(description), reason,
            B64(error), detailsOrigin, B64(string.Join("\n", scenes.ToArray())));
    }
    private static IEnumerator States(Session session, string kind, string id, string source, bool builderRequired)
    {
        string before = Clock();
        foreach (var mode in new string[] { "translated", "original", "restored" })
        {
            session.SetMode(mode != "original");
            yield return new WaitForSecondsRealtime(0.12f);
            bool owns = OwnerEvidence(session, kind, id, mode);
            string builder = ((StringBuilder)Field(session.Timeline, "builder1")).ToString();
            session.Write("STATE", kind, id, mode, session.Text.GetInstanceID(), B64(source), Hash(source),
                B64(session.Text.text ?? ""), B64(builder), owns, Clock(), builderRequired);
            if (!owns) throw new InvalidOperationException("时间线正文不属于当前真实激活页面");
            if (builderRequired && builder != source) throw new InvalidOperationException("F8期间真实时间线builder源文发生变化");
        }
        if (Clock() != before) throw new InvalidOperationException("时间线F8三态期间时钟发生变化");
    }
    private static IEnumerator RealLoop(Session session)
    {
        var timeline = session.Timeline;
        var uiStrings = timeline.GetType().Assembly.GetType("Elsinore.Ui.UiStrings", true);
        var state = Field(timeline, "lastUsedGameState");
        var lookup = Property(state, "Lookup");
        var copies = new List<object>();
        foreach (var value in (IEnumerable)Field(timeline, "currentItems")) copies.Add(value);
        foreach (var tuple in copies)
        {
            if (Time.realtimeSinceStartup > session.Deadline - 4f) break;
            var item = Field(tuple, "Item1");
            var button = Field(tuple, "Item2");
            var type = Property(item, "Type");
            if (!(bool)Property(type, "IsEvent") || !Clickable(button)) continue;
            var timelineEvent = Property(type, "AsEvent");
            var eventId = Property(timelineEvent, "Id");
            var evt = Call(lookup, "Event", eventId);
            string description = Description(evt);
            session.SeenDescriptions.Add(description);
            bool attended = (bool)Property(item, "PlayerAttended");
            bool future = (bool)Call(item, "IsInFuture", state);
            var people = (Array)Property(timelineEvent, "VisibleParticipants");
            string room = Room(evt, uiStrings);
            bool needsEmpty = attended && !future && people.Length > 0
                && !session.Captured.Contains(people.Length == 1 ? "empty-one" : "empty-many");
            bool needsQueen = room == "Gertrude's Chambers" && !session.Captured.Contains("queen-room");
            if (!attended || future)
                Skipped(session, item, eventId, attended, future, description, "not-attended-or-future", "", "Details-not-called");
            if (!needsEmpty && !needsQueen) continue;
            if (attended && future) continue;
            int changes = -1;
            string detailsOrigin = "Details-not-called";
            // 原回调也只在PlayerAttended=true时调用Details；未参加/未来项不能借缺记录伪造成零Changes。
            if (attended)
            {
                try
                {
                    var details = Call(item, "Details", state);
                    changes = ((Array)Property(details, "Changes")).Length;
                    detailsOrigin = "TimelineItem.Details(lastUsedGameState)";
                }
                catch (TargetInvocationException error)
                {
                    Exception actual = error;
                    while (actual is TargetInvocationException && actual.InnerException != null) actual = actual.InnerException;
                    if (!(actual is KeyNotFoundException)) throw;
                    Skipped(session, item, eventId, attended, future, description, "details-missing-scene",
                        actual.GetType().Name + ": " + actual.Message, "TimelineItem.Details(lastUsedGameState)");
                    continue;
                }
            }
            string emptyRole = attended && changes == 0 && people.Length > 0 ? (people.Length == 1 ? "empty-one" : "empty-many") : null;
            string role = room == "Gertrude's Chambers" && !session.Captured.Contains("queen-room") ? "queen-room" : emptyRole;
            if (role == null || session.Captured.Contains(role)) continue;
            string id = "real-" + role;
            var names = new List<string>();
            var ids = new List<string>();
            foreach (var cid in people) { names.Add(Name(cid, uiStrings)); ids.Add((string)Property(cid, "Name")); }
            Click(button);
            yield return new WaitForSecondsRealtime(0.12f);
            string source = ((StringBuilder)Field(timeline, "builder1")).ToString();
            string body = ((StringBuilder)Field(timeline, "builder2")).ToString();
            bool tail = body.EndsWith("\n<line-height=40%>\n<line-height=90%>", StringComparison.Ordinal);
            session.Write("REAL", id, Field(timeline, "loopToShow"), B64((string)Property(item, "Key")),
                (string)Property(eventId, "Name"), attended, people.Length, changes, B64(room), B64(description),
                B64(string.Join("\n", names.ToArray())), B64(string.Join("\n", ids.ToArray())), B64(source), Hash(source),
                B64(body), tail, Owns(session), "button.OnClick", "currentItems", detailsOrigin);
            yield return States(session, "REAL", id, source, true);
            session.Captured.Add(role);
            if (emptyRole != null) session.Captured.Add(emptyRole);
            session.RealCount++;
        }
    }
    private static void FormatList(Type uiStrings, StringBuilder builder, Array people)
    {
        var cidType = people.GetType().GetElementType();
        var formatName = UiMethod(uiStrings, "FormatCharacterName", cidType);
        var formatter = Delegate.CreateDelegate(typeof(Func<,>).MakeGenericType(cidType, typeof(string)), formatName);
        ListMethod(uiStrings).MakeGenericMethod(cidType).Invoke(null, new object[] { builder, formatter, people });
    }
    private static object FrozenEvent(IDictionary events, string description)
    {
        foreach (DictionaryEntry item in events) if (Description(item.Value) == description) return item.Value;
        throw new InvalidOperationException("真实资源Lookup缺少已审事件：" + description);
    }
    private static Array FrozenPeople(object evt, string[] expectedNames, Type uiStrings)
    {
        var original = (Array)Property(evt, "Participants");
        var possible = new List<object>();
        foreach (var cid in original) possible.Add(cid);
        // 戏剧场景的观众可以来自真实Observers，而不属于演出动作Participants。
        foreach (var observer in (IEnumerable)Property(evt, "Observers")) possible.Add(Property(observer, "Item1"));
        var people = Array.CreateInstance(original.GetType().GetElementType(), expectedNames.Length);
        for (int index = 0; index < expectedNames.Length; index++)
        {
            object found = null;
            foreach (var cid in possible) if (Name(cid, uiStrings) == expectedNames[index]) { found = cid; break; }
            if (found == null) throw new InvalidOperationException("重放名单不属于该真实事件参与者：" + expectedNames[index]);
            people.SetValue(found, index);
        }
        return people;
    }
    private static object FrozenClock(Type uiStrings, string expected)
    {
        var method = UiMethod(uiStrings, "FormatTimeString", GameType("GameClock"));
        var clockType = method.GetParameters()[0].ParameterType;
        var clock = ClockAtDisplayTime(clockType, expected);
        if ((string)method.Invoke(null, new object[] { clock }) != expected)
            throw new InvalidOperationException("实际游戏模式的时钟格式器与截图时间不符");
        return clock;
    }
    private static object ClockAtDisplayTime(Type clockType, string expected)
    {
        string time = expected.Substring(expected.IndexOf(", ", StringComparison.Ordinal) + 2);
        int minutes = int.Parse(time.Substring(0, 2)) * 60 + int.Parse(time.Substring(3, 2));
        for (int day = 0; day < 6; day++)
        {
            // GameClock纪元从06:00起，真实Hour/Minute/日期getter统一加360分钟。
            var clock = Activator.CreateInstance(clockType, new object[] { (float)(day * 1440 + minutes - 360) });
            if ((string)Property(clock, "AsStringWithDayOfWeek") == expected) return clock;
        }
        throw new InvalidOperationException("真实时钟格式器无法还原截图时间参数");
    }
    public static string[] ValidateClockFixtures()
    {
        var type = GameType("GameClock");
        string[] dates = { "Thursday, 06:02", "Thursday, 11:43", "Saturday, 08:02", "Friday, 17:15", "Saturday, 00:30" };
        foreach (string date in dates)
            if ((string)Property(ClockAtDisplayTime(type, date), "AsStringWithDayOfWeek") != date)
                throw new InvalidOperationException("真实GameClock离线回归失败：" + date);
        var legacy = Activator.CreateInstance(type, new object[] { 362f });
        if ((int)Property(legacy, "Hour") != 12 || (int)Property(legacy, "Minute") != 2)
            throw new InvalidOperationException("旧时钟误用的六小时偏差没有复现");
        return dates;
    }
    private static IEnumerator Replay(Session session)
    {
        var uiStrings = session.Timeline.GetType().Assembly.GetType("Elsinore.Ui.UiStrings", true);
        var lookup = Property(Field(session.Timeline, "lastUsedGameState"), "Lookup");
        var events = (IDictionary)Field(lookup, "hevents");
        string[] descriptions = { "Hamlet's ravings interrupt my sleep.", "Polonius questions Hamlet.",
            "Horatio and Gertrude have a heart to heart.", "Quince puts on the play that Hamlet designed.",
            "Hamlet presses his Mother on Claudius's actions." };
        string[] clocks = { "Thursday, 06:02", "Thursday, 11:43", "Saturday, 08:02", "Friday, 17:15", "Saturday, 00:30" };
        string[] rooms = { "Ophelia's Chambers", "The Royal Gallery", "The Grounds", "The Great Hall", "Gertrude's Chambers" };
        string[] keys = { "hamlet-sleep", "polonius-question", "horatio-queen", "hamlet-play", "queen-not-attended" };
        string[][] names = { new string[] { "Hamlet" }, new string[] { "Hamlet", "Polonius" },
            new string[] { "Queen Gertrude", "Horatio" },
            new string[] { "King Claudius", "Queen Gertrude", "Hamlet", "Horatio", "Quince" }, new string[0] };
        for (int index = 0; index < descriptions.Length; index++)
        {
            if (Time.realtimeSinceStartup > session.Deadline - 0.8f) throw new TimeoutException("时间线重放超过10秒额外预算");
            var evt = FrozenEvent(events, descriptions[index]);
            var primary = Property(evt, "PrimaryRoom");
            if (Room(evt, uiStrings) != rooms[index]) throw new InvalidOperationException("已审事件真实PrimaryRoom与截图房间不符");
            var clock = FrozenClock(uiStrings, clocks[index]);
            var people = FrozenPeople(evt, names[index], uiStrings);
            var opener = UiMethod(uiStrings, "FormatLogEntryOpener", typeof(StringBuilder), GameType("GameClock"),
                typeof(Nullable<>).MakeGenericType(GameType("RoomId")), typeof(bool));
            var roomParameter = Activator.CreateInstance(opener.GetParameters()[2].ParameterType, new object[] { primary });
            var builder = new StringBuilder();
            var secondary = new StringBuilder();
            UiMethod(uiStrings, "SetLineHeight", typeof(StringBuilder)).Invoke(null, new object[] { builder });
            UiMethod(uiStrings, "SetLineHeight", typeof(StringBuilder)).Invoke(null, new object[] { secondary });
            opener.Invoke(null, new object[] { builder, clock, roomParameter, false });
            UiMethod(uiStrings, "FormatEvent", typeof(StringBuilder), GameType("ElsinoreEvent")).Invoke(null, new object[] { builder, evt });
            if (index == 4) secondary.Append("Ophelia did not attend this event.\n");
            else
            {
                secondary.Append("Including ");
                FormatList(uiStrings, secondary, people);
                secondary.Append('.');
                UiMethod(uiStrings, "AddParagraphBreakIfPriorContent", typeof(StringBuilder)).Invoke(null, new object[] { secondary });
            }
            UiMethod(uiStrings, "AddParagraphBreakIfPriorContent", typeof(StringBuilder)).Invoke(null, new object[] { builder });
            builder.Append(secondary);
            string source = builder.ToString();
            string id = "replay-" + keys[index];
            var actualNames = new List<string>();
            var actualIds = new List<string>();
            foreach (var cid in people) { actualNames.Add(Name(cid, uiStrings)); actualIds.Add((string)Property(cid, "Name")); }
            session.Write("REPLAY", id, (string)Property(Property(evt, "Id"), "Name"), B64(descriptions[index]),
                Hash(descriptions[index]), B64(rooms[index]), B64(clocks[index]), B64(string.Join("\n", actualNames.ToArray())),
                B64(source), Hash(source), "real-resource-formatter-component", "not-acquired-story",
                B64(string.Join("\n", actualIds.ToArray())), "ElsinoreEvent.Participants+Observers/UiStrings.FormatCharacterName");
            // 只重放组件输入，不制造TimelineItem或改写存档/游戏进度。
            session.Text.SetText(new StringBuilder(source));
            yield return States(session, "REPLAY", id, source, false);
        }
    }
    private static string InitialKey(Session session)
    {
        var timeline = session.Timeline;
        var state = Field(timeline, "lastUsedGameState");
        var uiStrings = timeline.GetType().Assembly.GetType("Elsinore.Ui.UiStrings", true);
        foreach (var pair in (IEnumerable)Field(timeline, "currentItems"))
        {
            if (!Clickable(Field(pair, "Item2"))) continue;
            var item = Field(pair, "Item1");
            var first = new StringBuilder();
            var second = new StringBuilder();
            // 仅让原格式器生成局部builder来匹配已有详情，不写控件或造TimelineItem。
            try
            {
                ExactMethod(timeline.GetType(), "createEventContent", true, typeof(StringBuilder), typeof(StringBuilder),
                    GameType("GameState"), GameType("TimelineItem")).Invoke(null, new object[] { first, second, state, item });
            }
            catch (TargetInvocationException error)
            {
                Exception actual = error;
                while (actual is TargetInvocationException && actual.InnerException != null) actual = actual.InnerException;
                if (!(actual is KeyNotFoundException)) throw;
                var type = Property(item, "Type");
                if (!(bool)Property(type, "IsEvent")) throw;
                var eventId = Property(Property(type, "AsEvent"), "Id");
                var evt = Call(Property(state, "Lookup"), "Event", eventId);
                Skipped(session, item, eventId, (bool)Property(item, "PlayerAttended"), (bool)Call(item, "IsInFuture", state),
                    Description(evt), "details-missing-scene", actual.GetType().Name + ": " + actual.Message,
                    "createEventContent->TimelineItem.Details(lastUsedGameState)");
                continue;
            }
            UiMethod(uiStrings, "AddParagraphBreakIfPriorContent", typeof(StringBuilder)).Invoke(null, new object[] { first });
            first.Append(second);
            if (first.ToString() == session.InitialSource) return (string)Property(item, "Key");
        }
        throw new InvalidOperationException("最初详情原文无法绑定真实currentItems键，禁止未经来源确认的恢复");
    }
    private static IEnumerator Restore(Session session)
    {
        session.SetMode(true);
        Call(session.Timeline, "DeactivateEventInfoPopup");
        int attempts = 0;
        while (Convert.ToInt32(Field(session.Timeline, "loopToShow")) != session.InitialLoop && attempts++ < 3)
        {
            int before = Convert.ToInt32(Field(session.Timeline, "loopToShow"));
            // loopToShow=0为当前循环，历史越早索引越大；Previous递增，Next递减。
            string field = before > session.InitialLoop ? "NextLoopButton" : "PreviousLoopButton";
            Click(Field(session.Timeline, field));
            yield return null;
            float until = Time.realtimeSinceStartup + 0.8f;
            while ((bool)Field(session.Timeline, "isLoading") && Time.realtimeSinceStartup < until) yield return null;
            int after = Convert.ToInt32(Field(session.Timeline, "loopToShow"));
            bool complete = !(bool)Field(session.Timeline, "isLoading");
            session.Write("LOOP_NAV", field + ".OnClick", before, after, complete);
            if (!complete || after == before) throw new InvalidOperationException("恢复原循环的真实按钮请求没有完成");
        }
        if (Convert.ToInt32(Field(session.Timeline, "loopToShow")) != session.InitialLoop)
            throw new InvalidOperationException("真实左右按钮未恢复最初循环");
        object selected = null;
        foreach (var pair in (IEnumerable)Field(session.Timeline, "currentItems"))
            if ((string)Property(Field(pair, "Item1"), "Key") == session.InitialKey && Clickable(Field(pair, "Item2")))
            { selected = Field(pair, "Item2"); break; }
        if (selected == null) throw new InvalidOperationException("原循环恢复后没有最初详情的真实按钮");
        Click(selected);
        yield return new WaitForSecondsRealtime(0.12f);
        string actual = ((StringBuilder)Field(session.Timeline, "builder1")).ToString();
        session.Write("RESTORE", session.InitialLoop, B64(session.InitialKey), B64(session.InitialSource),
            B64(actual), actual == session.InitialSource, Owns(session), "original-item.button.OnClick");
        if (actual != session.InitialSource || !Owns(session)) throw new InvalidOperationException("最初详情源或UI归属未恢复");
    }
    private static IEnumerator Core(Session session)
    {
        session.Write("SCHEMA", 1);
        session.Write("METHOD", "真实时间线按钮采样与真实资源格式器组件重放分别验证；不称完整游玩E2E");
        if (!OwnerEvidence(session, "INITIAL", "initial", "translated"))
            throw new InvalidOperationException("Capture须在真实时间线详情页激活后调用");
        int startLoop = Convert.ToInt32(Field(session.Timeline, "loopToShow"));
        session.InitialLoop = startLoop;
        session.InitialSource = ((StringBuilder)Field(session.Timeline, "builder1")).ToString();
        session.InitialKey = InitialKey(session);
        session.Write("START_LOOP", startLoop);
        session.Write("INITIAL_DETAIL", B64(session.InitialKey), B64(session.InitialSource), Hash(session.InitialSource), Owns(session));
        yield return RealLoop(session);
        int moved = 0;
        while (moved < 2 && Time.realtimeSinceStartup < session.Deadline - 5f
            && (!session.Captured.Contains("empty-one") || !session.Captured.Contains("empty-many") || !session.Captured.Contains("queen-room")))
        {
            Call(session.Timeline, "DeactivateEventInfoPopup");
            var previous = Field(session.Timeline, "PreviousLoopButton");
            if (!Clickable(previous)) break;
            int before = Convert.ToInt32(Field(session.Timeline, "loopToShow"));
            Click(previous);
            float wait = Math.Min(session.Deadline - 4.5f, Time.realtimeSinceStartup + 0.8f);
            yield return null;
            while ((bool)Field(session.Timeline, "isLoading") && Time.realtimeSinceStartup < wait) yield return null;
            int after = Convert.ToInt32(Field(session.Timeline, "loopToShow"));
            bool complete = !(bool)Field(session.Timeline, "isLoading");
            session.Write("LOOP_NAV", "PreviousLoopButton.OnClick", before, after, complete);
            if (after != before + 1 || !complete) break;
            moved++;
            // 没有开着详情时先点真实事件，随后再采集目标。
            yield return RealLoop(session);
        }
        foreach (var role in new string[] { "empty-one", "empty-many", "queen-room" })
            session.Write("COVERAGE", role, session.Captured.Contains(role) ? "AVAILABLE" : "UNAVAILABLE",
                B64(session.Captured.Contains(role) ? "真实currentItems按钮已采样" : "冻结存档在有限当前/历史循环导航中没有可点击的该类事件；不造剧情"));
        foreach (var description in new string[] { "Hamlet's ravings interrupt my sleep.", "Polonius questions Hamlet.",
            "Horatio and Gertrude have a heart to heart.", "Quince puts on the play that Hamlet designed.", "Hamlet presses his Mother on Claudius's actions." })
            session.Write("STORY_COVERAGE", B64(description), session.SeenDescriptions.Contains(description) ? "PRESENT_IN_VISITED_ITEMS" : "UNAVAILABLE",
                "仅记录当前与已访问历史loop；资源重放不提高此覆盖结论");
        // 若无代表性目标，仍需真实打开一项后才能向激活的InfoText做组件重放。
        if (!session.Text.gameObject.activeInHierarchy)
        {
            object first = null;
            foreach (var tuple in (IEnumerable)Field(session.Timeline, "currentItems"))
                if (Clickable(Field(tuple, "Item2"))) { first = Field(tuple, "Item2"); break; }
            if (first == null) throw new InvalidOperationException("真实时间线没有可打开的详情控件");
            Click(first);
            yield return null;
        }
        string originalBuilder = ((StringBuilder)Field(session.Timeline, "builder1")).ToString();
        try { yield return Replay(session); }
        finally
        {
            session.SetMode(true);
            session.Text.SetText(new StringBuilder(originalBuilder));
        }
        yield return Restore(session);
        session.Write("STATUS", "COMPLETE", session.RealCount, Time.realtimeSinceStartup - (session.Deadline - 10f));
    }
    private static IEnumerator Guard(Session session)
    {
        var stack = new Stack<IEnumerator>();
        stack.Push(Core(session));
        while (stack.Count > 0)
        {
            bool more;
            object current = null;
            try { more = stack.Peek().MoveNext(); if (more) current = stack.Peek().Current; }
            catch (Exception error)
            {
                foreach (var routine in stack) { var disposable = routine as IDisposable; if (disposable != null) disposable.Dispose(); }
                session.SetMode(true);
                session.Write("FAILURE", B64(error.ToString()));
                session.Write("STATUS", "FAILED");
                yield break;
            }
            if (!more) { stack.Pop(); continue; }
            var nested = current as IEnumerator;
            if (nested != null) { stack.Push(nested); continue; }
            yield return current;
        }
    }
    public static IEnumerator Capture(string outputDirectory, Action<bool> setMode)
    {
        if (setMode == null) throw new ArgumentNullException("setMode");
        Directory.CreateDirectory(outputDirectory);
        var timeline = (Component)Field(ObjectTracker.Instance.Gui, "timelineCanvas");
        var session = new Session { Path = System.IO.Path.Combine(outputDirectory, "timeline-followup.tsv"),
            Deadline = Time.realtimeSinceStartup + 10f, Timeline = timeline,
            Text = (TMP_Text)Field(timeline, "InfoText"), SetMode = setMode };
        File.WriteAllText(session.Path, "", new UTF8Encoding(false));
        return Guard(session);
    }
}
