# F8 原文与译文切换

用户要求按 F8 方便游玩时核对原文。实现复用 XUnity 的现成切换能力：其内置 Alt+T 仍可用，新增 BepInEx x86 插件将 F8 接到同一个原文/译文缓存切换函数。无需反向翻译、联网或修改存档；进入新界面时沿用当前显示模式，再按一次恢复中文。

源码为 `tools/patch/TranslationToggle.cs`，构建入口 `build-toggle.ps1`。固定兼容当前 XUnity 5.6.2、Unity 2018.4.20f1、Mono x86；启动时检查切换入口，不能匹配时不启用扩展，不影响原游戏运行。

## 验证

实际后台游戏中调用与F8同一输入处理路径，完成中文菜单→真实原文→中文菜单往返；没有按键时模式不变。捕获的是实际 TMP 组件，不是给测试替换文字。10 项运行断言通过，9 项离线回归通过。

证据：[切换与UI核对摘要](../../../runtime/evidence/f8-toggle-verification.json)、[后台与静音确认](../../../runtime/evidence/f8-toggle-process.json)。测试临时插件与游戏进程已移除/退出；最终热键插件随完整补丁安装。

后台无窗口，`-batchmode -nographics -nosound`，Wwise Suspend 确认成功，低优先级、10fps。没有要求用户手动截图，也没有让游戏抢前台。

首次后台验证因Steam不可用而直接进入默认场景，没有显示主菜单，已如实判失败。探针随后通过真实UI状态机仅展示已有SplashScreen，再点击实际设置按钮；不重置、开始或继续存档。原文按钮实际为Options，验证器最初只接受Settings，已用冻结真实记录纠正并补回归。通用EventSystem日志不能冒充点击设置的证据。

这是实际游戏UI组件与插件集成验证；后台没有渲染像素，也没有注入物理键盘F8事件，不宣称全剧情排版或物理键盘E2E通过。发布插件的Update直接使用Unity `Input.GetKeyDown(KeyCode.F8)`，每次按下只切换一次。
