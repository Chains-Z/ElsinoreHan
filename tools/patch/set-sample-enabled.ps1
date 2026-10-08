param(
    [bool]$Enabled = $false,
    [string]$GamePath = 'D:\SteamLibrary\steamapps\common\Elsinore'
)
$ErrorActionPreference = 'Stop'
if (Get-Process -Name Elsinore -ErrorAction SilentlyContinue) { throw '请先关闭游戏。' }
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$manifest = Get-Content -LiteralPath (Join-Path $projectRoot 'runtime\evidence\installed-files.json') -Raw | ConvertFrom-Json
$resolved = (Resolve-Path -LiteralPath $GamePath).Path
if ($resolved -ne $manifest.game_path) { throw '游戏目录与安装记录不一致。' }
$configuration = Join-Path $resolved 'doorstop_config.ini'
$content = Get-Content -LiteralPath $configuration -Raw
$value = if ($Enabled) { 'true' } else { 'false' }
$content = [regex]::Replace($content, '(?m)^enabled\s*=\s*(?:true|false)\s*$', 'enabled = ' + $value)
Set-Content -LiteralPath $configuration -Value $content -Encoding utf8
Write-Output ('离线样板启用状态：' + $Enabled)
