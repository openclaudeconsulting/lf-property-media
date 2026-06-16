# Registers bot_supervisor.py as a Windows scheduled task so the LF Discord bot
# starts silently at every user logon. Run once per machine.
# Easiest way: double-click install-autostart.bat (which calls this with the
# right ExecutionPolicy bypass).

$ErrorActionPreference = "Stop"
$TaskName = "LFPropertyMediaBot"
$BotDir = $PSScriptRoot
$Supervisor = Join-Path $BotDir "bot_supervisor.py"

# Prefer pythonw.exe (no console window); fall back to python.exe.
$python = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $python) {
    $python = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
    Write-Warning "pythonw.exe not found; using python.exe (a console window may appear)."
}
if (-not $python) {
    Write-Error "Python not found on PATH. Install Python and re-run."
    exit 1
}

# Tear down any prior task (idempotent).
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$action = New-ScheduledTaskAction -Execute $python -Argument "`"$Supervisor`"" -WorkingDirectory $BotDir
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Seconds 0) -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Principal $principal -Settings $settings | Out-Null

Start-ScheduledTask -TaskName $TaskName
$state = (Get-ScheduledTask -TaskName $TaskName).State
Write-Host "Registered + started scheduled task '$TaskName' (state: $state)."
Write-Host "Logs: $(Join-Path (Split-Path $BotDir -Parent) 'bot.log')"
Write-Host "Tail logs:  Get-Content '$(Join-Path (Split-Path $BotDir -Parent) 'bot.log')' -Wait -Tail 50"
