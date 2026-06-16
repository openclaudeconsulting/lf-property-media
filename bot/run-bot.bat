@echo off
REM Manual foreground run for testing (Ctrl+C to stop). Leave open while testing.
REM For always-on background operation, use install-autostart.bat instead.
cd /d "%~dp0.."
python "bot\bot_supervisor.py"
pause
