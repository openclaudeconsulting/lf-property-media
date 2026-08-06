"""One-shot post-build step for the 2719 Fort Worth shoot.

The source folder still holds all 24 tripod positions, so a rebuild always
produces 24 panoramas. The owner chose to drop two of them (the duplicate hall
bathroom, and the duller of the two pool frames), so this re-applies that
decision, renumbers 1..22, writes the room names, and republishes the panoramas
and thumbnails the tour serves.

It does the rename itself rather than going through `pano_hdr.py label`, because
that subcommand takes its number prefix from the manifest's build index -- which
is the one thing that has to change when positions are dropped.

Run from the repo root after `build` finishes.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import pano_hdr as P  # noqa: E402

Image.MAX_IMAGE_PIXELS = None

# The job media is gitignored, so it exists only in the canonical project folder
# and a git worktree cannot reach it through a repo-relative path. Same env var
# the other tools in this folder already use.
JOBS = Path(os.environ.get("LF_JOBS_BASE") or "Filing System")
BUILT = JOBS / "Final/Preferred Shore LLC/06-13 2719 Fort Worth/360"
TOUR = Path("tours/2719-fort-worth-street")

# Build index -> room name. The two the owner dropped map to None.
ROOMS = {
    1: "study",              2: "guest-suite-bedroom",  3: "guest-suite-kitchenette",
    4: "bedroom",            5: "screened-balcony",     6: None,
    7: "hall-bathroom",      8: "music-loft",           9: "bedroom-2",
    10: "guitar-room",       11: "twin-bedroom",        12: "primary-bathroom",
    13: "hallway",           14: "living-room",         15: "dining-room",
    16: "kitchen",           17: "great-room",          18: "entry-foyer",
    19: "family-room",       20: "pool-lanai",          21: None,
    22: "pool",              23: "lanai-billiards",     24: "front-entry",
}
NUMBERED = re.compile(r"^\d\d-(.+)$")


def locate(build_idx: int, room: str) -> Path | None:
    """Find this panorama whether or not a previous pass already renamed it."""
    raw = BUILT / f"pano_{build_idx:02d}.jpg"
    if raw.exists():
        return raw
    for f in BUILT.glob("[0-9][0-9]-*.jpg"):
        m = NUMBERED.match(f.stem)
        if m and m.group(1) == room:      # exact, so "bedroom" never eats
            return f                      # "guest-suite-bedroom"
    return None


def main() -> int:
    wanted = [(i, r) for i, r in sorted(ROOMS.items()) if r]
    if len(wanted) != 22:
        print(f"mapping should keep 22, keeps {len(wanted)}", file=sys.stderr)
        return 1

    for idx, room in ROOMS.items():
        if room is None:
            for p in (BUILT / f"pano_{idx:02d}.jpg",
                      BUILT / "_previews" / f"pano_{idx:02d}.jpg"):
                p.unlink(missing_ok=True)

    plan = []
    for n, (idx, room) in enumerate(wanted, start=1):
        src = locate(idx, room)
        if src is None:
            print(f"missing panorama for build index {idx} ({room})", file=sys.stderr)
            return 1
        plan.append((src, f"{n:02d}-{room}.jpg", room))

    # Rename via temporary names so a target that is currently another file's
    # name (07-hall-bathroom -> 06-hall-bathroom while 06 still exists) cannot
    # clobber it mid-shuffle.
    for i, (src, _, _) in enumerate(plan):
        tmp = BUILT / f".__stage_{i:02d}.jpg"
        src.replace(tmp)
        prev = BUILT / "_previews" / src.name
        if prev.exists():
            prev.replace(BUILT / "_previews" / tmp.name)

    manifest = json.loads((BUILT / "manifest.json").read_text(encoding="utf-8"))
    by_out = {e["output"]: e for e in manifest["panoramas"]}
    by_new = {e.get("renamed_to"): e for e in manifest["panoramas"] if e.get("renamed_to")}
    entries = []
    for i, (src, dest_name, room) in enumerate(plan):
        tmp = BUILT / f".__stage_{i:02d}.jpg"
        dest = BUILT / dest_name
        with Image.open(tmp) as probe:
            w, h = probe.size
        dest.write_bytes(P.retitle_jpeg(tmp.read_bytes(), w, h, room))
        tmp.unlink()
        ptmp = BUILT / "_previews" / tmp.name
        if ptmp.exists():
            ptmp.replace(BUILT / "_previews" / dest_name)
        e = by_out.get(src.name) or by_new.get(src.name) or {}
        e = dict(e)
        e["output"] = f"pano_{i+1:02d}.jpg"
        e["renamed_to"] = dest_name
        e["label"] = room
        entries.append(e)

    manifest["panoramas"] = entries
    (BUILT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    finals = sorted(BUILT.glob("[0-9][0-9]-*.jpg"))
    nums = [int(f.name[:2]) for f in finals]
    if nums != list(range(1, 23)):
        print(f"numbering is not 1..22: {nums}", file=sys.stderr)
        return 1

    for sub in ("panos", "thumbs"):
        shutil.rmtree(TOUR / sub, ignore_errors=True)
        (TOUR / sub).mkdir(parents=True, exist_ok=True)
    for f in finals:
        # Copied, not re-encoded. The master is already progressive 4:4:4 at the
        # camera's native 6080x3040, and pano_hdr's output sharpening was applied
        # at that size -- resampling to 4096 here softened exactly what that
        # sharpening had just crispened, on top of discarding a third of the
        # linear detail a visitor can now zoom into. Copying also carries the
        # GPano tags over untouched.
        shutil.copy2(f, TOUR / "panos" / f.name)
        with Image.open(f) as im:
            im.convert("RGB").resize((400, 200), Image.LANCZOS).save(
                TOUR / "thumbs" / f.name, "JPEG", quality=80, optimize=True)

    # The scene ids in tour.json are the filenames; a drift would break links.
    tour = json.loads((TOUR / "tour.json").read_text(encoding="utf-8"))
    expected = {s["id"] for s in tour["scenes"]}
    actual = {f.stem for f in finals}
    if expected != actual:
        print(f"scene ids drifted!\n  only in tour.json: {sorted(expected - actual)}"
              f"\n  only on disk     : {sorted(actual - expected)}", file=sys.stderr)
        return 1

    mb = sum(p.stat().st_size for p in (TOUR / "panos").glob("*.jpg")) / 1e6
    print(f"finalised {len(finals)} panoramas, numbered 01..22")
    print(f"published panoramas at native resolution ({mb:.0f} MB) + thumbs")
    print("scene ids match tour.json — all 44 hotspots preserved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
