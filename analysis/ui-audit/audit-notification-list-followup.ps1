$ErrorActionPreference = 'Stop'
# 只读原程序集，核验多人通知的姓名标记、动作模板及弹窗段落填充。
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$null = [Reflection.Assembly]::LoadFrom((Join-Path $root 'runtime/vendor/BepInEx5/BepInEx/core/Mono.Cecil.dll'))
$managed = 'D:/SteamLibrary/steamapps/common/Elsinore/Elsinore_Data/Managed'
$files = @()
$methods = @()
foreach ($filename in @('Elsinore.dll', 'Assembly-CSharp.dll')) {
    $path = Join-Path $managed $filename
    $files += [ordered]@{ path=$path; sha256=(Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant() }
    $assembly = [Mono.Cecil.AssemblyDefinition]::ReadAssembly($path)
    try {
        foreach ($type in $assembly.MainModule.GetTypes()) {
            foreach ($method in $type.Methods | Where-Object HasBody) {
                $wanted = ($type.FullName -eq 'Elsinore.Game.Model' -and $method.Name -in @('formatCharacters','formatGroupedLiterals','posstr@551')) -or
                    ($type.FullName -eq 'Elsinore.Ui.DialogueUI' -and $method.Name -eq 'onStartLogicChange') -or
                    ($type.FullName -eq 'Elsinore.Ui.UiStrings' -and $method.Name -in @('AddParagraphBreak','SetLineHeight'))
                if ($wanted) {
                    $methods += [ordered]@{ assembly=$filename; method=$method.FullName; il=@($method.Body.Instructions | ForEach-Object ToString) }
                }
            }
        }
    } finally { $assembly.Dispose() }
}
$report = [ordered]@{ schema_version=1; verification_method='只读 Mono.Cecil IL；未启动游戏、读取存档或修改用户进程'; source_files=$files; methods=$methods }
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'notification-list-followup-il.json'), ($report | ConvertTo-Json -Depth 14), [Text.UTF8Encoding]::new($false))
Write-Output ('真实方法数：' + $methods.Count)
