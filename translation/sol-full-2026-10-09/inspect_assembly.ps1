# 静态读取方法体与字符串用途，不加载或执行游戏程序集。
$ErrorActionPreference = 'Stop'
$inspectionRoot = Split-Path -Parent $PSScriptRoot
$inspectionRoot = Split-Path -Parent $inspectionRoot
$inspectionRows = Get-Content -LiteralPath (Join-Path $inspectionRoot 'analysis/assembly_review.json') -Raw | ConvertFrom-Json
$inspectionOffsets = @{}
for ($inspectionIndex = 0; $inspectionIndex -lt $inspectionRows.Count; $inspectionIndex++) {
    $inspectionOffset = [int]($inspectionRows[$inspectionIndex].origin.Split(':')[-1])
    $inspectionOffsets[$inspectionOffset] = $inspectionIndex
}
$inspectionOpcodes = @{}
foreach ($inspectionField in [System.Reflection.Emit.OpCodes].GetFields()) {
    if ($inspectionField.FieldType -eq [System.Reflection.Emit.OpCode]) {
        $inspectionOpcode = $inspectionField.GetValue($null)
        $inspectionOpcodes[[int]($inspectionOpcode.Value -band 65535)] = $inspectionOpcode
    }
}
$inspectionStream = [System.IO.File]::OpenRead('D:\SteamLibrary\steamapps\common\Elsinore\Elsinore_Data\Managed\Assembly-CSharp.dll')
$inspectionPe = [System.Reflection.PortableExecutable.PEReader]::new($inspectionStream)
$inspectionMetadata = [System.Reflection.Metadata.PEReaderExtensions]::GetMetadataReader($inspectionPe)
$inspectionResults = [System.Collections.Generic.List[object]]::new()
try {
    foreach ($inspectionHandle in $inspectionMetadata.MethodDefinitions) {
        $inspectionMethod = $inspectionMetadata.GetMethodDefinition($inspectionHandle)
        if ($inspectionMethod.RelativeVirtualAddress -eq 0) { continue }
        $inspectionType = $inspectionMetadata.GetTypeDefinition($inspectionMethod.GetDeclaringType())
        $inspectionTypeName = $inspectionMetadata.GetString($inspectionType.Name)
        $inspectionParentHandle = $inspectionType.GetDeclaringType()
        while (-not $inspectionParentHandle.IsNil) {
            $inspectionParent = $inspectionMetadata.GetTypeDefinition($inspectionParentHandle)
            $inspectionTypeName = $inspectionMetadata.GetString($inspectionParent.Name) + '+' + $inspectionTypeName
            $inspectionParentHandle = $inspectionParent.GetDeclaringType()
        }
        $inspectionName = $inspectionTypeName + '.' + $inspectionMetadata.GetString($inspectionMethod.Name)
        $inspectionBody = [System.Reflection.Metadata.PEReaderExtensions]::GetMethodBody($inspectionPe, $inspectionMethod.RelativeVirtualAddress)
        $inspectionBytes = $inspectionBody.GetILBytes()
        $inspectionPosition = 0
        while ($inspectionPosition -lt $inspectionBytes.Length) {
            $inspectionInstruction = $inspectionPosition
            $inspectionOpcodeValue = [int]$inspectionBytes[$inspectionPosition++]
            if ($inspectionOpcodeValue -eq 254) {
                $inspectionOpcodeValue = 65024 + [int]$inspectionBytes[$inspectionPosition++]
            }
            $inspectionOpcode = $inspectionOpcodes[$inspectionOpcodeValue]
            if ($null -eq $inspectionOpcode) { throw '未知 IL 操作码' }
            $inspectionOperandType = $inspectionOpcode.OperandType.ToString()
            if ($inspectionOperandType -eq 'InlineString') {
                $inspectionToken = [BitConverter]::ToInt32($inspectionBytes, $inspectionPosition)
                $inspectionStringOffset = $inspectionToken -band 16777215
                if ($inspectionOffsets.ContainsKey($inspectionStringOffset)) {
                    $inspectionResults.Add([PSCustomObject]@{ index = $inspectionOffsets[$inspectionStringOffset]; method = $inspectionName; il_offset = $inspectionInstruction })
                }
            }
            $inspectionSize = switch ($inspectionOperandType) {
                'InlineNone' { 0 }
                'ShortInlineBrTarget' { 1 }
                'ShortInlineI' { 1 }
                'ShortInlineVar' { 1 }
                'InlineVar' { 2 }
                'InlineI8' { 8 }
                'InlineR' { 8 }
                'InlineSwitch' { 4 + 4 * [BitConverter]::ToInt32($inspectionBytes, $inspectionPosition) }
                default { 4 }
            }
            $inspectionPosition += $inspectionSize
        }
    }
    $inspectionResults | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'assembly-callsites.json') -Encoding utf8
    [PSCustomObject]@{ references = $inspectionResults.Count; distinct_strings = ($inspectionResults.index | Sort-Object -Unique).Count } | ConvertTo-Json
}
finally {
    $inspectionPe.Dispose()
    $inspectionStream.Dispose()
}
