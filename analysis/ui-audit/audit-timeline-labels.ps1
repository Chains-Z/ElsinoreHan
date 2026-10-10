$ErrorActionPreference = 'Stop'
# 只读时间线标签和详情的真实分支，不启动游戏或访问存档。
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$null = [Reflection.Assembly]::LoadFrom((Join-Path $root 'runtime/vendor/BepInEx5/BepInEx/core/Mono.Cecil.dll'))
$assemblyPath = 'D:/SteamLibrary/steamapps/common/Elsinore/Elsinore_Data/Managed/Assembly-CSharp.dll'
$assembly = [Mono.Cecil.AssemblyDefinition]::ReadAssembly($assemblyPath)
$methods = @()
function Get-AllTypes($types) {
    foreach ($type in $types) {
        $type
        Get-AllTypes $type.NestedTypes
    }
}
try {
    foreach ($type in (Get-AllTypes $assembly.MainModule.Types)) {
        foreach ($method in $type.Methods) {
            if (-not $method.HasBody) { continue }
            $matches = @($method.Body.Instructions | Where-Object {
                $_.OpCode.Name -eq 'ldstr' -and $_.Operand -in @('Unlikely event: ', 'Impossible event: ',
                    'This will not happen based on current conditions.', 'This event did not happen.')
            })
            if ($matches.Count -eq 0) { continue }
            $methods += [ordered]@{ method=$method.FullName; il=@($method.Body.Instructions | ForEach-Object { $_.ToString() }) }
        }
    }
} finally { $assembly.Dispose() }
$report = [ordered]@{ assembly_sha256=(Get-FileHash -LiteralPath $assemblyPath).Hash.ToLowerInvariant(); methods=$methods }
$json = $report | ConvertTo-Json -Depth 12
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'timeline-label-source-audit.json'),
    $json.Replace("`r`n", "`n") + "`n", [Text.UTF8Encoding]::new($false))
Write-Output ('时间线标签相关真实方法数：' + $methods.Count)
