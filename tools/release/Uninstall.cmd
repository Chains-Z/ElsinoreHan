@echo off
setlocal
if "%~1"=="" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall.ps1"
) else (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall.ps1" -GamePath "%~1"
)
set "result=%errorlevel%"
pause
exit /b %result%
