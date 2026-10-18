param([string]$GamePath = 'D:\SteamLibrary\steamapps\common\Elsinore')
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$managed = Join-Path $GamePath 'Elsinore_Data/Managed'
$compiler = Join-Path $env:WINDIR 'Microsoft.NET/Framework/v4.0.30319/csc.exe'
$output = Join-Path $projectRoot 'runtime/build/ElsinoreHan.TranslationToggle.dll'
$buildRecord = Join-Path $projectRoot 'runtime/build/translation-toggle-build.json'
$source = Join-Path $PSScriptRoot 'TranslationToggle.cs'
$references = @(
    (Join-Path $projectRoot 'runtime/vendor/BepInEx5/BepInEx/core/BepInEx.dll'),
    (Join-Path $projectRoot 'runtime/vendor/BepInEx5/BepInEx/core/0Harmony.dll'),
    (Join-Path $projectRoot 'runtime/vendor/XUnity/BepInEx/plugins/XUnity.AutoTranslator/XUnity.AutoTranslator.Plugin.Core.dll'),
    (Join-Path $managed 'Unity.TextMeshPro.dll'),
    (Join-Path $managed 'UnityEngine.UI.dll'),
    (Join-Path $managed 'UnityEngine.UIModule.dll'),
    (Join-Path $managed 'UnityEngine.dll'),
    (Join-Path $managed 'UnityEngine.CoreModule.dll'),
    (Join-Path $managed 'UnityEngine.InputModule.dll')
    (Join-Path $managed 'UnityEngine.TextCoreModule.dll')
)
# 旧编译器每次产生新的模块标识；只有输入及产物哈希均一致时复用，避免安装后无意义重建。
$anchorSource = Join-Path $PSScriptRoot 'LogScrollAnchor.cs'
$invitedSource = Join-Path $PSScriptRoot 'InvitedEventNotice.cs'
$strictSource = Join-Path $PSScriptRoot 'StrictLogTranslation.cs'
$splotchSource = Join-Path $PSScriptRoot 'LeadSplotchLayout.cs'
$geometrySource = Join-Path $PSScriptRoot 'SplotchTileGeometry.cs'
$speakerSource = Join-Path $PSScriptRoot 'LogSpeakerLayout.cs'
$bookSource = Join-Path $PSScriptRoot 'EndingBookLabels.cs'
$paperSource = Join-Path $PSScriptRoot 'BookPaperReconstruction.cs'
$creditsSource = Join-Path $PSScriptRoot 'CreditsHoldSkip.cs'
$gestureSource = Join-Path $PSScriptRoot 'CreditsSkipGesture.cs'
$ringSource = Join-Path $PSScriptRoot 'CreditsSkipRing.cs'
$fingerprint = (@($compiler, $source, $anchorSource, $invitedSource, $strictSource, $splotchSource, $geometrySource, $speakerSource, $bookSource, $paperSource, $creditsSource, $gestureSource, $ringSource) + $references | ForEach-Object { (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash }) -join ':'
if ((Test-Path -LiteralPath $buildRecord) -and (Test-Path -LiteralPath $output)) {
    $previous = Get-Content -LiteralPath $buildRecord -Raw | ConvertFrom-Json
    if ($previous.input_fingerprint -eq $fingerprint -and $previous.output_sha256 -eq (Get-FileHash -LiteralPath $output).Hash) {
        Write-Output $output
        return
    }
}
$arguments = @('/nologo', '/target:library', '/platform:x86', ('/out:' + $output))
foreach ($reference in $references) { $arguments += '/reference:' + $reference }
$arguments += $source
$arguments += $anchorSource
$arguments += $invitedSource
$arguments += $strictSource
$arguments += $splotchSource
$arguments += $geometrySource
$arguments += $speakerSource
$arguments += $bookSource
$arguments += $paperSource
$arguments += $creditsSource
$arguments += $gestureSource
$arguments += $ringSource
& $compiler @arguments
if ($LASTEXITCODE -ne 0) { throw 'F8扩展编译失败' }
[pscustomobject]@{ input_fingerprint=$fingerprint; output_sha256=(Get-FileHash -LiteralPath $output).Hash } | ConvertTo-Json | Set-Content -LiteralPath $buildRecord -Encoding utf8
Write-Output $output
