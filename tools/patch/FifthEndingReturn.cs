using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using System.Reflection.Emit;
using HarmonyLib;

// 仅补第五次归来的缺口，不改计数、持久事实或原游戏文件。
public static class FifthEndingReturn
{
    public const string TargetMethod = "Invoke_Spine_ReturnToGame__SC_SPINE_ReturnToGame__0";
    public const string CommonLine = "<i>Let me give you what you came here for. We have nothing more to say to one another, after all.</i>";
    private static FieldInfo logicStateField;
    private static Action<string> warning;
    private static bool warned;

    public static void Apply(Harmony harmony, Action<string> logWarning)
    {
        Type generated = AccessTools.TypeByName("GameDataGenerated");
        MethodInfo method = generated == null ? null : AccessTools.DeclaredMethod(generated, TargetMethod, Type.EmptyTypes);
        logicStateField = generated == null ? null : AccessTools.Field(generated, "_logicState");
        if (method == null || method.ReturnType != typeof(void) || logicStateField == null
            || logicStateField.FieldType.FullName != "Agakme.Logic+LogicState")
            throw new MissingMethodException("第五次归来场景或逻辑状态接口不兼容");
        warning = logWarning;
        harmony.Patch(method, transpiler: new HarmonyMethod(typeof(FifthEndingReturn), "Transpile"));
    }

    public static IEnumerable<CodeInstruction> Transpile(IEnumerable<CodeInstruction> instructions)
    {
        var code = new List<CodeInstruction>(instructions);
        int match = -1;
        for (int index = 0; index + 2 < code.Count; index++)
        {
            FieldInfo condition = code[index].operand as FieldInfo;
            MethodInfo holds = code[index + 1].operand as MethodInfo;
            if (code[index].opcode != OpCodes.Ldfld || condition == null
                || condition.DeclaringType.FullName != "GameDataGenerated" || condition.Name != "allocated_1383"
                || code[index + 1].opcode != OpCodes.Call || holds == null || holds.Name != "holds"
                || holds.ReturnType != typeof(bool) || holds.GetParameters().Length != 1
                || holds.GetParameters()[0].ParameterType.FullName != "Agakme.CompiledCnf"
                || (code[index + 2].opcode != OpCodes.Brfalse && code[index + 2].opcode != OpCodes.Brfalse_S))
                continue;
            bool ellipsis = false, common = false;
            for (int next = index + 3; next < Math.Min(code.Count, index + 45); next++)
            {
                if (code[next].opcode != OpCodes.Ldstr) continue;
                ellipsis |= (string)code[next].operand == "<i>...</i>";
                common |= (string)code[next].operand == CommonLine;
            }
            if (!ellipsis || !common || match >= 0)
                throw new InvalidOperationException("归来共用对白分支不唯一或结构已变化");
            match = index + 2;
        }
        if (match < 0) throw new InvalidOperationException("未找到已核实的第五次归来条件缺口");
        // holds原结果留在栈上；只在这个调用点加第五次的兼容判断。
        code.InsertRange(match, new CodeInstruction[] {
            new CodeInstruction(OpCodes.Ldarg_0),
            new CodeInstruction(OpCodes.Call, typeof(FifthEndingReturn).GetMethod("IncludeFifth"))
        });
        return code;
    }

    public static bool IncludeFifth(bool original, object interpreter)
    {
        if (original) return true;
        try
        {
            FieldInfo field = logicStateField ?? AccessTools.Field(interpreter.GetType(), "_logicState");
            object state = field.GetValue(interpreter);
            object domain = state.GetType().GetProperty("Domain").GetValue(state, null);
            IEnumerable counters = (IEnumerable)domain.GetType().GetProperty("AllCounters").GetValue(domain, null);
            // 根据实际域查找命名计数器，不硬编码玩家存档或编译域的下标。
            foreach (object counter in counters)
            {
                PropertyInfo name = counter.GetType().GetProperty("Name");
                PropertyInfo args = counter.GetType().GetProperty("Args");
                if (name == null || args == null || (string)name.GetValue(counter, null) != "numberEndingsBurned") continue;
                if (((IEnumerable)args.GetValue(counter, null)).GetEnumerator().MoveNext()) continue;
                MethodInfo value = state.GetType().GetMethod("CounterValue", new Type[] { counter.GetType() });
                if (value == null) throw new MissingMethodException("LogicState.CounterValue");
                return (int)value.Invoke(state, new object[] { counter }) == 5;
            }
            throw new MissingFieldException("numberEndingsBurned");
        }
        catch (Exception error)
        {
            if (!warned)
            {
                warned = true;
                if (warning != null) warning("第五次归来计数接口不兼容，保留原行为：" + error.GetType().Name);
            }
            return original;
        }
    }
}
