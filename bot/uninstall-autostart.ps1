# Removes the LF Discord bot scheduled task and stops the running bot.
$ErrorActionPreference = "SilentlyContinue"
$TaskName = "LFPropertyMediaBot"
Stop-ScheduledTask -TaskName $TaskName
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host "Removed scheduled task '$TaskName'."
Write-Host "If a bot is still running, stop it with:  taskkill /F /IM pythonw.exe"
