# 隔离性能采样与组件回归；不安装到主游戏，不覆盖既有阶段证据。
param(
    [string[]]$Modes = @('translated', 'original'),
    [string]$PluginPath,
    [string]$GamePath = 'D:\MyProjects\ElsinoreHan\runtime\game-test\settings-options'
)
$ErrorActionPreference = 'Stop'
$project = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
if (-not $PluginPath) { $PluginPath = Join-Path $project 'runtime/build/ElsinoreHan.TranslationToggle.dll' }
$gameCopy = (Resolve-Path -LiteralPath $GamePath).Path
$targetPlugin = Join-Path $gameCopy 'BepInEx/plugins/ElsinoreHan.TranslationToggle.dll'
$config = Join-Path $gameCopy 'BepInEx/config/AutoTranslatorConfig.ini'
$dictionary = Join-Path $gameCopy 'BepInEx/Translation/zh-CN/Text/ElsinoreHan-Sol.txt'
$dynamic = Join-Path $gameCopy 'BepInEx/Translation/zh-CN/Text/ElsinoreHan-Dynamic.txt'
$restore = @{}
foreach ($path in @($targetPlugin, $config, $dictionary, $dynamic,
    (Join-Path $project 'runtime/evidence/headless-ui-verification.json'),
    (Join-Path $project 'runtime/evidence/headless-process.json'))) {
    $restore[$path] = [IO.File]::ReadAllBytes($path)
}
$variables = @('ELSINOREHAN_PROBE_JOURNAL', 'ELSINOREHAN_PROBE_CREDITS_SKIP', 'ELSINOREHAN_PROBE_CLOSEUP_IDS', 'ELSINOREHAN_PROBE_FONT_NAME', 'ELSINOREHAN_PROBE_CREDITS_PROFILE')
$previous = @{}
foreach ($name in $variables) { $previous[$name] = [Environment]::GetEnvironmentVariable($name) }
try {
    Copy-Item -LiteralPath (Join-Path $project 'runtime/sample/AutoTranslatorConfig.ini') -Destination $config
    Copy-Item -LiteralPath (Join-Path $project 'runtime/package/ElsinoreHan-Sol/BepInEx/Translation/zh-CN/Text/ElsinoreHan-Sol.txt') -Destination $dictionary
    Copy-Item -LiteralPath (Join-Path $project 'runtime/package/ElsinoreHan-Sol/BepInEx/Translation/zh-CN/Text/ElsinoreHan-Dynamic.txt') -Destination $dynamic
    $env:ELSINOREHAN_PROBE_JOURNAL = '1'
    $env:ELSINOREHAN_PROBE_CREDITS_SKIP = '1'
    $env:ELSINOREHAN_PROBE_CLOSEUP_IDS = Join-Path $project 'runtime/build/closeup-ids.txt'
    $env:ELSINOREHAN_PROBE_FONT_NAME = 'ElsinoreHan Sans SDF'
    foreach ($mode in $Modes) {
        $sourcePlugin = (Resolve-Path -LiteralPath $PluginPath).Path
        if ($mode.StartsWith('component', [StringComparison]::Ordinal)) { $env:ELSINOREHAN_PROBE_CREDITS_PROFILE = $null } else { $env:ELSINOREHAN_PROBE_CREDITS_PROFILE = $mode }
        Copy-Item -LiteralPath $sourcePlugin -Destination $targetPlugin
        $started = [DateTime]::UtcNow
        $failure = $null
        try { & (Join-Path $project 'tools/patch/run-headless-probe.ps1') -GamePath $gameCopy }
        catch { $failure = $_.Exception.Message }
        if ($failure) { throw ('隔离运行未完成：' + $failure) }
        $runs = @(Get-ChildItem -LiteralPath (Join-Path $project 'runtime/evidence/headless') -Directory | Where-Object CreationTimeUtc -ge $started)
        if ($runs.Count -ne 1) { throw '无法唯一定位本轮隔离运行' }
        $run = $runs[0]
        $reportPath = Join-Path $run.FullName 'credits-skip.json'
        if (-not (Test-Path -LiteralPath $reportPath)) {
            $reportPath = Join-Path $gameCopy ('ElsinoreHanProbe/' + $run.Name + '/credits-skip.json')
        }
        $report = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
        $proof = [ordered]@{
            date = '2026-10-19'; mode = $mode; run_id = $run.Name
            plugin_sha256 = (Get-FileHash -LiteralPath $targetPlugin).Hash.ToLowerInvariant()
            runner_error = $failure; report = $report
            save_protection = (Get-Content -LiteralPath (Join-Path $run.FullName 'save-protection.json') -Raw | ConvertFrom-Json)
            process = (Get-Content -LiteralPath (Join-Path $run.FullName 'process.json') -Raw | ConvertFrom-Json)
            isolated_save_removed = -not (Test-Path -LiteralPath (Join-Path $run.FullName 'isolated-save'))
        }
        $output = Join-Path $project ('runtime/evidence/credits-performance-' + $mode + '-2026-10-19.json')
        if (Test-Path -LiteralPath $output) { throw ('拒绝覆盖既有阶段证据：' + $output) }
        $proof | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $output -Encoding utf8
        if (-not $proof.save_protection.original_save_files_unchanged -or -not $proof.isolated_save_removed) { throw '存档隔离或清理未通过' }
        if ($failure -or -not $report.passed) { throw ('性能采样失败：' + $failure) }
        if ($mode.StartsWith('component', [StringComparison]::Ordinal)) { Write-Output ('组件回归完成：' + $report.checks.Count + '项断言') }
        else {
            Write-Output ('性能采样完成：' + $mode + ';frames=' + $report.frames.Count + ';characters=' + $report.body_source_characters)
            $report.methods | Sort-Object maximum_ms -Descending | Select-Object -First 7 method,calls,maximum_ms,total_ms | ConvertTo-Json -Depth 3
        }

    }
} finally {
    $restoreErrors = @()
    foreach ($path in $restore.Keys) {
        try {
            # 原字节未变时不重写，避免刚退出进程的文件映射尚未释放导致无意义失败。
            $sha = [Security.Cryptography.SHA256]::Create()
            try { $expected = [BitConverter]::ToString($sha.ComputeHash($restore[$path])).Replace('-', '') }
            finally { $sha.Dispose() }
            if ((Get-FileHash -LiteralPath $path).Hash -ne $expected) { [IO.File]::WriteAllBytes($path, $restore[$path]) }
        } catch { $restoreErrors += ($path + ': ' + $_.Exception.Message) }
    }
    foreach ($name in $variables) { [Environment]::SetEnvironmentVariable($name, $previous[$name]) }
    if ($restoreErrors.Count) { throw ($restoreErrors -join "`n") }
}
