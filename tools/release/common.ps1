# 此文件与安装器一起解压；兼容 Windows PowerShell 5.1。
Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$script:EhStateName = 'ElsinoreHan.install.json'
$script:EhExclusive = @(
    'elsinorehan_sans_sdf_u2018', 'BepInEx/plugins/ElsinoreHan.TranslationToggle.dll',
    'BepInEx/Translation/zh-CN/Text/ElsinoreHan-Dynamic.txt', 'BepInEx/Translation/zh-CN/Text/ElsinoreHan-Sol.txt',
    'licenses/ElsinoreHanSans-NOTICE.txt', 'licenses/ElsinoreHanSans-OFL.txt'
)
$script:EhAllowed = @(
    '.doorstop_version', 'changelog.txt', 'doorstop_config.ini', 'elsinorehan_sans_sdf_u2018', 'README.md', 'winhttp.dll', 'XUnity-LICENSE',
    'BepInEx/config/AutoTranslatorConfig.ini',
    'BepInEx/core/0Harmony.dll', 'BepInEx/core/0Harmony.xml', 'BepInEx/core/0Harmony20.dll',
    'BepInEx/core/BepInEx.dll', 'BepInEx/core/BepInEx.Harmony.dll', 'BepInEx/core/BepInEx.Harmony.xml',
    'BepInEx/core/BepInEx.Preloader.dll', 'BepInEx/core/BepInEx.Preloader.xml', 'BepInEx/core/BepInEx.xml',
    'BepInEx/core/HarmonyXInterop.dll', 'BepInEx/core/Mono.Cecil.dll', 'BepInEx/core/Mono.Cecil.Mdb.dll',
    'BepInEx/core/Mono.Cecil.Pdb.dll', 'BepInEx/core/Mono.Cecil.Rocks.dll',
    'BepInEx/core/MonoMod.RuntimeDetour.dll', 'BepInEx/core/MonoMod.RuntimeDetour.xml',
    'BepInEx/core/MonoMod.Utils.dll', 'BepInEx/core/MonoMod.Utils.xml', 'BepInEx/core/XUnity.Common.dll',
    'BepInEx/plugins/ElsinoreHan.TranslationToggle.dll', 'BepInEx/plugins/README (AutoTranslator).md',
    'BepInEx/plugins/XUnity.AutoTranslator/ExIni.dll',
    'BepInEx/plugins/XUnity.AutoTranslator/XUnity.AutoTranslator.Plugin.BepInEx.dll',
    'BepInEx/plugins/XUnity.AutoTranslator/XUnity.AutoTranslator.Plugin.Core.dll',
    'BepInEx/plugins/XUnity.AutoTranslator/XUnity.AutoTranslator.Plugin.ExtProtocol.dll',
    'BepInEx/plugins/XUnity.ResourceRedirector/XUnity.ResourceRedirector.BepInEx.dll',
    'BepInEx/plugins/XUnity.ResourceRedirector/XUnity.ResourceRedirector.dll',
    'BepInEx/Translation/zh-CN/Text/ElsinoreHan-Dynamic.txt', 'BepInEx/Translation/zh-CN/Text/ElsinoreHan-Sol.txt',
    'licenses/ElsinoreHanSans-NOTICE.txt', 'licenses/ElsinoreHanSans-OFL.txt', 'licenses/TextMeshPro-Unity-Companion-License.txt'
)

function Assert-EhNoLink([string]$Path) {
    $cursor = [IO.Path]::GetFullPath($Path)
    while ($cursor) {
        try { $item = Get-Item -LiteralPath $cursor -Force -ErrorAction Stop }
        catch [System.Management.Automation.ItemNotFoundException] { $item = $null }
        if ($null -ne $item) {
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "拒绝重解析点：$cursor"
            }
        }
        $parent = [IO.Path]::GetDirectoryName($cursor)
        if ($parent -eq $cursor) { break }
        $cursor = $parent
    }
}

