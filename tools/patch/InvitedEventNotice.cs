using System;
using System.Collections;
using System.Reflection;
using System.Text;
using HarmonyLib;

// 原格式器缺少负向 invited 分支；仅补齐时间线信息撤回的玩家提示。
// 不改逻辑事实、事件排程、存档或正向获知通知，正文仍交给 XUnity 离线翻译。
public static class InvitedEventNotice
{
    private const BindingFlags Members = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
    public const string SingleWithoutDescription = "<b>Ophelia</b> no longer has a future event on her <b>Timeline</b>.";
    public const string Multiple = "<b>Ophelia</b> no longer has multiple future events on her <b>Timeline</b>.";
    public const string DescribedPrefix = "<b>Ophelia</b> no longer has this future event on her <b>Timeline</b>: ";

    public static void Apply(Harmony harmony)
    {
        foreach (Assembly assembly in AppDomain.CurrentDomain.GetAssemblies())
        {
            Type model = assembly.GetType("Elsinore.Game.Model", false);
            if (model == null) continue;
            Type state = assembly.GetType("Elsinore.Game.GameState", true);
            Type group = assembly.GetType("Agakme.Scripting.GroupedLiterals", true);
            MethodInfo formatter = model.GetMethod("formatGroupedLiterals", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic,
                null, new Type[] { state, typeof(StringBuilder), group }, null);
            if (formatter == null || formatter.ReturnType != typeof(void)) throw new MissingMethodException("Model.formatGroupedLiterals");
            harmony.Patch(formatter, prefix: new HarmonyMethod(typeof(InvitedEventNotice).GetMethod("Prefix")));
            return;
        }
        throw new TypeLoadException("Elsinore.Game.Model");
    }

    // Harmony 按参数序号绑定，避免对原 F# 参数名作假设。
    public static bool Prefix(object __0, StringBuilder __1, object __2)
    {
        string notice;
        if (__1 == null || !TryFormat(__0, __2, out notice)) return true;
        __1.Append(notice);
        return false;
    }

    public static bool TryFormat(object state, object group, out string notice)
    {
        notice = null;
        try
        {
            if (state == null || group == null || group.GetType().FullName != "Agakme.Scripting.GroupedLiterals") return false;
            Array literals = Read(group, "Literals") as Array;
            if (literals == null || literals.Length == 0) return false;
            object schedule = Read(Read(state, "Data"), "Schedule");
            if (schedule == null) return false;
            Assembly gameAssembly = state.GetType().Assembly;
            Type eventIdType = gameAssembly.GetType("Elsinore.Game.HEventId", false);
            if (eventIdType == null) return false;
            MethodInfo eventOf = schedule.GetType().GetMethod("EventOf", Members, null, new Type[] { eventIdType }, null);
            if (eventOf == null) return false;
            string firstDescription = null;
            for (int index = 0; index < literals.Length; index++)
            {
                object literal = literals.GetValue(index);
                if (!Object.Equals(Read(literal, "IsPositive"), false)) return false;
                object atom = Read(literal, "Atom");
                if (!Object.Equals(Read(atom, "Name"), "invited")) return false;
                IEnumerable arguments = Read(atom, "Args") as IEnumerable;
                if (arguments == null) return false;
                object argument = null;
                int count = 0;
                foreach (object value in arguments) { argument = value; count++; }
                if (count != 1) return false;
                string eventName = Read(argument, "AsSymbolConstant") as string;
                if (String.IsNullOrEmpty(eventName)) return false;
                object eventId = Activator.CreateInstance(eventIdType, new object[] { eventName });
                object actualEvent = eventOf.Invoke(schedule, new object[] { eventId });
                if (actualEvent == null) return false;
                object descriptionOption = Read(actualEvent, "Description");
                string description = descriptionOption == null ? null : Read(descriptionOption, "Value") as string;
                if (descriptionOption != null && description == null) return false;
                if (index == 0) firstDescription = description;
            }
            notice = literals.Length > 1 ? Multiple : firstDescription == null ? SingleWithoutDescription
                : DescribedPrefix + firstDescription;
            return true;
        }
        catch
        {
            // 无法确认反射契约或事件来源时保守放行，绝不猜测内部 ID 的含义。
            notice = null;
            return false;
        }
    }

    private static object Read(object owner, string name)
    {
        if (owner == null) return null;
        Type type = owner.GetType();
        PropertyInfo property = type.GetProperty(name, Members);
        if (property != null) return property.GetValue(owner, null);
        FieldInfo field = type.GetField(name + "@", Members) ?? type.GetField(name, Members);
        return field == null ? null : field.GetValue(owner);
    }
}
