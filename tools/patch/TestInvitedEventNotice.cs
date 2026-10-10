using System;
using System.IO;
using System.Text;
using System.Reflection;
using System.Runtime.InteropServices;
using Agakme;
using Agakme.Scripting;
using Elsinore.Game;
using Microsoft.FSharp.Collections;
using HarmonyLib;

// 在 CLR 内解析真实资源并调用真实 Model；不启动 Unity 或读取存档。
public static class TestInvitedEventNotice
{
    [DllImport("kernel32.dll")]
    private static extern uint GetErrorMode();
    private static int assertions;
    private static void Equal(object actual, object expected, string name)
    {
        if (!Object.Equals(actual, expected)) throw new Exception(name + ": " + actual + " != " + expected);
        assertions++;
    }
    private static GroundLiteral Literal(string eventId, bool positive)
    {
        return new GroundLiteral(Model.Atom.Invited(new HEventId(eventId)), positive);
    }
    private static GroupedLiterals Group(params GroundLiteral[] literals)
    {
        return new GroupedLiterals(null, literals);
    }
    private static string Format(GameState state, GroupedLiterals group)
    {
        StringBuilder builder = new StringBuilder("existing-prefix|");
        Model.formatGroupedLiterals(state, builder, group);
        return builder.ToString();
    }
    public static void Main(string[] args)
    {
        Console.OutputEncoding = Encoding.UTF8;
        try
        {
            // 防护必须由父进程在启动前设置，覆盖 CLR 进入 Main 之前的加载错误。
            Equal((GetErrorMode() & 3u), 3u, "继承父进程的错误窗口抑制");
            Run(args);
        }
        catch (Exception error)
        {
            string detail = error.Message ?? "";
            if (detail.Length > 800) detail = detail.Substring(detail.Length - 800);
            Console.Error.WriteLine(error.GetType().FullName + ": " + detail);
            System.Environment.ExitCode = 1;
        }
    }
    private static void Run(string[] args)
    {
        var parsed = Agakme.IO.Json.ParseWithMeta(File.ReadAllText(args[0]), "schedule");
        var schedule = Schedule.Parse(FSharpList<Agakme.IO.Json.ParseResult>.Cons(parsed, FSharpList<Agakme.IO.Json.ParseResult>.Empty));
        var names = NameList.Parse(Agakme.IO.Json.ParseWithMeta(File.ReadAllText(args[1]), "names"));
        var data = new ElsinoreData(default(GameMode), null, schedule, names, null, null, null, null, null, null, null, null, null, null, null, null, null);
        var state = new GameState(data, null, null, null, null, null, null);
        var negative = Group(Literal("SC_SPINE_ThePlay", false));
        var positive = Group(Literal("SC_SPINE_ThePlay", true));
        var mixed = Group(Literal("SC_SPINE_ThePlay", false), Literal("SC_ASSN_ThePlay_Assassin", true));
        var unrelated = Group(new GroundLiteral(new GroundAtom("unknown_internal", FSharpList<GroundTerm>.Empty), false));
        Equal(Format(state, negative), "existing-prefix|ERROR: UNFORMATTED: invited(SC_SPINE_ThePlay)", "原格式器复现负向缺口");
        string positiveBefore = Format(state, positive);
        string mixedBefore = Format(state, mixed);
        string unrelatedBefore = Format(state, unrelated);
        string scheduleBefore = Agakme.IO.Json.Serialize(schedule.ToJson());
        InvitedEventNotice.Apply(new Harmony("elsinorehan.test.invited-event-notice"));
        string description = schedule.EventOf(new HEventId("SC_SPINE_ThePlay")).Description.Value;
        Equal(Format(state, negative), "existing-prefix|" + InvitedEventNotice.DescribedPrefix + description, "真实方法注册后的负向通知");
        Equal(Format(state, positive), positiveBefore, "正向通知保持原格式器");
        Equal(Format(state, mixed), mixedBefore, "混合正负保持原格式器");
        Equal(Format(state, unrelated), unrelatedBefore, "其它谓词保持原格式器");
        Equal(Format(state, Group(Literal("SC_SPINE_ThePlay", false), Literal("SC_ASSN_ThePlay_Assassin", false))),
            "existing-prefix|" + InvitedEventNotice.Multiple, "多个负向事件");
        string noDescriptionId = null;
        foreach (var item in schedule.Events) if (item.Description == null) { noDescriptionId = item.Id.Name; break; }
        if (noDescriptionId == null) throw new Exception("真实 schedule 缺少无描述测试条目");
        Equal(Format(state, Group(Literal(noDescriptionId, false))), "existing-prefix|" + InvitedEventNotice.SingleWithoutDescription,
            "无描述负向事件");
        StringBuilder untouched = new StringBuilder("existing-prefix|");
        Equal(InvitedEventNotice.Prefix(state, untouched, Group(Literal("not-a-real-event", false))), true, "未知事件保守放行");
        Equal(untouched.ToString(), "existing-prefix|", "放行时 builder 未写入");
        Equal(InvitedEventNotice.Prefix(null, untouched, negative), true, "空 state 保守放行");
        Equal(InvitedEventNotice.Prefix(state, untouched, Group()), true, "空组保守放行");
        Equal(InvitedEventNotice.Prefix(state, null, negative), true, "空 builder 保守放行");
        Equal(Agakme.IO.Json.Serialize(schedule.ToJson()), scheduleBefore, "实际排程逐字未改");
        Equal(negative.Literals[0].IsPositive, false, "原逻辑条件未翻为正向");
        Equal(negative.Literals[0].Atom.Args.Head.AsSymbolConstant, "SC_SPINE_ThePlay", "原逻辑参数未改");
        Console.WriteLine("{\"passed\":true,\"assertions\":" + assertions + ",\"real_formatter\":true,\"game_started\":false}");
    }
}
