param([string]$GamePath = 'D:\SteamLibrary\steamapps\common\Elsinore')
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$managed = Join-Path $GamePath 'Elsinore_Data/Managed'
$compiler = Join-Path $env:WINDIR 'Microsoft.NET/Framework/v4.0.30319/csc.exe'
$output = Join-Path $projectRoot 'runtime/build/ElsinoreHan.TranslationToggle.dll'
$arguments = @('/nologo', '/target:library', '/platform:x86', ('/out:' + $output))
foreach ($reference in @(
    (Join-Path $projectRoot 'runtime/vendor/BepInEx5/BepInEx/core/BepInEx.dll'),
    (Join-Path $managed 'UnityEngine.dll'),
    (Join-Path $managed 'UnityEngine.CoreModule.dll'),
    (Join-Path $managed 'UnityEngine.InputModule.dll')
)) { $arguments += '/reference:' + $reference }
$arguments += Join-Path $PSScriptRoot 'TranslationToggle.cs'
& $compiler @arguments
if ($LASTEXITCODE -ne 0) { throw 'F8扩展编译失败' }
Write-Output $output
