$ErrorActionPreference = 'Stop'
# 只读实际游戏程序集，记录对话记录的控件绑定及正常自动滚动入口。
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$null = [System.Reflection.Assembly]::LoadFrom((Join-Path $projectRoot 'runtime/vendor/BepInEx5/BepInEx/core/Mono.Cecil.dll'))
$assemblyPath = 'D:/SteamLibrary/steamapps/common/Elsinore/Elsinore_Data/Managed/Assembly-CSharp.dll'
$assembly = [Mono.Cecil.AssemblyDefinition]::ReadAssembly($assemblyPath)
try {
    $type = $assembly.MainModule.Types | Where-Object { $_.FullName -eq 'Elsinore.Ui.LogUI' }
    if ($null -eq $type) { throw '真实程序集没有 LogUI' }
    $report = [ordered]@{
        schema_version = 1
        verified_at = '2026-10-10'
        assembly_sha256 = (Get-FileHash -LiteralPath $assemblyPath -Algorithm SHA256).Hash.ToLower()
        fields = @($type.Fields | ForEach-Object { $_.FullName })
        methods = @($type.Methods | Where-Object {
            $_.Name -in @('Update', 'Initialize', 'ScrollToBottom', 'Elsinore.Ui.IActivatableModalCanvas.Activate')
        } | ForEach-Object {
            [ordered]@{ method=$_.FullName; il=@($_.Body.Instructions | ForEach-Object { $_.ToString() }) }
        })
        findings = @(
            '真实 ScrollArea 为 ScrollRect，Content 为 VerticalLayoutGroup，createdEntries 为 TMP 控件列表',
            'Activate 按相同 index 将 HistoryText[index] 赋给 createdEntries[index]，每个事件有独立控件',
            '正常 Activate 会启动 ScrollToBottom；F8 段落保护不拦截或修改该正常入口',
            'F8 重排后只恢复同一日志控件中同一显式换行段落起点的视口基线，不按整体高度比例对应',
            '历史源、控件身份或显式换行数量改变时跳过恢复；首尾布局边界可能限制目标位置')
    }
    $report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'log-scroll-source-audit.json') -Encoding utf8
} finally { $assembly.Dispose() }
