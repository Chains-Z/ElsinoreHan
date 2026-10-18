# 第三方组件与许可

本文件随 ElsinoreHan 离线中文补丁分发。运行组件位于游戏目录；本文件所在的 `ElsinoreHan/licenses/` 和相邻的 `ElsinoreHan/sources/` 保留许可与对应源码。第三方组件分别遵守以下许可，不由本项目统一改换许可证。

| 组件及实际版本 | 补丁中的文件 | 版权、许可与来源 |
| --- | --- | --- |
| BepInEx 5.4.23.5，`57f1fb859bd4d0264cd2a59074d0e96c6a492a33` | `BepInEx/core/BepInEx.dll`、`BepInEx.Preloader.dll` 及文档、启动配置 | Bepis，MIT；[许可](BepInEx-LICENSE.txt)、[精确版本源码](https://github.com/BepInEx/BepInEx/tree/v5.4.23.5) |
| BepInEx.Harmony，`d4cdcb4cdeac14a0b77012165f5f5a9f5032a9fa` | `BepInEx.Harmony.dll`、`0Harmony20.dll`、`HarmonyXInterop.dll` 及 XML 文档 | BepInEx.Harmony 作者，MIT；[许可](BepInEx.Harmony-LICENSE.txt)、[精确提交](https://github.com/BepInEx/BepInEx.Harmony/tree/d4cdcb4cdeac14a0b77012165f5f5a9f5032a9fa) |
| HarmonyX 2.9.0，包含 Harmony 与 JetBrains.Annotations | `BepInEx/core/0Harmony.dll` 及 XML 文档 | BepInEx、Andreas Pardeike、JetBrains；MIT；[HarmonyX](HarmonyX-LICENSE.txt)、[Harmony](Harmony-LICENSE.txt)、[JetBrains.Annotations](JetBrains.Annotations-LICENSE.txt)、[源码](https://github.com/BepInEx/HarmonyX/tree/v2.9.0) |
| Mono.Cecil 0.10.4 | `Mono.Cecil.dll`、`Mono.Cecil.Mdb.dll`、`Mono.Cecil.Pdb.dll`、`Mono.Cecil.Rocks.dll` | Jb Evain、Novell；MIT；[许可](Mono.Cecil-LICENSE.txt)、[源码](https://github.com/jbevain/cecil/tree/0.10.4) |
| MonoMod 22.01.29.01 | `MonoMod.RuntimeDetour.dll`、`MonoMod.Utils.dll` 及 XML 文档 | 0x0ade；MIT；[许可](MonoMod-LICENSE.txt)、[源码](https://github.com/MonoMod/MonoMod/tree/v22.01.29.01) |
| Unity Doorstop 4.5.0，`33dab9a6733862eb81869ff08431d9478b28784b` | `winhttp.dll`、`.doorstop_version` | NeighTools / Doorstop 贡献者；LGPL-2.1；[完整许可](UnityDoorstop-LGPL-2.1.txt)、[随附源码](../sources/UnityDoorstop-4.5.0-source.zip)、[构建说明](UnityDoorstop-SOURCE.md)、[官方源码](https://github.com/NeighTools/UnityDoorstop/tree/v4.5.0) |
| XUnity.AutoTranslator 5.6.2，`c6b79bfbcc26c33e69056152b90ebae79384d6a3`；XUnity.Common 1.0.5；ResourceRedirector 2.1.0；ExtProtocol 1.0.1 | `XUnity.Common.dll`、`XUnity.AutoTranslator.Plugin.*.dll`、`XUnity.ResourceRedirector*.dll` 及上游说明 | Bepis / XUnity 贡献者；MIT；[许可](XUnity.AutoTranslator-LICENSE.txt)、[源码](https://github.com/bbepis/XUnity.AutoTranslator/tree/v5.6.2) |
| SimpleJSON，XUnity 5.6.2 内含版本 | `XUnity.AutoTranslator.Plugin.Core.dll` 中的 JSON 代码 | Markus Göbel (Bunny83)，MIT；[许可](SimpleJSON-LICENSE.txt)、[对应源文件](https://github.com/bbepis/XUnity.AutoTranslator/blob/v5.6.2/src/XUnity.AutoTranslator.Plugin.Core/Json/SimpleJson.cs) |
| ExIni 1.0.2.1，`cf85ca6f3fc361cf48bf56107e4cec9102b7f5eb` | `BepInEx/plugins/XUnity.AutoTranslator/ExIni.dll` | Usagirei，MIT；[许可](ExIni-LICENSE.txt)、[精确源码](https://github.com/usagirei/ExIni/tree/cf85ca6f3fc361cf48bf56107e4cec9102b7f5eb) |
| ElsinoreHan Sans SDF，派生自 Source Han Sans SC Regular 2.005R | `elsinorehan_sans_sdf_u2018` 的字体字形、图集和度量 | Adobe；OFL-1.1；[许可](ElsinoreHanSans-OFL.txt)、[来源与改名](ElsinoreHanSans-NOTICE.txt)、[官方字体](https://github.com/adobe-fonts/source-han-sans/tree/2.005R) |
| TextMeshPro 字体资产兼容结构、材质及着色器 | 同一字体包中的 `TMP_FontAsset` 引用、Material、`TextMeshPro/Mobile/Distance Field` 与 `TextMeshPro/Distance Field` Shader | Unity Technologies；[Unity Companion Package License v1.0](TextMeshPro-Unity-Companion-License.txt)，限 Unity 引擎依赖内容；[官方许可](https://docs.unity3d.com/Packages/com.unity.textmeshpro@1.0/license/LICENSE.html) |

`XUnity.Common` 中参考 MonoMod 和 Harmony 的反射辅助实现同时保留上述 MonoMod、Harmony 许可。DLL 的版本元数据只有版权简写，不替代这些完整许可文本。

## Doorstop 的使用与源码

`winhttp.dll` 使用 LGPL-2.1。随补丁直接附上精确版本的完整、可机读源码，包含平台源文件、接口头文件、代理导出生成器和 `build.ps1` / `build.sh` / `xmake.lua`。源码 ZIP 保留上游许可、源码版权头和 BSD 许可的 plthook 文件；plthook 仅用于源码中的 Unix 平台分支，Windows DLL 不包含该分支。

本项目未修改或重新编译该 DLL；它与 Doorstop 官方 4.5.0 Windows x86 发行文件、BepInEx 官方 5.4.23.5 x86 发行文件逐字节相同。用户可根据随附源码修改并重新构建 Doorstop，在游戏关闭后替换 `winhttp.dll`；补丁不限制为修改 Doorstop 而进行的调试、修改和逆向工程。对应源码随每一份补丁复制，不依赖上游链接长期有效，也不采用书面要约替代源码。

## 字体与游戏内容

派生字体使用独立名称 `ElsinoreHan Sans SDF`，没有使用保留字体名 Source 作为字体名称；字体部分仍按 OFL 分发，不得单独出售。现字体包含重新生成的思源字形与图集，旧 Arial 字形、kerning 和资源流已经替换或移除。TMP 兼容结构、材质和着色器来源于 XUnity 官方旧字体样板；它们按 Unity Companion License 用于本 Unity 游戏，不声称属于 OFL 字体或本项目原创内容。

本补丁不包含游戏可执行文件、UnityPlayer、原始场景/剧情资源、游戏托管程序集或玩家存档。游戏内容及商标归其权利人所有。本清单不构成对游戏版权、项目译文或本项目插件的另行授权，也不暗示第三方为本补丁背书。
