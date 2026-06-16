"""
LF Property Media — bot health check.

Reads the supervisor + bot heartbeats and reports OK / STALE / DEAD.
Exit code 0 = healthy, 1 = stale (wedged), 2 = dead (not running).

  python bot/bot_status.py          # full report
  python bot/bot_status.py --quiet  # print only on problems (cron-friendly)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SUP_HEARTBEAT = REPO_ROOT / ".supervisor.heartbeat"
BOT_HEARTBEAT = REPO_ROOT / ".bot.heartbeat"
STALE = 120

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # emoji on Windows cp1252
except Exception:  # noqa: BLE001
    pass


def age(path: Path) -> float | None:
    try:
        return time.time() - int(path.read_text(encoding="utf-8").strip())
    except Exception:  # noqa: BLE001
        return None


def main() -> int:
    quiet = "--quiet" in sys.argv
    sup, bot = age(SUP_HEARTBEAT), age(BOT_HEARTBEAT)

    def state(a):
        if a is None:
            return "DEAD", 2
        if a > STALE:
            return "STALE", 1
        return "OK", 0

    sup_s, sup_code = state(sup)
    bot_s, bot_code = state(bot)
    worst = max(sup_code, bot_code)

    if worst != 0 or not quiet:
        print(f"supervisor: {sup_s}" + (f" ({sup:.0f}s ago)" if sup is not None else ""))
        print(f"bot:        {bot_s}" + (f" ({bot:.0f}s ago)" if bot is not None else ""))
        if worst == 2:
            print("\nNot running. Start it:  python bot/bot_supervisor.py")
        elif worst == 1:
            print("\nWedged. Restart:  taskkill /F /IM pythonw.exe  &&  python bot/bot_supervisor.py")
    return worst


if __name__ == "__main__":
    sys.exit(main())
