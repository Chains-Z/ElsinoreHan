param([string]$GamePath = 'D:\SteamLibrary\steamapps\common\Elsinore')
$ErrorActionPreference = 'Stop'
if ($env:ELSINOREHAN_PROBE_BOOK_PAGES -and ($env:ELSINOREHAN_PROBE_JOURNAL -ne '1' -or -not (Test-Path -LiteralPath $env:ELSINOREHAN_PROBE_BOOK_PAGES -PathType Leaf))) { throw '命运书页回归需要资料模式及真实资源输入。' }
if ($env:ELSINOREHAN_PROBE_BOOK_ONLY -eq '1' -and -not $env:ELSINOREHAN_PROBE_BOOK_PAGES) { throw '命运书页专项模式缺少页面输入。' }
if ($env:ELSINOREHAN_PROBE_FONT_SOURCE -and -not $env:ELSINOREHAN_PROBE_FONT_CHARACTERS) { throw '字体生成缺少受控字符集，禁止启动。' }
if ($env:ELSINOREHAN_PROBE_MENU_RETRY_DELAY_SECONDS) {
    $retrySeconds = [float]0
    if (-not [float]::TryParse($env:ELSINOREHAN_PROBE_MENU_RETRY_DELAY_SECONDS, [Globalization.NumberStyles]::Float, [Globalization.CultureInfo]::InvariantCulture, [ref]$retrySeconds) -or [float]::IsNaN($retrySeconds) -or [float]::IsInfinity($retrySeconds) -or $retrySeconds -lt 1 -or $retrySeconds -gt 10) {
        throw 'ELSINOREHAN_PROBE_MENU_RETRY_DELAY_SECONDS 必须在1到10秒之间，禁止启动。'
    }
}
if ($env:ELSINOREHAN_PROBE_ITALIC -eq '1' -and $env:ELSINOREHAN_PROBE_JOURNAL -ne '1') {
    throw 'ELSINOREHAN_PROBE_ITALIC 必须与资料模式一起运行。'
}
if ($env:ELSINOREHAN_PROBE_LOG_SCROLL -eq '1' -and $env:ELSINOREHAN_PROBE_JOURNAL -ne '1') {
    throw 'ELSINOREHAN_PROBE_LOG_SCROLL 必须与真实资料模式一起运行，禁止启动。'
}
if ($env:ELSINOREHAN_PROBE_LOG_FORMATTER -and ($env:ELSINOREHAN_PROBE_JOURNAL -ne '1' -or -not (Test-Path -LiteralPath $env:ELSINOREHAN_PROBE_LOG_FORMATTER -PathType Leaf))) {
    throw '日志格式器核查需要真实资料模式与冻结输入，禁止启动。'
}
if ($env:ELSINOREHAN_PROBE_LOG_SPEAKERS -and ($env:ELSINOREHAN_PROBE_JOURNAL -ne '1' -or -not (Test-Path -LiteralPath $env:ELSINOREHAN_PROBE_LOG_SPEAKERS -PathType Leaf))) {
    throw '日志姓名排版回归需要真实资料模式与资源重放输入，禁止启动。'
}
if ($env:ELSINOREHAN_PROBE_BIO_SCROLL -eq '1' -and $env:ELSINOREHAN_PROBE_JOURNAL -ne '1') {
    throw '人物介绍阅读位置回归必须使用真实资料模式，禁止启动。'
}
if ($env:ELSINOREHAN_PROBE_LEAD_LAYOUT -eq '1' -and $env:ELSINOREHAN_PROBE_JOURNAL -ne '1') {
    throw '任务按钮布局回归必须使用真实资料模式，禁止启动。'
}
if ($env:ELSINOREHAN_PROBE_DOCUMENT_SCROLL_IDS) {
    if ($env:ELSINOREHAN_PROBE_JOURNAL -ne '1' -or -not $env:ELSINOREHAN_PROBE_CLOSEUP_IDS -or -not (Test-Path -LiteralPath $env:ELSINOREHAN_PROBE_CLOSEUP_IDS -PathType Leaf)) {
        throw '文档阅读位置诊断必须使用资料模式和冻结文档ID文件。'
    }
    $knownDocuments = @(Get-Content -LiteralPath $env:ELSINOREHAN_PROBE_CLOSEUP_IDS | ForEach-Object { ($_ -split "`t")[0].Trim() })
    $requestedDocuments = @($env:ELSINOREHAN_PROBE_DOCUMENT_SCROLL_IDS -split ';')
    if (@($requestedDocuments | Select-Object -Unique).Count -ne $requestedDocuments.Count -or @($requestedDocuments | Where-Object { $_ -notin $knownDocuments }).Count -gt 0) {
        throw '文档阅读位置诊断ID重复或不在冻结真实文档中。'
    }
}
if ($env:ELSINOREHAN_PROBE_BIOGRAPHY_CASES -and ($env:ELSINOREHAN_PROBE_JOURNAL -ne '1' -or -not (Test-Path -LiteralPath $env:ELSINOREHAN_PROBE_BIOGRAPHY_CASES -PathType Leaf))) {
    throw '人物资料重放必须使用资料模式和冻结真实资源用例，禁止启动。'
}
if ($env:ELSINOREHAN_PROBE_UI_FOLLOWUP -eq '1' -and ($env:ELSINOREHAN_PROBE_JOURNAL -ne '1' -or -not $env:ELSINOREHAN_PROBE_LEAD_CASES -or -not (Test-Path -LiteralPath $env:ELSINOREHAN_PROBE_LEAD_CASES -PathType Leaf))) {
    throw 'ELSINOREHAN_PROBE_UI_FOLLOWUP 必须使用资料模式和已核实线索重放文件，禁止启动。'
}
if ($env:ELSINOREHAN_PROBE_JOURNAL -eq '1' -and (-not $env:ELSINOREHAN_PROBE_CLOSEUP_IDS -or -not (Test-Path -LiteralPath $env:ELSINOREHAN_PROBE_CLOSEUP_IDS -PathType Leaf))) {
    throw 'ELSINOREHAN_PROBE_CLOSEUP_IDS 缺少冻结资料ID文件，禁止启动。'
}
foreach ($variableName in @('ELSINOREHAN_PROBE_TRANSLATIONS', 'ELSINOREHAN_PROBE_CHARACTERS', 'ELSINOREHAN_PROBE_CACHE_CASES', 'ELSINOREHAN_PROBE_CLOSEUP_IDS', 'ELSINOREHAN_PROBE_LEAD_CASES', 'ELSINOREHAN_PROBE_BIOGRAPHY_CASES', 'ELSINOREHAN_PROBE_FONT_SOURCE', 'ELSINOREHAN_PROBE_FONT_CHARACTERS', 'ELSINOREHAN_PROBE_NOTIFICATION_EVIDENCE', 'ELSINOREHAN_PROBE_STRICT_LOG_CASES')) {
    $inputPath = [Environment]::GetEnvironmentVariable($variableName)
    if ($inputPath -and -not (Test-Path -LiteralPath $inputPath -PathType Leaf)) { throw ($variableName + ' 指向的文件不存在，禁止启动。') }
}
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
if ($env:ELSINOREHAN_PROBE_FONT_NAME -eq 'ElsinoreHan Sans SDF' -and $env:ELSINOREHAN_PROBE_FONT_CHARACTERS) {
    if (-not $env:ELSINOREHAN_PROBE_FONT_BAKE_EVIDENCE -or -not (Test-Path -LiteralPath (Join-Path $env:ELSINOREHAN_PROBE_FONT_BAKE_EVIDENCE 'font-bake-verification.json') -PathType Leaf)) { throw '新字体回归缺少真实生成核验，禁止启动。' }
}
$GamePath = (Resolve-Path -LiteralPath $GamePath).Path
if (Get-Process -Name Elsinore -ErrorAction SilentlyContinue | Where-Object { $_.MainModule.FileName -eq (Join-Path $GamePath 'Elsinore.exe') }) { throw '目标目录的游戏正在运行，禁止介入。' }
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
$loaderConfigPath = Join-Path $GamePath 'BepInEx/config/BepInEx.cfg'
$originalLoaderConfig = [IO.File]::ReadAllBytes($loaderConfigPath)
[IO.File]::WriteAllBytes((Join-Path $runDirectory 'loader-config-before.bin'), $originalLoaderConfig)
$previousRunId = $env:ELSINOREHAN_PROBE_RUN_ID
$previousSavePath = $env:ELSINOREHAN_PROBE_SAVE_PATH
$originalSavePath = Join-Path ([Environment]::GetFolderPath('ApplicationData')) 'Golden Glitch Studios/Elsinore'
$concurrentGameActive = [bool](Get-Process -Name Elsinore -ErrorAction SilentlyContinue)
$saveSourcePath = $originalSavePath
if ($env:ELSINOREHAN_PROBE_SAVE_SOURCE) { $saveSourcePath = (Resolve-Path -LiteralPath $env:ELSINOREHAN_PROBE_SAVE_SOURCE).Path }
if ($concurrentGameActive -and $saveSourcePath -eq $originalSavePath) { throw '用户游戏正在运行；诊断须使用既有冻结存档副本，避免读取正在写入的存档。' }
$isolatedSavePath = Join-Path $runDirectory 'isolated-save'
try {
    New-Item -ItemType Directory -Path $isolatedSavePath -Force | Out-Null
    . (Join-Path $PSScriptRoot 'ProbeSaveSnapshot.ps1')
    $saveSnapshot = @(Get-ProbeSaveSnapshot -Path $originalSavePath -ConcurrentGameActive $concurrentGameActive)
    $sourceSnapshot = @()
    foreach ($file in Get-ChildItem -LiteralPath $saveSourcePath -File -Recurse -Force) {
        $relative = $file.FullName.Substring($saveSourcePath.Length + 1)
        $destination = Join-Path $isolatedSavePath $relative
        New-Item -ItemType Directory -Path (Split-Path $destination) -Force | Out-Null
        Copy-Item -LiteralPath $file.FullName -Destination $destination
        $sourceSnapshot += [pscustomobject]@{ path=$relative; sha256=(Get-FileHash -LiteralPath $file.FullName).Hash }
    }
    $saveSnapshot | ConvertTo-Json -AsArray | Set-Content -LiteralPath (Join-Path $runDirectory 'original-save-before.json') -Encoding utf8
    # Application 带 BeforeFieldInit，旧入口可能迟于游戏启动时的分辨率应用。
    # 临时改到实际业务 Awake 之前加载保护；只改测试配置，退出后按字节还原。
    $loaderLines = [IO.File]::ReadAllLines($loaderConfigPath)
    $inEntrypoint = $false
    $entryValues = @{ Assembly='Assembly-CSharp.dll'; Type='GameInitialization'; Method='Awake' }
    $updatedEntryKeys = @()
    for ($index = 0; $index -lt $loaderLines.Length; $index++) {
        if ($loaderLines[$index] -match '^\[(.+)\]$') { $inEntrypoint = $Matches[1] -eq 'Preloader.Entrypoint' }
        if ($inEntrypoint -and $loaderLines[$index] -match '^(Assembly|Type|Method)\s*=') {
            $key = $Matches[1]
            $loaderLines[$index] = $key + ' = ' + $entryValues[$key]
            $updatedEntryKeys += $key
        }
    }
    if ($updatedEntryKeys.Count -ne 3) { throw '无法建立测试早期加载入口，禁止启动。' }
    [IO.File]::WriteAllLines($loaderConfigPath, $loaderLines, [Text.UTF8Encoding]::new($false))
    Copy-Item -LiteralPath (Join-Path $projectRoot 'runtime\build\ElsinoreHan.RuntimeProbe.dll') -Destination $plugin
    $createdPlugin = $true
    if ($createdAppId) { Set-Content -LiteralPath $appIdPath -Value '512890' -Encoding ascii }
    $env:ELSINOREHAN_PROBE_RUN_ID = $runId
    $env:ELSINOREHAN_PROBE_SAVE_PATH = $isolatedSavePath
    $launchedAt = [DateTime]::UtcNow
    $process = Start-Process -FilePath (Join-Path $GamePath 'Elsinore.exe') -ArgumentList $arguments -WorkingDirectory $GamePath -WindowStyle Hidden -PassThru
    $process.PriorityClass = 'BelowNormal'
    $timer = [Diagnostics.Stopwatch]::StartNew()
    $timeoutSeconds = if ($env:ELSINOREHAN_PROBE_FONT_SOURCE) { 240 } elseif ($env:ELSINOREHAN_PROBE_JOURNAL -eq '1') { 150 } elseif ($env:ELSINOREHAN_PROBE_SETTINGS_OPTIONS -eq '1') { 70 } else { 50 }
    while (-not $process.HasExited -and $timer.Elapsed.TotalSeconds -lt $timeoutSeconds) {
        $process.Refresh()
        if ($process.MainWindowHandle -ne [IntPtr]::Zero) {
            $process.MainWindowTitle | Set-Content -LiteralPath (Join-Path $runDirectory 'unexpected-window.txt') -Encoding utf8
            Stop-Process -Id $process.Id -Force
            throw '后台进程出现窗口，已立即终止。'
        }
        Start-Sleep -Milliseconds 200
    }
    if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force; throw '后台探针超时，已终止。' }
    $process.WaitForExit()
    if ($process.ExitCode -ne 0) { throw ('后台探针退出码异常：' + $process.ExitCode) }
    $reports = if ($env:ELSINOREHAN_PROBE_FONT_SOURCE) { @('font-bake.json', 'font-atlas-alpha8.bin') } else { @('menu-texts.txt', 'settings-texts.txt') }
    if ($env:ELSINOREHAN_PROBE_STRICT_LOG_CASES) { $reports += 'strict-log-cache.tsv' }
    if ($env:ELSINOREHAN_PROBE_LOG_FORMATTER) { $reports += 'ambient-log-formatter.json' }
    if ($env:ELSINOREHAN_PROBE_TOGGLE -eq '1') { $reports += @('original-menu-texts.txt', 'restored-menu-texts.txt') }
    if ($env:ELSINOREHAN_PROBE_SETTINGS_OPTIONS -eq '1') { $reports += 'settings-options.txt' }
    if ($env:ELSINOREHAN_PROBE_JOURNAL -eq '1') { $reports += 'journal-ui.txt' }
    if ($env:ELSINOREHAN_PROBE_BOOK_PAGES) { $reports += 'ending-book.json' }
    if ($env:ELSINOREHAN_PROBE_ITALIC -eq '1') { $reports += 'italic-geometry.json' }
    if ($env:ELSINOREHAN_PROBE_LOG_SCROLL -eq '1') { $reports += @('log-scroll-anchor.tsv', 'log-bottom-anchor.tsv') }
    if ($env:ELSINOREHAN_PROBE_LOG_SPEAKERS) { $reports += 'log-speaker-layout.tsv' }
    if ($env:ELSINOREHAN_PROBE_BIO_SCROLL -eq '1') { $reports += 'biography-scroll.tsv' }
    if ($env:ELSINOREHAN_PROBE_LEAD_LAYOUT -eq '1') { $reports += 'lead-layout.tsv' }
    if ($env:ELSINOREHAN_PROBE_DOCUMENT_SCROLL_IDS) { $reports += 'document-scroll-anchor.tsv' }
    if ($env:ELSINOREHAN_PROBE_BIOGRAPHY_CASES) { $reports += 'biography-replay.tsv' }
    if ($env:ELSINOREHAN_PROBE_UI_FOLLOWUP -eq '1') { $reports += @('lead-followup.tsv', 'map-followup.tsv', 'timeline-followup.tsv') }
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
    # 用户正在游玩时不读取被独占的实时日志/存档；只核验已冻结来源，原存档比较明确标为无法下结论。
    $saveUnchanged = if ($concurrentGameActive) { $null } else { $true }
    foreach ($file in $saveSnapshot) {
        $path = Join-Path $originalSavePath $file.path
        if (-not (Test-Path -LiteralPath $path) -or (Get-FileHash -LiteralPath $path).Hash -ne $file.sha256 -or (Get-Item -LiteralPath $path).LastWriteTimeUtc.ToString('o') -ne $file.write_time) { $saveUnchanged = $false }
    }
    if (-not $concurrentGameActive -and (@(Get-ChildItem -LiteralPath $originalSavePath -File -Recurse -Force -ErrorAction SilentlyContinue)).Count -ne $saveSnapshot.Count) { $saveUnchanged = $false }
    $sourceUnchanged = -not (@($sourceSnapshot | Where-Object { (Get-FileHash -LiteralPath (Join-Path $saveSourcePath $_.path)).Hash -ne $_.sha256 }).Count)
    [pscustomobject]@{ original_save_files_unchanged=$saveUnchanged; original_save_comparison_conclusive=(-not $concurrentGameActive); concurrent_user_game=$concurrentGameActive; frozen_source_unchanged=$sourceUnchanged; save_source_path=$saveSourcePath; isolated_save_path=$isolatedSavePath; files=$saveSnapshot } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $runDirectory 'save-protection.json') -Encoding utf8
    if (-not $sourceUnchanged -or (-not $saveUnchanged -and -not $concurrentGameActive)) { throw '存档保护核验失败。' }
    if ($env:ELSINOREHAN_PROBE_FONT_SOURCE) {
        python (Join-Path $PSScriptRoot 'verify-font-bake.py') --evidence $runDirectory --characters $env:ELSINOREHAN_PROBE_FONT_CHARACTERS
        if ($LASTEXITCODE -ne 0) { throw '真实字体引擎生成未完成或产物不完整。' }
        Write-Output ('本轮字体生成证据：' + $runDirectory)
        return
    }
    if ($env:ELSINOREHAN_PROBE_STRICT_LOG_CASES) {
        python (Join-Path $PSScriptRoot 'verify-strict-log-cache.py') --evidence (Join-Path $runDirectory 'strict-log-cache.tsv') --cases $env:ELSINOREHAN_PROBE_STRICT_LOG_CASES
        if ($LASTEXITCODE -ne 0) { throw '完整日志缓存修复、拒绝未知项或F8回归失败。' }
    }
    if ($env:ELSINOREHAN_PROBE_LOG_FORMATTER) {
        $formatter = Get-Content -LiteralPath (Join-Path $runDirectory 'ambient-log-formatter.json') -Raw | ConvertFrom-Json
        if (-not $formatter.passed -or $formatter.entries -ne 4 -or $formatter.actual_base64 -cne $formatter.expected_base64 -or $formatter.input_sha256 -ne (Get-FileHash -LiteralPath $env:ELSINOREHAN_PROBE_LOG_FORMATTER).Hash.ToLowerInvariant()) {
            throw '真实日志格式器边界或输入绑定失败。'
        }
    }
    if ($env:ELSINOREHAN_PROBE_FONT_NAME -eq 'ElsinoreHan Sans SDF' -and $env:ELSINOREHAN_PROBE_FONT_CHARACTERS) {
        foreach ($name in @('font-regression.json', 'font-runtime-atlas.bin')) {
            $source = Join-Path $GamePath ('ElsinoreHanProbe\' + $runId + '\' + $name)
            if ((Get-Item -LiteralPath $source).LastWriteTimeUtc -lt $launchedAt) { throw '字体回归证据不是本轮生成。' }
            Copy-Item -LiteralPath $source -Destination (Join-Path $runDirectory $name)
        }
        python (Join-Path $PSScriptRoot 'verify-font-regression.py') --evidence $runDirectory --bake-directory $env:ELSINOREHAN_PROBE_FONT_BAKE_EVIDENCE
        if ($LASTEXITCODE -ne 0) { throw '实际字体纹理、字形坐标或沉字笔画回归失败。' }
    }
    $verifyArguments = @((Join-Path $PSScriptRoot 'verify-probe.py'), '--evidence', $runDirectory)
    if ($env:ELSINOREHAN_PROBE_JOURNAL -eq '1') { $verifyArguments += '--menu-only' }
    if ($env:ELSINOREHAN_PROBE_TRANSLATIONS) { $verifyArguments += @('--translations', $env:ELSINOREHAN_PROBE_TRANSLATIONS) }
    if ($env:ELSINOREHAN_PROBE_SETTINGS_OPTIONS -eq '1') { $verifyArguments += '--require-settings-options' }
    python @verifyArguments
    if ($LASTEXITCODE -ne 0) { throw '后台 UI 集成断言失败。' }
    if ($env:ELSINOREHAN_PROBE_BOOK_PAGES) {
        $bookReport = Get-Content -LiteralPath (Join-Path $runDirectory 'ending-book.json') -Raw | ConvertFrom-Json
        $bookCases = @(Get-Content -LiteralPath $env:ELSINOREHAN_PROBE_BOOK_PAGES | Where-Object { ($_ -split "`t")[1] -eq 'True' })
        if (-not $bookReport.passed -or $bookReport.page_count -ne $bookCases.Count -or $bookReport.pages.Count -ne $bookCases.Count -or $bookReport.input_sha256 -ne (Get-FileHash -LiteralPath $env:ELSINOREHAN_PROBE_BOOK_PAGES).Hash.ToLowerInvariant()) { throw '命运之书回归不完整或来源哈希不符。' }
    }
    if ($env:ELSINOREHAN_PROBE_JOURNAL -eq '1' -and $env:ELSINOREHAN_PROBE_BOOK_ONLY -ne '1') {
        $journalArguments = @((Join-Path $PSScriptRoot 'verify-journal-probe.py'), (Join-Path $runDirectory 'journal-ui.txt'), '--output', (Join-Path $runDirectory 'journal-analysis.json'))
        if ($env:ELSINOREHAN_PROBE_JOURNAL_BASELINE -ne '1') { $journalArguments += '--require-translated' }
        if ($env:ELSINOREHAN_PROBE_NOTIFICATION_EVIDENCE) { $journalArguments += @('--notification-evidence', $env:ELSINOREHAN_PROBE_NOTIFICATION_EVIDENCE) }
        python @journalArguments
        if ($LASTEXITCODE -ne 0) { throw '资料页面采集或真实译文断言失败；菜单通过不能替代资料验收。' }
    }
    if ($env:ELSINOREHAN_PROBE_ITALIC -eq '1') {
        $italicArguments = @((Join-Path $PSScriptRoot 'verify-italic-geometry.py'), (Join-Path $runDirectory 'italic-geometry.json'))
        if ($env:ELSINOREHAN_PROBE_FONT_NAME) { $italicArguments += @('--font', $env:ELSINOREHAN_PROBE_FONT_NAME) }
        python @italicArguments
        if ($LASTEXITCODE -ne 0) { throw '中文斜体几何验收失败，禁止宣称字体修复通过。' }
    }
    if ($env:ELSINOREHAN_PROBE_LEAD_LAYOUT -eq '1') {
        python (Join-Path $PSScriptRoot 'verify-lead-layout.py') (Join-Path $runDirectory 'lead-layout.tsv') --output (Join-Path $runDirectory 'lead-layout-analysis.json')
        if ($LASTEXITCODE -ne 0) { throw '任务背景几何或F8交互回归失败。' }
    }
    if ($env:ELSINOREHAN_PROBE_UI_FOLLOWUP -eq '1') {
        python (Join-Path $PSScriptRoot 'verify-lead-followup.py') (Join-Path $runDirectory 'lead-followup.tsv') --output (Join-Path $runDirectory 'lead-followup-analysis.json')
        if ($LASTEXITCODE -ne 0) { throw '线索完整正文与F8断言失败。' }
        python (Join-Path $PSScriptRoot 'verify-map-followup.py') (Join-Path $runDirectory 'map-followup.tsv') --output (Join-Path $runDirectory 'map-followup-analysis.json')
        if ($LASTEXITCODE -ne 0) { throw '地图确认与取消移动断言失败。' }
        python (Join-Path $PSScriptRoot 'verify-timeline-followup.py') (Join-Path $runDirectory 'timeline-followup.tsv') --output (Join-Path $runDirectory 'timeline-followup-analysis.json')
        if ($LASTEXITCODE -ne 0) { throw '时间线完整正文与F8断言失败。' }
    }
    Copy-Item -LiteralPath (Join-Path $runDirectory 'verification.json') -Destination (Join-Path $projectRoot 'runtime\evidence\headless-ui-verification.json') -Force
    if ($env:ELSINOREHAN_PROBE_LOG_SCROLL -eq '1') {
        python (Join-Path $PSScriptRoot 'verify-log-scroll-anchor.py') (Join-Path $runDirectory 'log-scroll-anchor.tsv') --journal-report (Join-Path $runDirectory 'journal-ui.txt') --output (Join-Path $runDirectory 'log-scroll-anchor-analysis.json')
        if ($LASTEXITCODE -ne 0) { throw 'F8对话记录同段落与真实位置断言失败。' }
        python (Join-Path $PSScriptRoot 'verify-log-bottom-anchor.py') (Join-Path $runDirectory 'log-bottom-anchor.tsv') --journal-report (Join-Path $runDirectory 'journal-ui.txt') --output (Join-Path $runDirectory 'log-bottom-anchor-analysis.json')
        if ($LASTEXITCODE -ne 0) { throw 'F8日志底部保持或手动滚离底部回归失败。' }
    }
    if ($env:ELSINOREHAN_PROBE_LOG_SPEAKERS -and $env:ELSINOREHAN_PROBE_BIO_SCROLL -eq '1') {
        python (Join-Path $PSScriptRoot 'verify-reading-layout.py') --directory $runDirectory --speaker-cases $env:ELSINOREHAN_PROBE_LOG_SPEAKERS --output (Join-Path $runDirectory 'reading-layout-analysis.json')
        if ($LASTEXITCODE -ne 0) { throw '日志姓名排版或人物介绍F8位置回归失败。' }
    }
    if ($env:ELSINOREHAN_PROBE_DOCUMENT_SCROLL_IDS) {
        python (Join-Path $PSScriptRoot 'verify-document-scroll-anchor.py') (Join-Path $runDirectory 'document-scroll-anchor.tsv') --journal-report (Join-Path $runDirectory 'journal-ui.txt') --ids $env:ELSINOREHAN_PROBE_DOCUMENT_SCROLL_IDS --output (Join-Path $runDirectory 'document-scroll-anchor-analysis.json')
        if ($LASTEXITCODE -ne 0) { throw '文档F8同段落、真实坐标或正常滚动断言失败。' }
    }
    if ($env:ELSINOREHAN_PROBE_BIOGRAPHY_CASES) {
        python (Join-Path $PSScriptRoot 'verify-biography-replay.py') (Join-Path $runDirectory 'biography-replay.tsv') --cases $env:ELSINOREHAN_PROBE_BIOGRAPHY_CASES --journal-report (Join-Path $runDirectory 'journal-ui.txt') --output (Join-Path $runDirectory 'biography-replay-analysis.json')
        if ($LASTEXITCODE -ne 0) { throw '人物资料真实组件、完整正文、F8或原显示恢复断言失败。' }
    }
    Copy-Item -LiteralPath (Join-Path $runDirectory 'process.json') -Destination (Join-Path $projectRoot 'runtime\evidence\headless-process.json') -Force
    Write-Output ('本轮后台证据：' + $runDirectory)
} finally {
    if ($process -and -not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
        if (-not $process.WaitForExit(10000)) { throw '测试进程未退出，禁止清理其存档副本。' }
    }
    # 诊断插件退出后移除，避免用户后续正常游玩被自动退出或静音。
    if ($createdPlugin -and (Test-Path -LiteralPath $plugin)) { Remove-Item -LiteralPath $plugin }
    if ($createdAppId -and (Test-Path -LiteralPath $appIdPath)) { Remove-Item -LiteralPath $appIdPath }
    [IO.File]::WriteAllBytes($loaderConfigPath, $originalLoaderConfig)
    $env:ELSINOREHAN_PROBE_RUN_ID = $previousRunId
    $env:ELSINOREHAN_PROBE_SAVE_PATH = $previousSavePath
    # 临时隔离存档仅服务本轮测试，退出后不作长期备份留存。
    $saveCleanupRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot 'runtime/evidence/headless')) + [IO.Path]::DirectorySeparatorChar
    $saveCleanupPath = [IO.Path]::GetFullPath($isolatedSavePath)
    if (-not $saveCleanupPath.StartsWith($saveCleanupRoot, [StringComparison]::OrdinalIgnoreCase) -or (Split-Path $saveCleanupPath -Leaf) -ne 'isolated-save') { throw '临时存档清理路径越界。' }
    if (Test-Path -LiteralPath $saveCleanupPath) { Remove-Item -LiteralPath $saveCleanupPath -Recurse -Force }
}
