#!/usr/bin/env python3
"""
LF Property Media — new-job folder generator (Phase 5 of the workflow brief).

Creates the standard raw + final folder structure for a shoot, so the owner
never has to hand-build folders again.

Structure produced (under --base, default = $LF_JOBS_BASE or your home folder):

    <base>/Real Estate/<Realtor Name>/<Address>/<Month-Day>/   (raw capture)
        Photos/  Drone/  360/  Video/
    <base>/Final/<Realtor Name>/<Address>/<Month-Day>/         (edited output)
        Home/  Aerial/  Amenities/  Video/  360/  Floorplan/

The "Final" sub-folders mirror the Pixieset galleries (Home / Aerial / Amenities)
plus a home for the video, 360s, and the 2D floor plan.

Usage
-----
  python tools/new-job.py --realtor "John Smith" --address "2719 Fort Worth Street, Sarasota"
  python tools/new-job.py --realtor "John Smith" --address "2719 Fort Worth Street" --date 2026-06-26
  python tools/new-job.py                          # interactive — prompts for everything
  python tools/new-job.py ... --open               # open the raw folder in Explorer when done
  python tools/new-job.py ... --dry-run            # show what would be created, create nothing

Set the base once so you never pass --base:
  Windows (PowerShell):  setx LF_JOBS_BASE "D:\\LF Property Media"
  Then new folders land under  D:\\LF Property Media\\Real Estate\\...  and  ...\\Final\\...

Double-clickable: run tools/new-job.bat (prompts interactively).
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, date
from pathlib import Path

# ----------------------------------------------------------------------------
# Config — tweak these to change the convention for every future job.
# ----------------------------------------------------------------------------
DEFAULT_BASE = os.environ.get("LF_JOBS_BASE") or str(Path.home())
RAW_PARENT = "Real Estate"
FINAL_PARENT = "Final"
RAW_SUBFOLDERS = ["Photos", "Drone", "360", "Video"]
FINAL_SUBFOLDERS = ["Home", "Aerial", "Amenities", "Video", "360", "Floorplan"]
ADDRESS_WORDS = 3          # how many leading address words to use for the folder
DATE_FMT = "%m-%d"         # folder date format, e.g. 06-26  (change to "%m%d" for 0626)

# Date input formats we will try, in order.
DATE_INPUT_FORMATS = ["%Y-%m-%d", "%m-%d-%Y", "%m/%d/%Y", "%m-%d", "%m/%d", "%b %d", "%B %d"]

_ILLEGAL = '<>:"/\\|?*'


def sanitize(name: str) -> str:
    """Make a string safe as a single Windows/macOS folder name."""
    cleaned = "".join(("-" if ch in _ILLEGAL else ch) for ch in name)
    # Collapse whitespace, strip trailing dots/spaces (illegal on Windows).
    cleaned = " ".join(cleaned.split()).strip(" .")
    return cleaned


def realtor_folder(raw: str) -> str:
    """Title-case the realtor's name for a tidy, consistent folder."""
    return sanitize(" ".join(w.capitalize() for w in raw.split()))


def address_folder(raw: str, words: int = ADDRESS_WORDS) -> str:
    """First few words of the address, e.g. '2719 Fort Worth Street, Sarasota' -> '2719 Fort Worth'."""
    tokens = raw.replace(",", " ").split()
    return sanitize(" ".join(tokens[:words]))


def parse_date(value: str | None) -> date:
    """Parse a flexible date string; default to today. Year defaults to current."""
    if not value or value.strip().lower() in ("", "today", "t"):
        return date.today()
    value = value.strip()
    for fmt in DATE_INPUT_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt).date()
            # Formats without a year parse to 1900 — pin to the current year.
            if "%Y" not in fmt:
                parsed = parsed.replace(year=date.today().year)
            return parsed
        except ValueError:
            continue
    raise ValueError(
        f"Could not read date '{value}'. Try 2026-06-26, 06-26, or 6/26/2026."
    )


def build_job(base: Path, realtor: str, address: str, shoot: date,
              words: int, dry_run: bool) -> tuple[Path, Path, int]:
    """Create both trees. Returns (raw_root, final_root, folders_created)."""
    r = realtor_folder(realtor)
    a = address_folder(address, words)
    d = shoot.strftime(DATE_FMT)

    raw_root = base / RAW_PARENT / r / a / d
    final_root = base / FINAL_PARENT / r / a / d

    targets = [raw_root / sub for sub in RAW_SUBFOLDERS]
    targets += [final_root / sub for sub in FINAL_SUBFOLDERS]

    created = 0
    for t in targets:
        existed = t.exists()
        if not dry_run:
            t.mkdir(parents=True, exist_ok=True)
        if not existed:
            created += 1
    return raw_root, final_root, created


def print_tree(raw_root: Path, final_root: Path) -> None:
    print(f"\n  {RAW_PARENT}/{raw_root.parent.parent.name}/{raw_root.parent.name}/{raw_root.name}/")
    for sub in RAW_SUBFOLDERS:
        print(f"      {sub}/")
    print(f"  {FINAL_PARENT}/{final_root.parent.parent.name}/{final_root.parent.name}/{final_root.name}/")
    for sub in FINAL_SUBFOLDERS:
        print(f"      {sub}/")


def prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        val = input(f"{label}{suffix}: ").strip()
    except EOFError:
        val = ""
    return val or default


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description="Create the standard raw + final folder structure for a shoot.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--realtor", help="Realtor first & last name, e.g. \"John Smith\"")
    p.add_argument("--address", help="Property address, e.g. \"2719 Fort Worth Street, Sarasota\"")
    p.add_argument("--date", help="Shoot date (default today). e.g. 2026-06-26, 06-26, 6/26/2026")
    p.add_argument("--base", default=DEFAULT_BASE, help=f"Folder that holds 'Real Estate' and 'Final' (default: {DEFAULT_BASE})")
    p.add_argument("--words", type=int, default=ADDRESS_WORDS, help=f"Leading address words for the folder (default {ADDRESS_WORDS})")
    p.add_argument("--open", action="store_true", help="Open the raw folder in your file manager when done")
    p.add_argument("--dry-run", action="store_true", help="Preview only; create nothing")
    args = p.parse_args(argv)

    # Fill any missing required values interactively.
    realtor = args.realtor or prompt("Realtor (first & last name)")
    address = args.address or prompt("Property address")
    if not realtor or not address:
        print("Realtor and address are required.", file=sys.stderr)
        return 1
    date_in = args.date if args.date is not None else prompt("Shoot date", "today")

    try:
        shoot = parse_date(date_in)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    base = Path(args.base).expanduser()

    raw_root, final_root, created = build_job(
        base, realtor, address, shoot, args.words, args.dry_run
    )

    tag = "Would create" if args.dry_run else "Created"
    print(f"{tag} job folders under: {base}")
    print_tree(raw_root, final_root)
    if not args.dry_run:
        skipped = len(RAW_SUBFOLDERS) + len(FINAL_SUBFOLDERS) - created
        note = f" ({skipped} already existed)" if skipped else ""
        print(f"\n{created} new folder(s) created{note}.")
        print(f"Raw:   {raw_root}")
        print(f"Final: {final_root}")

    if args.open and not args.dry_run:
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(raw_root))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                os.system(f'open "{raw_root}"')
            else:
                os.system(f'xdg-open "{raw_root}"')
        except Exception as e:  # pragma: no cover — convenience only
            print(f"(could not open folder: {e})", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
