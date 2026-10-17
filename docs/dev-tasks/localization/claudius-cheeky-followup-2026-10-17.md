# 克劳狄斯调情对白校订

状态：用户确认修改；已导出并生成待安装候选包，尚未安装到主游戏。插件保持1.5.9。见[候选核验](../../../runtime/evidence/claudius-cheeky-verification-2026-10-17.json)。

## 原文与语境

`p09518-1b2d2dfe69a1`，原文为`Cheeky, cheeky girl.`，来自真实`scenes`资产的`FLAVOR_ClaudiusRomanceNight2`第26674行，资产SHA256为`6f4f49b19b3822498a7941716ea1353b8e9073dc4873406fa0fc351170acea0a`。

前一句奥菲莉娅问`Why don't you show me what a King can do?`，克劳狄斯以`[happy] {Chuckle}`回应。这里是带笑的调情打趣，旧译“真是个放肆、放肆的姑娘。”重复生硬，且显得像严厉斥责。按用户确认改为：

> 你这姑娘，胆子可真不小。

保留大胆冒昧的意味，以中文口语承接原句重复的强调，不添加动作或关系。通过`local-corrections.json`的`apply_at_export`应用，记录准确旧值、源哈希和来源；冻结输入、raw、outputs与审计保持不变。

## 验证与范围

- 真实资源核对角色、场景、行号及前一句；3项真实XUnity逆序首匹配、递归上限64的组件消费者通过，覆盖裸句、角色日志及同场景相邻对白组合。用例见[消费者夹具](../../../translation/supplemental/claudius-cheeky-tests.json)。
- 15项导出治理测试通过；导出差异精确为这一条，17,067词条、157动态规则保持不变，全部中文字集合不变，无需更新字体。
- `package-full.ps1 -PendingInstall`已生成候选包，40文件与ZIP逐项一致。未修改游戏安装、启动游戏或访问存档；本轮未执行UI像素或完整剧情端到端测试。
- Windows PowerShell 5.1直接读取无BOM的UTF-8验证脚本时解析失败；改用当前PowerShell运行同一脚本后3项消费者通过，未改验证脚本或降低验证标准。
