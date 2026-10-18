param([Parameter(Mandatory)][string]$BaselinePlugin)
$ErrorActionPreference = 'Stop'
$project = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$baseline = (Resolve-Path -LiteralPath $BaselinePlugin).Path
$candidate = Join-Path $project 'runtime/build/ElsinoreHan.TranslationToggle.dll'
$compiler = Join-Path $env:WINDIR 'Microsoft.NET/Framework/v4.0.30319/csc.exe'
$directory = Join-Path $project 'runtime/build/credits-stall'
[void][IO.Directory]::CreateDirectory($directory)
$executable = Join-Path $directory 'CreditsStallRegressionTests.exe'
& $compiler /nologo /target:exe /platform:x86 /codepage:65001 ('/out:' + $executable) (Join-Path $PSScriptRoot 'CreditsStallRegressionTests.cs')
if ($LASTEXITCODE -ne 0) { throw '长帧离线对照CLI编译失败' }
$results = @()
foreach ($mode in @('baseline', 'candidate')) {
    $plugin = if ($mode -eq 'baseline') { $baseline } else { $candidate }
    $output = & $executable $plugin $mode
    if ($LASTEXITCODE -ne 0) { throw ('真实插件长帧离线对照失败：' + $mode) }
    $row = $output | ConvertFrom-Json
    $row | Add-Member plugin_sha256 (Get-FileHash -LiteralPath $plugin).Hash.ToLowerInvariant()
    $results += $row
}
$proof = [ordered]@{ passed=$true; scope='真实已编译插件的纯手势类离线对照，受控采样间隔；不是Unity运行、物理按键或CPU卡顿根因定位'; rows=$results }
$proof | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $directory 'binary-comparison.json') -Encoding utf8
$proof | ConvertTo-Json -Depth 5
