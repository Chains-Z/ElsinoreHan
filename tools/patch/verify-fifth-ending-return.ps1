param([string]$GamePath = 'D:\SteamLibrary\steamapps\common\Elsinore')
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$managed = Join-Path $GamePath 'Elsinore_Data/Managed'
$compiler = Join-Path $env:WINDIR 'Microsoft.NET/Framework/v4.0.30319/csc.exe'
$outputDirectory = Join-Path $projectRoot 'runtime/build/fifth-ending-return'
[void][IO.Directory]::CreateDirectory($outputDirectory)
$output = Join-Path $outputDirectory 'FifthEndingReturnTests.exe'
& (Join-Path $PSScriptRoot 'build-toggle.ps1') -GamePath $GamePath | Out-Null
$arguments = @('/nologo', '/target:exe', '/platform:x86', '/codepage:65001', '/reference:System.Web.Extensions.dll',
    ('/reference:' + (Join-Path $projectRoot 'runtime/vendor/BepInEx5/BepInEx/core/0Harmony.dll')),
    ('/reference:' + (Join-Path $projectRoot 'runtime/build/ElsinoreHan.TranslationToggle.dll')),
    ('/reference:' + (Join-Path $managed 'Elsinore.dll')),
    ('/reference:' + (Join-Path $managed 'FSharp.Core.dll')),
    ('/out:' + $output), (Join-Path $PSScriptRoot 'FifthEndingReturnTests.cs'))
& $compiler @arguments
if ($LASTEXITCODE -ne 0) { throw '第五次归来离线集成测试编译失败' }
# 仅运行托管CLI，使用临时内存逻辑域；不启动Unity或读取玩家存档。
$result = & $output $projectRoot $managed
if ($LASTEXITCODE -ne 0) { throw '第五次归来离线集成回归失败' }
$proof = $result | ConvertFrom-Json
if (-not $proof.passed -or -not $proof.original_fifth_missing_reproduced) { throw '缺少原版失败和修复通过证据' }
[IO.File]::WriteAllText((Join-Path $outputDirectory 'result.json'), ($result -join "`n") + "`n", [Text.UTF8Encoding]::new($false))
Write-Output $result
