# Steam Deck公开状态及配置说明

2026-10-19。用户要求补充Steam Deck启动参数，并确认游戏本体能否在Steam Deck上运行。只查公开资料，不在本机模拟设备或声称实机验证。

## 已确认与限制

- Valve官方兼容性接口返回appid 512890，resolved_category为3（Verified）。四项结果为默认控制器配置可用、按键图标匹配、界面文字可读、默认配置性能合格。
- Steam商店及官方appdetails接口都列出Windows、macOS及Linux原生版。官方报告没有提供本次测试的具体运行方式，不能从“已验证”推断我们修改后的Windows／Proton组合也已通过验证。
- 本补丁运行包是Windows x86的Doorstop／BepInEx5组合，不是原生Linux加载器包。SteamOS下的说明要求先选择Proton并取得Windows版，再解压至含Elsinore.exe的目录，设置winhttp DLL覆盖。
- BepInEx官方文档说明Proton/Wine下需要配置本地winhttp代理加载，并提供Steam启动选项方式。采用用户提出的常用无后缀库名写法：`WINEDLLOVERRIDES="winhttp=n,b" %command%`。
- 本汉化没有Steam Deck实机或Proton执行验证，不宣传“Steam Deck汉化已验证”或原生Linux支持。包内Windows的.cmd／.ps1工具不作为SteamOS本机安装方法；只提供手动解压说明。

## 文档范围

仓库README、包内使用／安装／常见问题／更新说明、GitHub发布页和Steam指南草稿均补上配置参考及未实机验证边界。F8、Ctrl可由玩家使用外接键盘或Steam输入映射。本次不为Steam Deck加入新加载器、自动脚本或运行逻辑，不改玩家安装、存档及任何Steam设置。

## 来源与证据

- [Valve官方兼容性接口](https://store.steampowered.com/saleaction/ajaxgetdeckappcompatibilityreport?nAppID=512890)
- [Steam商店](https://store.steampowered.com/app/512890/Elsinore/)
- [Steam官方平台接口](https://store.steampowered.com/api/appdetails?appids=512890&l=english)
- [Valve验证分类说明](https://www.steamdeck.com/en/verified)
- [BepInEx官方Proton／Wine说明](https://docs.bepinex.dev/master/articles/advanced/steam_interop.html#adding-the-dll-override)
- [公开来源快照](../../../runtime/evidence/steamdeck-public-source-verification-2026-10-19.json)

ProtonDB页面及摘要接口本轮未能取得可用数据，没有把其他游戏的社区体验当成Elsinore的实测，也没有由报错推断本游戏不可运行。
