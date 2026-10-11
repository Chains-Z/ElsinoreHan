# 公开分享字体选型

2026-10-11。用户计划在游玩、校对完成后免费分享汉化补丁。本轮仅调查许可、字符覆盖与适配路径，未替换主游戏字体，未更新候选包。

## 推荐方案

首选 **Source Han Sans SC Regular（思源黑体简体中文版常规字重）2.005**。黑体风格接近现有补丁，适合对白、界面及长文；这是基于字体样张的选型判断。静态OTF来自 [Adobe官方2.005R发布标签](https://github.com/adobe-fonts/source-han-sans/tree/2.005R/OTF/SimplifiedChinese)，文件为 `SourceHanSansSC-Regular.otf`。

该字体使用 [SIL Open Font License 1.1](https://raw.githubusercontent.com/adobe-fonts/source-han-sans/2.005R/LICENSE.txt)，允许随软件打包、修改及再分发，包含免费分享场景。许可同时允许商业使用，无需因此付费。打包时保留原版权声明、完整OFL及字体来源；不能单独出售字体，派生字体仍须遵循OFL。生成TMP/SDF属于格式转换，按修改版处理；原字体保留名称为 `Source`，拟将派生字体命名为 `ElsinoreHan Sans`，避免使用保留名称，仍在说明中注明来源。依据见 [OFL官方FAQ](https://openfontlicense.org/ofl-faq/)。

本机源字体和同标签许可保存在被忽略的 `runtime/vendor/fonts/source-han-sans/`。GitHub API出现限流，本轮改用发布标签下载，并记录文件SHA256；未取得准确上游提交哈希，不把标签描述成提交锁定。

## 核验结果

- fontTools读取字体cmap：现有全部2,816个汉字均有字形。
- 合并词表共2,936个非空白可见字符，仅4个带音符拉丁字母 `čłřš` 不在源字体中；它们只出现于保留的字体测试样例 `u00027-aef783a99d65`，其余译文字符全部覆盖。测试样例应依靠原英文字体或独立合法回退字体，不为消除测试差异而修改冻结源。
- 使用Pillow从官方OTF渲染“沉迷恶习／沉沈冗几”及真实译句，目测“沉”的右侧上横完整。预览为 `runtime/build/font-research/source-han-sans-preview.png`；这是源字体样张，未模拟TMP SDF或游戏布局。
- 来源、版本、下载字节哈希、覆盖范围与局限见 [调研证据](../../../runtime/evidence/shareable-font-research-2026-10-11.json)。覆盖检查绑定该阶段词表SHA，后续对白变化需按新快照重验。

原 `arialuni_sdf_u2018` 的“沉”在字体图集中已缺少该横，与用户截图一致；安装字体和原包SHA相同。原Arial字库仍为正式安装，许可未核实问题没有因找到新字体而自动解决。

## 备选与兼容路径

备选为 [霞鹜文楷GB](https://github.com/lxgw/LxgwWenkaiGB)，同样采用 [OFL](https://raw.githubusercontent.com/lxgw/LxgwWenkaiGB/main/OFL.txt)，风格更有书写感。MoeFont仓库提供Unity2018资产，具有现成资源优势，但其 [仓库说明](https://github.com/sorrowmoil/sorrowmoil-MoeFont-for-XUnity.AutoTranslator) 不代替原字体授权，现成资产的来源、保留名称与字形还需逐项核查。本轮未下载或验证该备选，暂不作为首选。

本游戏TMP1.4.0不能直接套用XUnity“指定系统字体名”方式，该功能要求TMP3.2.0及以上；需生成与Unity2018/TMP兼容的AssetBundle。依据为 [XUnity5.6.2字体说明](https://github.com/bbepis/XUnity.AutoTranslator/blob/v5.6.2/README.md#font-overriding) 与 [官方构建指南](https://github.com/bbepis/XUnity.AutoTranslator/wiki/TextMeshPro-Font-Asset-Creation-%26-Packaging-Guide)。指南的Unity6示例不能直接用于本游戏。当前只发现Unity Hub，未发现默认Editor目录中的Unity编辑器，尚未生成新资源包。

替换实施时需要：

1.在兼容Unity2018/TMP环境烘焙受控字符集，检查SDF图集内“沉”和易损细笔画；兼顾未来校订新增字符，不能仅凭原OTF完整就认定SDF完整。
2.使用独立派生名称，携带OFL、版权和来源；不混入Arial Unicode字形。保留英文字体回退并核对实际字符链。
3.更新中文字体识别：当前 `TranslationToggle.ConfigureChineseItalic` 只匹配 `ARIALUNI SDF`，新字体要保留既有斜体行为，不能仅改配置文件名。
4.在隔离游戏副本验证加载、全字符、粗斜体、对白/日志/长文档布局与F8往返，并补对缺横问题的最低层回归；不把源字体cmap检查称作游戏内通过。
5.通过验证后再更新安装与打包白名单、配置、许可附件和卸载流程。公开发布还需完成第三方许可整理及干净目录安装验收。
