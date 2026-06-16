@echo off
REM Double-click to install the LF Discord bot as a Windows auto-start task.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-autostart.ps1"
pause
