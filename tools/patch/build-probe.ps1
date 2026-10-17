param([string]$GamePath = 'D:\SteamLibrary\steamapps\common\Elsinore')
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$managed = Join-Path $GamePath 'Elsinore_Data\Managed'
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework\v4.0.30319\csc.exe'
$output = Join-Path $projectRoot 'runtime\build\ElsinoreHan.RuntimeProbe.dll'
New-Item -ItemType Directory -Path (Split-Path $output) -Force | Out-Null
$references = @(
    (Join-Path $projectRoot 'runtime\vendor\BepInEx5\BepInEx\core\BepInEx.dll'),
    (Join-Path $projectRoot 'runtime\vendor\BepInEx5\BepInEx\core\0Harmony.dll'),
    (Join-Path $managed 'Unity.TextMeshPro.dll'),
    (Join-Path $managed 'UnityEngine.dll'),
    (Join-Path $managed 'Assembly-CSharp.dll'),
    (Join-Path $managed 'UnityEngine.AudioModule.dll'),
    (Join-Path $managed 'UnityEngine.CoreModule.dll'),
    (Join-Path $managed 'UnityEngine.JSONSerializeModule.dll'),
    (Join-Path $managed 'UnityEngine.ScreenCaptureModule.dll'),
    (Join-Path $managed 'UnityEngine.UI.dll')
    (Join-Path $managed 'UnityEngine.UIModule.dll')
    (Join-Path $managed 'UnityEngine.TextCoreModule.dll')
    (Join-Path $managed 'UnityEngine.TextRenderingModule.dll')
    (Join-Path $projectRoot 'runtime/vendor/XUnity/BepInEx/plugins/XUnity.AutoTranslator/XUnity.AutoTranslator.Plugin.Core.dll')
)
$arguments = @('/nologo', '/target:library', '/platform:x86', ('/out:' + $output))
$arguments += $references | ForEach-Object { '/reference:' + $_ }
$arguments += Join-Path $PSScriptRoot 'RuntimeProbe.cs'
$arguments += Join-Path $PSScriptRoot 'ItalicGeometryProbe.cs'
$arguments += Join-Path $PSScriptRoot 'LeadFollowupProbe.cs'
$arguments += Join-Path $PSScriptRoot 'LeadLayoutProbe.cs'
$arguments += Join-Path $PSScriptRoot 'MapFollowupProbe.cs'
$arguments += Join-Path $PSScriptRoot 'TimelineFollowupProbe.cs'
$arguments += Join-Path $PSScriptRoot 'LogScrollAnchorProbe.cs'
$arguments += Join-Path $PSScriptRoot 'LogSpeakerLayoutProbe.cs'
$arguments += Join-Path $PSScriptRoot 'DocumentScrollAnchorProbe.cs'
$arguments += Join-Path $PSScriptRoot 'BiographyReplayProbe.cs'
$arguments += Join-Path $PSScriptRoot 'BiographyScrollProbe.cs'
$arguments += Join-Path $PSScriptRoot 'FontBakeProbe.cs'
$arguments += Join-Path $PSScriptRoot 'FontRegressionProbe.cs'
$arguments += Join-Path $PSScriptRoot 'StrictLogCacheProbe.cs'
$arguments += Join-Path $PSScriptRoot 'AmbientLogFormatterProbe.cs'
$arguments += Join-Path $PSScriptRoot 'EndingBookProbe.cs'
$arguments += Join-Path $PSScriptRoot 'EndingBookArtProbe.cs'
& $compiler @arguments
if ($LASTEXITCODE -ne 0) { throw '运行时探针编译失败。' }
Write-Output $output
