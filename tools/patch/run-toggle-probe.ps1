param([string]$GamePath = 'D:\SteamLibrary\steamapps\common\Elsinore')
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$GamePath = (Resolve-Path -LiteralPath $GamePath).Path
if (Get-Process -Name Elsinore -ErrorAction SilentlyContinue | Where-Object { $_.MainModule.FileName -eq (Join-Path $GamePath 'Elsinore.exe') }) { throw '目标目录的游戏正在运行，禁止介入' }
& (Join-Path $PSScriptRoot 'build-toggle.ps1') -GamePath $GamePath
$source = Join-Path $projectRoot 'runtime/build/ElsinoreHan.TranslationToggle.dll'
$target = Join-Path $GamePath 'BepInEx/plugins/ElsinoreHan.TranslationToggle.dll'
$created = -not (Test-Path -LiteralPath $target)
if (-not $created -and (Get-FileHash -LiteralPath $source).Hash -ne (Get-FileHash -LiteralPath $target).Hash) { throw '现有热键插件不同，拒绝覆盖' }
$previousMode = $env:ELSINOREHAN_PROBE_TOGGLE
try {
    if ($created) { Copy-Item -LiteralPath $source -Destination $target }
    $env:ELSINOREHAN_PROBE_TOGGLE = '1'
    & (Join-Path $PSScriptRoot 'run-headless-probe.ps1') -GamePath $GamePath
} finally {
    $env:ELSINOREHAN_PROBE_TOGGLE = $previousMode
    if ($created -and (Test-Path -LiteralPath $target)) { Remove-Item -LiteralPath $target }
}
