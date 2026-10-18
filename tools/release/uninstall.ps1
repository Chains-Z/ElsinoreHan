param([string]$GamePath)
$ErrorActionPreference = 'Stop'
try {
    . (Join-Path $PSScriptRoot 'common.ps1')
    Uninstall-EhPackage $PSScriptRoot $GamePath
} catch { Write-Error $_; exit 1 }
