# 后台诊断触发退出保存的记录

2026-10-09 排查发现，运行 3e72975326af433bb4ce44611f5dccd2 虽未点击开始/继续按钮，游戏仍已自动加载既有进度，并在退出时保存。player.log 有 loading state from progress、quick saving on exit、saving data；实际 game.save 的修改时间与退出日志一致，为 2026-10-08 20:21:42 UTC（本地次日04:21:42）。因此不能声称此前诊断未触碰存档。

实际路径：C:\Users\71095\AppData\Roaming\Golden Glitch Studios\Elsinore\game.save。排查只读取程序集IL、日志和文件元数据，没有解读存档正文；无法确认剧情进度差异。退出保存链为 ImTheBoss.OnDestroy → QuickSaver.QuickSaveMostRecent → SaveLoad.SaveData → GameRunner.SaveProgress。游戏保存成功后删除替换过程生成的 .bak，现场未找到此次写入前的旧版备份，因此没有自动恢复。

当前版本已复制保留在 runtime/backups/probe-save-*，这些本地存档副本被Git忽略，不进入补丁ZIP，也不发送给翻译模型。

## 已修复的诊断保护

- 每次测试先复制真实存档目录至工作区的独立副本，记录原目录文件哈希和修改时间。
- 临时 RuntimeProbe 在启动游戏业务前，通过 Harmony 将 SaveLoad.SaveFileDirectory 指向隔离副本，并阻断 SaveLoad.SaveData 和旧存档迁移入口。
- 任一保护配置或拦截建立失败时直接终止进程，避免普通退出回调再次保存。
- 测试后逐文件检查原存档哈希、修改时间和文件数量；有变化就拒绝通过。
- 诊断插件在 finally 清理；该保存拦截不会被打入用户汉化补丁，不影响用户正常游玩和保存。

隔离修复后的运行5879b078bd9444669819cf0743b949b9及后续运行已确认原存档目录不变。该早期修复运行的缓存/存档保护通过，但菜单测试失败，不能将其记成完整UI通过；菜单显示另需走游戏的真实暂停动作，避免运行状态立即切回探索界面。

这次修改解决后续诊断的写盘问题，不能据此抹去修复前已发生的存档写入。
