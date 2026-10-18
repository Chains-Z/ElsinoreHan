using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.Remoting.Messaging;
using System.Runtime.Remoting.Proxies;
using System.Web.Script.Serialization;
using Agakme;
using HarmonyLib;
using Microsoft.FSharp.Collections;

// 离线运行真实生成场景；舞台API仅记录排队，不执行Unity、音频、保存或退出。
public static class FifthEndingReturnTests
{
    private static string[] directories;
    private static int assertions;

    private sealed class SilentApi : RealProxy
    {
        public SilentApi(Type type) : base(type) { }
        public override IMessage Invoke(IMessage message)
        {
            var call = (IMethodCallMessage)message;
            var method = (MethodInfo)call.MethodBase;
            object value = method.ReturnType.IsValueType && method.ReturnType != typeof(void)
                ? Activator.CreateInstance(method.ReturnType) : null;
            return new ReturnMessage(value, new object[0], 0, call.LogicalCallContext, call);
        }
    }

    private static Assembly Resolve(object sender, ResolveEventArgs args)
    {
        string name = new AssemblyName(args.Name).Name + ".dll";
        foreach (string directory in directories)
        {
            string path = Path.Combine(directory, name);
            if (File.Exists(path)) return Assembly.LoadFrom(path);
        }
        return null;
    }

    private static void Check(bool value, string message)
    {
        assertions++;
        if (!value) throw new InvalidOperationException(message);
    }

    private static FieldInfo Field(Type type, string name) { return AccessTools.Field(type, name); }

    private static Agakme.Logic.LogicState State(int value)
    {
        var empty = FSharpList<GroundTerm>.Empty;
        var counters = new Tuple<GroundAtom, Agakme.Logic.TruthMode>[] {
            Tuple.Create(new GroundAtom("unrelatedCounter", empty), Agakme.Logic.TruthMode.Persistent),
            Tuple.Create(new GroundAtom("numberEndingsBurned", empty), Agakme.Logic.TruthMode.Persistent)
        };
        var domain = new Agakme.Logic.LogicDomain(new Agakme.Logic.LogicDomainData(
            new Tuple<GroundAtom, Agakme.Logic.TruthMode>[0], counters));
        var state = new Agakme.Logic.LogicState(domain);
        Field(state.GetType(), "counters").SetValue(state, new int[] { 77, value });
        // 真实生成Cnf使用原版域下标；只在隔离测试内设置相应布尔输入。
        Field(state.GetType(), "facts").SetValue(state, new bool[30000]);
        return state;
    }

    private static void SetCondition(Agakme.Logic.LogicState state, object interpreter, string field, bool value)
    {
        var cnf = (CompiledCnf)Field(interpreter.GetType(), field).GetValue(interpreter);
        var facts = (bool[])Field(state.GetType(), "facts").GetValue(state);
        foreach (CompiledLiteral[] clause in cnf.CompiledConjuncts)
            foreach (CompiledLiteral literal in clause)
            {
                facts[literal.Index] = literal.IsPositive ? value : !value;
            }
    }

    private static List<string> RunScene(Type generated, MethodInfo method, int count)
    {
        object interpreter = Activator.CreateInstance(generated);
        var state = State(count);
        Field(generated, "_logicState").SetValue(interpreter, state);
        foreach (string name in new string[] { "_stageApi", "_scriptApi" })
        {
            FieldInfo field = Field(generated, name);
            field.SetValue(interpreter, new SilentApi(field.FieldType).GetTransparentProxy());
        }
        Field(generated, "doCollectActions").SetValue(interpreter, true);
        foreach (string name in new string[] { "simulationResult", "logicChanges", "blocks" })
        {
            FieldInfo field = Field(generated, name);
            field.SetValue(interpreter, Activator.CreateInstance(field.FieldType));
        }
        SetCondition(state, interpreter, "allocated_1368", count == 1);
        SetCondition(state, interpreter, "allocated_1380", count == 2);
        SetCondition(state, interpreter, "allocated_1381", count == 3);
        SetCondition(state, interpreter, "allocated_1382", count == 4);
        SetCondition(state, interpreter, "allocated_1383", count > 5);
        method.Invoke(interpreter, null);
        var text = new List<string>();
        foreach (object action in (IEnumerable)Field(generated, "simulationResult").GetValue(interpreter))
            text.Add(action.ToString());
        Check(state.CounterValue(new GroundAtom("numberEndingsBurned", FSharpList<GroundTerm>.Empty)) == count,
              "归来修复不得改写正式采用次数");
        Check(state.CounterValue(new GroundAtom("unrelatedCounter", FSharpList<GroundTerm>.Empty)) == 77,
              "不得改写其他计数器");
        return text;
    }

