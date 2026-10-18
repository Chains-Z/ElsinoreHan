param([string]$EvidencePath)
# 隔离文件系统集成测试；只启动自己编译的休眠哨兵，不启动真实游戏。
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
$project = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$testRoot = Join-Path $project ('runtime/game-test/release-' + [guid]::NewGuid().ToString('N'))
if (-not $testRoot.StartsWith((Join-Path $project 'runtime/game-test') + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw '测试目录越界' }
$results = New-Object 'System.Collections.Generic.List[object]'
$script:processes = @()
$script:caseNumber = 0
function Put([string]$Path, [string]$Value) {
    New-Item -ItemType Directory -Path (Split-Path $Path) -Force | Out-Null
    [IO.File]::WriteAllText($Path, $Value, (New-Object Text.UTF8Encoding($false)))
}
function Assert([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Throws([scriptblock]$Action, [string]$Expected) {
    try { & $Action | Out-Null } catch {
        if ($_.Exception.Message -notlike ('*' + $Expected + '*')) { throw "预期拒绝原因 '$Expected'，实际：$_" }
        return
    }
    throw "预期拒绝但实际成功：$Expected"
}
function Save-Manifest($Fixture) {
    Put (Join-Path $Fixture.package 'manifest.json') ($Fixture.manifest | ConvertTo-Json -Depth 6)
}
function Fixture {
    $script:caseNumber++
    $root = Join-Path $testRoot ([string]$script:caseNumber)
    $source = Join-Path $root 'release'
    $package = Join-Path $source 'ElsinoreHan'
    $game = Join-Path $root 'game'
    foreach ($relative in @('Elsinore.exe','UnityPlayer.dll','Elsinore_Data/resources.assets','Elsinore_Data/Managed/Assembly-CSharp.dll','save-sentinel.txt')) {
        Put (Join-Path $game $relative) ('原件哨兵：' + $relative)
    }
    $files = @()
    foreach ($relative in @('winhttp.dll','BepInEx/config/AutoTranslatorConfig.ini','BepInEx/plugins/ElsinoreHan.TranslationToggle.dll')) {
        $path = Join-Path $source $relative
        Put $path ('新版本：' + $relative)
        $files += [pscustomobject]@{path=$relative; sha256=(Get-EhHash $path);size=(Get-Item -LiteralPath $path).Length}
    }
    $manifest = [pscustomobject]@{schema_version=1;package_id='ElsinoreHan';release_id='fixture-1';files=$files;legacy_files=@()}
    $fixture = [pscustomobject]@{root=$root;source=$source;package=$package;game=$game;manifest=$manifest}
    Save-Manifest $fixture
    foreach ($scriptName in @('common.ps1','install.ps1','uninstall.ps1')) { Copy-Item -LiteralPath (Join-Path $PSScriptRoot $scriptName) -Destination (Join-Path $package $scriptName) }
    return $fixture
}
function Check-Sentinels($Fixture) {
    foreach ($relative in @('UnityPlayer.dll','Elsinore_Data/resources.assets','Elsinore_Data/Managed/Assembly-CSharp.dll','save-sentinel.txt')) {
        Assert (([IO.File]::ReadAllText((Join-Path $Fixture.game $relative))) -ceq ('原件哨兵：' + $relative)) "哨兵改变：$relative"
    }
}
function Case([string]$Name, [scriptblock]$Action) {
    & $Action
    $results.Add([pscustomobject]@{name=$Name;passed=$true})
    Write-Output "通过：$Name"
}
try {
    Case '原生PowerShell5.1独立脚本干净安装、重复安装、卸载及四原件保护' {
        $f = Fixture
        $originalExe = Get-EhHash (Join-Path $f.game 'Elsinore.exe')
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $f.package 'install.ps1') -GamePath $f.game | Out-Null
        Assert ($LASTEXITCODE -eq 0) '独立安装脚本失败'
        Install-EhPackage $f.package $f.game | Out-Null
        $receipt = Get-Content -LiteralPath (Join-Path $f.game $script:EhStateName) -Raw -Encoding UTF8 | ConvertFrom-Json
        Assert ($receipt.files.Count -eq 3) '干净安装应拥有全部三文件'
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $f.package 'uninstall.ps1') -GamePath $f.game | Out-Null
        Assert ($LASTEXITCODE -eq 0) '独立卸载脚本失败'
        Assert (-not (Test-Path -LiteralPath (Join-Path $f.game 'winhttp.dll'))) '加载依赖未删除'
        Assert (-not (Test-Path -LiteralPath (Join-Path $f.game $script:EhStateName))) '无残余时未清理记录'
        Assert ((Get-EhHash (Join-Path $f.game 'Elsinore.exe')) -ceq $originalExe) 'exe改变'
        Check-Sentinels $f
    }
    Case '未知冲突整批预检拒绝且不写任何文件' {
        $f = Fixture
        Put (Join-Path $f.game 'BepInEx/config/AutoTranslatorConfig.ini') '未知配置'
        Throws { Install-EhPackage $f.package $f.game } '未知文件冲突'
        Assert (-not (Test-Path -LiteralPath (Join-Path $f.game 'winhttp.dll'))) '冲突后仍写入'
        Assert (-not (Test-Path -LiteralPath (Join-Path $f.game $script:EhStateName))) '冲突后仍写记录'
        Check-Sentinels $f
    }
    Case '已有同哈希共享依赖不认领且卸载保留' {
        $f = Fixture
        Copy-Item -LiteralPath (Join-Path $f.source 'winhttp.dll') -Destination (Join-Path $f.game 'winhttp.dll')
        Install-EhPackage $f.package $f.game | Out-Null
        Uninstall-EhPackage $f.package $f.game | Out-Null
        Assert (Test-Path -LiteralPath (Join-Path $f.game 'winhttp.dll')) '共享依赖被删除'
        Check-Sentinels $f
    }
    Case '安装后加入其他模组时卸载保留完整共享运行环境' {
        $f = Fixture
        Install-EhPackage $f.package $f.game | Out-Null
        $other = Join-Path $f.game 'BepInEx/plugins/OtherMod/OtherMod.dll'
        Put $other '其他模组'
        Uninstall-EhPackage $f.package $f.game | Out-Null
        Assert (([IO.File]::ReadAllText($other)) -ceq '其他模组') '其他模组被改动'
        Assert (Test-Path -LiteralPath (Join-Path $f.game 'winhttp.dll')) '其他模组加载器被删除'
        Assert (Test-Path -LiteralPath (Join-Path $f.game 'BepInEx/config/AutoTranslatorConfig.ini')) '共享配置被删除'
        Assert (-not (Test-Path -LiteralPath (Join-Path $f.game 'BepInEx/plugins/ElsinoreHan.TranslationToggle.dll'))) '本项目独有文件未移除'
        Check-Sentinels $f
    }
    Case '共享配置已修改时卸载保留共享运行环境' {
        $f = Fixture
        Install-EhPackage $f.package $f.game | Out-Null
        Put (Join-Path $f.game 'BepInEx/config/AutoTranslatorConfig.ini') '用户或其他模组配置'
        Uninstall-EhPackage $f.package $f.game | Out-Null
        Assert (Test-Path -LiteralPath (Join-Path $f.game 'winhttp.dll')) '共享配置改动后删除了加载器'
        Assert (([IO.File]::ReadAllText((Join-Path $f.game 'BepInEx/config/AutoTranslatorConfig.ini'))) -ceq '用户或其他模组配置') '修改配置被改变'
    }
    Case '有清单升级接受已拥有哈希' {
        $f = Fixture
        Install-EhPackage $f.package $f.game | Out-Null
        $old = $f.manifest.files[2]
        Put (Join-Path $f.source $old.path) '新版本2'
        $f.manifest.legacy_files = @($old)
        $f.manifest.files[2] = [pscustomobject]@{path=$old.path;sha256=(Get-EhHash (Join-Path $f.source $old.path));size=(Get-Item -LiteralPath (Join-Path $f.source $old.path)).Length}
        Save-Manifest $f
        Install-EhPackage $f.package $f.game | Out-Null
        Assert ((Get-EhHash (Join-Path $f.game $old.path)) -ceq $f.manifest.files[2].sha256) '升级内容错误'
        Uninstall-EhPackage $f.package $f.game | Out-Null
    }
    Case '旧正式证明允许无清单升级' {
        $f = Fixture
        $oldPath = Join-Path $f.game 'winhttp.dll'
        Put $oldPath '已知旧依赖'
        $f.manifest.legacy_files = @([pscustomobject]@{path='winhttp.dll';sha256=(Get-EhHash $oldPath);size=(Get-Item -LiteralPath $oldPath).Length})
        Save-Manifest $f
        Install-EhPackage $f.package $f.game | Out-Null
        Uninstall-EhPackage $f.package $f.game | Out-Null
        Assert (-not (Test-Path -LiteralPath $oldPath)) '旧证明认领文件未清理'
    }
    Case '修改自有文件拒绝升级、卸载保留并记录' {
        $f = Fixture
        Install-EhPackage $f.package $f.game | Out-Null
        $changed = Join-Path $f.game 'BepInEx/plugins/ElsinoreHan.TranslationToggle.dll'
        Put $changed '用户改动'
        Throws { Install-EhPackage $f.package $f.game } '自有文件已被修改'
        Uninstall-EhPackage $f.package $f.game | Out-Null
        Assert (([IO.File]::ReadAllText($changed)) -ceq '用户改动') '修改文件被删除'
        $state = Get-Content -LiteralPath (Join-Path $f.game $script:EhStateName) -Raw -Encoding UTF8 | ConvertFrom-Json
        Assert (@($state.files).Count -eq 1) '残余记录错误'
        Check-Sentinels $f
    }
    Case '平铺直接解压无清单卸载仅清理项目独有文件' {
        $f = Fixture
        foreach ($entry in $f.manifest.files) { Put (Join-Path $f.game $entry.path) ([IO.File]::ReadAllText((Join-Path $f.source $entry.path))) }
        Uninstall-EhPackage $f.package $f.game | Out-Null
        Assert (Test-Path -LiteralPath (Join-Path $f.game 'winhttp.dll')) '无清单删除共享加载器'
        Assert (Test-Path -LiteralPath (Join-Path $f.game 'BepInEx/config/AutoTranslatorConfig.ini')) '无清单删除配置'
        Assert (-not (Test-Path -LiteralPath (Join-Path $f.game 'BepInEx/plugins/ElsinoreHan.TranslationToggle.dll'))) '未删除独有插件'
        Check-Sentinels $f
    }
    Case '平铺源等于目标时辅助安装不自拷贝' {
        $f = Fixture
        foreach ($entry in $f.manifest.files) { Put (Join-Path $f.game $entry.path) ([IO.File]::ReadAllText((Join-Path $f.source $entry.path))) }
        $scriptDir = Join-Path $f.game 'ElsinoreHan'
        New-Item -ItemType Directory -Path $scriptDir -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $f.package 'manifest.json') -Destination (Join-Path $scriptDir 'manifest.json')
        Install-EhPackage $scriptDir $f.game | Out-Null
        $state = Get-Content -LiteralPath (Join-Path $f.game $script:EhStateName) -Raw -Encoding UTF8 | ConvertFrom-Json
        Assert (@($state.files).Count -eq 1) '直接解压后应仅认领独有文件'
    }
    Case 'manifest路径穿越、原游戏文件及大小写变体被拒绝' {
        foreach ($bad in @('../outside.txt','Elsinore.exe','Elsinore_Data/Managed/Assembly-CSharp.dll','WINHTTP.DLL','BepInEx\\plugins\\other.dll','C:/outside.txt','winhttp.dll:stream')) {
            $f = Fixture
            $f.manifest.files[0].path = $bad
            Save-Manifest $f
            Throws { Install-EhPackage $f.package $f.game } '非白名单路径'
            Check-Sentinels $f
        }
    }
    Case 'manifest哈希大小及重复项拒绝' {
        $f = Fixture
        $f.manifest.files[0].sha256 = ('0' * 64)
        Save-Manifest $f
        Throws { Install-EhPackage $f.package $f.game } '补丁内容校验失败'
        $f = Fixture
        $f.manifest.files[0].size++
        Save-Manifest $f
        Throws { Install-EhPackage $f.package $f.game } '补丁内容校验失败'
        $f = Fixture
        $f.manifest.files += $f.manifest.files[0]
        Save-Manifest $f
        Throws { Install-EhPackage $f.package $f.game } '清单重复'
    }
    Case '伪造安装记录的任意哈希和越界拒绝' {
        $f = Fixture
        Install-EhPackage $f.package $f.game | Out-Null
        $statePath = Join-Path $f.game $script:EhStateName
        $state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
        $state.files[0].sha256 = '0' * 64
        Put $statePath ($state | ConvertTo-Json -Depth 6)
        Throws { Uninstall-EhPackage $f.package $f.game } '安装记录未被当前包认可'
        $state.files[0].path = '../outside.txt'
        Put $statePath ($state | ConvertTo-Json -Depth 6)
        Throws { Uninstall-EhPackage $f.package $f.game } '非白名单路径'
        Assert (Test-Path -LiteralPath (Join-Path $f.game 'winhttp.dll')) '拒绝后仍删除文件'
    }
    Case '目标目录链接拒绝且外部哨兵不变' {
        $f = Fixture
        $outside = Join-Path $f.root 'outside'
        Put (Join-Path $outside 'sentinel.txt') '不能改变'
        $link = Join-Path $f.game 'licenses'
        New-Item -ItemType Junction -Path $link -Target $outside | Out-Null
        try { Throws { Get-EhTarget $f.game 'licenses/ElsinoreHanSans-OFL.txt' } '重解析点' }
        finally { [IO.Directory]::Delete($link) }
        Assert (([IO.File]::ReadAllText((Join-Path $outside 'sentinel.txt'))) -ceq '不能改变') '链接外部内容改变'
    }
    Case '源目录链接和游戏根链接拒绝' {
        $f = Fixture
        $sourceLink = Join-Path $f.root 'source-link'
        $gameLink = Join-Path $f.root 'game-link'
        New-Item -ItemType Junction -Path $sourceLink -Target $f.source | Out-Null
        New-Item -ItemType Junction -Path $gameLink -Target $f.game | Out-Null
        try {
            Throws { Install-EhPackage (Join-Path $sourceLink 'ElsinoreHan') $f.game } '重解析点'
            Throws { Install-EhPackage $f.package $gameLink } '重解析点'
        } finally { [IO.Directory]::Delete($sourceLink); [IO.Directory]::Delete($gameLink) }
    }
    Case '安装目标子目录链接整批拒绝且不写入' {
        $f = Fixture
        $outside = Join-Path $f.root 'external-config'
        Put (Join-Path $outside 'AutoTranslatorConfig.ini') '外部配置哨兵'
        $link = Join-Path $f.game 'BepInEx/config'
        New-Item -ItemType Junction -Path $link -Target $outside | Out-Null
        try {
            Throws { Install-EhPackage $f.package $f.game } '重解析点'
            Assert (-not (Test-Path -LiteralPath (Join-Path $f.game 'winhttp.dll'))) '链接冲突后仍写入'
            Assert (([IO.File]::ReadAllText((Join-Path $outside 'AutoTranslatorConfig.ini'))) -ceq '外部配置哨兵') '外部文件改变'
        } finally { [IO.Directory]::Delete($link) }
    }
    Case '同名异路径哨兵不阻挡、目标路径运行拒绝且不操作进程' {
        $f = Fixture
        $sentinel = Join-Path $f.root 'sentinel/Elsinore.exe'
        New-Item -ItemType Directory -Path (Split-Path $sentinel) -Force | Out-Null
        Add-Type -TypeDefinition 'public class ReleaseSleepSentinel { public static void Main() { System.Threading.Thread.Sleep(60000); } }' -OutputAssembly $sentinel -OutputType ConsoleApplication
        $other = Start-Process -FilePath $sentinel -WindowStyle Hidden -PassThru
        $script:processes += $other
        Install-EhPackage $f.package $f.game | Out-Null
        Uninstall-EhPackage $f.package $f.game | Out-Null
        Copy-Item -LiteralPath $sentinel -Destination (Join-Path $f.game 'Elsinore.exe') -Force
        $running = Start-Process -FilePath (Join-Path $f.game 'Elsinore.exe') -WindowStyle Hidden -PassThru
        $script:processes += $running
        try {
            Throws { Install-EhPackage $f.package $f.game } '目标游戏正在运行'
            Throws { Uninstall-EhPackage $f.package $f.game } '目标游戏正在运行'
            Assert (-not $running.HasExited) '工具操作了目标进程'
            Assert (-not $other.HasExited) '工具操作了其它目录进程'
        } finally {
            foreach ($process in @($running,$other)) { if (-not $process.HasExited) { Stop-Process -Id $process.Id; $process.WaitForExit() } }
        }
    }
    Case '文件位置被目录占用拒绝' {
        $f = Fixture
        New-Item -ItemType Directory -Path (Join-Path $f.game 'winhttp.dll') | Out-Null
        Throws { Install-EhPackage $f.package $f.game } '文件位置被目录占用'
    }
    $scriptHashes = @{}
    foreach ($name in @('common.ps1','install.ps1','uninstall.ps1','Install.cmd','Uninstall.cmd','test-installer.ps1')) { $scriptHashes[$name] = Get-EhHash (Join-Path $PSScriptRoot $name) }
    $evidence = [ordered]@{schema_version=1;passed=$true;time_utc=[DateTime]::UtcNow.ToString('o');powershell_version=$PSVersionTable.PSVersion.ToString();case_count=$results.Count;cases=$results.ToArray();script_sha256=$scriptHashes;real_game_started=$false;player_saves_accessed=$false;test_processes_exited=$true;temporary_directory_removed=$true;scope='临时目录文件系统集成及原生PowerShell5.1脚本测试；非真实游戏E2E'}
} finally {
    foreach ($process in $script:processes) { if (-not $process.HasExited) { Stop-Process -Id $process.Id; $process.WaitForExit() } }
    if (Test-Path -LiteralPath $testRoot) { Remove-Item -LiteralPath $testRoot -Recurse -Force }
}
if ($EvidencePath) { Put $EvidencePath ($evidence | ConvertTo-Json -Depth 8) }
Write-Output "共 $($results.Count) 项隔离集成测试通过；临时文件及哨兵进程已清理。"
