param([string]$GamePath = 'D:\SteamLibrary\steamapps\common\Elsinore')
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$GamePath = (Resolve-Path -LiteralPath $GamePath).Path
if (Get-Process -Name Elsinore -ErrorAction SilentlyContinue) { throw '游戏正在运行，禁止安装' }
if (-not (Test-Path -LiteralPath (Join-Path $GamePath 'Elsinore.exe'))) { throw '不是Elsinore游戏目录' }
$proofPath = Join-Path $projectRoot 'translation/sol-full-2026-10-09/verification.json'
if (-not (Test-Path -LiteralPath $proofPath)) { throw '全文尚未通过验证，禁止安装' }
$proof = Get-Content -LiteralPath $proofPath -Raw | ConvertFrom-Json
if (-not $proof.id_count_order_source_hashes_and_markers_passed) { throw '全文验证未通过' }
$sourceRoot = Join-Path $projectRoot 'runtime/package/ElsinoreHan-Sol'
$dictionary = Join-Path $sourceRoot 'BepInEx/Translation/zh-CN/Text/ElsinoreHan-Sol.txt'
if ((Get-FileHash -LiteralPath $dictionary -Algorithm SHA256).Hash.ToLowerInvariant() -ne $proof.dictionary_sha256) { throw '词表哈希与验证记录不符' }
$dynamic = Join-Path $sourceRoot 'BepInEx/Translation/zh-CN/Text/ElsinoreHan-Dynamic.txt'
if ((Get-FileHash -LiteralPath $dynamic -Algorithm SHA256).Hash.ToLowerInvariant() -ne $proof.dynamic_dictionary_sha256) { throw '动态词表哈希与验证记录不符' }
$config = Join-Path $GamePath 'BepInEx/config/AutoTranslatorConfig.ini'
if (-not (Test-Path -LiteralPath $config)) { throw '缺少已验证的加载器配置' }
$sample = Join-Path $GamePath 'BepInEx/Translation/zh-CN/Text/sample.txt'
$disabled = Join-Path $GamePath 'BepInEx/Translation/zh-CN/Text/sample.txt.disabled-by-sol'
if ((Test-Path -LiteralPath $sample) -and (Test-Path -LiteralPath $disabled)) { throw '已有样板停用文件，安装前拒绝覆盖' }
& (Join-Path $PSScriptRoot 'build-toggle.ps1') -GamePath $GamePath
$backup = Join-Path $projectRoot ('runtime/backups/full-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $backup | Out-Null
$changes = [System.Collections.Generic.List[object]]::new()
function Install-OwnedFile([string]$source, [string]$relative) {
    $target = [IO.Path]::GetFullPath((Join-Path $GamePath $relative))
    if (-not $target.StartsWith($GamePath + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw '安装目标越界' }
    if (Test-Path -LiteralPath $target) {
        $saved = Join-Path $backup $relative
        New-Item -ItemType Directory -Path (Split-Path $saved) -Force | Out-Null
        Copy-Item -LiteralPath $target -Destination $saved
    }
    New-Item -ItemType Directory -Path (Split-Path $target) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $target -Force
    $changes.Add([pscustomobject]@{ path=$relative; sha256=(Get-FileHash -LiteralPath $target).Hash })
}
Install-OwnedFile $dictionary 'BepInEx/Translation/zh-CN/Text/ElsinoreHan-Sol.txt'
Install-OwnedFile $dynamic 'BepInEx/Translation/zh-CN/Text/ElsinoreHan-Dynamic.txt'
Install-OwnedFile (Join-Path $projectRoot 'runtime/build/ElsinoreHan.TranslationToggle.dll') 'BepInEx/plugins/ElsinoreHan.TranslationToggle.dll'

# 只停用本项目早期样板，避免旧译名与全文词表相互覆盖；保留备份。
if (Test-Path -LiteralPath $sample) {
    Copy-Item -LiteralPath $sample -Destination (Join-Path $backup 'sample.txt')
    Move-Item -LiteralPath $sample -Destination $disabled
}
Copy-Item -LiteralPath $config -Destination (Join-Path $backup 'AutoTranslatorConfig.ini')
$lines = [System.Collections.Generic.List[string]]::new()
$section = ''
foreach ($line in Get-Content -LiteralPath $config) {
    if ($line -match '^\[(.+)\]') { $section = $Matches[1] }
    if ($line -match '^\[Behaviour\]') {
        $lines.Add($line)
        $lines.Add('MaxTextParserRecursion=64')
        continue
    }
    if ($section -eq 'Behaviour' -and $line -match '^MaxTextParserRecursion\s*=') { continue }
    if ($section -eq 'Service' -and $line -match '^(Endpoint|FallbackEndpoint)\s*=') { $line = $Matches[1] + '=' }
    if ($section -eq 'General' -and $line -match '^Language\s*=') { $line = 'Language=zh-CN' }
    if ($section -eq 'General' -and $line -match '^FromLanguage\s*=') { $line = 'FromLanguage=en' }
    # 上游固定在线请求上限为2500；离线词表查找在该门槛前，长资料仍可完整加载。
    if ($section -eq 'Behaviour' -and $line -match '^MaxCharactersPerTranslation\s*=') { $line = 'MaxCharactersPerTranslation=2500' }
    $lines.Add($line)
}
[IO.File]::WriteAllLines($config, $lines, [Text.UTF8Encoding]::new($false))
$changes.Add([pscustomobject]@{ path='BepInEx/config/AutoTranslatorConfig.ini'; sha256=(Get-FileHash -LiteralPath $config).Hash })
[pscustomobject]@{ game_path=$GamePath; backup_path=$backup; dictionary_count=$proof.count; files=$changes } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $projectRoot 'runtime/evidence/full-installed-files.json') -Encoding utf8
Write-Output ('全文离线补丁已安装，F8切换原文/译文；备份：' + $backup)
