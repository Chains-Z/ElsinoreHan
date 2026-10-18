$ErrorActionPreference = 'Stop'
# 只读提取结局界面 IL；不启动游戏、不加载或读取玩家存档。
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$null = [Reflection.Assembly]::LoadFrom((Join-Path $root 'runtime/vendor/BepInEx5/BepInEx/core/Mono.Cecil.dll'))
$managed = 'D:/SteamLibrary/steamapps/common/Elsinore/Elsinore_Data/Managed'
$output = Join-Path $root 'runtime/build/post-burn-availability'
New-Item -ItemType Directory -Path $output -Force | Out-Null
$files = @()
$methods = @()
foreach ($filename in @('Assembly-CSharp.dll', 'Elsinore.dll')) {
    $path = Join-Path $managed $filename
    $files += [ordered]@{ path=$path; sha256=(Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant() }
    $assembly = [Mono.Cecil.AssemblyDefinition]::ReadAssembly($path)
    try {
        foreach ($type in $assembly.MainModule.GetTypes()) {
            foreach ($method in $type.Methods | Where-Object HasBody) {
                $wanted = ($type.FullName -like 'Elsinore.Ui.EndingSelectUI*') -or
                    ($type.FullName -like 'Elsinore.Ui.GameOverUI*') -or
                    ($type.FullName -eq 'EndingBookObject') -or
                    ($type.FullName -eq 'GameDataGenerated' -and $method.Name -like 'Invoke_Spine_OpheliaHamletStarter*') -or
                    ($method.Name -like '*AllowInteraction*') -or
                    ($type.FullName -eq 'Elsinore.Ui.ElsinoreButton' -and $method.Name -like '*Tooltip*')
                if ($wanted) {
                    $methods += [ordered]@{ assembly=$filename; type=$type.FullName; name=$method.FullName; il=@($method.Body.Instructions | ForEach-Object ToString) }
                }
            }
        }
    } finally { $assembly.Dispose() }
}
$report = [ordered]@{ source_files=$files; methods=$methods }
[IO.File]::WriteAllText((Join-Path $output 'current-ui-il.json'), ($report | ConvertTo-Json -Depth 14), [Text.UTF8Encoding]::new($false))
Write-Output ('只读提取方法数：' + $methods.Count)
