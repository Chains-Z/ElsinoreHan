$ErrorActionPreference = 'Stop'
# 只读真实程序集 IL 和既有场景字节，不启动游戏、不读取存档。
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$null = [System.Reflection.Assembly]::LoadFrom((Join-Path $root 'runtime/vendor/BepInEx5/BepInEx/core/Mono.Cecil.dll'))
$assemblyPath = 'D:/SteamLibrary/steamapps/common/Elsinore/Elsinore_Data/Managed/Assembly-CSharp.dll'
$assembly = [Mono.Cecil.AssemblyDefinition]::ReadAssembly($assemblyPath)
$methods = [System.Collections.Generic.List[object]]::new()
try {
    foreach ($type in $assembly.MainModule.Types) {
        foreach ($method in $type.Methods) {
            $wanted = ($type.FullName -eq 'Elsinore.Ui.UiStrings' -and $method.Name -in @(
                'FormatList', 'FormatCharacterName', 'FormatRoomId', 'FormatLogEntryOpener',
                'FormatEvent', 'SetLineHeight', 'AddParagraphBreak', 'AddParagraphBreakIfPriorContent')) -or
                ($type.FullName -eq 'Elsinore.Ui.TimelineUI' -and $method.Name -in @('createEventContent', 'onEventClick'))
            if ($wanted -and $method.HasBody) {
                $methods.Add([ordered]@{
                    method = $method.FullName
                    il = @($method.Body.Instructions | ForEach-Object { $_.ToString() })
                })
            }
        }
    }
} finally { $assembly.Dispose() }
$resourceRows = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'resource-strings.json') | ConvertFrom-Json
$rooms = @($resourceRows | Where-Object { $_.category -eq 'room_name' })
$queenRoom = @($rooms | Where-Object { $_.source -eq "Gertrude's Chambers" })
if ($queenRoom.Count -ne 1 -or $queenRoom[0].origin.field -ne 'playerFacingName') {
    throw '乔特鲁德寝室的唯一真实显示字段来源不符'
}
$scenePath = Join-Path (Split-Path (Split-Path $assemblyPath)) $queenRoom[0].origin.file
$sceneBytes = [System.IO.File]::ReadAllBytes($scenePath)
$offset = [int]$queenRoom[0].origin.absolute_offset
$length = [BitConverter]::ToInt32($sceneBytes, $offset)
$actual = [Text.Encoding]::UTF8.GetString($sceneBytes, $offset + 4, $length)
if ($actual -cne $queenRoom[0].source) { throw '原场景字段字节与源审计不符' }
$report = [ordered]@{
    schema_version = 1
    verified_at = '2026-10-10'
    verification_method = '只读 Mono.Cecil IL、原场景显示字段字节及冻结资源来源；未启动游戏、读取存档或联网'
    source_files = @(
        [ordered]@{ name = 'Assembly-CSharp.dll'; sha256 = (Get-FileHash -LiteralPath $assemblyPath -Algorithm SHA256).Hash.ToLower() },
        [ordered]@{ name = $queenRoom[0].origin.file; sha256 = (Get-FileHash -LiteralPath $scenePath -Algorithm SHA256).Hash.ToLower() })
    methods = @($methods)
    room_sources = @($rooms)
    queen_room_scene_bytes_verified = $true
    findings = @(
        '名单规则已有末尾句点；原单人/双人/Oxford名单测试无法覆盖真实尾格式',
        'createEventContent在PlayerAttended=true时先向builder2追加段间距；Changes.Length=0仍留下空尾段',
        'onEventClick把builder1和builder2合并到InfoText；空尾段使要求非空right的paragraph规则失败',
        'Gertrude''s Chambers来自level1 RoomMarker.playerFacingName，冻结p00130已覆盖；旧room集合仅选补译候选漏掉已译房间',
        '人物名单来源为VisibleParticipants经FormatCharacterName读取NameMap；只接受真实有限姓名集合',
        '未参加分支原句自带换行；通用通知末尾换行规则会剥掉它，冻结词表没有无换行别名，须由精确时间线封套保留原换行直接消费')
}
$report | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'timeline-followup-source-audit.json') -Encoding utf8
