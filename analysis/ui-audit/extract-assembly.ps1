$PSRequiredVersion = '7.0'
# 此脚本由项目当前的 PowerShell 7 执行，避免 Windows PowerShell 5 的 UTF-8 解析差异。
if ($PSVersionTable.PSVersion -lt [version]$PSRequiredVersion) { throw 'PowerShell 7 required' }
$ErrorActionPreference = 'Stop'
# 只读取 IL 元数据，不加载、执行游戏代码。
$cecilAssembly = [System.Reflection.Assembly]::LoadFrom('D:/MyProjects/ElsinoreHan/runtime/vendor/BepInEx5/BepInEx/core/Mono.Cecil.dll')
$gameManaged = 'D:/SteamLibrary/steamapps/common/Elsinore/Elsinore_Data/Managed'
$results = [System.Collections.Generic.List[object]]::new()
function Read-TypeStrings($type, $assemblyName) {
    foreach ($method in $type.Methods) {
        if (-not $method.HasBody) { continue }
        $instructions = $method.Body.Instructions
        for ($index = 0; $index -lt $instructions.Count; $index++) {
            $instruction = $instructions[$index]
            if ($instruction.OpCode.Name -ne 'ldstr') { continue }
            $context = @()
            for ($near = [Math]::Max(0, $index - 5); $near -le [Math]::Min($instructions.Count - 1, $index + 8); $near++) {
                $context += $instructions[$near].ToString()
            }
            $results.Add([ordered]@{
                source = [string]$instruction.Operand
                assembly = $assemblyName
                owner = $method.FullName
                il_offset = ('IL_{0:x4}' -f $instruction.Offset)
                context = $context
            })
        }
    }
    foreach ($nested in $type.NestedTypes) { Read-TypeStrings $nested $assemblyName }
}
foreach ($name in @('Assembly-CSharp.dll', 'Elsinore.dll')) {
    $assembly = [Mono.Cecil.AssemblyDefinition]::ReadAssembly([string](Join-Path $gameManaged $name))
    try {
        foreach ($module in $assembly.Modules) {
            foreach ($type in $module.Types) { Read-TypeStrings $type $name }
        }
    } finally { $assembly.Dispose() }
}
$results | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath 'D:/MyProjects/ElsinoreHan/analysis/ui-audit/assembly-raw-occurrences.json' -Encoding UTF8
