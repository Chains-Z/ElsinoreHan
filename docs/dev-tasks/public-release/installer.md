# 公开包辅助安装与卸载

当前工具实现于 `tools/release/`，面向 Windows 原生 PowerShell 5.1。发布包把 `common.ps1`、`install.ps1`、`uninstall.ps1`、`Install.cmd`、`Uninstall.cmd` 与 `manifest.json` 放在 `ElsinoreHan/`，运行文件平铺在其父目录。普通用户可把完整包直接解压到游戏目录；辅助工具用于外部目录解压后的冲突检查与有记录安装，以及保守卸载。

## 集成接口

`manifest.json` 必须为 UTF-8 JSON，结构如下，路径使用固定大小写及 `/`：

```json
{
  "schema_version": 1,
  "package_id": "ElsinoreHan",
  "release_id": "2026-10-19",
  "files": [{"path": "winhttp.dll", "sha256": "64位小写十六进制SHA256", "size": 123}],
  "legacy_files": []
}
```

`files` 为欲安装文件，当前包为既有40文件去掉旧 `README.md` 后的39文件。`legacy_files` 接受历史正式证明中的同路径多个已知哈希，`path:sha256` 组合不得重复，大小必须准确。外层文档、许可汇总、对应源码和工具自身不进入安装清单。运行文件路径还必须通过工具内固定40路径白名单，原游戏四文件、存档、任意其他插件及目录越界路径均不在白名单内。

从解压目录执行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ElsinoreHan\install.ps1 -GamePath 'D:\SteamLibrary\steamapps\common\Elsinore'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ElsinoreHan\uninstall.ps1 -GamePath 'D:\SteamLibrary\steamapps\common\Elsinore'
```

双击 `.cmd` 后输入游戏路径，命令行也可把路径作为第一个参数；不请求UAC、不联网。PS1文件保留UTF-8 BOM，避免原生PowerShell5.1把中文错误解码。

## 安装与归属

安装前读取全部运行文件并核对大小、SHA256，随后检查目标路径、原游戏四文件存在、所有相关祖先目录和文件均无重解析点，以及目标路径的 `Elsinore.exe` 未运行。其他路径的同名进程不阻挡；无法读取同名进程路径时保守拒绝。工具不终止任何游戏进程。

新建文件归属本项目，已有清单文件必须仍匹配清单。没有清单时，未知冲突整批拒绝；已知历史正式哈希允许升级并认领；现有内容与新版本完全相同的共享依赖保留且不认领。6个项目独有路径可以按当前包准确哈希认领：字体包、兼容插件、Sol与Dynamic词表、两份ElsinoreHanSans许可。不会备份旧补丁。

拥有范围写入游戏根目录 `ElsinoreHan.install.json`，同样包含固定项目ID、版本、路径、大小及SHA256。读取清单时，路径仍需在固定白名单中，哈希和大小还需被当前包的当前/历史正式证明认可。安装前完成整批冲突预检，写入后逐个核对哈希。写入前先记下预期拥有范围，以便中断后保守清理；不保证跨文件原子提交。异常中断后可能保留旧文件并拒绝后续自动升级，应根据报告核对文件和原版本，不能把未知文件强行当作本项目文件覆盖。

## 卸载及直接解压限制

有清单时只删除仍与清单哈希及大小一致的自有文件。修改过的文件保留并逐个报告，残余归属清单保留，便于恢复原字节后再次卸载。无残余时移除清单。不递归删除目录，因此其他模组与运行期间生成的日志或配置不会一并删除。

若 `BepInEx/plugins`、`patchers` 或 `core` 中发现非本包DLL或链接，或拥有的共享配置/依赖已被修改，卸载保留整组共享运行环境并逐项报告。这样即使其他模组在本补丁安装后才加入，也不会仅因本项目曾创建加载器而将其删除；残余记录继续保留。工具不进入未知链接目录。

直接解压没有归属记录，无法判断解压前是否已有共享加载器。卸载器只按当前固定清单检查6个项目独有文件，精确匹配则删除，修改则保留并报告；Doorstop、BepInEx、AutoTranslator、配置及第三方许可等全部保留。它不能声称把游戏恢复成解压前的干净目录，也不会删除 `ElsinoreHan/` 文档及工具自身。

直接覆盖解压由资源管理器执行，无法执行工具的冲突、运行与重解析点预检。已有其他模组或升级时应从外部解压目录使用辅助安装器。不要把直接解压的便捷流程描述为已执行安全安装预检。

## 验证

运行 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/release/test-installer.ps1 -EvidencePath runtime/evidence/public-release-installer-tests-2026-10-19.json`。

18组隔离文件系统集成测试通过，含原生PowerShell5.1独立脚本安装/卸载、重复安装、清单升级、旧正式哈希升级、未知冲突整批拒绝、共享依赖保留、安装后加入其他模组及共享配置改动时保留运行环境、用户修改拒绝升级及卸载保留、无清单直解压保守卸载、源目标相同、清单路径/哈希/大小/重复/伪造归属拒绝、源根/目标根/目标子目录链接拒绝、文件位置被目录占用，以及同名异路径与目标路径进程检查。

进程测试仅运行自行编译的隐藏休眠哨兵 `Elsinore.exe`；测试明确验证工具未结束哨兵。测试结束后由测试器终止其自身进程并清理临时目录。未启动真实游戏，未访问玩家存档。证据为 [隔离验证记录](../../../runtime/evidence/public-release-installer-tests-2026-10-19.json)，不能称真实游戏E2E。最终发布包39运行文件的完整集成检查由发布打包流程另行记录。
