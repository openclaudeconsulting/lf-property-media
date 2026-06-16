@echo off
REM LF Property Media - double-click to create a new shoot's folders.
REM Prompts for realtor, address, and date, then builds the raw + final trees
REM and opens the raw folder. Requires Python installed.
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel%==0 (
  python "new-job.py" --open
) else (
  py "new-job.py" --open
)
echo.
pause
