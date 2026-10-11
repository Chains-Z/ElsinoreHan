# 思源字体替换与安装验证

2026-10-11，按用户要求将原先许可未核实的Arial Unicode字体换为可随汉化补丁分享的思源黑体，并在验证后备份安装。正式兼容插件为1.5.2，词表仍为17,041条、155动态规则；近期三轮对白校订一并安装。

## 来源与许可

源字体为Adobe官方 `Source Han Sans SC Regular` 2.005R，来自[官方发布标签](https://github.com/adobe-fonts/source-han-sans/tree/2.005R)，完整字体许可为SIL OFL1.1。具体授权及争议检索记录见[选型记录](shareable-font-research-2026-10-11.md)和[许可风险复核](font-license-risk-check-2026-10-11.md)。派生字体使用独立名称 `ElsinoreHan Sans SDF`，不使用保留名Source作为字体名称，不暗示Adobe背书。

补丁及主游戏均附带 `licenses/ElsinoreHanSans-OFL.txt`、`ElsinoreHanSans-NOTICE.txt` 和 `TextMeshPro-Unity-Companion-License.txt`。字体软件与字形按OFL；兼容资产内的TMP材质/着色器按[Unity Companion License](https://docs.unity.cn/Packages/com.unity.textmeshpro@1.0/license/LICENSE.html)，用于本Unity游戏。不能把后者说成OFL字体的一部分。

| 产物 | SHA256 |
| --- | --- |
| 官方OTF | `f1d8611151880c6c336aabeac4640ef434fa13cbfbf1ffe82d0a71b2a5637256` |
| 官方OFL原文 | `fcac737e761ec63dbfbdce11030a1780161920d80315edba9c8beff1c2bac5a2` |
| 新TMP字体包 | `60fdd8619c0d83acbe762d8cba88d5655254f73b898280b8a7f09ae712b617fc` |
| 实际原生及运行时Alpha8纹理 | `3771fcff32a341040edea57f07c51898a4ecbc9af179de795c0cae93c4efef20` |

本轮解决字体再分发来源和许可问题；公开发布仍需其他依赖许可整理、完整卸载说明和干净目录安装验证，当前ZIP继续标为个人备份。

## 字体生成与兼容实现

本机没有Unity Editor。使用独立游戏副本的真实Unity2018 FontEngine从官方OTF生成SDF8图集：采样56、padding6、8192×8192 Alpha8，共7,660个Unicode、7,657个独立源字形。集合包含GB2312、源字体支持的基础及扩展拉丁字符和当前玩家译文，覆盖本轮2,816个中文字符。

`u00027-aef783a99d65` 是程序保留的字体测试样本，含源字体不支持的č、ł、ř、š及额外符号；它不作为玩家正文补字依据。其他实际译文逐字检查无缺字。`prepare-font-characters.py` 对玩家译文或GB2312缺字直接报错；已验证其再生输入与本轮烘焙字符文件逐字节一致。

`FontBakeProbe.cs` 在现有存档和静音保护建立后，调用本引擎的精确反射签名并按64字形分批生成。生成阶段编号 `353ff8f287fe4ec7a5c8fe14cef26e61`。`build-shareable-font.py` 仅复用旧包的兼容序列化结构及TMP材质/着色器，全部替换字形、metrics、图集和kerning，并删除含旧Arial图集的整个 `.resS` 资源流。每个原生glyph index均须等于官方OTF的cmap索引；装配后重读并核对所有坐标、推进宽度及完整纹理。

旧版TMP升级序列化字段时只会恢复SDF16/32，无法保留本次原生SDF8。正式插件在新字体 `ReadFontAssetDefinition` 后，通过内部setter的精确反射将 `atlasRenderMode` 恢复为SDF8。此操作限定本项目字体名称。

新字体沿用旧剪切参数10时，两句斜体样本出现最小 `-0.6214` UI的相邻边界间距。改为5后，12份正常/斜体/压力样本通过，修复样本最小间距为 `0.7250061` UI，字符推进宽度不变。旧Arial兼容分支保持10，压力对照保持35；这些参数不等于倾斜角，斜体格式仍保留。

## 维护入口

源字体与UnityPy等本地依赖不入Git；装配需要 `fontTools` 和 `UnityPy`（本轮1.25.4，置于 `runtime/build/font-audit-deps/`）。已有BepInEx/XUnity、游戏Managed依赖与隔离副本准备方式沿用[后台测试约定](handoff.md#后台探针与真实导航)。不要在主游戏运行本节的字体生成或资料探针。

```powershell
# 当前译文的受控字符集
python tools/patch/prepare-font-characters.py

# 只在隔离副本使用；先准备冻结存档来源，生成模式不叠加资料/斜体/F8模式
$env:ELSINOREHAN_PROBE_SAVE_SOURCE = (Resolve-Path 'runtime/backups/probe-save-6f413db42b4842f99a322ede96cdd074').Path
$env:ELSINOREHAN_PROBE_FONT_SOURCE = (Resolve-Path 'runtime/vendor/fonts/source-han-sans/SourceHanSansSC-Regular.otf').Path
$env:ELSINOREHAN_PROBE_FONT_CHARACTERS = (Resolve-Path 'runtime/build/font-replacement/font-characters.txt').Path
./tools/patch/run-headless-probe.ps1 -GamePath 'D:\MyProjects\ElsinoreHan\runtime\game-test\settings-options'

# 将上一步输出的真实证据目录传给装配器
python tools/patch/build-shareable-font.py --bake-directory runtime/evidence/headless/353ff8f287fe4ec7a5c8fe14cef26e61
```

切换到加载回归时清除 `ELSINOREHAN_PROBE_FONT_SOURCE`，把新字体、插件及配置放入隔离副本。以 `run-toggle-probe.ps1` 运行资料与斜体检查，设置如下输入；路径须解析为绝对路径，保存来源仍使用冻结副本。

| 环境变量后缀（均加 `ELSINOREHAN_PROBE_`） | 输入 |
| --- | --- |
| `FONT_NAME` | `ElsinoreHan Sans SDF` |
| `FONT_CHARACTERS` | 再生的 `font-characters.txt` |
| `FONT_BAKE_EVIDENCE` | 本轮实际生成且通过验证的证据目录 |
| `TRANSLATIONS`、`CHARACTERS`、`CACHE_CASES` | 冻结全文目录中的 `translations.json`、`chinese-characters.txt`、`runtime-cache-cases.tsv` |
| `CLOSEUP_IDS` | `runtime/build/closeup-ids.txt`，来自冻结真实资料来源 |
| `NOTIFICATION_EVIDENCE` | `runtime/evidence/font-notification-consumer-verification.json`；仅适用于该证明绑定的当前夹具与规则 |
| `JOURNAL`、`ITALIC` | 均为 `1` |

字体生成验证通过不代表装配后加载通过。`FontRegressionProbe.cs` 读取实际加载的7,660字形和完整64MiB纹理；`verify-font-regression.py` 同时核对来源、SDF模式、坐标、推进宽度、纹理字节和“沉”右侧几部件的上横。

安装器绑定 `font-replacement-verification.json` 中的字体、插件、词表及许可哈希；将来重新生成或改变插件后必须先完成相应验证并更新候选证明，不能绕过哈希门禁安装。

## 验证结果与修复证据

最终完整成功编号为 `6823aa701d0948a4a1b232648ea0c9f6`，汇总在[字体候选核验](../../../runtime/evidence/font-replacement-verification.json)，原始大纹理、日志和网格位于被忽略的本机证据目录。

- 7,660个实际运行字形坐标及推进宽度与原生生成值一致，完整图集逐字节一致；“沉”的上横检测通过，原字体缺横已排除。
- 冻结存档的14份文档、14名人物资料、7个真实日志索引、相关HUD/Journal/Timeline/分享预览及F8往返全部通过相应组件断言；分享预览未提交。
- 12份正常/斜体/压力网格通过；没有缓存译文与实际显示文本差异。
- 30项近期对白、616项通知真实XUnity消费者及15项导出检查通过。判定器回归为字体相关9项、斜体29项、资料39项、启动保护10项；5个修改的PowerShell脚本语法检查通过。
- 最终探针无可见窗口，批处理、静音、低优先级和10FPS均确认；保护后的原8个存档及冻结来源不变，临时入口已按原字节还原，探针与appid清理完成。

曾出现两类验证器问题，均保留原因与回归：原生生成的完成标记在 `player.log`，不是BepInEx日志；修正读取位置并增加拒绝仅有进度标记的3项门禁测试。通知断言初次读取旧阶段消费者哈希，不能认定新候选通过；实际重跑616项消费者后，通过显式新证明核验，旧审计快照不改写，并补3项失效证明测试。斜体10导致的负间距也已在真实最终单轮重跑中修复。

这些是实际字体纹理、资源重放和组件验收，不代表完整页面屏幕像素、物理键盘输入或全剧情E2E。没有重新跑本轮未改变的全量日志排列、设置逐档或剧情分支测试。

## 主游戏安装与备份

用户已授权“验证没有问题，关闭游戏后安装”。检测到游戏退出后，通过 `install-full.ps1` 备份安装，没有启动主游戏；原游戏四文件及8个存档的SHA、修改时间、大小和数量均未变。配置仅将回退字体键改为新字体，其他配置保持原有内容。旧Arial已备份并移除。

备份：`runtime/backups/full-c0d1205a32b14ea0abeaccfe52c3bc7d`，旧词表两份、插件、配置及字体共5文件均已核对。38运行文件与40文件包目录及ZIP逐项一致；两份额外包文件为README与XUnity许可。安装后复用游戏实际配置重新打包，候选快照保持原始哈希。

正式ZIP SHA256：`c133d3551823229697d903fb013e2a7716b548370482c52874f1b3c4f23013ec`。当前安装依据为[正式安装核验](../../../runtime/evidence/font-replacement-install-verification.json)及[安装清单](../../../runtime/evidence/full-installed-files.json)，之前1.5.1安装证据保持历史快照。

本轮还包含“一场更大的游戏”、贝尔纳多友谊回应和[高级大臣校订](othello-term-review-2026-10-11.md)；用户明确选择保留“抓住你的脑袋”及其斩首呼应，因此该句未改。
