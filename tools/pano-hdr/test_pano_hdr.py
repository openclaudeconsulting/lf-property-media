"""Self-contained tests for pano_hdr.py.

Builds synthetic bracketed panoramas in a temp directory -- a room-like scene
with a blown window and a dark corner, rendered at five exposures the way a
camera would -- then runs the real pipeline over them and checks the things
that would actually ruin a tour: wrong 360 metadata, a seam down the wrap edge,
blown windows, crushed shadows, quality lost to labelling.

    python tools/pano-hdr/test_pano_hdr.py
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import pano_hdr as P  # noqa: E402

SCRIPT = Path(__file__).parent / "pano_hdr.py"
Image.MAX_IMAGE_PIXELS = None

W, H = 2400, 1200
N_POSITIONS = 3
BRACKET = 5
STOPS = [-2.0, -1.0, 0.0, 1.0, 2.0]

_failures: list[str] = []
_checks = 0


def check(name: str, ok: bool, detail: str = "") -> bool:
    global _checks
    _checks += 1
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{'  ' + detail if detail else ''}")
    if not ok:
        _failures.append(name)
    return ok


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True)


# ---------------------------------------------------------------- fixtures

def scene(seed: int) -> np.ndarray:
    """A room in linear light. Built from functions of longitude so the left
    and right edges are genuinely continuous -- that is what makes the seam
    test meaningful."""
    rng = np.random.default_rng(seed)
    lon = np.linspace(0, 2 * np.pi, W, endpoint=False)[None, :]
    lat = np.linspace(np.pi / 2, -np.pi / 2, H)[:, None]

    walls = 0.05 + 0.03 * np.sin(lon * 4 + seed) + 0.02 * np.cos(lon * 7)
    vertical = 0.6 + 0.5 * np.clip(lat / (np.pi / 2), -1, 1)
    base = walls * vertical

    # Daylight through a window, some 200x brighter than the interior.
    offset = (lon - (1.2 + seed * 0.9) + np.pi) % (2 * np.pi) - np.pi
    window = np.exp(-(offset ** 2) / 0.05) * np.exp(-((lat - 0.15) ** 2) / 0.08)
    # A corner only the longest exposure sees into.
    corner_off = (lon - 4.5 + np.pi) % (2 * np.pi) - np.pi
    corner = np.exp(-(corner_off ** 2) / 0.3) * np.exp(-((lat + 0.5) ** 2) / 0.2)

    lit = base * (1 - 0.85 * corner) + window * 12.0
    rgb = np.stack([lit * 1.04, lit, lit * 0.92], axis=-1)  # tungsten cast
    rgb += rng.normal(0, 0.0008, rgb.shape)
    return np.clip(rgb, 0, None).astype(np.float32)


def encode(linear: np.ndarray) -> np.ndarray:
    x = np.clip(linear, 0, 1)
    srgb = np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055)
    return (srgb * 255 + 0.5).astype(np.uint8)


def build_equirect_fixtures(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    t0 = datetime(2026, 8, 5, 14, 30, 0)
    for pos in range(N_POSITIONS):
        base = scene(pos)
        for i, stop in enumerate(STOPS):
            stamp = t0 + timedelta(seconds=pos * 90 + i * 1.2)
            exif = Image.Exif()
            exif[0x0132] = stamp.strftime("%Y:%m:%d %H:%M:%S")
            exif[0x8769] = {0x9003: stamp.strftime("%Y:%m:%d %H:%M:%S"),
                            0x9204: stop}
            Image.fromarray(encode(base * (2.0 ** stop) * 3.0)).save(
                dest / f"IMG_20260805_{pos:03d}_{i:02d}.jpg", "JPEG",
                quality=95, exif=exif.tobytes())


def build_fisheye_fixtures(dest: Path) -> None:
    """Two circles side by side with black corners, as .insp."""
    dest.mkdir(parents=True, exist_ok=True)
    w, h = 1200, 600
    yy, xx = np.mgrid[0:h, 0:w]
    frame = np.zeros((h, w, 3), np.float32)
    for cx in (w // 4, 3 * w // 4):
        r = np.hypot(xx - cx, yy - h / 2) / (h / 2)
        inside = r < 0.98
        lit = np.stack([0.35 + 0.25 * np.sin(r * 8), 0.35 + 0.2 * np.cos(r * 6),
                        0.30 + 0.2 * np.sin(r * 5)], axis=-1)
        frame[inside] = lit[inside]
    for i, stop in enumerate(STOPS):
        Image.fromarray((np.clip(frame * 2.0 ** stop, 0, 1) * 255).astype(np.uint8)
                        ).save(dest / f"IMG_000_{i:02d}.insp", "JPEG", quality=92)


# ---------------------------------------------------------------- helpers

def xmp_of(path: Path) -> str | None:
    data = path.read_bytes()
    i = 2
    while i < len(data) - 1 and data[i] == 0xFF:
        marker = data[i + 1]
        if marker in (0xD9, 0xDA):
            break
        length = int.from_bytes(data[i + 2:i + 4], "big")
        body = data[i + 4:i + 2 + length]
        if marker == 0xE1 and body.startswith(P.XMP_SIG):
            return body[len(P.XMP_SIG):].decode("utf-8", "replace")
        i += 2 + length
    return None


def tag(text: str, name: str) -> str | None:
    m = re.search(rf"<{name}>(.*?)</{name}>", text)
    return m.group(1) if m else None


def seam_ratio(img: np.ndarray) -> float:
    """How discontinuous the wrap edge is, relative to an ordinary column
    step. ~1 means the seam is invisible."""
    seam = float(np.abs(img[:, 0] - img[:, -1]).mean())
    interior = float(np.abs(img[:, 1:-1] - img[:, 2:]).mean())
    return seam / max(interior, 1e-9)


def as_float(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path), dtype=np.float32) / 255.0


# ---------------------------------------------------------------- the tests

def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="pano_hdr_test_"))
    try:
        src, out = tmp / "src", tmp / "out"
        build_equirect_fixtures(src)

        print("\n--- grouping ---")
        proc = run("scan", str(src))
        check("scan succeeds", proc.returncode == 0, proc.stderr.strip()[:120])
        check(f"{N_POSITIONS * BRACKET} frames group into {N_POSITIONS} panoramas",
              f"-> {N_POSITIONS} panorama" in proc.stdout)

        print("\n--- build ---")
        proc = run("build", str(src), str(out))
        check("build succeeds", proc.returncode == 0, proc.stderr.strip()[:200])
        made = sorted(out.glob("pano_*.jpg"))
        check(f"wrote {N_POSITIONS} panoramas", len(made) == N_POSITIONS,
              f"got {len(made)}")
        if not made:
            raise SystemExit("nothing to test against")
        first = made[0]

        print("\n--- 360 metadata (what CloudPano reads) ---")
        text = xmp_of(first)
        check("XMP is present in an APP1 segment", text is not None)
        if text:
            w, h = Image.open(first).size
            check("ProjectionType is equirectangular",
                  tag(text, "GPano:ProjectionType") == "equirectangular")
            check("UsePanoramaViewer is set",
                  tag(text, "GPano:UsePanoramaViewer") == "True")
            check("full pano size matches the pixels",
                  tag(text, "GPano:FullPanoWidthPixels") == str(w)
                  and tag(text, "GPano:FullPanoHeightPixels") == str(h),
                  f"{w}x{h}")
            check("cropped area covers the whole frame",
                  tag(text, "GPano:CroppedAreaImageWidthPixels") == str(w)
                  and tag(text, "GPano:CroppedAreaLeftPixels") == "0")
            check("output is exactly 2:1", abs(w / h - 2.0) < 1e-6, f"{w}x{h}")

        print("\n--- seam continuity across the wrap ---")
        built = as_float(first)
        ratio = seam_ratio(built)
        check("wrap edge is no worse than an ordinary column step",
              ratio < 2.5, f"ratio {ratio:.2f}")

        print("\n--- dynamic range ---")
        base = as_float(src / "IMG_20260805_000_02.jpg")  # the 0 EV frame
        lum_base, lum_out = base.mean(axis=2), built.mean(axis=2)
        blown_before = float((lum_base > 0.995).mean())
        blown_after = float((lum_out > 0.995).mean())
        check("blown highlights are recovered", blown_after < blown_before,
              f"{blown_before*100:.2f}% -> {blown_after*100:.2f}%")
        check("nothing clips to pure white (soft shoulder holds)",
              float((lum_out >= 0.999).mean()) < 0.0005)
        dark = lum_base < 0.06
        check("deep shadows are lifted, not crushed",
              bool(dark.any()) and lum_out[dark].mean() > lum_base[dark].mean(),
              f"{lum_base[dark].mean():.4f} -> {lum_out[dark].mean():.4f}")
        check("overall exposure is lifted", lum_out.mean() > lum_base.mean(),
              f"{lum_base.mean():.4f} -> {lum_out.mean():.4f}")

        def rb(a):
            m = a.reshape(-1, 3).mean(axis=0)
            return float(m[0] / m[2])
        check("tungsten cast is pulled toward neutral",
              abs(rb(built) - 1) < abs(rb(base) - 1),
              f"R/B {rb(base):.3f} -> {rb(built):.3f}")

        print("\n--- both fusion engines agree ---")
        stack = [P.read_image(f) for f in
                 sorted(src.glob("IMG_20260805_000_*.jpg"))]
        lum_fuse = P.fuse_luminosity(stack, True)
        mer_fuse = P.fuse_mertens(stack, True)
        check("engines land within 5% on overall exposure",
              abs(float(lum_fuse.mean()) - float(mer_fuse.mean())) < 0.05,
              f"{float(lum_fuse.mean()):.4f} vs {float(mer_fuse.mean()):.4f}")
        check("mertens wrap padding clears its seam",
              seam_ratio(mer_fuse) < 2.5, f"ratio {seam_ratio(mer_fuse):.2f}")
        check("luminosity engine holds shadow detail better than mertens",
              float(P.luminance(lum_fuse)[dark].mean())
              > float(P.luminance(mer_fuse)[dark].mean()),
              f"{float(P.luminance(lum_fuse)[dark].mean()):.4f} vs "
              f"{float(P.luminance(mer_fuse)[dark].mean()):.4f}")

        print("\n--- presets ---")
        means = {}
        for preset in ("flat", "natural", "bright"):
            pdir = tmp / f"out_{preset}"
            run("build", str(src), str(pdir), "--preset", preset)
            means[preset] = float(as_float(pdir / "pano_01.jpg").mean())
        check("flat < natural < bright",
              means["flat"] < means["natural"] < means["bright"],
              " < ".join(f"{k} {v:.4f}" for k, v in means.items()))

        print("\n--- resize and overrides ---")
        rdir = tmp / "out_resize"
        run("build", str(src), str(rdir), "--max-width", "1024", "--nadir", "25")
        size = Image.open(rdir / "pano_01.jpg").size
        check("--max-width downscales and keeps 2:1", size == (1024, 512),
              f"{size[0]}x{size[1]}")
        check("--nadir writes without error", (rdir / "pano_01.jpg").exists())

        print("\n--- labelling ---")
        before = (out / "pano_01.jpg").read_bytes()
        before_px = as_float(out / "pano_01.jpg")
        labels = tmp / "labels.json"
        labels.write_text(json.dumps({
            "pano_01.jpg": "Living Room",
            "pano_02.jpg": "Primary Bath",
            "pano_03.jpg": "Upstairs Bedroom 2"}), encoding="utf-8")
        proc = run("label", str(out), "--map", str(labels))
        check("label succeeds", proc.returncode == 0, proc.stderr.strip()[:120])
        renamed = out / "01-living-room.jpg"
        check("renamed with order prefix and slug", renamed.exists())
        check("preview follows the rename",
              (out / "_previews" / "01-living-room.jpg").exists())
        if renamed.exists():
            check("pixels are byte-identical (label is lossless)",
                  np.array_equal(as_float(renamed), before_px))
            text = xmp_of(renamed)
            check("room name lands in the title",
                  bool(text) and "Living Room" in text)
            check("GPano tags survive labelling",
                  bool(text) and tag(text, "GPano:ProjectionType") == "equirectangular")
            check("exactly one XMP block after labelling",
                  renamed.read_bytes().count(P.XMP_SIG) == 1)
            check("only metadata grew, image data untouched",
                  abs(len(renamed.read_bytes()) - len(before)) < 4096)
        man = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        check("manifest records label and sources",
              man["panoramas"][0]["label"] == "Living Room"
              and len(man["panoramas"][0]["sources"]) == BRACKET)

        print("\n--- fallbacks ---")
        noexif = tmp / "noexif"
        noexif.mkdir()
        for i, f in enumerate(sorted(src.glob("IMG_20260805_000_*.jpg"))):
            Image.open(f).save(noexif / f"shot_{i+1}.jpg", "JPEG", quality=92)
        proc = run("scan", str(noexif))
        check("missing EXIF falls back to filename order",
              "-> 1 panorama" in proc.stdout and "no EXIF capture time" in proc.stdout)

        partial = tmp / "partial"
        partial.mkdir()
        for i, f in enumerate(sorted(src.glob("IMG_20260805_000_*.jpg"))[:3]):
            Image.open(f).save(partial / f"p_{i+1}.jpg", "JPEG", quality=92)
        proc = run("build", str(partial), str(tmp / "out_partial"))
        check("an incomplete bracket set is refused, not silently processed",
              proc.returncode != 0 and "No complete bracket sets" in proc.stderr)

        fe_src, fe_out = tmp / "fisheye", tmp / "out_fisheye"
        build_fisheye_fixtures(fe_src)
        proc = run("build", str(fe_src), str(fe_out))
        check("dual-fisheye input is detected",
              "detected dual-fisheye" in proc.stdout)
        merged = fe_out / "merged_01.insp"
        check("fisheye output is a .insp for Studio, not a finished pano",
              merged.exists() and not list(fe_out.glob("pano_*.jpg")))
        if merged.exists():
            check("fisheye output carries NO 360 tags", xmp_of(merged) is None)

        # A dim room shot with an unpatched nadir has a black floor strip and a
        # ceiling nearly as dark, which looks exactly like a fisheye frame's
        # dark corners. What separates them is the horizon: this one is lit all
        # the way across, including at the seam.
        dark = np.full((600, 1200, 3), 0.03, np.float32)
        dark[150:480] = 0.28
        check("a dark room with a black nadir is NOT called dual-fisheye",
              not P.looks_like_dual_fisheye(dark))

        print("\n--- Studio DNG exports ---")
        check(".dng is an accepted input extension", ".dng" in P.READABLE_EXT)
        # Every frame of one tripod position shares the filename time field.
        # This is what holds the brackets together: Studio overwrites the DNG's
        # own timestamp with the *export* time, so grouping on file metadata
        # would interleave positions that were shot minutes apart.
        setA = [Path(f"IMG_20260608_100615_00_{n:03d}.dng") for n in range(20, 29)]
        setB = [Path(f"IMG_20260608_100734_00_{n:03d}.dng") for n in range(29, 38)]
        stampsA = {P.capture_time_from_name(p) for p in setA}
        stampsB = {P.capture_time_from_name(p) for p in setB}
        check("one bracket set shares a single filename timestamp",
              len(stampsA) == 1 and None not in stampsA)
        check("the next tripod position gets a different timestamp",
              len(stampsB) == 1 and stampsA != stampsB)
        check("the gap between positions exceeds the default --gap",
              (stampsB.pop() - stampsA.pop()).total_seconds() > 6.0)
        check("a non-Insta360 filename yields no timestamp",
              P.capture_time_from_name(Path("shot_1.jpg")) is None
              and P.capture_time_from_name(Path("IMG_20260805_000_02.jpg")) is None)
        check("a .dng never reports its own (export-time) metadata as capture time",
              P.read_capture_meta(Path("no_such_file.dng")) == (None, None)
              and P.read_capture_meta(setA[0])[0] == datetime(2026, 6, 8, 10, 6, 15))

        print("\n--- trailer splitting (the .insp metadata block) ---")
        plain = (out / "01-living-room.jpg").read_bytes()
        img_part, trailer = P.split_jpeg_trailer(plain)
        check("a plain JPEG splits with an empty trailer",
              trailer == b"" and img_part == plain)
        marked = plain + b"INSTA360_BLOCK_XYZ" * 4
        img_part, trailer = P.split_jpeg_trailer(marked)
        check("an appended block is recovered intact",
              img_part == plain and trailer == b"INSTA360_BLOCK_XYZ" * 4)

        print("\n" + "=" * 62)
        print(f"{_checks - len(_failures)}/{_checks} checks passed")
        for name in _failures:
            print(f"  FAILED: {name}")
        return 1 if _failures else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
