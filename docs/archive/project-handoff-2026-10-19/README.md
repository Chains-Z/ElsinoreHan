# 项目交接与恢复

2026-10-19。本轮汉化已完成并发布，用户准备卸载游戏、删除所有本地项目文件。今后的维护来源是[GitHub仓库](https://github.com/Chains-Z/ElsinoreHan)与[Release附件](https://github.com/Chains-Z/ElsinoreHan/releases)，不要求保留旧电脑、工作目录、存档或缓存。仓库继续公开并保留Issue入口，未设置为只读归档；后续按具体反馈定向维护。

## 已发布入口

- [Steam汉化下载指南](https://steamcommunity.com/sharedfiles/filedetails/?id=3822643409)。百度提取码fate；夸克提取码AmiA。网盘链接以指南当前内容为准，未将网盘文件冒称已经回读核验。
- [汉化补丁v1.0.0](https://github.com/Chains-Z/ElsinoreHan/releases/tag/v1.0.0)，下载附件`ElsinoreHan-v1.0.0-windows.zip`。对外补丁1.0.0／内部插件1.5.15独立编号；本次交接不改变发行标签及运行包。
- ZIP SHA256：`8cc8121aac0b4726d8568b68b6b496a2fa1418dbb8d3da203227ee1a059f166e`，69文件，其中39运行文件。
- [维护交接](../../dev-tasks/localization/handoff.md)、[当前发布证明](../../../runtime/evidence/public-release-1.0.0-published-2026-10-19.json)、[Steam指南草稿](../../release/Steam指南草稿.txt)。草稿保留下载占位，已发布指南由用户管理。

## 保存范围

Git保存插件与工具源码、冻结的全文翻译输入／响应／输出、来源和校订层、动态规则、回归用例、完整许可、实现说明和验收摘要。112批全文导出所需的451份输入、输出、原始JSON及治理文件均已跟踪；不需要重新请求模型或取得原API Key。

另保存三份此前仅存在本地的原始维护元数据，索引与哈希见[恢复基线清单](../../../runtime/evidence/recovery-baseline/manifest.json)：

| 文件 | 用途 |
| --- | --- |
| plugin-build.json | 原发行DLL的编译器、13个源文件及10个引用哈希；没有它，重新编译不能复原原始构建证明 |
| font-assembly.json | 当前7661字形字体的装配证明，个人候选打包脚本需要读取 |
| font-bake.json | 与装配证明绑定的原生字体参数与字形度量；保留原始字节和来源哈希 |

运行DLL、字体成品、Doorstop源码归档及其余第三方组件由Release ZIP保存，不重复塞入Git。API密钥、个人存档／检查点、游戏本体、测试游戏副本、旧字体缓存、64MiB图集、窗口截图、日志和重复生成夹具不上传。后续维护以最终GPT-6.1-sol译文、现有校订及具体反馈为基础。

这份归档不能恢复玩家进度。旧本地检查点的位置和曾完成的恢复记录仅是历史证据，不表示GitHub保有对应存档；本次没有删除、卸载或改写用户文件。

## 从干净仓库恢复当前维护环境

需要Git、Python 3.10或更新版本；下载附件可用浏览器或GitHub CLI。不需要启动游戏，不需要API Key，也不会访问存档。以下PowerShell命令在新工作目录中执行：

```powershell
git clone https://github.com/Chains-Z/ElsinoreHan.git
Set-Location ElsinoreHan
New-Item -ItemType Directory -Force runtime/downloads | Out-Null
gh release download v1.0.0 --repo Chains-Z/ElsinoreHan --pattern ElsinoreHan-v1.0.0-windows.zip --dir runtime/downloads
python tools/release/restore-release-workspace.py --archive runtime/downloads/ElsinoreHan-v1.0.0-windows.zip
```

也可以用浏览器下载同名ZIP，把最后一行的路径改为下载位置。恢复器先验证ZIP整体哈希、全部69个条目、39个运行文件、插件原始源码指纹及字体证明，再恢复以下被忽略的本地目录；已有文件不同会拒绝覆盖，未冲突的重复执行可安全复用：

- `runtime/package/ElsinoreHan-Sol/`：39个原始发行运行文件。
- `runtime/vendor/BepInEx5/`与`runtime/vendor/XUnity/`：当前维护／编译用的公开依赖。
- `runtime/vendor/fonts/`：当前成品字体及装配证明；不包含源OTF或旧模板。
- `runtime/build/`：原发行插件DLL、原始编译记录和Doorstop源码归档。

随后可离线重导出词表并重打当前公开包：

```powershell
python tools/translation/export_sol_full.py
python -m unittest discover -s tools/translation -p test_export_sol_full.py
python -m unittest discover -s tools/release -p 'test_*.py'
python tools/release/build-public-release.py
```

导出器只使用仓库中冻结的结果和校订层，不调用翻译API。新ZIP的容器时间戳可能不同，应比较所有条目的内容与哈希，不要求新ZIP整体哈希等于原附件。当前恢复基线固定对应1.0.0；将来改版本或运行文件后应新增经核验的基线，不把旧证明套用到新产物。恢复程序不会安装补丁，也不会启动或下载游戏。

## 后续修改与验收边界

修改词表时按AGENTS及[单一译文与格式派生规则](../../dev-tasks/localization/variant-generation-2026-10-19/README.md)操作，只改受治理的校订层，保留准确旧值、来源哈希及原文格式。导出后运行受影响消费者，检查新增字形；需要更新实际运行文件时完成对应候选验证，不能只改历史安装证明。

修改插件需要自行安装Windows版游戏并提供其Managed程序集，按[源码构建说明](../../release/SOURCE-BUILD.md)操作。编译器或游戏引用变化会触发重新编译，新DLL通常具有不同哈希，须重新验收并更新候选证明；不能保证旧`install-full.ps1`在新电脑直接通过。玩家恢复已发布汉化，直接解压Release即可。

只有实际新增字形或修改字体时才需重新生成：源字体为官方Source Han Sans SC Regular 2.005R，版本、官方下载和哈希见[字体构建记录](../../dev-tasks/localization/font-replacement-2026-10-11.md)及[第三方来源](../../../licenses/THIRD-PARTY-NOTICES.md)。原字体模板与组件可按[依赖下载脚本](../../../tools/patch/download-dependencies.ps1)和[依赖哈希](../../../runtime/evidence/dependencies.json)重取；当前公开包已保留可直接使用的字体成品。原始烘焙图集不在Git中，需要运行验证或新烘焙时在隔离副本重新生成，不能伪造旧运行证据。

测试只用隔离游戏及临时存档，遵守静音、隐藏窗口和存档保护规则。用户不再保留旧存档，未来复现需自行取得合法游戏与新的测试进度，或让反馈者自愿提供必要资料。不要从过往日志中的绝对路径推断文件仍存在。

## 最终核验

干净克隆恢复、发行附件回读、重新导出与逐文件比较结果记录在[交接核验](../../../runtime/evidence/project-handoff-verification-2026-10-19.json)。该记录区分仓库恢复检查与真实游戏验收；本次不重跑游戏、不修改玩家安装或存档。
