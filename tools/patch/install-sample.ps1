param([string]$GamePath = 'D:\SteamLibrary\steamapps\common\Elsinore')
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$GamePath = (Resolve-Path -LiteralPath $GamePath).Path
if (Get-Process -Name Elsinore -ErrorAction SilentlyContinue) { throw '请先关闭游戏。' }
foreach ($name in @('BepInEx', 'winhttp.dll', 'doorstop_config.ini', 'arialuni_sdf_u2018')) {
    if (Test-Path -LiteralPath (Join-Path $GamePath $name)) { throw ('检测到既有文件，拒绝覆盖：' + $name) }
}
# 本安装只增加此前不存在的文件，既有游戏文件不作覆盖。
$baseline = @('Elsinore.exe', 'UnityPlayer.dll', 'Elsinore_Data\resources.assets', 'Elsinore_Data\Managed\Assembly-CSharp.dll') | ForEach-Object {
    $file = Join-Path $GamePath $_
    [pscustomobject]@{ path = $_; sha256 = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash }
}
$evidence = Join-Path $projectRoot 'runtime\evidence'
$baseline | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $evidence 'original-game-hashes.json') -Encoding utf8
$sources = @(
    (Join-Path $projectRoot 'runtime\vendor\BepInEx5'),
    (Join-Path $projectRoot 'runtime\vendor\XUnity')
)
$added = [System.Collections.Generic.List[object]]::new()
foreach ($source in $sources) {
    foreach ($file in Get-ChildItem -LiteralPath $source -File -Recurse) {
        $relative = $file.FullName.Substring($source.Length + 1)
        # 离线样板无需携带任何网络翻译端点程序集。
        if ($relative -match '\\Translators\\') { continue }
        $target = Join-Path $GamePath $relative
        if (Test-Path -LiteralPath $target) { throw ('目标存在，拒绝覆盖：' + $target) }
        New-Item -ItemType Directory -Path (Split-Path $target) -Force | Out-Null
        Copy-Item -LiteralPath $file.FullName -Destination $target
        $added.Add([pscustomobject]@{ path = $relative; sha256 = (Get-FileHash -LiteralPath $target).Hash })
    }
}
$extra = @(
    @{ source = 'runtime\vendor\fonts\arialuni_sdf_u2018'; target = 'arialuni_sdf_u2018' },
    @{ source = 'runtime\sample\AutoTranslatorConfig.ini'; target = 'BepInEx\config\AutoTranslatorConfig.ini' },
    @{ source = 'runtime\sample\sample.txt'; target = 'BepInEx\Translation\zh-CN\Text\sample.txt' }
)
foreach ($item in $extra) {
    $target = Join-Path $GamePath $item.target
    if (Test-Path -LiteralPath $target) { throw ('目标存在，拒绝覆盖：' + $target) }
    New-Item -ItemType Directory -Path (Split-Path $target) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $projectRoot $item.source) -Destination $target
    $added.Add([pscustomobject]@{ path = $item.target; sha256 = (Get-FileHash -LiteralPath $target).Hash })
}
[pscustomobject]@{ game_path = $GamePath; installed_at = (Get-Date -Format o); files = $added } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $evidence 'installed-files.json') -Encoding utf8
Write-Output '离线样板已安装；所有翻译端点为空，未覆盖游戏原文件。后台测试使用 run-headless-probe.ps1；正常游玩不会自动退出。'
