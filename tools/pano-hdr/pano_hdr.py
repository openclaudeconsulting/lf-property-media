"""
pano_hdr.py -- bracketed 360 photo merger + real-estate grade for CloudPano.

Takes the bracketed exposures an Insta360 camera shoots for each position
(5 by default), fuses them into one clean panorama, applies a light real-estate
grade, tags it as a 360 image, and writes a CloudPano-ready JPEG.

Three subcommands:

    python pano_hdr.py scan  <input_dir>
        Group the files into bracket sets and print what it found.
        Run this first -- it touches nothing.

    python pano_hdr.py build <input_dir> <output_dir> [options]
        Fuse + grade + tag. Writes pano_01.jpg, pano_02.jpg, ...
        plus _previews/ (horizon strips for identifying rooms)
        and manifest.json.

    python pano_hdr.py label <output_dir> --map labels.json
        Rename the outputs to room names and write the name into the
        file's title metadata. labels.json is {"pano_01.jpg": "living-room"}.

Input should be *stitched equirectangular* frames (2:1) -- export the brackets
out of Insta360 Studio first. Studio exports JPEG/TIFF from .insp sources and
16-bit linear DNG from .dng sources; all of those are read here. Raw dual-fisheye
.insp files are detected and handled in --fisheye mode, but see README for the
caveat, and raw dual-fisheye .dng straight off the camera is refused outright --
it has to go through Studio to be stitched.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None  # 72 MP panoramas are normal here, not a decompression bomb

EPS = 1e-6
READABLE_EXT = {".jpg", ".jpeg", ".tif", ".tiff", ".png", ".insp", ".dng"}

# ---------------------------------------------------------------- grade presets

@dataclass
class Grade:
    """Everything applied after the exposures are fused. All values are gentle
    by design -- the goal is to match the look of the operator's existing
    camera-shot listing photos, not to produce an 'HDR' image."""
    wb: float = 0.50        # 0..1 strength of the neutral white-balance pull
    warmth: float = 0.0     # positive nudges toward warm after neutralising
    ev: float = 0.12        # exposure, in stops
    highlights: float = 0.08
    shadows: float = 0.10
    contrast: float = 0.05  # gentle S-curve, never clips
    vibrance: float = 0.06  # saturation boost, weighted toward flat colours
    clarity: float = 0.08   # wide-radius local contrast
    shoulder: float = 0.90  # soft-clip knee; keeps windows off pure white
    sharpen: float = 0.35   # output sharpening, applied after the final resize


PRESETS = {
    # Default. Matches "slightly increase the highlights, slightly increase
    # the exposure" -- a clean lift, nothing stylised.
    "natural": Grade(),
    # A touch brighter and airier, for dim interiors or north-facing rooms.
    "bright": Grade(ev=0.28, highlights=0.14, shadows=0.18, contrast=0.07,
                    vibrance=0.10, clarity=0.10),
    # Fuse only. No colour or tone changes at all -- use when the panorama is
    # going into Lightroom afterwards.
    "flat": Grade(wb=0.0, warmth=0.0, ev=0.0, highlights=0.0, shadows=0.0,
                  contrast=0.0, vibrance=0.0, clarity=0.0, shoulder=1.0,
                  sharpen=0.0),
}


# ---------------------------------------------------------------- colour maths

def srgb_to_linear(x: np.ndarray) -> np.ndarray:
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0.0, None)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * (x ** (1 / 2.4)) - 0.055)


def luminance(rgb: np.ndarray) -> np.ndarray:
    return (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2])


def smoothstep(edge0: float, edge1: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - edge0) / max(edge1 - edge0, EPS), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def wrap_blur(img: np.ndarray, sigma: float, wrap: bool) -> np.ndarray:
    """Gaussian blur that respects the equirectangular seam.

    The left and right edges of an equirectangular panorama are the same place
    in the room. Blurring with ordinary edge padding leaves a visible vertical
    line at the stitch once it is wrapped onto a sphere, so pad horizontally by
    wrapping the image around itself first.
    """
    if sigma <= 0:
        return img
    ksize = int(sigma * 4) | 1
    if not wrap:
        return cv2.GaussianBlur(img, (ksize, ksize), sigma,
                                borderType=cv2.BORDER_REPLICATE)
    pad = min(ksize, img.shape[1] // 2)
    wide = np.concatenate([img[:, -pad:], img, img[:, :pad]], axis=1)
    wide = cv2.GaussianBlur(wide, (ksize, ksize), sigma,
                            borderType=cv2.BORDER_REPLICATE)
    return wide[:, pad:pad + img.shape[1]]


# ---------------------------------------------------------------- file reading

def read_dng(path: Path) -> np.ndarray:
    """Read an Insta360-Studio-exported equirectangular DNG to float32 RGB 0..1.

    Studio writes 16-bit *linear* DNG when the source frames were raw: already
    stitched and demosaiced, but with no white balance, no gamma and still in
    camera colour space. libraw (via rawpy) applies the shot white balance and
    the camera->sRGB matrix, which hand-rolling gets subtly wrong.

    no_auto_bright is essential: rawpy would otherwise stretch each bracket
    frame to full range independently, destroying the exposure differences that
    the whole fuse depends on.
    """
    try:
        import rawpy
    except ImportError:
        raise ValueError("reading .dng needs rawpy -- pip install rawpy") from None
    with rawpy.imread(str(path)) as raw:
        # A camera-original dual-fisheye frame still carries its Bayer mosaic.
        # Those are not panoramas and must go through Studio first; decoding one
        # here would silently produce a 1:2 portrait "panorama" that wraps to
        # garbage on a sphere.
        if raw.raw_pattern is not None:
            raise ValueError(
                "this is a raw dual-fisheye DNG straight off the camera, not a "
                "stitched panorama -- export it from Insta360 Studio first "
                "(Export > Export 360 photo, Original Resolution)")
        rgb = raw.postprocess(output_bps=16, use_camera_wb=True,
                              no_auto_bright=True, gamma=(2.222, 4.5),
                              output_color=rawpy.ColorSpace.sRGB)
    return np.ascontiguousarray(rgb.astype(np.float32) / np.float32(65535.0))


def read_image(path: Path) -> np.ndarray:
    """Read any of jpg/tif/png/insp/dng to float32 RGB in 0..1.

    Goes through imdecode rather than imread so that non-ASCII paths work on
    Windows, and so that .insp files decode as the JPEG they actually are.
    """
    if path.suffix.lower() == ".dng":
        return read_dng(path)
    raw = np.fromfile(str(path), dtype=np.uint8)
    if raw.size == 0:
        raise ValueError("file is empty")
    img = cv2.imdecode(raw, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError("could not decode (RAW/DNG needs exporting to JPEG or "
                         "TIFF from Insta360 Studio first)")
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    if img.shape[2] == 4:
        img = img[:, :, :3]
    scale = 65535.0 if img.dtype == np.uint16 else 255.0
    img = img[:, :, ::-1].astype(np.float32) / np.float32(scale)
    return np.ascontiguousarray(img)


# Insta360 names every frame IMG_<date>_<time>_<seq>_<n>. The time field is
# stamped once per tripod position, so all the frames of one bracket share it --
# which makes it a better grouping key than any timestamp, not just a fallback.
_INSTA_NAME = re.compile(r"IMG_(\d{8})_(\d{6})_")


def capture_time_from_name(path: Path) -> datetime | None:
    m = _INSTA_NAME.match(path.name)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
    except ValueError:
        return None


def read_capture_meta(path: Path) -> tuple[datetime | None, float | None]:
    """(capture time, exposure-bias in stops) from EXIF, either may be None."""
    if path.suffix.lower() == ".dng":
        # Studio stamps its *export* time into the exported DNG and drops
        # DateTimeOriginal entirely, so the file's own timestamp says when it
        # was converted, not when it was shot. Grouping on that would scatter
        # the brackets. The filename still carries the real capture time.
        return capture_time_from_name(path), None
    try:
        with Image.open(path) as im:
            exif = im.getexif()
            sub = exif.get_ifd(0x8769) if exif else {}
    except Exception:
        return None, None
    stamp = None
    for tag in (0x9003, 0x9004, 0x0132):  # DateTimeOriginal, Digitized, DateTime
        val = sub.get(tag) or (exif.get(tag) if exif else None)
        if val:
            try:
                stamp = datetime.strptime(str(val)[:19], "%Y:%m:%d %H:%M:%S")
                break
            except ValueError:
                continue
    bias = None
    raw_bias = sub.get(0x9204)
    if raw_bias is not None:
        try:
            bias = float(raw_bias)
        except (TypeError, ValueError):
            bias = None
    return stamp, bias


def natural_key(path: Path):
    """Sort so IMG_2 lands before IMG_10."""
    return [int(t) if t.isdigit() else t.lower()
            for t in re.split(r"(\d+)", path.name)]


# ---------------------------------------------------------------- bracket grouping

@dataclass
class Group:
    index: int
    files: list[Path]
    note: str = ""


def group_brackets(files: list[Path], size: int, gap: float) -> tuple[list[Group], list[str]]:
    """Split a flat list of frames into bracket sets.

    Primary signal is capture time -- the frames in one bracket are shot within
    a couple of seconds of each other, and there is a much longer gap while the
    operator walks to the next position. Falls back to slicing the sorted list
    into fixed runs when the files carry no usable EXIF timestamps.
    """
    warnings: list[str] = []
    stamped = [(f, read_capture_meta(f)[0]) for f in files]
    have_time = sum(1 for _, t in stamped if t is not None)

    if have_time < len(files):
        fallback = ("filename order" if have_time == 0
                    else "file modification time")
        warnings.append(
            f"{len(files) - have_time} of {len(files)} files have no EXIF capture "
            f"time; ordering those by {fallback}. Check the grouping below.")

    if have_time == 0:
        ordered = sorted(files, key=natural_key)
        runs = [ordered[i:i + size] for i in range(0, len(ordered), size)]
    else:
        ordered = sorted(
            stamped,
            key=lambda p: (p[1] or datetime.fromtimestamp(p[0].stat().st_mtime),
                           natural_key(p[0])))
        runs, current, prev = [], [], None
        for path, stamp in ordered:
            stamp = stamp or datetime.fromtimestamp(path.stat().st_mtime)
            if prev is not None and (stamp - prev).total_seconds() > gap:
                runs.append(current)
                current = []
            current.append(path)
            prev = stamp
        if current:
            runs.append(current)

        # A too-long run means the gap threshold merged two positions shot
        # back to back. Re-slice those by the expected bracket size.
        resliced = []
        for run in runs:
            if len(run) > size and len(run) % size == 0:
                resliced += [run[i:i + size] for i in range(0, len(run), size)]
            else:
                resliced.append(run)
        runs = resliced

    groups = []
    for i, run in enumerate(runs, start=1):
        note = "" if len(run) == size else f"expected {size} frames, found {len(run)}"
        groups.append(Group(index=i, files=run, note=note))
    return groups, warnings


# ---------------------------------------------------------------- layout detect

def looks_like_dual_fisheye(img: np.ndarray) -> bool:
    """Dual-fisheye frames have two dark-cornered circles side by side; a
    stitched equirectangular frame fills its corners with real image data."""
    h, w = img.shape[:2]
    if not (1.6 < w / h < 2.4):
        return False
    box_h, box_w = max(h // 12, 1), max(w // 24, 1)
    corners = [
        img[:box_h, :box_w], img[:box_h, w // 2 - box_w:w // 2],
        img[-box_h:, :box_w], img[-box_h:, w // 2 - box_w:w // 2],
        img[:box_h, w // 2:w // 2 + box_w], img[:box_h, -box_w:],
        img[-box_h:, w // 2:w // 2 + box_w], img[-box_h:, -box_w:],
    ]
    corner_level = float(np.mean([c.mean() for c in corners]))
    centre = float(img[h // 3:2 * h // 3].mean())
    if not (corner_level < 0.10 and corner_level < centre * 0.25):
        return False

    # Dark corners alone are not enough: a dim room shot with an unpatched
    # nadir has a black floor strip and can have a ceiling almost as dark, which
    # is exactly what the test above is looking for. The horizon tells the two
    # apart. A dual-fisheye frame is two circles, so its mid-height row falls to
    # black where each circle ends -- at x = 0, w/2 and w -- while staying lit
    # at the circle centres. An equirectangular frame carries real image data
    # straight across that row and wraps continuously at the seam.
    half = max(h // 200, 1)
    band = img[h // 2 - half:h // 2 + half]
    edge = max(w // 200, 1)
    seam = float(np.mean([band[:, :edge].mean(),
                          band[:, w // 2 - edge:w // 2 + edge].mean(),
                          band[:, -edge:].mean()]))
    lobe = float(np.mean([band[:, w // 4 - edge:w // 4 + edge].mean(),
                          band[:, 3 * w // 4 - edge:3 * w // 4 + edge].mean()]))
    return seam < lobe * 0.35


# ---------------------------------------------------------------- exposure fusion

MERTENS_PAD = 0.25  # measured: 0.0 leaves a 10x seam, 0.125 a 2.4x one, 0.25 clears it


def fuse_mertens(stack: list[np.ndarray], wrap: bool) -> np.ndarray:
    """OpenCV's Mertens exposure fusion.

    Two corrections are needed to make it safe for equirectangular input:

    * MergeMertens always rescales its input by 1/255 -- it assumes 8-bit
      frames even when handed floats -- so pre-multiply to cancel that out.
      Scaling rather than casting to uint8 keeps the extra precision of
      16-bit TIFF sources through the fusion.
    * Its Laplacian pyramid pads at the frame border, which lays a visible
      vertical line down the panorama's wrap seam. Wrapping the frames around
      themselves first and cropping afterwards moves that artefact into
      padding that gets thrown away.
    """
    width = stack[0].shape[1]
    pad = int(width * MERTENS_PAD) if wrap else 0
    if pad:
        stack = [np.concatenate([im[:, -pad:], im, im[:, :pad]], axis=1)
                 for im in stack]
    bgr = [np.ascontiguousarray(im[:, :, ::-1] * np.float32(255.0)) for im in stack]
    fused = cv2.createMergeMertens(1.0, 1.0, 1.0).process(bgr)[:, :, ::-1]
    if pad:
        fused = fused[:, pad:pad + width]
    return np.clip(fused, 0.0, 1.0).astype(np.float32)


def fuse_luminosity(stack: list[np.ndarray], wrap: bool) -> np.ndarray:
    """Smooth luminosity-mask blend -- the low-memory path.

    Per-frame quality weights are computed on a downscaled copy, blurred, then
    scaled back up and used to blend the full-resolution frames a slice at a
    time. Because the weight maps are heavily smoothed this is free of the
    halos a per-pixel blend would produce, and it is the same technique used
    for hand-blended real-estate interiors.
    """
    h, w = stack[0].shape[:2]
    small_w = min(w, 1600)
    small_h = max(int(round(h * small_w / w)), 1)

    weights = []
    for im in stack:
        s = cv2.resize(im, (small_w, small_h), interpolation=cv2.INTER_AREA)
        lum = luminance(s)
        contrast = np.abs(cv2.Laplacian(lum, cv2.CV_32F))
        saturation = s.std(axis=2)
        # Well-exposedness: how close each channel sits to a mid-tone.
        exposed = np.prod(np.exp(-((s - 0.5) ** 2) / (2 * 0.2 ** 2)), axis=2)
        wmap = (contrast + 0.01) * (saturation + 0.01) * (exposed + 0.01)
        weights.append(wmap.astype(np.float32))

    total = np.sum(weights, axis=0) + EPS
    weights = [wmap / total for wmap in weights]
    weights = [wrap_blur(wmap, small_w * 0.01, wrap) for wmap in weights]
    total = np.sum(weights, axis=0) + EPS
    weights = [wmap / total for wmap in weights]

    # Accumulate one frame at a time, and one channel at a time within it, so
    # the only full-resolution temporaries alive at once are a single weight
    # map and a single channel -- not the whole stack's worth.
    out = np.zeros((h, w, 3), dtype=np.float32)
    for im, wmap in zip(stack, weights):
        full = cv2.resize(wmap, (w, h), interpolation=cv2.INTER_LINEAR)
        for c in range(3):
            out[:, :, c] += im[:, :, c] * full
        del full
    return np.clip(out, 0.0, 1.0)


def align_stack(stack: list[np.ndarray]) -> list[np.ndarray]:
    """Median-threshold-bitmap alignment. Only worth running for handheld
    captures -- brackets shot on a tripod are already pixel-aligned."""
    as_u8 = [(np.clip(im, 0, 1) * 255).astype(np.uint8)[:, :, ::-1] for im in stack]
    cv2.createAlignMTB().process(as_u8, as_u8)
    return [im[:, :, ::-1].astype(np.float32) / np.float32(255.0) for im in as_u8]


# ---------------------------------------------------------------- grading

def apply_grade(img: np.ndarray, g: Grade, wrap: bool) -> np.ndarray:
    out = img

    # --- white balance -----------------------------------------------------
    # Interiors almost always mix daylight through the windows with tungsten
    # from the fixtures. Neutralise partially: full correction strips the warmth
    # buyers respond to, none of it leaves the orange cast the camera records.
    if g.wb > 0:
        lum = luminance(out)
        lo, hi = np.percentile(lum, [25, 97])
        mask = (lum >= lo) & (lum <= hi)
        if mask.sum() > 64:
            means = np.array([out[..., c][mask].mean() for c in range(3)],
                             dtype=np.float32)
            target = float(means.mean())
            gains = np.clip(target / np.maximum(means, EPS), 0.75, 1.35)
            gains = 1.0 + (gains - 1.0) * g.wb
            out = out * gains[None, None, :]
    if g.warmth:
        out = out * np.array([1.0 + g.warmth, 1.0, 1.0 - g.warmth],
                             dtype=np.float32)[None, None, :]
    out = np.clip(out, 0.0, None)

    # --- exposure ----------------------------------------------------------
    # Exposure is a physical scaling of the light, so it belongs in linear.
    if g.ev:
        out = linear_to_srgb(srgb_to_linear(np.clip(out, 0.0, 1.0))
                             * np.float32(2.0 ** g.ev))
    out = np.clip(out, 0.0, 1.0)

    # --- highlights and shadows -------------------------------------------
    # Both run in display space, where the masks line up with what the eye
    # calls "bright" and "dark".
    if g.highlights:
        lum = luminance(out)
        out = out * (1.0 + g.highlights * smoothstep(0.55, 1.0, lum))[:, :, None]
        out = np.clip(out, 0.0, 1.0)
    if g.shadows:
        # A masked gamma, not a gain: multiplying a 0.02 pixel by 1.1 does
        # nothing visible, whereas pulling gamma down genuinely opens the
        # dark corners of a room without touching the mid-tones.
        lum = luminance(out)
        gamma = 1.0 - (g.shadows * 1.5) * (1.0 - smoothstep(0.0, 0.50, lum))
        out = np.power(out, gamma[:, :, None])

    # --- soft shoulder -----------------------------------------------------
    # Roll the top end off asymptotically so window panes keep a trace of
    # detail instead of clipping to paper white. Driven off the max channel so
    # no single channel can clip and shift the hue.
    if g.shoulder < 1.0:
        k = g.shoulder
        peak = out.max(axis=2)
        over = peak > k
        if over.any():
            rolled = k + (1.0 - k) * (1.0 - np.exp(-(peak - k) / (1.0 - k)))
            scale = np.where(over, rolled / np.maximum(peak, EPS), 1.0)
            out = out * scale[:, :, None]
    out = np.clip(out, 0.0, 1.0)

    # --- contrast ----------------------------------------------------------
    if g.contrast:
        out = out * (1.0 - g.contrast) + g.contrast * (out * out * (3.0 - 2.0 * out))

    # --- vibrance ----------------------------------------------------------
    if g.vibrance:
        mx, mn = out.max(axis=2), out.min(axis=2)
        sat = (mx - mn) / np.maximum(mx, EPS)
        boost = 1.0 + g.vibrance * (1.0 - sat)
        grey = luminance(out)
        out = grey[:, :, None] + (out - grey[:, :, None]) * boost[:, :, None]
        out = np.clip(out, 0.0, 1.0)

    # --- clarity (wide-radius local contrast on luminance only) ------------
    if g.clarity:
        lum = luminance(out)
        blurred = wrap_blur(lum, max(out.shape[1] * 0.004, 1.0), wrap)
        lifted = lum + g.clarity * (lum - blurred)
        out = out * (lifted / np.maximum(lum, EPS))[:, :, None]
        out = np.clip(out, 0.0, 1.0)

    return out


def sharpen(img: np.ndarray, amount: float, wrap: bool) -> np.ndarray:
    if amount <= 0:
        return img
    lum = luminance(img)
    blurred = wrap_blur(lum, 1.0, wrap)
    lifted = lum + amount * (lum - blurred)
    return np.clip(img * (lifted / np.maximum(lum, EPS))[:, :, None], 0.0, 1.0)


def patch_nadir(img: np.ndarray, degrees: float, logo: Path | None) -> np.ndarray:
    """Cover the tripod at the bottom of the sphere.

    Fills the bottom `degrees` of the panorama by feathering the ring of pixels
    directly above it downward, then optionally centres a logo in it.
    """
    if degrees <= 0:
        return img
    h, w = img.shape[:2]
    start = int(h * (1.0 - degrees / 180.0))
    if start >= h - 1:
        return img
    out = img.copy()

    ring = img[max(start - max(h // 200, 1), 0):start]
    fill = ring.reshape(-1, 3).mean(axis=0) if ring.size else img[-1].mean(axis=0)
    band_h = h - start
    for i in range(band_h):
        t = smoothstep(0.0, 1.0, np.array(i / max(band_h - 1, 1), dtype=np.float32))
        out[start + i] = img[start] * (1.0 - t) + fill * t
    out[start:] = wrap_blur(out[start:], max(w * 0.004, 1.0), True)

    if logo and logo.exists():
        mark = cv2.imdecode(np.fromfile(str(logo), dtype=np.uint8),
                            cv2.IMREAD_UNCHANGED)
        if mark is not None:
            target = max(int(w * 0.05), 8)
            scaled = cv2.resize(mark, (target, target), interpolation=cv2.INTER_AREA)
            alpha = (scaled[:, :, 3:4].astype(np.float32) / 255.0
                     if scaled.shape[2] == 4 else np.ones((target, target, 1), np.float32))
            rgb = scaled[:, :, :3][:, :, ::-1].astype(np.float32) / 255.0
            y0 = min(h - target, start + (band_h - target) // 2)
            x0 = (w - target) // 2
            region = out[y0:y0 + target, x0:x0 + target]
            out[y0:y0 + target, x0:x0 + target] = region * (1 - alpha) + rgb * alpha
    return np.clip(out, 0.0, 1.0)


# ---------------------------------------------------------------- writing

XMP_TEMPLATE = """<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:GPano="http://ns.google.com/photos/1.0/panorama/"
    xmlns:dc="http://purl.org/dc/elements/1.1/">
   <GPano:UsePanoramaViewer>True</GPano:UsePanoramaViewer>
   <GPano:ProjectionType>equirectangular</GPano:ProjectionType>
   <GPano:CroppedAreaImageWidthPixels>{w}</GPano:CroppedAreaImageWidthPixels>
   <GPano:CroppedAreaImageHeightPixels>{h}</GPano:CroppedAreaImageHeightPixels>
   <GPano:FullPanoWidthPixels>{w}</GPano:FullPanoWidthPixels>
   <GPano:FullPanoHeightPixels>{h}</GPano:FullPanoHeightPixels>
   <GPano:CroppedAreaLeftPixels>0</GPano:CroppedAreaLeftPixels>
   <GPano:CroppedAreaTopPixels>0</GPano:CroppedAreaTopPixels>
   <GPano:PoseHeadingDegrees>0</GPano:PoseHeadingDegrees>
   <dc:title><rdf:Alt><rdf:li xml:lang="x-default">{title}</rdf:li></rdf:Alt></dc:title>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>"""


def xmp_escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))


def split_jpeg_trailer(data: bytes) -> tuple[bytes, bytes]:
    """Split a JPEG into (image, anything appended after EOI).

    Insta360 hangs its own block on the end of a .insp file after the JPEG's
    end-of-image marker; Studio needs that block to stitch. Inside the entropy
    stream every 0xFF is followed by a stuff byte or a restart marker, so the
    first 0xFFD9 after SOS is the real EOI.
    """
    i = 2
    while i < len(data) - 1 and data[i] == 0xFF:
        marker = data[i + 1]
        if marker == 0xD9:
            return data[:i + 2], data[i + 2:]
        length = int.from_bytes(data[i + 2:i + 4], "big")
        i += 2 + length
        if marker == 0xDA:
            break
    else:
        return data, b""
    while i < len(data) - 1:
        if data[i] == 0xFF:
            marker = data[i + 1]
            if marker == 0xD9:
                return data[:i + 2], data[i + 2:]
            if marker == 0x00 or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
        i += 1
    return data, b""


def write_pano(img: np.ndarray, dest: Path, title: str, quality: int,
               max_width: int, sharpen_amount: float, wrap: bool,
               equirect: bool = True) -> None:
    if max_width and img.shape[1] > max_width:
        new_h = max(int(round(img.shape[0] * max_width / img.shape[1])), 1)
        img = cv2.resize(img, (max_width, new_h), interpolation=cv2.INTER_AREA)
    img = sharpen(img, sharpen_amount, wrap)

    h, w = img.shape[:2]
    as_u8 = (np.clip(img, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
    # Only a stitched equirectangular frame gets the GPano tags -- claiming a
    # projection the pixels do not have would send a viewer like CloudPano
    # off wrapping a dual-fisheye frame onto a sphere.
    extra = {}
    if equirect:
        extra["xmp"] = XMP_TEMPLATE.format(
            w=w, h=h, title=xmp_escape(title)).encode("utf-8")
    Image.fromarray(as_u8, "RGB").save(
        dest, "JPEG", quality=quality, optimize=True, progressive=True,
        subsampling=0, **extra)


XMP_SIG = b"http://ns.adobe.com/xap/1.0/\x00"


def retitle_jpeg(data: bytes, width: int, height: int, title: str) -> bytes:
    """Return `data` with its XMP block rewritten to carry `title`.

    Splices the JPEG's marker segments rather than decoding and re-encoding,
    so putting a room name on a panorama costs it nothing in quality.
    """
    payload = XMP_SIG + XMP_TEMPLATE.format(
        w=width, h=height, title=xmp_escape(title)).encode("utf-8")
    segment = b"\xFF\xE1" + (len(payload) + 2).to_bytes(2, "big") + payload

    i = 2
    while i < len(data) - 1 and data[i] == 0xFF:
        marker = data[i + 1]
        if marker in (0xD8, 0xD9, 0xDA):
            break
        length = int.from_bytes(data[i + 2:i + 4], "big")
        if marker == 0xE1 and data[i + 4:i + 4 + len(XMP_SIG)] == XMP_SIG:
            return data[:i] + segment + data[i + 2 + length:]
        i += 2 + length
    return data[:2] + segment + data[2:]  # no XMP yet -- insert one after SOI


def write_preview(img: np.ndarray, dest: Path) -> None:
    """A horizon strip -- enough of the room to recognise it, small enough to
    skim a whole shoot at once."""
    h = img.shape[0]
    band = img[int(h * 0.26):int(h * 0.80)]
    target_w = 1600
    target_h = max(int(round(band.shape[0] * target_w / band.shape[1])), 1)
    band = cv2.resize(band, (target_w, target_h), interpolation=cv2.INTER_AREA)
    as_u8 = (np.clip(band, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
    Image.fromarray(as_u8, "RGB").save(dest, "JPEG", quality=82, optimize=True)


# ---------------------------------------------------------------- subcommands

def collect_inputs(input_dir: Path) -> list[Path]:
    return sorted((p for p in input_dir.iterdir()
                   if p.is_file() and p.suffix.lower() in READABLE_EXT),
                  key=natural_key)


def cmd_scan(args) -> int:
    input_dir = Path(args.input_dir)
    files = collect_inputs(input_dir)
    if not files:
        print(f"No readable images in {input_dir}", file=sys.stderr)
        return 1
    groups, warnings = group_brackets(files, args.bracket, args.gap)
    for w in warnings:
        print(f"note: {w}")
    print(f"\n{len(files)} files -> {len(groups)} panorama(s)\n")
    bad = 0
    for grp in groups:
        flag = "  <-- " + grp.note if grp.note else ""
        bad += bool(grp.note)
        print(f"  pano_{grp.index:02d}  ({len(grp.files)} frames){flag}")
        for f in grp.files:
            print(f"      {f.name}")
    if bad:
        print(f"\n{bad} group(s) do not have {args.bracket} frames. Check the "
              f"--bracket count or widen --gap, then re-run scan.")
    return 0


def cmd_build(args) -> int:
    input_dir, output_dir = Path(args.input_dir), Path(args.output_dir)
    files = collect_inputs(input_dir)
    if not files:
        print(f"No readable images in {input_dir}", file=sys.stderr)
        return 1

    grade = PRESETS[args.preset]
    for field in ("ev", "highlights", "shadows", "contrast", "vibrance",
                  "clarity", "wb", "warmth", "sharpen"):
        override = getattr(args, field)
        if override is not None:
            grade = Grade(**{**asdict(grade), field: override})

    groups, warnings = group_brackets(files, args.bracket, args.gap)
    for w in warnings:
        print(f"note: {w}")
    groups = [g for g in groups if not g.note or args.allow_partial]
    if not groups:
        print("No complete bracket sets. Run `scan` to see the grouping.",
              file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    preview_dir = output_dir / "_previews"
    preview_dir.mkdir(exist_ok=True)

    manifest = {"preset": args.preset, "grade": asdict(grade), "panoramas": []}
    failures = []

    for grp in groups:
        name = f"pano_{grp.index:02d}.jpg"
        print(f"\n[{grp.index}/{len(groups)}] {name}  ({len(grp.files)} frames)")
        try:
            stack = []
            for f in grp.files:
                print(f"    read {f.name}")
                stack.append(read_image(f))
            shapes = {im.shape for im in stack}
            if len(shapes) > 1:
                raise ValueError(f"frames differ in size: {sorted(shapes)}")

            # read_dng refuses anything still carrying a Bayer mosaic, so a .dng
            # that got this far is a Studio export: already stitched, already
            # demosaiced. Guessing from pixels would only invent false positives.
            stitched = grp.files[0].suffix.lower() == ".dng"
            fisheye = args.fisheye or (not stitched
                                       and looks_like_dual_fisheye(stack[0]))
            wrap = not fisheye
            if fisheye and not args.fisheye:
                print("    detected dual-fisheye input -- see README, these need "
                      "stitching in Insta360 Studio")

            if args.align:
                print("    aligning")
                stack = align_stack(stack)

            h, w = stack[0].shape[:2]
            engine = args.engine
            if engine == "mertens":
                pad = (1 + 2 * MERTENS_PAD) if wrap else 1.0
                est_gb = w * h * 3 * 4 * (len(stack) + 4) * pad / 1e9
                print(f"    fuse ({engine}, {w}x{h}, ~{est_gb:.1f} GB peak)")
            else:
                print(f"    fuse ({engine}, {w}x{h})")
            fused = (fuse_mertens(stack, wrap) if engine == "mertens"
                     else fuse_luminosity(stack, wrap))
            del stack

            print(f"    grade ({args.preset})")
            fused = apply_grade(fused, grade, wrap)
            if args.nadir and not fisheye:
                fused = patch_nadir(fused, args.nadir,
                                    Path(args.nadir_logo) if args.nadir_logo else None)

            if fisheye:
                # Not a panorama yet -- this is a merged dual-fisheye frame
                # that still has to go through Insta360 Studio. Carry the
                # source's trailing Insta360 block over so Studio recognises
                # it, and keep native size since Studio will resample anyway.
                name = f"merged_{grp.index:02d}.insp"
                dest = output_dir / name
                write_pano(fused, dest, dest.stem, args.quality, 0,
                           grade.sharpen, False, equirect=False)
                trailer = split_jpeg_trailer(grp.files[0].read_bytes())[1]
                if trailer:
                    with dest.open("ab") as fh:
                        fh.write(trailer)
                    print(f"    carried over {len(trailer)} bytes of Insta360 "
                          f"metadata from {grp.files[0].name}")
                else:
                    print(f"    warning: no Insta360 metadata block found in "
                          f"{grp.files[0].name}; Studio may refuse to stitch it")
            else:
                dest = output_dir / name
                write_pano(fused, dest, dest.stem, args.quality,
                           args.max_width, grade.sharpen, wrap)
            write_preview(fused, preview_dir / f"pano_{grp.index:02d}.jpg")
            del fused

            size_mb = dest.stat().st_size / 1e6
            print(f"    wrote {dest.name}  {size_mb:.1f} MB")
            manifest["panoramas"].append({
                "output": name, "label": None, "engine": engine,
                "fisheye": fisheye, "sources": [f.name for f in grp.files]})
        except Exception as e:
            failures.append((name, e))
            print(f"    FAILED: {e}", file=sys.stderr)

    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")

    print("\n" + "=" * 62)
    print(f"Wrote {len(manifest['panoramas'])} file(s) to {output_dir}")
    print(f"Previews for room identification: {preview_dir}")
    if failures:
        print(f"\n{len(failures)} failed:")
        for name, e in failures:
            print(f"  {name}: {e}")
    if any(p["fisheye"] for p in manifest["panoramas"]):
        print("\nThese are merged dual-fisheye frames, NOT finished panoramas."
              "\nOpen the .insp files in Insta360 Studio, export equirectangular,"
              "\nthen run this again on the exports with --preset flat.")
    else:
        print("\nNext: name the rooms, then\n"
              f"  python pano_hdr.py label \"{output_dir}\" --map labels.json")
    return 1 if failures and not manifest["panoramas"] else 0


def cmd_label(args) -> int:
    output_dir = Path(args.output_dir)
    manifest_path = output_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"No manifest.json in {output_dir} -- run `build` first.",
              file=sys.stderr)
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mapping = json.loads(Path(args.map).read_text(encoding="utf-8"))

    renamed, missing = [], []
    for entry in manifest["panoramas"]:
        current = entry.get("renamed_to") or entry["output"]
        label = mapping.get(entry["output"]) or mapping.get(current)
        if not label:
            continue
        src = output_dir / current
        if not src.exists():
            missing.append(current)
            continue

        slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") or "pano"
        order = re.search(r"_(\d+)", entry["output"])
        dest = output_dir / (f"{order.group(1) if order else '00'}-{slug}"
                             f"{src.suffix}")

        with Image.open(src) as probe:
            width, height = probe.size
        dest.write_bytes(retitle_jpeg(src.read_bytes(), width, height, label))
        if src.resolve() != dest.resolve():
            src.unlink()
        preview = output_dir / "_previews" / current
        if preview.exists():
            preview.rename(preview.with_name(dest.name))

        entry["label"] = label
        entry["renamed_to"] = dest.name
        renamed.append((current, dest.name))
        print(f"  {current}  ->  {dest.name}")

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nRenamed {len(renamed)} file(s).")
    if missing:
        print(f"Not found on disk: {', '.join(missing)}")
    unlabelled = [e["output"] for e in manifest["panoramas"] if not e.get("label")]
    if unlabelled:
        print(f"Still unlabelled: {', '.join(unlabelled)}")
    return 0


# ---------------------------------------------------------------- cli

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pano_hdr.py",
        description="Merge bracketed Insta360 exposures into CloudPano-ready 360s.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    def add_grouping(p):
        p.add_argument("--bracket", type=int, default=5,
                       help="frames per bracket set")
        p.add_argument("--gap", type=float, default=6.0,
                       help="seconds of separation that starts a new position")

    p_scan = sub.add_parser("scan", help="show how files group into bracket sets")
    p_scan.add_argument("input_dir")
    add_grouping(p_scan)
    p_scan.set_defaults(func=cmd_scan)

    p_build = sub.add_parser("build", help="fuse, grade and tag the panoramas")
    p_build.add_argument("input_dir")
    p_build.add_argument("output_dir")
    add_grouping(p_build)
    p_build.add_argument("--preset", choices=sorted(PRESETS), default="natural")
    p_build.add_argument("--engine", choices=("luminosity", "mertens"),
                         default="luminosity",
                         help="exposure-fusion method; luminosity holds shadow "
                              "detail better and uses far less memory")
    p_build.add_argument("--align", action="store_true",
                         help="align frames first (handheld captures only)")
    p_build.add_argument("--fisheye", action="store_true",
                         help="force raw dual-fisheye handling")
    p_build.add_argument("--allow-partial", action="store_true",
                         help="also process groups without a full bracket set")
    p_build.add_argument("--max-width", type=int, default=8192,
                         help="downscale wider panoramas; 0 keeps native size")
    p_build.add_argument("--quality", type=int, default=90, help="JPEG quality")
    p_build.add_argument("--nadir", type=float, default=0.0,
                         help="degrees of tripod patch at the bottom, e.g. 25")
    p_build.add_argument("--nadir-logo", help="PNG to centre in the nadir patch")
    for field in ("ev", "highlights", "shadows", "contrast", "vibrance",
                  "clarity", "wb", "warmth", "sharpen"):
        p_build.add_argument(f"--{field}", type=float, default=None,
                             help=f"override the preset's {field}")
    p_build.set_defaults(func=cmd_build)

    p_label = sub.add_parser("label", help="rename outputs to room names")
    p_label.add_argument("output_dir")
    p_label.add_argument("--map", required=True,
                         help='JSON of {"pano_01.jpg": "living-room"}')
    p_label.set_defaults(func=cmd_label)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
