param(
    [string]$GameDir = 'D:\SteamLibrary\steamapps\common\Elsinore',
    [string]$TestsPath = 'translation/supplemental/dynamic-ui-tests.json'
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$compiler = Join-Path $env:WINDIR 'Microsoft.NET/Framework/v4.0.30319/csc.exe'
$output = Join-Path $root 'runtime/build/VerifyRecursiveUiRules.exe'
$core = Join-Path $GameDir 'BepInEx/plugins/XUnity.AutoTranslator/XUnity.AutoTranslator.Plugin.Core.dll'
if (-not (Test-Path -LiteralPath $compiler) -or -not (Test-Path -LiteralPath $core)) {
    throw '本机 .NET Framework 编译器或真实 XUnity 插件缺失'
}
# 只编译本地组件验证器，不启动游戏、不访问存档或在线翻译服务。
New-Item -ItemType Directory -Path (Split-Path $output) -Force | Out-Null
$arguments = @('/nologo', '/target:exe', '/reference:System.Web.Extensions.dll', '/reference:System.Core.dll',
    ('/out:' + $output), (Join-Path $PSScriptRoot 'VerifyRecursiveUiRules.cs'))
& $compiler @arguments
if ($LASTEXITCODE -ne 0) { throw '真实递归消费者验证器编译失败' }
Push-Location $root
try {
    & $output $core 'translation/sol-full-2026-10-09/dynamic-rules.json' 'translation/sol-full-2026-10-09/translations.json' $TestsPath
    if ($LASTEXITCODE -ne 0) { throw '真实递归消费者组件回归失败' }
} finally {
    Pop-Location
}
