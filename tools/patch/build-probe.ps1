param([string]$GamePath = 'D:\SteamLibrary\steamapps\common\Elsinore')
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$managed = Join-Path $GamePath 'Elsinore_Data\Managed'
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework\v4.0.30319\csc.exe'
$output = Join-Path $projectRoot 'runtime\build\ElsinoreHan.RuntimeProbe.dll'
New-Item -ItemType Directory -Path (Split-Path $output) -Force | Out-Null
$references = @(
    (Join-Path $projectRoot 'runtime\vendor\BepInEx5\BepInEx\core\BepInEx.dll'),
    (Join-Path $managed 'Unity.TextMeshPro.dll'),
    (Join-Path $managed 'UnityEngine.dll'),
    (Join-Path $managed 'Assembly-CSharp.dll'),
    (Join-Path $managed 'UnityEngine.AudioModule.dll'),
    (Join-Path $managed 'UnityEngine.CoreModule.dll'),
    (Join-Path $managed 'UnityEngine.ScreenCaptureModule.dll'),
    (Join-Path $managed 'UnityEngine.UI.dll')
)
$arguments = @('/nologo', '/target:library', '/platform:x86', ('/out:' + $output))
$arguments += $references | ForEach-Object { '/reference:' + $_ }
$arguments += Join-Path $PSScriptRoot 'RuntimeProbe.cs'
& $compiler @arguments
if ($LASTEXITCODE -ne 0) { throw '运行时探针编译失败。' }
Write-Output $output
