# ElsinoreHan

《Elsinore》的离线中文补丁。**17,027 条离线词条已完成并安装**，正常从 Steam 启动即可使用中文。

按 **F8** 切换当前文字的英文原文与中文译文，再按一次恢复中文；修改词表后可按 Alt+R 重新加载。译文是供游玩校订的完整初稿，普通对白自然易读，适度保留原文的戏剧感。游戏运行时不调用翻译 API，无需额外 Key。

完整本地备份包：[ElsinoreHan-Sol.zip](runtime/package/ElsinoreHan-Sol.zip)。适用于本机已验证的 Windows x86、Unity Mono《Elsinore》1.4.1（3678），安装位置为 D:\SteamLibrary\steamapps\common\Elsinore。

完整词表解析、动态参数消费、后台中文字体及 F8 往返检查通过；全剧情分支和对白/资料像素排版没有逐项验收，可边玩边反馈。详情见[全文交付与验证](docs/dev-tasks/localization/sol-full.md)。

兼容插件1.4.0和138条动态规则已安装。本轮修复日志中通知与对白交错的边界，统一两人的“骑士卫队”称号，并保留固定通知尾换行。114,028项消费者和111项真实游戏离线API检查通过；范围是当前资源与有限格式矩阵，不代表全剧情零漏译。见[本轮修复与验证](docs/dev-tasks/localization/mixed-log-followup-2026-10-10.md)。前轮[日志F8阅读位置保护](docs/dev-tasks/localization/log-followup-2026-10-10.md)、[线索等修复](docs/dev-tasks/localization/ui-followup-2026-10-10.md)与[字体证据](docs/dev-tasks/localization/runtime-ui-followup.md)保留。

## 目录与维护

| 路径 | 内容 |
| --- | --- |
| AGENTS.md | 项目约定与最新交接 |
| docs/dev-tasks/localization/sol-full.md | 全文来源、套餐实际 token 记录、验证与维护入口 |
| translation/sol-full-2026-10-09/translations.json | 精确原文、译文与稳定 ID |
| translation/sol-full-2026-10-09/ | 分批输入、冻结模型响应、输出和审计 |
| tools/translation/ | 真实来源适配、Sol 调用、校验及离线词表导出 |
| tools/patch/ | 插件源码、构建、备份安装、后台自动检查及打包 |
| runtime/evidence/mixed-log-verification.json | 最新混合日志、离线API、安装与ZIP核验摘要 |
| analysis/ | 原始只读提取脚本、候选清单和统计 |
| docs/dev-tasks/localization/README.md | 历史研究、模型比较及实施记录索引 |

原模型比较已停止，不重复调用百炼。下载依赖、字体、安装备份、ZIP 和密钥不纳入 Git；仓库只在本机提交，未推送。
