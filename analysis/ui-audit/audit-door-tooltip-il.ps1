$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
[void][Reflection.Assembly]::LoadFrom((Join-Path $root 'runtime/vendor/BepInEx5/BepInEx/core/Mono.Cecil.dll'))
$path = 'D:/SteamLibrary/steamapps/common/Elsinore/Elsinore_Data/Managed/Assembly-CSharp.dll'
$assembly = [Mono.Cecil.AssemblyDefinition]::ReadAssembly($path)
try {
    $type = $assembly.MainModule.GetTypes() | Where-Object FullName -eq 'DoorMarker'
    $method = $type.Methods | Where-Object Name -eq 'Elsinore.Ui.IInteractable.get_Tooltip'
    if (-not $method.HasBody) { throw 'Missing DoorMarker tooltip getter body' }
    $report = [ordered]@{
        assembly = $path
        sha256 = (Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant()
        methods = @([ordered]@{ method = $method.FullName; il = @($method.Body.Instructions | ForEach-Object ToString) })
    }
} finally {
    $assembly.Dispose()
}
$outputDirectory = Join-Path $root 'runtime/build/out-to-sea-audit'
[void][IO.Directory]::CreateDirectory($outputDirectory)
[IO.File]::WriteAllText((Join-Path $outputDirectory 'ui-path-il.json'), ($report | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
