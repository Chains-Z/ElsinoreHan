# 首个公开补丁包

2026-10-19。用户明确授权安装最新校订、恢复保留的检查点、检查不应公开的内容，并将可直接解压使用的ZIP发布到 GitHub Release。

状态：本地安装、存档恢复、许可材料、公开包及干净目录验收完成，已正式发布[GitHub Release](https://github.com/Chains-Z/ElsinoreHan/releases/tag/v1.0.0)，云端附件回读逐字节一致。[发布核验](../../../runtime/evidence/public-release-1.0.0-published-2026-10-19.json)记录标签、源码提交、附件哈希及审计范围。不是重新翻译全文或重跑全部剧情。

## 交付

- 版本：`v1.0.0`，兼容插件仍为1.5.15。
- 公开包：`runtime/package/public-release/ElsinoreHan-v1.0.0-windows.zip`，配 `SHA256SUMS.txt`。
- 39个运行文件直接平铺，完整解压至 `Elsinore.exe` 旁即可使用。四份中文TXT说明位于根目录；可选安装卸载工具、18份许可（第三方16份、项目2份）、项目插件及Doorstop对应源码位于 `ElsinoreHan/`；共69文件。
- 主游戏已通过既有安装器安装累计15条校订，无待安装内容。原游戏4文件不变。
- 用户另行要求将主存档恢复为第58轮特殊结局前检查点，8文件哈希及mtime与备份一致。保留检查点，不把存档恢复功能或备份发进公开包。

## 入口

- [玩家文档](../../release/README.md)、[GitHub发布说明](../../release/GITHUB-RELEASE.md)
- [许可与对应源码](licenses.md)
- [项目LGPL授权及源码随附](project-license.md)
- [Steam简介、汉化声明及文案范围](localization-statement.md)
- [Steam Deck官方状态与未实测配置参考](steamdeck.md)
- [辅助安装／卸载契约](installer.md)
- [验收与边界](verification.md)
- [独立版本号约定与本次验证范围](versioning.md)
- [包内白名单及哈希](../../../runtime/evidence/public-release-1.0.0-package-verification-2026-10-19.json)

构建入口 `python tools/release/build-public-release.py` 只消费经验证的本机运行包、明确文件白名单和来源审计；不会递归打包仓库或游戏目录。ZIP、字体、依赖和对应源码归档作为Release附件分发，不纳入Git树。发布前运行完整Git历史与工作区扫描，发布后下载附件复核哈希。
