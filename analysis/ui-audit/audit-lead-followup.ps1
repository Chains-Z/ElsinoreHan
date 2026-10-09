$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
[void][Reflection.Assembly]::LoadFrom((Join-Path $root 'runtime/vendor/BepInEx5/BepInEx/core/Mono.Cecil.dll'))
$managed = 'D:/SteamLibrary/steamapps/common/Elsinore/Elsinore_Data/Managed'
$methods = @()
$files = @()
foreach ($name in @('Assembly-CSharp.dll', 'Elsinore.dll')) {
    $path = Join-Path $managed $name
    $files += [pscustomobject]@{ path=$path; sha256=(Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant() }
    $assembly = [Mono.Cecil.AssemblyDefinition]::ReadAssembly($path)
    try {
        foreach ($type in $assembly.MainModule.GetTypes()) {
            foreach ($method in $type.Methods | Where-Object HasBody) {
                $selected = ($type.FullName -eq 'Elsinore.Ui.GuiUtils' -and $method.Name -eq 'FormatLeadText') -or
                    ($type.FullName -eq 'Elsinore.Ui.UiStrings' -and $method.Name -in @('SetLineHeight','SetTextWithLineHeight')) -or
                    ($type.FullName -like 'Elsinore.Ui.JournalLeadsTab*' -and $method.Name -eq '<OnEnable>b__3') -or
                    ($type.FullName -eq 'Elsinore.Game.CompilerPasses' -and $method.Name -in @('f@294-51','f@294-50','doTextReplacement'))
                if ($selected) {
                    $methods += [pscustomobject]@{ assembly=$name; method=$method.FullName; full_il=@($method.Body.Instructions | ForEach-Object ToString) }
                }
            }
        }
    } finally { $assembly.Dispose() }
}
$output = [pscustomobject]@{ scope='静态IL，只读原程序集；线索活动段按资源顺序用双LF连接，前置90%行高；LeadLine编译时执行九步破折号替换'; files=$files; methods=$methods }
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'lead-followup-il.json'), ($output | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))
Write-Output ('线索真实方法数：' + $methods.Count)
