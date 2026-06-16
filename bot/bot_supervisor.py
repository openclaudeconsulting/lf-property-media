"""
LF Property Media — Discord bot supervisor.

Keeps discord_bot.py alive: restarts it on any exit (10s backoff) and kills +
restarts it if its event loop wedges (heartbeat goes stale). Designed to run
via pythonw.exe from a Windows scheduled task at user logon (see
install-autostart.ps1) so the bot is always up without a terminal open.

Simpler than the Southern Barn supervisor: LF's backend is pure Python
(new-job.py / build-property.py), so there's no local HTTP server or headless
Chrome to babysit — just the one bot process.

Manual run (foreground, for testing): python bot/bot_supervisor.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
import threading
from pathlib import Path

BOT_DIR = Path(__file__).resolve().parent
REPO_ROOT = BOT_DIR.parent
BOT_SCRIPT = BOT_DIR / "discord_bot.py"

BOT_HEARTBEAT = REPO_ROOT / ".bot.heartbeat"
SUP_HEARTBEAT = REPO_ROOT / ".supervisor.heartbeat"
LOG_FILE = REPO_ROOT / "bot.log"

RESTART_DELAY_SECONDS = 10
BOT_HEARTBEAT_STALE_SECONDS = 120   # 4× the bot's 30s write interval
STARTUP_GRACE_SECONDS = 60          # let login + gateway handshake settle

_CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


def log(msg: str) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:  # noqa: BLE001
        pass


def _supervisor_heartbeat_loop() -> None:
    while True:
        try:
            SUP_HEARTBEAT.write_text(str(int(time.time())), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
        time.sleep(60)


def _bot_heartbeat_age() -> float | None:
    try:
        return time.time() - int(BOT_HEARTBEAT.read_text(encoding="utf-8").strip())
    except Exception:  # noqa: BLE001
        return None


MAX_BACKOFF_SECONDS = 600  # cap so a permanent misconfig doesn't hot-loop


def run_bot_loop() -> None:
    consecutive_fast = 0  # exits that happened before the startup grace window
    while True:
        log("Starting discord_bot.py ...")
        try:
            BOT_HEARTBEAT.unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            pass

        proc = subprocess.Popen(
            [sys.executable, str(BOT_SCRIPT)],
            cwd=str(REPO_ROOT),
            creationflags=_CREATE_NO_WINDOW,
        )
        started = time.time()

        # Watch the process + heartbeat.
        while True:
            ret = proc.poll()
            if ret is not None:
                log(f"discord_bot.py exited with code {ret}.")
                break
            if time.time() - started > STARTUP_GRACE_SECONDS:
                age = _bot_heartbeat_age()
                if age is not None and age > BOT_HEARTBEAT_STALE_SECONDS:
                    log(f"Bot heartbeat stale ({age:.0f}s) — event loop appears wedged. Killing.")
                    try:
                        proc.kill()
                        proc.wait(timeout=10)
                    except Exception:  # noqa: BLE001
                        pass
                    break
            time.sleep(5)

        # A bot that dies before the grace window is almost always a permanent
        # misconfig (bad token/key, missing dep). Back off instead of hot-looping.
        ran_for = time.time() - started
        if ran_for < STARTUP_GRACE_SECONDS:
            consecutive_fast += 1
        else:
            consecutive_fast = 0

        if consecutive_fast >= 3:
            delay = min(MAX_BACKOFF_SECONDS, RESTART_DELAY_SECONDS * (2 ** (consecutive_fast - 2)))
            log(f"{consecutive_fast} fast exits in a row — likely a config problem "
                f"(check .discord_bot.env / .anthropic_api_key and bot.log). Backing off {delay}s.")
        else:
            delay = RESTART_DELAY_SECONDS
        log(f"Restarting in {delay}s ...")
        time.sleep(delay)


def main() -> None:
    log("Supervisor starting.")
    if not BOT_SCRIPT.exists():
        log(f"FATAL: {BOT_SCRIPT} not found.")
        sys.exit(1)
    threading.Thread(target=_supervisor_heartbeat_loop, daemon=True).start()
    try:
        run_bot_loop()
    except KeyboardInterrupt:
        log("Supervisor stopped by user.")


if __name__ == "__main__":
    main()