function Get-EhTarget([string]$Root, [string]$Relative) {
    if ($script:EhAllowed -cnotcontains $Relative) { throw "非白名单路径：$Relative" }
    $target = [IO.Path]::GetFullPath((Join-Path $Root $Relative))
    if (-not $target.StartsWith($Root.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "路径越界：$Relative"
    }
    Assert-EhNoLink $target
    if ((Test-Path -LiteralPath $target) -and -not (Test-Path -LiteralPath $target -PathType Leaf)) { throw "文件位置被目录占用：$target" }
    return $target
}

function Get-EhHash([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }

function Read-EhEntries($Entries, [bool]$AllowRepeatedPath) {
    $seen = @{}
    foreach ($entry in @($Entries)) {
        if ($null -eq $entry -or $entry.PSObject.Properties.Name -notcontains 'path' -or
            $entry.PSObject.Properties.Name -notcontains 'sha256' -or $entry.PSObject.Properties.Name -notcontains 'size') { throw '文件清单字段不完整' }
        if ($entry.path -isnot [string] -or $script:EhAllowed -cnotcontains $entry.path) { throw "非白名单路径：$($entry.path)" }
        if ($entry.sha256 -isnot [string] -or $entry.sha256 -cnotmatch '^[a-f0-9]{64}$') { throw '文件清单哈希无效' }
        if ($entry.size -isnot [long] -and $entry.size -isnot [int]) { throw '文件清单大小无效' }
        if ($entry.size -lt 0) { throw '文件清单大小不能为负数' }
        $key = if ($AllowRepeatedPath) { $entry.path + ':' + $entry.sha256 } else { $entry.path }
        if ($seen.ContainsKey($key)) { throw "清单重复：$key" }
        $seen[$key] = $true
        $entry
    }
}

function Read-EhManifest([string]$PackageRoot, [bool]$VerifyPayload) {
    Assert-EhNoLink $PackageRoot
    $path = Join-Path $PackageRoot 'manifest.json'
    Assert-EhNoLink $path
    $manifest = Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($manifest.schema_version -ne 1 -or $manifest.package_id -cne 'ElsinoreHan' -or
        [string]::IsNullOrWhiteSpace($manifest.release_id)) { throw '不支持的补丁清单' }
    $files = @(Read-EhEntries $manifest.files $false)
    if ($files.Count -eq 0) { throw '补丁文件清单为空' }
    $legacy = @(Read-EhEntries $manifest.legacy_files $true)
    $known = @{}
    foreach ($entry in @($files) + @($legacy)) { $known[$entry.path + ':' + $entry.sha256] = [long]$entry.size }
    if ($VerifyPayload) {
        # 辅助工具位于 ElsinoreHan/，运行文件平铺在其父目录。
        $payload = [IO.Path]::GetFullPath((Join-Path $PackageRoot '..'))
        Assert-EhNoLink $payload
        foreach ($entry in $files) {
            $source = Get-EhTarget $payload $entry.path
            if (-not (Test-Path -LiteralPath $source -PathType Leaf) -or (Get-Item -LiteralPath $source).Length -ne $entry.size -or
                (Get-EhHash $source) -cne $entry.sha256) { throw "补丁内容校验失败：$($entry.path)" }
        }
        # 源目录可与游戏目录相同。只消费清单条目，不枚举或复制其余文件。
    }
    return [pscustomobject]@{ files=$files; legacy_files=$legacy; known=$known; release_id=$manifest.release_id }
}

function Get-EhGameRoot([string]$GamePath) {
    if ([string]::IsNullOrWhiteSpace($GamePath)) { $GamePath = Read-Host '请输入 Elsinore 游戏目录（包含 Elsinore.exe）' }
    $root = [IO.Path]::GetFullPath($GamePath.Trim('"')).TrimEnd('\', '/')
    Assert-EhNoLink $root
    foreach ($relative in @('Elsinore.exe', 'UnityPlayer.dll', 'Elsinore_Data/resources.assets', 'Elsinore_Data/Managed/Assembly-CSharp.dll')) {
        $target = Join-Path $root $relative
        Assert-EhNoLink $target
        if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { throw "不是受支持的游戏目录，缺少：$relative" }
    }
    Assert-EhNotRunning $root
    return $root
}

function Assert-EhNotRunning([string]$GameRoot) {
    $exe = [IO.Path]::GetFullPath((Join-Path $GameRoot 'Elsinore.exe'))
    foreach ($process in @(Get-Process -Name Elsinore -ErrorAction SilentlyContinue)) {
        try { $processPath = $process.Path } catch { throw '无法确认同名游戏进程路径，请先退出游戏后重试' }
        if (-not $processPath) { throw '无法确认同名游戏进程路径，请先退出游戏后重试' }
        if ([IO.Path]::GetFullPath($processPath).Equals($exe, [StringComparison]::OrdinalIgnoreCase)) { throw '目标游戏正在运行，请保存并退出后重试' }
    }
}

function Read-EhState([string]$GameRoot, $Manifest) {
    $path = Join-Path $GameRoot $script:EhStateName
    Assert-EhNoLink $path
    if (-not (Test-Path -LiteralPath $path)) { return @() }
    $state = Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($state.schema_version -ne 1 -or $state.package_id -cne 'ElsinoreHan') { throw '已有安装记录不属于本项目或格式无效' }
    $entries = @(Read-EhEntries $state.files $false)
    foreach ($entry in $entries) {
        $key = $entry.path + ':' + $entry.sha256
        if (-not $Manifest.known.ContainsKey($key) -or $Manifest.known[$key] -ne $entry.size) { throw "安装记录未被当前包认可：$($entry.path)" }
        [void](Get-EhTarget $GameRoot $entry.path)
    }
    return $entries
}

function Write-EhState([string]$GameRoot, [string]$ReleaseId, $Entries) {
    $path = Join-Path $GameRoot $script:EhStateName
    Assert-EhNoLink $path
    $state = [ordered]@{ schema_version=1; package_id='ElsinoreHan'; release_id=$ReleaseId; files=@($Entries) }
    [IO.File]::WriteAllText($path, ($state | ConvertTo-Json -Depth 6), (New-Object Text.UTF8Encoding($false)))
}

function Test-EhOtherMods([string]$GameRoot, $Manifest) {
    $knownPaths = @{}
    foreach ($entry in @($Manifest.files) + @($Manifest.legacy_files)) { $knownPaths[$entry.path] = $true }
    $queue = New-Object 'System.Collections.Generic.Queue[string]'
    foreach ($relative in @('BepInEx/plugins', 'BepInEx/patchers', 'BepInEx/core')) {
        $path = Join-Path $GameRoot $relative
        if (Test-Path -LiteralPath $path) { $queue.Enqueue($path) }
    }
    while ($queue.Count -gt 0) {
        $directory = $queue.Dequeue()
        # 不进入未知模组的链接；发现链接时按仍有其他模组处理。
        if (((Get-Item -LiteralPath $directory -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { return $true }
        foreach ($item in Get-ChildItem -LiteralPath $directory -Force) {
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { return $true }
            if ($item.PSIsContainer) { $queue.Enqueue($item.FullName) }
            elseif ($item.Extension -ieq '.dll') {
                $relative = $item.FullName.Substring($GameRoot.Length + 1).Replace('\', '/')
                if (-not $knownPaths.ContainsKey($relative)) { return $true }
            }
        }
    }
    return $false
}

function Install-EhPackage([string]$PackageRoot, [string]$GamePath) {
    $manifest = Read-EhManifest $PackageRoot $true
    $root = Get-EhGameRoot $GamePath
    $previous = @(Read-EhState $root $manifest)
    $owned = @{}
    foreach ($entry in $previous) { $owned[$entry.path] = $entry }
    $next = @{}
    $copy = @()
    $shared = @()
    foreach ($entry in $manifest.files) {
        $target = Get-EhTarget $root $entry.path
        $claim = $false
        if (Test-Path -LiteralPath $target) {
            $hash = Get-EhHash $target
            $size = (Get-Item -LiteralPath $target).Length
            if ($owned.ContainsKey($entry.path)) {
                if ($hash -cne $owned[$entry.path].sha256 -or $size -ne $owned[$entry.path].size) { throw "自有文件已被修改，拒绝升级：$($entry.path)" }
                $claim = $true
            } elseif ($hash -ceq $entry.sha256 -and $size -eq $entry.size) {
                # 没有归属记录的同内容依赖视为共享，卸载不会删除。
                if ($script:EhExclusive -ccontains $entry.path) { $claim = $true }
                else { $shared += $entry.path }
            } elseif (@($manifest.legacy_files | Where-Object { $_.path -ceq $entry.path -and $_.sha256 -ceq $hash -and $_.size -eq $size }).Count -gt 0) {
                $claim = $true
            } else { throw "发现未知文件冲突，未执行安装：$($entry.path)" }
        } else { $claim = $true }
        if ($claim) { $next[$entry.path] = $entry; $copy += $entry }
    }
    $remove = @()
    foreach ($entry in $previous) {
        if ($next.ContainsKey($entry.path)) { continue }
        $target = Get-EhTarget $root $entry.path
        if (Test-Path -LiteralPath $target) {
            if ((Get-EhHash $target) -cne $entry.sha256 -or (Get-Item -LiteralPath $target).Length -ne $entry.size) { throw "旧自有文件已修改，拒绝移除：$($entry.path)" }
            $remove += $entry
        }
    }
    Assert-EhNotRunning $root
    # 先保存本次拥有范围。中断后，卸载仍只删除匹配已知哈希的文件。
    $receipt = @($next.Values) + @($remove)
    Write-EhState $root $manifest.release_id $receipt
    foreach ($entry in $copy) {
        $target = Get-EhTarget $root $entry.path
        New-Item -ItemType Directory -Path (Split-Path $target) -Force | Out-Null
        $source = Get-EhTarget ([IO.Path]::GetFullPath((Join-Path $PackageRoot '..'))) $entry.path
        if (-not $source.Equals($target, [StringComparison]::OrdinalIgnoreCase)) { Copy-Item -LiteralPath $source -Destination $target -Force }
        if ((Get-EhHash $target) -cne $entry.sha256) { throw "写入后校验失败：$($entry.path)" }
    }
    foreach ($entry in $remove) { Remove-Item -LiteralPath (Get-EhTarget $root $entry.path) -Force }
    Write-EhState $root $manifest.release_id @($next.Values | Sort-Object path)
    Write-Output "安装完成：$($manifest.release_id)；拥有 $($next.Count) 个文件，共享保留 $($shared.Count) 个文件。"
    foreach ($path in $shared) { Write-Output "共享文件（卸载保留）：$path" }
}

function Uninstall-EhPackage([string]$PackageRoot, [string]$GamePath) {
    $manifest = Read-EhManifest $PackageRoot $false
    $root = Get-EhGameRoot $GamePath
    $previous = @(Read-EhState $root $manifest)
    if (-not (Test-Path -LiteralPath (Join-Path $root $script:EhStateName))) {
        $previous = @($manifest.files | Where-Object { $script:EhExclusive -ccontains $_.path })
        Write-Output '未找到安装归属记录：仅检查本项目独有文件；共享加载器、配置及依赖全部保留。'
    }
    $keep = @()
    $remove = @()
    $sharedKeep = @()
    $otherMods = Test-EhOtherMods $root $manifest
    # 共享配置或依赖已改动也可能供其他模组使用，保守保留整组共享运行环境。
    foreach ($entry in $previous) {
        if ($script:EhExclusive -ccontains $entry.path) { continue }
        $target = Get-EhTarget $root $entry.path
        if ((Test-Path -LiteralPath $target) -and ((Get-EhHash $target) -cne $entry.sha256 -or (Get-Item -LiteralPath $target).Length -ne $entry.size)) { $otherMods = $true }
    }
    foreach ($entry in $previous) {
        $target = Get-EhTarget $root $entry.path
        if (Test-Path -LiteralPath $target) {
            if ($otherMods -and $script:EhExclusive -cnotcontains $entry.path) { $sharedKeep += $entry }
            elseif ((Get-EhHash $target) -ceq $entry.sha256 -and (Get-Item -LiteralPath $target).Length -eq $entry.size) { $remove += $entry }
            else { $keep += $entry }
        }
    }
    Assert-EhNotRunning $root
    foreach ($entry in $remove) { Remove-Item -LiteralPath (Get-EhTarget $root $entry.path) -Force }
    $statePath = Join-Path $root $script:EhStateName
    if ($keep.Count + $sharedKeep.Count -gt 0) { Write-EhState $root $manifest.release_id @($keep + $sharedKeep) }
    elseif (Test-Path -LiteralPath $statePath) { Remove-Item -LiteralPath $statePath -Force }
    Write-Output "卸载完成：删除 $($remove.Count) 个自有文件，保留 $($keep.Count) 个已修改独有文件及 $($sharedKeep.Count) 个可能供其他模组使用的文件。"
    foreach ($entry in $keep) { Write-Output "已修改，保留（安装记录仍保留）：$($entry.path)" }
    foreach ($entry in $sharedKeep) { Write-Output "可能供其他模组使用，保留（安装记录仍保留）：$($entry.path)" }
}
