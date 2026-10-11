param([switch]$PendingInstall)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$package = Join-Path $projectRoot 'runtime/package/ElsinoreHan-Sol'
$proofPath = Join-Path $projectRoot 'translation/sol-full-2026-10-09/verification.json'
$proof = Get-Content -LiteralPath $proofPath -Raw | ConvertFrom-Json
if (-not $proof.id_count_order_source_hashes_and_markers_passed) { throw '全文未通过核验，禁止打包' }
$dictionaryRoot = Join-Path $package 'BepInEx/Translation/zh-CN/Text'
if ((Get-FileHash -LiteralPath (Join-Path $dictionaryRoot 'ElsinoreHan-Sol.txt')).Hash.ToLowerInvariant() -ne $proof.dictionary_sha256) { throw '正文字典与核验记录不符' }
if ((Get-FileHash -LiteralPath (Join-Path $dictionaryRoot 'ElsinoreHan-Dynamic.txt')).Hash.ToLowerInvariant() -ne $proof.dynamic_dictionary_sha256) { throw '动态字典与核验记录不符' }
$allowedFiles = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($relative in @('BepInEx/Translation/zh-CN/Text/ElsinoreHan-Sol.txt', 'BepInEx/Translation/zh-CN/Text/ElsinoreHan-Dynamic.txt', 'elsinorehan_sans_sdf_u2018', 'BepInEx/plugins/ElsinoreHan.TranslationToggle.dll', 'BepInEx/config/AutoTranslatorConfig.ini', 'README.md', 'XUnity-LICENSE', 'licenses/ElsinoreHanSans-OFL.txt', 'licenses/ElsinoreHanSans-NOTICE.txt', 'licenses/TextMeshPro-Unity-Companion-License.txt')) {
    [void]$allowedFiles.Add([IO.Path]::GetFullPath((Join-Path $package $relative)))
}
foreach ($source in @(
    (Join-Path $projectRoot 'runtime/vendor/BepInEx5'),
    (Join-Path $projectRoot 'runtime/vendor/XUnity')
)) {
    foreach ($file in Get-ChildItem -LiteralPath $source -File -Recurse) {
        $relative = $file.FullName.Substring($source.Length + 1)
        # 无需在线端点，完整补丁始终使用预制词表。
        if ($relative -match '\\Translators\\') { continue }
        $target = Join-Path $package $relative
        [void]$allowedFiles.Add([IO.Path]::GetFullPath($target))
        New-Item -ItemType Directory -Path (Split-Path $target) -Force | Out-Null
        Copy-Item -LiteralPath $file.FullName -Destination $target -Force
    }
}
$fontSource = Join-Path $projectRoot 'runtime/vendor/fonts/elsinorehan_sans_sdf_u2018'
$fontProof = Get-Content -LiteralPath ($fontSource + '.verification.json') -Raw | ConvertFrom-Json
if (-not $fontProof.old_font_atlas_stream_removed -or (Get-FileHash -LiteralPath $fontSource).Hash.ToLowerInvariant() -ne $fontProof.bundle_sha256) { throw '新字体缺少完整来源/字节核验，禁止打包' }
Copy-Item -LiteralPath $fontSource -Destination (Join-Path $package 'elsinorehan_sans_sdf_u2018') -Force
$oldFont = Join-Path $package 'arialuni_sdf_u2018'
if (Test-Path -LiteralPath $oldFont) { Remove-Item -LiteralPath $oldFont }
New-Item -ItemType Directory -Path (Join-Path $package 'licenses') -Force | Out-Null
foreach ($name in @('ElsinoreHanSans-OFL.txt', 'ElsinoreHanSans-NOTICE.txt', 'TextMeshPro-Unity-Companion-License.txt')) {
    Copy-Item -LiteralPath (Join-Path $projectRoot ('licenses/' + $name)) -Destination (Join-Path $package ('licenses/' + $name)) -Force
}
Copy-Item -LiteralPath (Join-Path $projectRoot 'runtime/build/ElsinoreHan.TranslationToggle.dll') -Destination (Join-Path $package 'BepInEx/plugins/ElsinoreHan.TranslationToggle.dll') -Force
New-Item -ItemType Directory -Path (Join-Path $package 'BepInEx/config') -Force | Out-Null
$config = Get-Content -LiteralPath (Join-Path $projectRoot 'runtime/sample/AutoTranslatorConfig.ini') -Raw
[IO.File]::WriteAllText((Join-Path $package 'BepInEx/config/AutoTranslatorConfig.ini'), $config, [Text.UTF8Encoding]::new($false))
$installationNote = if ($PendingInstall) { '此包为已验证的候选补丁，尚未安装到主游戏；请先保存并退出游戏，再执行安装。' } else { '本机安装已由项目执行。' }
$readme = @"
# Elsinore Sol 中文补丁

适用于本项目验证的 Windows 32位 Elsinore 1.4.1（3678），共 $($proof.count) 条预制译文。

正常启动游戏即可使用中文；按 F8 切换原文和译文，再按一次恢复中文。Alt+R 可重新加载修改后的词表。

中文使用基于思源黑体生成的 ElsinoreHan Sans SDF，字体许可与来源见 licenses/。此包不含旧 Arial Unicode 字库。

$installationNote 此文件夹作为完整备份包，包含离线加载器、中文字体和切换插件，不包含游戏本体、存档或任何API Key。

译文为Sol生成的完整初稿，尚未逐分支人工审校。发现错译时可按F8看原文，再记录原句以便校订。

所有在线翻译端点为空，不需要游戏运行时连接翻译API。源码、来源及验证记录位于项目 docs/dev-tasks/localization/sol-full.md。
"@
[IO.File]::WriteAllText((Join-Path $package 'README.md'), $readme, [Text.UTF8Encoding]::new($false))
$license = Join-Path $projectRoot 'runtime/vendor/XUnity-source-master/XUnity.AutoTranslator-master/LICENSE'
if (Test-Path -LiteralPath $license) { Copy-Item -LiteralPath $license -Destination (Join-Path $package 'XUnity-LICENSE') -Force }
$archive = Join-Path $projectRoot 'runtime/package/ElsinoreHan-Sol.zip'
foreach ($file in Get-ChildItem -LiteralPath $package -File -Recurse) {
    if (-not $allowedFiles.Contains($file.FullName)) { throw ('补丁包出现非白名单文件，拒绝打包：' + $file.FullName) }
}
Compress-Archive -Path (Join-Path $package '*') -DestinationPath $archive -Force
Write-Output $archive
