param([string]$OutputDirectory = 'runtime/build/dialogue-log-followup')
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$output = [IO.Path]::GetFullPath((Join-Path $root $OutputDirectory))
if (-not $output.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw '深度诊断产物必须位于项目目录内'
}
[void][IO.Directory]::CreateDirectory($output)
# 仅为既有真实XUnity消费者增加深度计数；64上限、首匹配和消费结果保持原样。
$source = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'VerifyRecursiveUiRules.cs'))
$source = $source.Replace('private static int depth;', 'private static int depth; private static int peakDepth;')
$source = $source.Replace('depth++;', 'depth++; peakDepth = Math.Max(peakDepth, depth);')
$source = $source.Replace('string actual = null;', 'peakDepth = 0; string actual = null;')
$needle = 'if (actual == (string)row["target"] && error == null) continue;'
if (-not $source.Contains($needle)) { throw '深度诊断消费者注入点变化，请重新核查' }
$insertion = 'File.AppendAllText(Assembly.GetExecutingAssembly().Location + ".depth.tsv", (string)row["id"] + "\t" + peakDepth + "\n"); '
$source = $source.Replace($needle, $insertion + $needle)
$sourcePath = Join-Path $output 'VerifyDialogueLogDepth.cs'
$executable = Join-Path $output 'VerifyDialogueLogDepth.exe'
[IO.File]::WriteAllText($sourcePath,$source,[Text.UTF8Encoding]::new($false))
& (Join-Path $env:WINDIR 'Microsoft.NET/Framework/v4.0.30319/csc.exe') '/nologo' '/platform:x86' '/reference:System.Web.Extensions.dll' ('/out:' + $executable) $sourcePath
if ($LASTEXITCODE -ne 0) { throw '深度计数消费者编译失败' }
Write-Output $executable
