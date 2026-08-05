#!/usr/bin/env python3
"""
LF Property Media — photo filer.

Drop a whole card's worth of photos into a shoot's job folder, then run this and it
sorts every file into the right subfolder. It finds the job by address (you don't have
to remember the realtor or the date), classifies each file by name/type, and moves it.

Two stages:
  raw   -> Real Estate/<Realtor>/<date address>/   into  Photos · Drone · 360 · Video
  final -> Final/<Realtor>/<date address>/          into  Home · Aerial · Amenities · Video · 360 · Floorplan

Usage
-----
  python tools/file-photos.py --address "2719 Fort Worth"                 # sort raw, in place
  python tools/file-photos.py --address "2719 Fort Worth" --stage final   # sort edited photos
  python tools/file-photos.py --address "2719 Fort Worth" --source "C:/Users/joshu/Downloads/card"
  python tools/file-photos.py --address "2719 Fort Worth" --dry-run       # preview, move nothing
  python tools/file-photos.py --address "2719 Fort Worth" --copy          # copy instead of move

By default it sorts the loose files already sitting in the job folder — so the natural
flow is: dump the photos into that folder, then run this. Point --source at another
folder (your Downloads, the card) to pull from there instead. Always safe to --dry-run
first; it never overwrites and never touches files already inside a subfolder.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

DEFAULT_BASE = os.environ.get("LF_JOBS_BASE") or str(Path.home())

STAGE = {
    "raw":   {"parent": "Real Estate", "subs": ["Photos", "Drone", "360", "Video"]},
    "final": {"parent": "Final",       "subs": ["Home", "Aerial", "Amenities", "Video", "360", "Floorplan"]},
}

PHOTO_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".heic", ".webp", ".avif",
             ".dng", ".arw", ".cr2", ".cr3", ".nef", ".raf", ".rw2", ".orf"}
VIDEO_EXT = {".mp4", ".mov", ".avi", ".m4v", ".mkv", ".insv"}
PANO_EXT = {".insp"}
DOC_EXT = {".pdf"}


def norm(s: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace — for fuzzy address matching."""
    out = "".join(c if (c.isalnum() or c.isspace()) else " " for c in s.lower())
    return " ".join(out.split())


def classify(filename: str, stage: str) -> str | None:
    """Destination subfolder for a file, or None to leave it where it is.

    Rules are filename/extension based — reliable for drone (DJI_/'drone'), video, 360
    (Insta360 .insp/.insv or '360'/'pano' in the name), and floor plans. Everything else
    that's a photo lands in the catch-all (Photos for raw, Home for final).
    """
    name = filename.lower()
    ext = os.path.splitext(name)[1]
    if ext in VIDEO_EXT:
        return "Video"
    if ext in PANO_EXT or "360" in name or "pano" in name or "equirect" in name:
        return "360"
    if stage == "final" and (ext in DOC_EXT or "floor" in name or "floorplan" in name):
        return "Floorplan"
    if name.startswith("dji_") or "drone" in name or "aerial" in name:
        return "Aerial" if stage == "final" else "Drone"
    if ext in PHOTO_EXT:
        return "Home" if stage == "final" else "Photos"
    return None


def find_job_folder(base: Path, parent: str, address: str) -> Path:
    """Locate the <date address> job folder under base/<parent>/<realtor>/ by address."""
    root = base / parent
    if not root.exists():
        raise FileNotFoundError(
            f"{root} doesn't exist yet — create the job first with new-job.py.")
    key = norm(address)
    matches = []
    for realtor_dir in root.iterdir():
        if not realtor_dir.is_dir():
            continue
        for job_dir in realtor_dir.iterdir():
            if job_dir.is_dir() and key in norm(job_dir.name):
                matches.append(job_dir)
    if not matches:
        raise FileNotFoundError(
            f"No '{parent}' job folder matching \"{address}\" under {root}.")
    if len(matches) > 1:
        listing = "\n".join(f"  - {m.relative_to(base)}" for m in matches)
        raise ValueError(
            f"More than one job matches \"{address}\":\n{listing}\nUse a more specific address.")
    return matches[0]


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description="Sort dumped photos into a shoot's job subfolders.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--address", required=True, help='Property address, e.g. "2719 Fort Worth"')
    p.add_argument("--stage", choices=["raw", "final"], default="raw",
                   help="raw = Real Estate folders (default); final = Final folders")
    p.add_argument("--source", help="Folder to pull files from (default: the job folder itself)")
    p.add_argument("--base", default=DEFAULT_BASE, help=f"Jobs base (default: {DEFAULT_BASE})")
    p.add_argument("--copy", action="store_true", help="Copy instead of move")
    p.add_argument("--dry-run", action="store_true", help="Preview only; move/copy nothing")
    args = p.parse_args(argv)

    base = Path(args.base).expanduser()
    cfg = STAGE[args.stage]

    try:
        job = find_job_folder(base, cfg["parent"], args.address)
    except (FileNotFoundError, ValueError) as e:
        print(str(e), file=sys.stderr)
        return 1

    source = Path(args.source).expanduser() if args.source else job
    if not source.exists():
        print(f"Source folder not found: {source}", file=sys.stderr)
        return 1

    # Gather loose files in the source (skip anything already inside a subfolder).
    plan: dict[str, list[Path]] = {}
    skipped: list[str] = []
    for f in source.iterdir():
        if not f.is_file():
            continue
        dest = classify(f.name, args.stage)
        if dest is None:
            skipped.append(f.name)
        else:
            plan.setdefault(dest, []).append(f)

    if not plan:
        print(f"No photos to file in {source}.")
        if skipped:
            print(f"({len(skipped)} non-photo file(s) left alone.)")
        return 0

    verb = "Would file" if args.dry_run else ("Copied" if args.copy else "Filed")
    print(f"{'(dry run) ' if args.dry_run else ''}Job: {job}")
    if source != job:
        print(f"Pulling from: {source}")

    moved = 0
    for sub in cfg["subs"]:
        items = plan.get(sub, [])
        if not items:
            continue
        dest_dir = job / sub
        if not args.dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n  {sub}/  ({len(items)})")
        for f in sorted(items, key=lambda x: x.name):
            print(f"      {f.name}")
            if not args.dry_run:
                target = dest_dir / f.name
                if args.copy:
                    shutil.copy2(str(f), str(target))
                else:
                    shutil.move(str(f), str(target))
            moved += 1

    folders_used = len([s for s in cfg["subs"] if plan.get(s)])
    print(f"\n{verb} {moved} file(s) into {folders_used} folder(s).")
    if skipped:
        shown = ", ".join(skipped[:5]) + ("..." if len(skipped) > 5 else "")
        print(f"Left {len(skipped)} non-photo file(s) alone: {shown}")
    if args.stage == "final" and plan.get("Home"):
        print("Note: amenity shots read the same as interior shots by filename, so they "
              "went to Home/. Move any amenities into Amenities/ if you separate them.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
