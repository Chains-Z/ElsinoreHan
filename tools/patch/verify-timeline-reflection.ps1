param([string]$GamePath = 'D:/SteamLibrary/steamapps/common/Elsinore')
$ErrorActionPreference = 'Stop'
# 编译离线元数据检查器；不启动游戏或读取存档。
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$managed = Join-Path $GamePath 'Elsinore_Data/Managed'
$compiler = Join-Path $env:WINDIR 'Microsoft.NET/Framework/v4.0.30319/csc.exe'
$helper = Join-Path $root 'runtime/build/TimelineFollowupProbe.dll'
$checker = Join-Path $root 'runtime/build/VerifyTimelineReflection.exe'
$proof = Join-Path $root 'runtime/evidence/timeline-reflection-verification.json'
$arguments = @('/nologo', '/target:library', '/platform:x86', ('/out:' + $helper))
foreach ($name in @('Unity.TextMeshPro.dll', 'UnityEngine.dll', 'Assembly-CSharp.dll', 'UnityEngine.CoreModule.dll', 'UnityEngine.UI.dll')) {
    $arguments += '/reference:' + (Join-Path $managed $name)
}
$arguments += Join-Path $PSScriptRoot 'TimelineFollowupProbe.cs'
& $compiler @arguments
if ($LASTEXITCODE -ne 0) { throw '时间线探针离线编译失败' }
& $compiler '/nologo' '/target:exe' '/platform:x86' '/reference:System.Web.Extensions.dll' ('/out:' + $checker) (Join-Path $PSScriptRoot 'VerifyTimelineReflection.cs')
if ($LASTEXITCODE -ne 0) { throw '时间线反射检查器编译失败' }
& $checker $helper $managed $proof
if ($LASTEXITCODE -ne 0) { throw '真实DLL反射签名自检失败' }
