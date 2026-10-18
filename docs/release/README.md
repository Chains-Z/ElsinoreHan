# ElsinoreHan 中文补丁

首个公开版本：`v1.5.15-zh.20261019`。兼容插件版本：`1.5.15`。

《Elsinore》的离线中文补丁，包含对白、人物资料、文档、线索、日志、地图、时间线等玩家文字的预制译文，以及中文字体和中英文切换功能。需要自行拥有并安装游戏；此包不包含游戏本体或存档。

已验证版本为 Windows 32 位、Unity 2018.4.20f1、Mono 版《Elsinore》1.4.1（3678）。其他平台、游戏版本及模组组合尚未验证。

## 安装与使用

保存进度并退出游戏，将 ZIP 中的所有内容解压到 `Elsinore.exe` 所在目录，保留原有目录结构，然后正常从 Steam 启动游戏即可。运行文件应直接位于游戏目录，不要额外套一层补丁文件夹。

首次安装到没有其他模组的游戏目录可直接解压使用；已有其他模组或升级旧补丁时，建议先解压到外部目录，使用可选安装器检查文件冲突，详见 [INSTALL.md](INSTALL.md)。

- 按 **F8** 在中文和英文原文之间切换，再按一次恢复中文。
- 按 **Alt+R** 重载本地词表。更新补丁、字体或配置后需要重启游戏。
- 运行时只读取本地译文，不调用在线翻译 API，也不需要 API Key。

详细安装、更新、停用和卸载步骤见 [INSTALL.md](INSTALL.md)；显示或启动问题见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)；本版变化见 [CHANGELOG.md](CHANGELOG.md)。

## 翻译状态与反馈

译文以机器翻译初稿为基础，已结合实际游玩持续校订。本版包含 17,069 条预制词条和 157 条动态文字规则。已有完整游玩反馈，但尚未对所有分支逐句人工校对，也不能保证未知动态文字、图片文字及全部排版均无遗漏。

工作人员姓名、歌曲名、技术品牌和按键名等部分内容会按原文保留。发现疑句时可按 F8 对照英文，并通过[项目仓库](https://github.com/Chains-Z/ElsinoreHan)反馈；请附原句、中文、说话人或界面位置及截图。提交公开截图时请标明剧透并遮盖个人信息，无需上传存档。完整反馈建议见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md#反馈问题)。

## 组件、字体与源码

补丁使用 BepInEx 5 x86、XUnity.AutoTranslator 5.6.2、ElsinoreHan 兼容插件，以及基于思源黑体 SC Regular 生成的 `ElsinoreHan Sans SDF` 中文字体。

第三方组件、版权和许可证索引见 [THIRD-PARTY-NOTICES.md](licenses/THIRD-PARTY-NOTICES.md)，完整许可位于本说明旁的 `licenses/`。随包第三方对应源码及说明位于 `sources/`。项目源码和译文维护资料见[项目仓库](https://github.com/Chains-Z/ElsinoreHan)。游戏本身的权利归原权利人所有。
