# 幽灵“更大的游戏”对白校订

用户实际日志截图中的“这是更大一场游戏的规则”语序不顺。真实资源 `scenes` 的 `GHOST_GhostApperation` 第9488行原文为 `It is impossible, yes. It is the rules of the larger game.`，前句询问其他人是否会相信奥菲莉娅，后句追问“在你看来，这是一场游戏？”。

按用户意见统一为“是的，那不可能。这是一场更大的游戏的规则。”。裸源此前为“这是那场更大的游戏的规则”，此次与幽灵斜体源同步；保留斜体和规则比喻，不补写幕后关系。两项准确旧值、源哈希与真实资源来源登记在 `translation/supplemental/dialogue-context-corrections.json`，冻结输入、输出与raw不改。

`prepare_ghost_context_followup.py` 可再生本轮及既有幽灵语境回归。22项真实XUnity递归消费者、15项导出检查通过；17,041词条和155规则数量不变，动态词表哈希不变。个人备份包通过 `package-full.ps1 -PendingInstall` 更新，37文件目录与ZIP逐项一致，证据为 `runtime/evidence/larger-game-followup-verification.json`。

本轮未操作主游戏或存档，尚未安装；当前正式安装证据仍为 `playthrough-install-verification-2026-10-11.json`。本轮为定向组件检查，不称完整游玩E2E或像素排版验收。
