# 思源黑体授权与争议复核

2026-10-11。用户要求进一步查证是否有人因使用思源黑体被索赔，避免仅凭“免费商用”宣传选择公开补丁字体。对象为已下载的Adobe官方 `SourceHanSansSC-Regular.otf` 2.005R，不将第三方衍生版或Adobe其他收费字体视作同一对象。

## 结论

继续推荐官方原版作为制作分享字体的来源。字体文件和同版本许可均明确使用OFL1.1，软件捆绑再分发在授权范围内。该结论以满足许可条件为前提，不以“非商业”或“从没人发过律师函”为依据。

确实查到收到版权通知的个人自述，但未找到足以核实其通知有效、索赔成立或合规使用官方原版被判侵权的公开材料。本轮属于公开网页检索，不是对全部司法数据库、未公开和解或历史纠纷的穷尽调查。

## 争议线索与证据等级

| 线索 | 能支持的事实 | 不能支持的结论 |
| --- | --- | --- |
| [2025-06-02 Reddit游戏开发者帖子](https://www.reddit.com/r/graphic_design/comments/1l1qgc8/does_monotype_own_source_sans/) | 发帖者转述项目经理收到声称来自Monotype、涉及Source Sans和Source Han Sans的侵权邮件 | 未公开邮件、涉案字体文件、判决或后续结果；不能认定真正发件方、有效索赔或诈骗，也不能认定原版OFL失效 |
| [2021-05-28创业者博客](https://wlj.me/posts/font-copyright-for-entrepreneurs/) | 作者称公司要求统一用思源黑体，仍收到过未具体给证据的律师函 | 未说明来函具体针对哪款字体及处理结果，不能等同于思源黑体侵权成立 |
| [猫啃网2025-08留言](https://www.maoken.com/messages/comment-page-30) | 留言者转述有人倒卖思源黑体被Adobe处理 | 没有案号、判决或Adobe声明，仅属传闻；所述单售字体也不同于随补丁免费捆绑 |

检索包含思源黑体/Source Han Sans与侵权、索赔、律师函、判决、Monotype、淘宝倒卖等中英文组合，并对 `court.gov.cn`、`gov.cn` 做限定检索。未检索到相关判决不等于证明没有判决。一般字体索赔文章、无关字体案件和带营销目的的“免费陷阱”文章，不作为此字体已发生侵权争议的证明。

## 官方授权与实际软件案例

- [Adobe官方字体FAQ](https://www.adobe.com/products/type/fonts-by-adobe.html) 把Source Han Sans列入其开源字体，并指向GitHub。该页也提到Monotype为部分Adobe字体许可的代理，因此不能只凭发件方名称断言诈骗；具体官方OFL版本仍应按该版本许可判断。
- [2.005R官方LICENSE](https://raw.githubusercontent.com/adobe-fonts/source-han-sans/2.005R/LICENSE.txt) 授予复制、嵌入、修改和再分发权限，要求保留版权及许可、修改版遵守保留字体名条件、字体部分继续采用OFL，不得单独出售字体。
- [OFL官方FAQ](https://openfontlicense.org/ofl-faq/) 1.3和1.4明确允许与软件、游戏捆绑，且不要求整个软件改为OFL；8.1说明许可修订不溯及既有许可，8.2说明另行许可不改变该字体已有OFL条件。仍须遵守原许可，不能据此免除违规后的终止条款。
- [Adobe官方仓库问题195](https://github.com/adobe-fonts/source-han-sans/issues/195) 是游戏开发者询问如何在分发包附版权声明，维护者提供获取声明的方法；这是具体分发说明，不是对本项目的单独授权或法律担保。
- [育碧Just Dance 2026官方片尾PDF](https://ubistatic-a.ubisoft.com/0106/gamesites/justdance/credits/JD26_Credits.pdf#page=92) 的第92页（PDF零起始页91）列明Source Han Sans 2.0及OFL。它证明真实商业游戏的字体法律声明中出现该字体，不证明本项目或所有使用方式无争议。
- [SIL官方社区2023年讨论](https://community.software.sil.org/t/how-to-restore-sil-ofl-granted-to-me-if-it-has-become-null-and-void/7158) 解释保留许可信息及转换字体保留名称问题；这是授权问答，没有被索赔或判赔的事实。

## 本项目已核验与发布要求

fontTools读取本机源字体内部name表：版权为Adobe，名称为 `Source Han Sans SC`，版本2.005，授权描述为OFL1.1，保留名称为 `Source`。`OS/2.fsType=0` 与允许嵌入的技术标记一致，但不替代法律许可。字体与LICENSE的SHA和上一轮调研证据一致。

后续制作与分享时，只从已记录的Adobe官方源字体生成中文资产，不混入Arial Unicode或来历不明字形；派生字体名使用 `ElsinoreHan Sans`，保留Adobe版权、商标来源说明和完整OFL，记录源文件及生成资产的哈希。派生字体部分仍按OFL分发，不附加与OFL冲突的限制；来源说明不暗示Adobe为本补丁背书。

本轮未生成字体包或替换主游戏，现有个人ZIP仍含许可未核实的Arial字库；不能据本次调查把现有ZIP改称可公开发布。

核验摘要见 [风险复核证据](../../../runtime/evidence/font-license-risk-check-2026-10-11.json)，原字形和覆盖研究见 [选型记录](shareable-font-research-2026-10-11.md)。
