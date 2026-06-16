@echo off
REM Double-click to remove the LF Discord bot auto-start task.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall-autostart.ps1"
pause
