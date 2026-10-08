$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$downloads = Join-Path $projectRoot 'runtime\downloads'
$vendor = Join-Path $projectRoot 'runtime\vendor'
New-Item -ItemType Directory -Path $downloads,$vendor -Force | Out-Null
$packages = @(
    @{ name = 'BepInEx_win_x86_5.4.23.5.zip'; url = 'https://github.com/BepInEx/BepInEx/releases/download/v5.4.23.5/BepInEx_win_x86_5.4.23.5.zip'; directory = 'BepInEx5'; sha256 = '' },
    @{ name = 'XUnity.AutoTranslator-BepInEx-5.6.2.zip'; url = 'https://github.com/bbepis/XUnity.AutoTranslator/releases/download/v5.6.2/XUnity.AutoTranslator-BepInEx-5.6.2.zip'; directory = 'XUnity'; sha256 = '836a4066b9369b0d23dc1b0ef6336ad7fe7ae16880931259ec4d157aff7a81c0' },
    @{ name = 'TMP_Font_AssetBundles_2025-12-08.7z'; url = 'https://github.com/bbepis/XUnity.AutoTranslator/releases/download/v5.5.0/TMP_Font_AssetBundles_2025-12-08.7z'; directory = 'fonts'; sha256 = '' }
)
$records = foreach ($package in $packages) {
    $archive = Join-Path $downloads $package.name
    if (-not (Test-Path -LiteralPath $archive)) { Invoke-WebRequest -Uri $package.url -OutFile $archive -TimeoutSec 180 }
    $hash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($package.sha256 -and $hash -ne $package.sha256) { throw ('官方哈希不匹配：' + $package.name) }
    $destination = Join-Path $vendor $package.directory
    if (-not (Test-Path -LiteralPath $destination)) {
        if ($package.name.EndsWith('.zip')) {
            Expand-Archive -LiteralPath $archive -DestinationPath $destination
        } else {
            # 字体包只用于当前个人样板，不纳入补丁分发。
            & 7z x $archive ('-o' + $destination) 'arialuni_sdf_u2018'
            if ($LASTEXITCODE -ne 0) { throw '字体包解压失败。' }
        }
    }
    [pscustomobject]@{ name = $package.name; url = $package.url; sha256 = $hash; upstream_hash_verified = [bool]$package.sha256 }
}
$records | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $projectRoot 'runtime\evidence\dependencies.json') -Encoding utf8
