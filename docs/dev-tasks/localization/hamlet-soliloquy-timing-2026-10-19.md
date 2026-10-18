# 礼拜堂独白开头的默认时刻

用户反复错过“To be or not to be”的第一句。本轮只读核对真实资源和调度IL，没有修改触发条件、时间或游戏逻辑，也没有启动游戏验证剧情。见[源字段及结论](../../../runtime/evidence/hamlet-soliloquy-timing-2026-10-19.json)。

原游戏`schedule`资产SHA256为`c9729c297f9df2d9442f9c899cb1fd2754ffe1af054ed24e385da837fa708f47`。事件`SC_SPINE_ToBeOrNotToBe`位于`chapel`，参与者哈姆雷特使用`chap_aisel`站位，时间下界为`[2,12,30]`，准备时长`assembly=30`。`GameClock.DayString`用`clockDays[day-1]`取星期，故第2天为星期五，默认12:30开始准备、13:00左右开口。

原`scenes`资产中的`Spine_ToBeOrNotToBe`先是`section shout 10`，仅含“To be or not to be...”及“That is the question.”两句；后面才是`section 60`的长段。编译器把首段设置为无交互触发的`AwaitingTriggerScene`，沿用父事件30分钟准备时长，首段窗口10个游戏内分钟；`ScheduleManager.UpdateTickSchedule`进入等待状态时启动这段背景对白。首段约13:00—13:10，后续交谈不重播首段。

建议12:45前到礼拜堂，站在哈姆雷特附近等，不要等交互气泡出现后才靠近。这里的时间是满足条件且未受其它剧情占用时的默认时序；事件条件为`wants(hamlet,avoid(ophelia))`，不是“国王死后经过固定分钟数”。剧情状态改变时可能不按默认日程发生。
