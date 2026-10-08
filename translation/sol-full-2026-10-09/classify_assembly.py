"""复建已人工审阅的程序集用途分类，不翻译、联网或运行游戏。"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "analysis"))
import analyze


TRANSLATE_UI = {
    12,13,15,722,912,918,919,920,921,924,925,926,928,929,930,931,932,933,934,935,936,937,
    940,941,942,943,944,945,947,948,949,951,952,953,954,
    *range(956,975),981,983,986,987,997,998,999,1028,1029,1030,
}
UNCERTAIN_SAMPLE_UI = {*range(810,842), *range(849,857), 863}
UNCERTAIN_OTHER = {982,1033}
ENGINE_IDENTIFIERS = {56,695}
INPUT_IDENTIFIERS = {842,843,846,847,848}
TEST_PLACEHOLDERS = {914,923}
UI_TEMPLATES = {928,929,930,932,933,941,942,947,948,949,951,952,
               956,961,963,965,967,969,971,973,997,999,1030}


def decision_for(index, methods):
    """索引集合来自全量逐条审阅，并以真实 IL 引用方法核对用途。"""
    if 57 <= index <= 687:
        if not all("DataGenerated.Invoke_" in method for method in methods):
            raise ValueError("对白引用范围出现非剧情方法，须重新人工核查")
        return "translate", "dialogue", "编译剧情方法中的角色对白/内心话或旁白；可见文本应翻译，保留原有富文本与打断。静态存在不证明本次游玩会触发。"
    if index in TRANSLATE_UI:
        if index in (12,13,15,943):
            reason = "存档版本迁移/进度重置的玩家告知，非内部修复日志。"
        elif index == 722:
            reason = "EndingBookObject 的 IInteractable.Tooltip 返回值，是交互物件提示名称。"
        elif 956 <= index <= 974:
            reason = "TutorialPromptUI.GetTutorialText 的操作教程；保留按键占位符和操作条件。"
        elif index in (929,986,987,997,998,999):
            reason = "游戏历史/日志界面的玩家可见叙述模板；不是调试日志，保留占位符及拼接边界。"
        elif index in (947,948,949,951,952,953,954,1028,1029,1030):
            reason = "TimelineUI 的事件状态、工具提示或时间线标题；保留条件和占位符。"
        elif index == 930:
            reason = "PauseUI.Awake 初始化的退出确认模板；--- 为初始占位内容，保留其形式，不与秒/分钟实际模板合并。"
        elif index in UI_TEMPLATES:
            reason = "实际游戏界面/提示的格式或拼接模板；只翻译可见措辞，完整保留参数、标记和边界空白。"
        else:
            reason = "实际游戏界面的按钮、确认/错误提示、结局说明或工具提示，具备明确玩家可见用途。"
        return "translate", "ui_template" if index in UI_TEMPLATES else "ui", reason
    if index in UNCERTAIN_SAMPLE_UI:
        return "uncertain", "sample_ui", "引用来自 Rewired 的控制器/重映射演示或样例界面；静态程序集含样例不证明 Elsinore 实际启用。暂不加入汉化词表，须证明玩家入口后再译。"
    if index == 982:
        return "uncertain", "build_label", "ExplorationUI.Activate 中的构建日期/版本标签；是否仅开发模式显示尚未核实。暂不加入词表，保留版本参数。"
    if index == 1033:
        return "uncertain", "missing_data_placeholder", "角色资料 OnEnable 回调中的 NO CHARACTER BIO 缺数据占位；可能只在异常/调试状态出现，尚未证明正常玩家入口。暂不加入词表。"
    if index in ENGINE_IDENTIFIERS:
        return "exclude", "engine_identifier", "Unity 图层名或反射相机对象标识，供程序匹配/内部对象命名，不是玩家文案，禁止翻译。"
    if index in INPUT_IDENTIFIERS:
        return "exclude", "input_identifier", "控制器样例 Update/GetInput 中的 Rewired 输入动作查询名；修改会破坏动作匹配，不是界面标签。"
    if index in TEST_PLACEHOLDERS:
        return "exclude", "test_placeholder", "界面初始化中的测试/示例占位文案，正文明确为 pretty long string 或重复 test，不作为正式玩家文案。"
    if 799 <= index <= 808 or index in (857,858):
        return "exclude", "diagnostic", "输入模块 ToString/指针事件样例的技术调试字段，非正常游戏玩家说明。"
    if 978 <= index <= 980 or 1001 <= index <= 1003:
        return "exclude", "developer_console", "开发者 Console/ElsinoreConsole 的命令帮助、模拟状态分析或未实现标记，非玩家界面文本。"
    if 760 <= index <= 795 or 1018 <= index <= 1020:
        return "exclude", "middleware_diagnostic", "Steamworks/Wwise 中间件初始化、音频库或参数错误诊断，不应进入汉化词表。"
    if 0 <= index <= 55 or 1004 <= index <= 1017:
        return "exclude", "diagnostic", "配置、存档、加载、调度或阶段执行的内部状态/错误日志；不是玩家提示。"
    return "exclude", "diagnostic", "路径、房间、角色动画、UI 状态、输入或遥测的内部诊断/异常文本；引用方法和内容均指向程序运行检查，不进入玩家词表。"


def main():
    source_path = ROOT / "analysis/assembly_review.json"
    review = json.loads(source_path.read_text(encoding="utf-8"))
    callsites = json.loads((OUT / "assembly-callsites.json").read_text(encoding="utf-8-sig"))
    grouped = {}
    for entry in callsites:
        grouped.setdefault(entry["index"], []).append({"method": entry["method"], "il_offset": entry["il_offset"]})
    if len(review) != 1036 or set(grouped) != set(range(1036)):
        raise ValueError("程序集候选或引用覆盖范围变更，须重新核查")
    assembly_path = analyze.GAME / "Managed/Assembly-CSharp.dll"
    raw_strings = dict(analyze.read_user_strings(assembly_path))
    classified = []
    for index, row in enumerate(review):
        offset = int(row["origin"].rsplit(":",1)[1])
        if raw_strings[offset] != row["text"]:
            raise ValueError(f"原始 #US 不一致: {index}")
        methods = sorted({value["method"] for value in grouped[index]})
        decision, kind, reason = decision_for(index, methods)
        classified.append({"index": index, "source": row["text"], "origin": row["origin"],
                           "decision": decision, "reason": reason, "kind": kind,
                           "source_sha256": hashlib.sha256(row["text"].encode()).hexdigest(),
                           "methods": methods, "references": grouped[index]})
    (OUT / "assembly-classification.json").write_text(json.dumps(classified, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    summary = {"count": len(classified), "decisions": dict(Counter(row["decision"] for row in classified)),
               "kinds": dict(Counter(row["kind"] for row in classified)),
               "assembly_sha256": hashlib.sha256(assembly_path.read_bytes()).hexdigest(),
               "review_file_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
               "all_exact_us_strings_verified": True, "all_static_references_found": True,
               "static_reference_count": len(callsites), "model_calls": 0,
               "notes": ["已逐条阅读候选，再核查静态 IL 的真实引用方法", "translate 不证明所有剧情分支或 UI 本次实际触发", "uncertain 必须先证明玩家入口，不能自动加入词表", "玩家历史界面的叙述格式模板可翻译，程序诊断日志不可翻译", "当前仅分类，没有正文译文"]}
    (OUT / "assembly-classification-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=True))


if __name__ == "__main__":
    main()
