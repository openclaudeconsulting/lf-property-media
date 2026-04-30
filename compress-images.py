"""
One-shot compressor for the gallery photo library.

What it does:
  * Resizes any image whose long edge exceeds MAX_LONG_EDGE.
  * Converts PNGs to JPEGs (photos compress dramatically better as JPEG).
  * Re-encodes JPEGs at QUALITY=85 with progressive + optimize.
  * Strips EXIF / orientation metadata after applying any rotation.

The originals in this repo are 6000x4000 lightly-compressed Sony JPEGs at
2-21 MB each. Browsers display them in masonry cards rarely wider than
~600 px, so the original resolution is wasted bandwidth. After this script
they typically land in the 200-700 KB range, visually indistinguishable.

Run from the project root:
    python compress-images.py
"""
from pathlib import Path
from PIL import Image, ImageOps
import sys

ROOT = Path(__file__).parent / "images"
TARGETS = [ROOT / "interior", ROOT / "exterior", ROOT / "aerial"]
MAX_LONG_EDGE = 2400
JPEG_QUALITY = 85


def compress_one(src: Path):
    """Compress a single file in place. Returns (orig_bytes, new_bytes, new_path, was_renamed)."""
    orig_size = src.stat().st_size
    with Image.open(src) as img:
        img = ImageOps.exif_transpose(img)
        long_edge = max(img.size)
        if long_edge > MAX_LONG_EDGE:
            ratio = MAX_LONG_EDGE / long_edge
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        if img.mode != "RGB":
            img = img.convert("RGB")
        new_path = src.with_suffix(".jpg")
        img.save(new_path, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    was_renamed = src.suffix.lower() != ".jpg"
    if was_renamed and new_path != src and src.exists():
        src.unlink()
    return orig_size, new_path.stat().st_size, new_path, was_renamed


def main():
    total_before = 0
    total_after = 0
    renamed = []
    errors = []
    count = 0

    for tgt in TARGETS:
        if not tgt.is_dir():
            print(f"skip {tgt} (not a directory)")
            continue
        print(f"\n--- {tgt.name} ---")
        for src in sorted(tgt.iterdir()):
            if src.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                continue
            try:
                orig, new, path, was_renamed = compress_one(src)
                total_before += orig
                total_after += new
                count += 1
                pct = 100 * new / orig
                arrow = "->" if was_renamed else "  "
                print(f"  {src.name:<44} {orig/1e6:6.2f} MB {arrow} {new/1e6:6.2f} MB ({pct:5.1f}%)")
                if was_renamed:
                    renamed.append((src.name, path.name))
            except Exception as e:
                errors.append((src, e))
                print(f"  {src.name}: ERROR {e}", file=sys.stderr)

    print()
    print("=" * 60)
    if total_before:
        print(f"Files processed: {count}")
        print(f"Total before:    {total_before/1e6:8.1f} MB")
        print(f"Total after:     {total_after/1e6:8.1f} MB")
        print(f"Savings:         {(total_before-total_after)/1e6:8.1f} MB ({100 - 100*total_after/total_before:.1f}%)")
    if renamed:
        print(f"\nRenamed {len(renamed)} PNG -> JPG (update HTML refs):")
        for old, new in renamed:
            print(f"  {old} -> {new}")
    if errors:
        print(f"\nErrors: {len(errors)}")
        for path, e in errors:
            print(f"  {path}: {e}")


if __name__ == "__main__":
    main()
