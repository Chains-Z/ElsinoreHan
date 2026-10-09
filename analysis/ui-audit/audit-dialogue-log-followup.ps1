$ErrorActionPreference = 'Stop'
# 只读原程序集，定位对白记录与编译变换，禁止启动游戏或读取存档。
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$null = [Reflection.Assembly]::LoadFrom((Join-Path $root 'runtime/vendor/BepInEx5/BepInEx/core/Mono.Cecil.dll'))
$managed = 'D:/SteamLibrary/steamapps/common/Elsinore/Elsinore_Data/Managed'
$files = @()
$methods = @()
foreach ($name in @('Assembly-CSharp.dll', 'Elsinore.dll')) {
    $path = Join-Path $managed $name
    $files += [ordered]@{ path=$path; sha256=(Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant() }
    $assembly = [Mono.Cecil.AssemblyDefinition]::ReadAssembly($path)
    try {
        foreach ($type in $assembly.MainModule.GetTypes()) {
            foreach ($method in $type.Methods | Where-Object HasBody) {
                $wanted = ($type.FullName -eq 'Elsinore.Ui.HistoryTracker') -or
                    ($type.FullName -like 'Elsinore.Ui.HistoryTracker/*') -or
                    ($type.FullName -eq 'Elsinore.Ui.LogUI') -or
                    ($type.FullName -eq 'Elsinore.Ui.DialogueUI' -and $method.Name -in @('onStartDialogue','animateText')) -or
                    ($type.FullName -eq 'Elsinore.Ui.UiStrings' -and $method.Name -in @('FormatLogEntryOpener','FormatCharacterName','FormatShortCharacterName','SetLineHeight','AddParagraphBreak')) -or
                    ($type.FullName -like 'Elsinore.Game.CompilerPasses*' -and ($method.Name -eq 'doTextReplacement' -or
                        $type.FullName -like '*italicizeAllDialogueOf*' -or $method.Name -eq 'italicizeAllDialogueOf' -or
                        ($method.Body.Instructions | Where-Object { $_.Operand -like '*doTextReplacement*' })))
                if ($wanted) {
                    $methods += [ordered]@{ assembly=$name; method=$method.FullName; il=@($method.Body.Instructions | ForEach-Object ToString) }
                }
            }
        }
    } finally { $assembly.Dispose() }
}
$report = [ordered]@{ schema_version=1; verification_method='只读 Mono.Cecil IL；未启动游戏、读取存档、安装或联网'; source_files=$files; methods=$methods }
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'dialogue-log-followup-il.json'), ($report | ConvertTo-Json -Depth 14), [Text.UTF8Encoding]::new($false))
Write-Output ('真实方法数：' + $methods.Count)
