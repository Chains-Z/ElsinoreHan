# ElsinoreHan

《Elsinore》的离线中文补丁。**17,027 条离线词条已完成并安装**，正常从 Steam 启动即可使用中文。

最新候选1.5.0已验证，含17,033条词表和154条规则：修复多人通知连带日志漏译、人物简介更新组合及长文档F8阅读位置，并校订近期截图中的称号、对白和文章。128,408项真实翻译消费者、131项真实游戏离线API及隔离副本页面检查通过。**用户主游戏仍在运行，本轮尚未安装**；详见[本轮交接](docs/dev-tasks/localization/reading-followup-2026-10-10.md)。

按 **F8** 切换当前文字的英文原文与中文译文，再按一次恢复中文；修改词表后可按 Alt+R 重新加载。译文是供游玩校订的完整初稿，普通对白自然易读，适度保留原文的戏剧感。游戏运行时不调用翻译 API，无需额外 Key。

完整本地备份包（当前为待安装候选1.5.0）：[ElsinoreHan-Sol.zip](runtime/package/ElsinoreHan-Sol.zip)。适用于本机已验证的 Windows x86、Unity Mono《Elsinore》1.4.1（3678），安装位置为 D:\SteamLibrary\steamapps\common\Elsinore。

完整词表解析、动态参数消费、后台中文字体及 F8 往返检查通过；全剧情分支和对白/资料像素排版没有逐项验收，可边玩边反馈。详情见[全文交付与验证](docs/dev-tasks/localization/sol-full.md)。

其他角色的方言和口语已定向审校621个角色/源句组合，六处校订已安装，2484项真实翻译消费者及15项导出治理检查通过。重点完整审查马塞勒斯、格蕾丝和常用省音拼写的配角；见[其他角色审校](docs/dev-tasks/localization/dialect-dialogue-review-2026-10-10.md)。

伊尔玛490条不同对白已集中审校，方言呼语和昵称已校订，马塞勒斯口语按用户意见调整并安装。1108项定向消费者、9项前轮正文消费者及19项治理/导出测试通过；见[厨娘对白审校](docs/dev-tasks/localization/irma-dialogue-review-2026-10-10.md)。Maike与远行表达的[前轮校订记录](docs/dev-tasks/localization/playthrough-text-2026-10-10.md)保留。

兼容插件1.4.0和138条动态规则已安装。本轮修复日志中通知与对白交错的边界，统一两人的“骑士卫队”称号，并保留固定通知尾换行。此前114,028项消费者和111项真实游戏离线API检查通过；范围是当前资源与有限格式矩阵，不代表全剧情零漏译。见[本轮修复与验证](docs/dev-tasks/localization/mixed-log-followup-2026-10-10.md)。前轮[日志F8阅读位置保护](docs/dev-tasks/localization/log-followup-2026-10-10.md)、[线索等修复](docs/dev-tasks/localization/ui-followup-2026-10-10.md)与[字体证据](docs/dev-tasks/localization/runtime-ui-followup.md)保留。

## 目录与维护

| 路径 | 内容 |
| --- | --- |
| AGENTS.md | 项目约定与最新交接 |
| docs/dev-tasks/localization/sol-full.md | 全文来源、套餐实际 token 记录、验证与维护入口 |
| translation/sol-full-2026-10-09/translations.json | 精确原文、译文与稳定 ID |
| translation/sol-full-2026-10-09/ | 分批输入、冻结模型响应、输出和审计 |
| tools/translation/ | 真实来源适配、Sol 调用、校验及离线词表导出 |
| tools/patch/ | 插件源码、构建、备份安装、后台自动检查及打包 |
| runtime/evidence/dialect-review-verification.json | 最新其他角色校订、定向消费者、安装与ZIP核验摘要 |
| runtime/evidence/reading-followup-verification.json | 本轮通知、简介、文档F8与候选包验证；待游戏退出安装 |
| runtime/evidence/irma-review-verification.json | 前轮厨娘审校与安装摘要 |
| runtime/evidence/mixed-log-verification.json | 前轮混合日志、离线API与安装摘要 |
| analysis/ | 原始只读提取脚本、候选清单和统计 |
| docs/dev-tasks/localization/README.md | 历史研究、模型比较及实施记录索引 |

原模型比较已停止，不重复调用百炼。下载依赖、字体、安装备份、ZIP 和密钥不纳入 Git；仓库只在本机提交，未推送。
