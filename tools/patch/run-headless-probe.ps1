param([string]$GamePath = 'D:\SteamLibrary\steamapps\common\Elsinore')
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
if (Get-Process -Name Elsinore -ErrorAction SilentlyContinue) { throw '请先关闭游戏。' }
$GamePath = (Resolve-Path -LiteralPath $GamePath).Path
& (Join-Path $PSScriptRoot 'build-probe.ps1') -GamePath $GamePath
$plugin = Join-Path $GamePath 'BepInEx\plugins\ElsinoreHan.RuntimeProbe.dll'
if (Test-Path -LiteralPath $plugin) { throw '检测到既有诊断插件，拒绝覆盖。' }
# Steam SDK 在明确 appid 文件存在时保留当前直接启动进程与批处理参数。
$appIdPath = Join-Path $GamePath 'steam_appid.txt'
$createdAppId = -not (Test-Path -LiteralPath $appIdPath)
$runId = [Guid]::NewGuid().ToString('N')
$runDirectory = Join-Path $projectRoot ('runtime\evidence\headless\' + $runId)
New-Item -ItemType Directory -Path $runDirectory -Force | Out-Null
$logFile = Join-Path $runDirectory 'player.log'
$arguments = @('-batchmode', '-nographics', '-nosound', '-logFile', ('"' + $logFile + '"'))
$process = $null
$createdPlugin = $false
$previousRunId = $env:ELSINOREHAN_PROBE_RUN_ID
try {
    Copy-Item -LiteralPath (Join-Path $projectRoot 'runtime\build\ElsinoreHan.RuntimeProbe.dll') -Destination $plugin
    $createdPlugin = $true
    if ($createdAppId) { Set-Content -LiteralPath $appIdPath -Value '512890' -Encoding ascii }
    $env:ELSINOREHAN_PROBE_RUN_ID = $runId
    $launchedAt = [DateTime]::UtcNow
    $process = Start-Process -FilePath (Join-Path $GamePath 'Elsinore.exe') -ArgumentList $arguments -WorkingDirectory $GamePath -WindowStyle Hidden -PassThru
    $process.PriorityClass = 'BelowNormal'
    $timer = [Diagnostics.Stopwatch]::StartNew()
    while (-not $process.HasExited -and $timer.Elapsed.TotalSeconds -lt 50) {
        $process.Refresh()
        if ($process.MainWindowHandle -ne [IntPtr]::Zero) {
            Stop-Process -Id $process.Id -Force
            throw '后台进程出现窗口，已立即终止。'
        }
        Start-Sleep -Milliseconds 200
    }
    if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force; throw '后台探针超时，已终止。' }
    $process.WaitForExit()
    if ($process.ExitCode -ne 0) { throw ('后台探针退出码异常：' + $process.ExitCode) }
    $reports = @('menu-texts.txt', 'settings-texts.txt')
    if ($env:ELSINOREHAN_PROBE_TOGGLE -eq '1') { $reports += @('original-menu-texts.txt', 'restored-menu-texts.txt') }
    foreach ($name in $reports) {
        $source = Join-Path $GamePath ('ElsinoreHanProbe\' + $runId + '\' + $name)
        if ((Get-Item -LiteralPath $source).LastWriteTimeUtc -lt $launchedAt) { throw ('探针记录不是本轮生成：' + $name) }
        Copy-Item -LiteralPath $source -Destination (Join-Path $runDirectory $name)
    }
    Copy-Item -LiteralPath (Join-Path $GamePath 'BepInEx\LogOutput.log') -Destination (Join-Path $runDirectory 'BepInEx.log')
    $runtimeLog = Get-Content -LiteralPath (Join-Path $runDirectory 'BepInEx.log') -Raw
    $batchMode = $runtimeLog.Contains('Application.isBatchMode=True')
    $muted = $runtimeLog.Contains('Wwise 后台音频暂停结果=AK_Success')
    [pscustomobject]@{ run_id = $runId; launched_at_utc = $launchedAt.ToString('o'); pid = $process.Id; exit_code = $process.ExitCode; main_window_detected = $false; batch_mode_confirmed = $batchMode; wwise_suspend_success = $muted; priority = 'BelowNormal'; target_frame_rate = 10; arguments = $arguments } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $runDirectory 'process.json') -Encoding utf8
    if (-not ($batchMode -and $muted)) { throw '后台模式或静音未确认，不能宣称验证通过。' }
    python (Join-Path $PSScriptRoot 'verify-probe.py') --evidence $runDirectory
    if ($LASTEXITCODE -ne 0) { throw '后台 UI 集成断言失败。' }
    Copy-Item -LiteralPath (Join-Path $runDirectory 'verification.json') -Destination (Join-Path $projectRoot 'runtime\evidence\headless-ui-verification.json') -Force
    Copy-Item -LiteralPath (Join-Path $runDirectory 'process.json') -Destination (Join-Path $projectRoot 'runtime\evidence\headless-process.json') -Force
    Write-Output ('本轮后台证据：' + $runDirectory)
} finally {
    if ($process -and -not $process.HasExited) { Stop-Process -Id $process.Id -Force }
    # 诊断插件退出后移除，避免用户后续正常游玩被自动退出或静音。
    if ($createdPlugin -and (Test-Path -LiteralPath $plugin)) { Remove-Item -LiteralPath $plugin }
    if ($createdAppId -and (Test-Path -LiteralPath $appIdPath)) { Remove-Item -LiteralPath $appIdPath }
    $env:ELSINOREHAN_PROBE_RUN_ID = $previousRunId
}
