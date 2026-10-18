# 特殊结局检查点备份与烧书入口

2026-10-19用户明确要求安装、检查当前存档并在达到共同分支节点时保留备份。已完成。安装证据见[本轮核验](../../../runtime/evidence/playmaster-tone-install-verification-2026-10-19.json)。本次保留一份玩家主动要求的检查点，不改变停止自动积累旧补丁备份和临时测试存档的约定。

## 检查点

用户游戏已退出；直接只读解析`game.save`的当前逻辑状态，没有启动游戏、运行存档加载业务、迁移或推进剧情。

- `mode=MainGame`，根存档`loop=58`。
- 11个普通结局的持久`viewedEnding`均为真，`numberEndingsBurned=11`。
- `perfectday=1`，`witnessed(SC_NOESCAPE_Ghostlastmanifest)=1`，`playerAttended(SC_NOESCAPE_Ghostlastmanifest)=true`。
- `leadActive(lead,Quince_Story,quince_complete)=true`，戏剧大师线索完成。
- `unlockedEnding(END_Revenge)=true`；`viewedEnding(END_Revenge)`与`viewedEnding(END_JoinQuince)`均为假。
- `ownedInformation(NotNeeded)=false`、`demontripped=false`，尚未接受升格路线关键情报或进入其后流程。

因此适合保留两个特殊终局之前的共同检查点。

## 备份

原存档：`C:\Users\71095\AppData\Roaming\Golden Glitch Studios\Elsinore`。

备份目录：`D:\MyProjects\ElsinoreHan\runtime\backups\player-checkpoints\before-special-endings-20261019-040551`。

实际数据在其`Elsinore`子目录，包含原存档目录全部8个文件；另有`backup-manifest.json`和`README.txt`说明状态及恢复注意事项。全部文件大小和SHA256逐项一致，备份前后及补丁安装前后的原文件哈希、大小、mtime、数量均未变。该目录已被Git忽略，不上传存档。

这是用户明确要求保留的备份，不作为可自动清理的临时测试副本。恢复必须在游戏退出后进行；恢复会撤销备份之后的本地进度，本轮没有执行恢复。

## 烧书结局走法

1.继续游戏，回奥菲莉娅的卧室，打开《命运之书》。
2.点击书本界面的烧书入口。
3.在“为复仇放弃选择？”确认框中选择“任它烧毁”，看完结局及片尾。

入口逻辑已核对`EndingSelectUI.Activate`：`END_Revenge`已解锁且未观看时显示`BurnBookButtons`。烧书按钮打开确认框，`Let It Burn`回调直接选择`END_Revenge`。对应中文已与当前安装词表核对。无需从普通命运页重新采用结局。

烧书后“继续”保留烧书结果，不会返回这个检查点。若要再体验另一特殊终局，应先退出游戏并恢复这份备份，再走另一条路线；恢复时核对Steam云同步方向，避免覆盖所需分支存档。

## 安装结果

通过`tools/patch/install-full.ps1`安装已验证候选，再生成已安装个人包。插件仍1.5.15，17,069词条、157动态规则、7,661字形；本轮累计561个词条目标变化均已安装，当前无待安装修改。38运行文件与实际游戏一致，40包文件与ZIP逐项一致；原游戏四文件和原8个存档均未变。本轮未启动主游戏或测试副本。
