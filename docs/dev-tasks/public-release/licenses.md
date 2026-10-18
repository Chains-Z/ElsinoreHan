# 第三方许可与对应源码审计

2026-10-19。范围为审计开始时 `runtime/package/ElsinoreHan-Sol/` 的 40 个文件，以及产生这些文件的本地 vendor 和官方上游。未运行游戏、安装补丁或接触存档。本页与[机器证据](../../../runtime/evidence/public-release-license-audit-2026-10-19.json)记录准备结果；最终 ZIP 是否含全部文件仍由公开包验证器判定。

## 已完成的结论

当前运行依赖中，没有查到 GPL 组件。BepInEx 5.4.23.5、BepInEx.Harmony、HarmonyX 2.9.0、Mono.Cecil 0.10.4、MonoMod 22.01.29.01、XUnity 5.6.2 与 ExIni 1.0.2.1 的精确版本均为 MIT。不能拿 BepInEx 当前主分支的 LGPL 概括本包的 BepInEx 5；已逐项读取[版本标签 LICENSE](https://github.com/BepInEx/BepInEx/blob/v5.4.23.5/LICENSE)及[构建依赖版本](https://github.com/BepInEx/BepInEx/blob/v5.4.23.5/BepInEx/BepInEx.csproj)，并对照本地 DLL 产品版本和提交标识。

仅依赖 DLL 的简写版权字段不够。本轮独立附上各项完整许可证，并补上 Harmony 原作者 Andreas Pardeike、HarmonyX 内的 JetBrains.Annotations，以及 XUnity 内的 SimpleJSON 许可。XUnity.Common 的反射辅助代码注明参考 MonoMod / Harmony；相关完整许可一并保留。没有把只存在于编译工具、未发运的翻译器插件、AiNiee 虚拟环境或游戏自带 Managed 程序集中的依赖列为补丁分发内容。

`0Harmony20.dll` 是 BepInEx.Harmony 同一精确提交构建的兼容程序集，不按文件名推定为另一个未知 Harmony 2 发行版；其产品版本、`BepInEx.Harmony.dll` 与 `HarmonyXInterop.dll` 都带提交 `d4cdcb4cdeac14a0b77012165f5f5a9f5032a9fa`。MonoMod 两程序集的版本是 22.1.29.1，对应源码标签拼法为 `v22.01.29.01`。

## Doorstop：已经实际准备对应源码

`winhttp.dll` 是 LGPL-2.1 的 Unity Doorstop 4.5.0，不能沿用 Doorstop 3 的 CC0，也不能因为 BepInEx 5 为 MIT 而省略 LGPL。来源链已核实：

- 待发布 DLL 与本地 BepInEx vendor、重新下载的 BepInEx 官方 x86 发行 ZIP、Doorstop 官方 4.5.0 x86 发行 ZIP 中的 DLL 逐字节一致，SHA256 均为 `cc643b54484f694a8e0e6641cac79d74141009afc9e24d826f6fd7fd48fd182a`。
- [BepInEx 5.4.23.5 的 build.cake](https://github.com/BepInEx/BepInEx/blob/v5.4.23.5/build.cake)固定下载 Doorstop 4.5.0，并将 x86 `winhttp.dll` 复制入分发包；不是本项目自行修改的 DLL。
- 已保存[官方 v4.5.0 完整源码归档](https://codeload.github.com/NeighTools/UnityDoorstop/zip/refs/tags/v4.5.0)，ZIP 注释的提交是 `33dab9a6733862eb81869ff08431d9478b28784b`，归档 55 个文件，SHA256 为 `7f0c963104aa08bf5fefef8ff85e7fecd8306838f5af3101487d9db4e9188d63`。
- 归档无 `.gitmodules`、没有需另补的源码子模块。Windows/Nix 平台源文件、接口头、代理导出与资源生成 Lua、xmake 配置和全部构建脚本均在内。Windows 构建不外取库源码；xmake 2.6.1、Visual Studio 工具与 SDK 属于构建工具，不是缺失的静态链接库。
- 源码原样保留 BSD plthook 的版权/许可头。plthook 由 `xmake.lua` 限定为 Linux/macOS 编译分支，Windows DLL 不编入该实现。

采用 LGPL-2.1 第 4 条的“直接随附完整对应源码”路径。公开 ZIP 必须包含 `ElsinoreHan/sources/UnityDoorstop-4.5.0-source.zip`、完整 LGPL 和构建说明；上游网页链接只用于溯源。不能用“源码可向官方获取”的话代替归档，也不采用要求至少三年履行的书面要约。第三方说明明确允许修改/调试和替换 Doorstop，不对接口兼容 DLL 施加本项目额外限制。

源码不入 Git，保存在忽略的 `runtime/build/public-license-audit/`；Git 中记录下载地址、提交和 SHA256。下载源 ZIP 后按上述哈希验证即可重建分发材料。没有执行上游构建脚本，也没有声称重编译得到了位级相同 DLL。

## 字体与残留资产的真实范围

OFL 来源与改名仍按[字体替换记录](../localization/font-replacement-2026-10-11.md)、[许可复核](../localization/font-license-risk-check-2026-10-11.md)。本次直接读取当前字体包：共 7 个对象，分别为两个 TMP Shader、一个 Texture2D、一个 Material、一个 TMP_FontAsset MonoBehaviour、一个 MonoScript 引用和一个 AssetBundle；没有 Font 对象、源 OTF 或额外资源流。MonoScript 是指向 `Unity.TextMeshPro.dll` 的序列化类型引用，包内未附带该 DLL。

字形、度量、kerning 和图集经项目生成器替换，旧 Arial `.resS` 已删除；这不等于全部资产都是项目原创。仍复用 XUnity 官方旧样板里的 TMP 兼容结构、材质和两个 Shader（`TextMeshPro/Mobile/Distance Field`、`TextMeshPro/Distance Field`），按 Unity Companion Package License v1.0 限于 Unity 引擎依赖的游戏内容。已保留 Unity 完整许可，并重新查证[官方 1.0 许可页](https://docs.unity3d.com/Packages/com.unity.textmeshpro@1.0/license/LICENSE.html)。不把上述对象归入 OFL，不宣称本轮对 Shader 编译产物与官方 Unity 包做过位级匹配；本轮身份依据为官方样板来源、实际对象结构与 Shader 标识。

本项目插件及译文未因为第三方依赖而自动改为 MIT/OFL/LGPL。本轮不擅自为权利人选择新的项目许可证；第三方清单不会声称整个项目已获得同一种开源授权。游戏英文内容权利也不由这些开源许可授予。

## 公开包白名单

运行文件保持既有 39 文件（原 40 文件去除个人包 README）。新增发行辅助材料放在 `ElsinoreHan/` 内，不覆盖原运行位置的 `licenses/` 三份旧字体许可，以保持安装器的既有哈希契约。

将仓库 `licenses/` 中下列文件逐一复制到 ZIP 的 `ElsinoreHan/licenses/`：

```text
BepInEx-LICENSE.txt
BepInEx.Harmony-LICENSE.txt
ElsinoreHanSans-NOTICE.txt
ElsinoreHanSans-OFL.txt
ExIni-LICENSE.txt
Harmony-LICENSE.txt
HarmonyX-LICENSE.txt
JetBrains.Annotations-LICENSE.txt
Mono.Cecil-LICENSE.txt
MonoMod-LICENSE.txt
SimpleJSON-LICENSE.txt
TextMeshPro-Unity-Companion-License.txt
THIRD-PARTY-NOTICES.md
UnityDoorstop-LGPL-2.1.txt
UnityDoorstop-SOURCE.md
XUnity.AutoTranslator-LICENSE.txt
```

另将 `runtime/build/public-license-audit/UnityDoorstop-4.5.0-source.zip` 复制到 ZIP 的 `ElsinoreHan/sources/UnityDoorstop-4.5.0-source.zip`。发行包检查必须验证许可证完整清单、所有文件哈希及源码归档内部文件集合；不能只看文件名存在。维护者重新生成时也应拒绝源码 SHA256 不符。

其他官方源码 ZIP 均仅用于本地许可审计，不进入补丁，不上传本地 vendor、历史 Arial 样板、UnityPy、fontTools、AiNiee 目录或其虚拟环境。源码 ZIP 不入仓库 Git 历史。
