# Unity Doorstop 4.5.0 对应源码

公开补丁中的 `winhttp.dll` 为 Doorstop 官方 4.5.0 Windows x86 发行文件，未修改。源码完整副本位于同一补丁包的 `ElsinoreHan/sources/UnityDoorstop-4.5.0-source.zip`。每次转发二进制补丁时，应一并保留本说明、LGPL-2.1 文本与源码 ZIP。

| 对象 | SHA256 |
| --- | --- |
| `winhttp.dll` | `cc643b54484f694a8e0e6641cac79d74141009afc9e24d826f6fd7fd48fd182a` |
| 官方 Windows 发行 ZIP | `7bb953e8d883c8bde76ced96f6d0e45660ad6e0151880d8ab5856bf4f532b147` |
| 随附源码 ZIP | `7f0c963104aa08bf5fefef8ff85e7fecd8306838f5af3101487d9db4e9188d63` |

源码为[官方 v4.5.0 标签归档](https://codeload.github.com/NeighTools/UnityDoorstop/zip/refs/tags/v4.5.0)，对应提交 `33dab9a6733862eb81869ff08431d9478b28784b`，包含 55 个文件，无 Git 子模块。完整保留源码版权头、`LICENSE`、配置及构建脚本；未删改或重打包。

源码解压后，在具备 Visual Studio C/C++ 构建工具与 Windows SDK 的 Windows 环境进入 `UnityDoorstop-4.5.0`，可按上游脚本构建 x86：

```powershell
./build.ps1 -Arch x86
```

脚本会下载 xmake 2.6.1。xmake、编译器和 Windows SDK 属于构建工具，不含在当前分发的 `winhttp.dll` 中；本补丁不分发这些工具。脚本、代理代码生成器和全部编译输入已在源码归档中提供。Windows 输出为 `build/windows/x86/release/doorstop.dll`；上游发行流程将其命名为 `winhttp.dll`。

游戏关闭后，用接口兼容的修改版替换游戏根目录的 `winhttp.dll` 即可使用；可保留同版本 `doorstop_config.ini`。补丁不对 Doorstop 加签或禁止用户替换。不要覆盖游戏的 `Elsinore.exe`、`UnityPlayer.dll`、`resources.assets` 或 `Assembly-CSharp.dll`。

官方发行归档：[doorstop_win_release_4.5.0.zip](https://github.com/NeighTools/UnityDoorstop/releases/download/v4.5.0/doorstop_win_release_4.5.0.zip)。官方源码与构建说明：[UnityDoorstop v4.5.0](https://github.com/NeighTools/UnityDoorstop/tree/v4.5.0)。完整条款见 [UnityDoorstop-LGPL-2.1.txt](UnityDoorstop-LGPL-2.1.txt)。本轮核实源码与发行来源，不声称已在本机重编译出位级相同的 DLL。