    public static IEnumerable<CodeInstruction> StopBeforeReturnTransition(IEnumerable<CodeInstruction> instructions)
    {
        var code = new List<CodeInstruction>(instructions);
        for (int index = 2; index < code.Count; index++)
        {
            var method = code[index].operand as MethodInfo;
            if (method == null || method.Name != "assertLogic") continue;
            // 对话分支之后原版会写本轮状态并递增其他计数；此离线重放在该处结束。
            // 保留原跳转标签，使所有原版分支正常汇入ret；这个截断只存在于测试CLI。
            Check(code[index - 2].opcode == OpCodes.Ldarg_0, "原版归来状态转换结构变化");
            code[index - 2].opcode = OpCodes.Ret;
            code[index - 2].operand = null;
            return code.GetRange(0, index - 1);
        }
        throw new InvalidOperationException("未找到对话之后的原版返回状态转换");
    }

    private static void Run(string root, string managed)
    {
        Assembly game = Assembly.LoadFrom(Path.Combine(managed, "Assembly-CSharp.dll"));
        Type generated = game.GetType("GameDataGenerated", true);
        MethodInfo method = generated.GetMethod(FifthEndingReturn.TargetMethod);
        var original = PatchProcessor.GetOriginalInstructions(method, (ILGenerator)null);
        var changed = new List<CodeInstruction>(FifthEndingReturn.Transpile(original));
        Check(changed.Count == original.Count + 2, "只能增加一个读取实例和一个局部判断调用");
        int before = 0, additions = 0;
        foreach (CodeInstruction instruction in changed)
        {
            if (before < original.Count && Object.ReferenceEquals(instruction, original[before])) before++;
            else additions++;
        }
        Check(before == original.Count && additions == 2, "原方法每条指令必须完整保留");
        bool rejected = false;
        try { new List<CodeInstruction>(FifthEndingReturn.Transpile(new CodeInstruction[0])); }
        catch (InvalidOperationException) { rejected = true; }
        Check(rejected, "未知版本结构应拒绝修补");
        var withoutLine = new List<CodeInstruction>();
        foreach (CodeInstruction instruction in original)
            withoutLine.Add(instruction.opcode == OpCodes.Ldstr && (string)instruction.operand == FifthEndingReturn.CommonLine
                ? new CodeInstruction(OpCodes.Ldstr, "未知版本的对白") : instruction);
        rejected = false;
        try { new List<CodeInstruction>(FifthEndingReturn.Transpile(withoutLine)); }
        catch (InvalidOperationException) { rejected = true; }
        Check(rejected, "已核实对白锚点改变时必须拒绝修补");
        var isolation = new Harmony("elsinorehan.tests.fifthreturn.isolation");
        isolation.Patch(method, transpiler: new HarmonyMethod(typeof(FifthEndingReturnTests), "StopBeforeReturnTransition"));
        var oldResults = new Dictionary<int, List<string>>();
        for (int count = 0; count <= 12; count++) oldResults[count] = RunScene(generated, method, count);
        var harmony = new Harmony("elsinorehan.tests.fifthreturn");
        FifthEndingReturn.Apply(harmony, message => { throw new InvalidOperationException(message); });
        try
        {
            for (int count = 0; count <= 12; count++)
            {
                List<string> after = RunScene(generated, method, count);
                string previous = String.Join("\n", oldResults[count].ToArray());
                string current = String.Join("\n", after.ToArray());
                if (count == 5)
                {
                    Check(!previous.Contains("We have nothing more"), "必须复现原版第五次漏分支");
                    Check(current.Contains("We have nothing more"), "第五次应排入原版共用对白");
                    Check(after.Count == oldResults[count].Count + 2, "恰好补入原来的两条对白队列项");
                }
                else Check(previous == current, "其他次数排队的舞台和对白必须逐字不变：" + count);
            }
        }
        finally { harmony.UnpatchSelf(); isolation.UnpatchSelf(); }
        Console.WriteLine(new JavaScriptSerializer().Serialize(new {
            passed = true, assertions = assertions, counts = 13,
            original_fifth_missing_reproduced = true, patched_fifth_common_dialogue = true,
            other_counts_unchanged = true, counters_unchanged = true,
            layer = "真实生成场景的对话分支与逻辑状态离线集成；舞台API替身，末尾状态转换截断"
        }));
    }

    public static int Main(string[] args)
    {
        try
        {
            string root = Path.GetFullPath(args[0]);
            directories = new string[] { args[1], Path.Combine(root, "runtime/build"),
                Path.Combine(root, "runtime/vendor/BepInEx5/BepInEx/core") };
            AppDomain.CurrentDomain.AssemblyResolve += Resolve;
            Run(root, args[1]);
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine(error.ToString());
            return 1;
        }
    }
}
