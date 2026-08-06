# pano-hdr — bracketed 360s → CloudPano

Turns the bracketed exposures an Insta360 shoots at each tripod position into
one finished, room-named 360 photo ready to upload to CloudPano.

```
5 bracketed frames  ->  fuse  ->  grade  ->  tag as 360  ->  01-living-room.jpg
```

It runs on Python 3 with `opencv-python`, `numpy` and `Pillow`, all of which are
already on this machine. Reading Studio's **DNG** exports additionally needs
`rawpy` (`pip install rawpy`); every other input format works without it.

---

## The input it wants

**Stitched equirectangular frames** — a 2:1 image that already looks like an
unrolled sphere. Export them out of Insta360 Studio first:

1. Load the shoot into Insta360 Studio.
2. Select all the bracketed frames.
3. **Export → Export 360 photo** (*not* "Export reframed photo", which writes a
   flat 16:9 crop), **Original Resolution**, horizon levelling on, bottom logo
   off. Leave every colour and HDR control alone — export the brackets as
   separate flat frames and let this tool do the fusing and grading.
4. Point this tool at that export folder.

Studio's stitching uses Insta360's own lens calibration. Nothing open-source
matches it, so it is worth doing that pass rather than trying to skip it.

**Studio picks the output format from the source, and the choice is locked.**
`.insp` sources export as JPEG; `.dng` sources export as DNG and the Output
Format dropdown is greyed out. Both are fine here:

| Source on the card | Studio writes | Notes |
|---|---|---|
| `.insp` | JPEG | 8-bit, Insta360's colour already baked in |
| `.dng`  | DNG  | 16-bit *linear* — more latitude, needs `rawpy` |

A Studio-exported DNG is a stitched, demosaiced, uncompressed 16-bit RGB frame
that happens to sit in a DNG container. It carries no white balance, no gamma
and camera-space colour, so it is decoded through libraw (`rawpy`) with the shot
white balance and the camera→sRGB matrix applied. Auto-brightening is disabled
deliberately: letting libraw normalise each frame on its own would flatten the
exposure differences the whole fuse depends on.

Two DNG-specific traps, both handled:

- **Raw dual-fisheye `.dng` straight off the camera is refused**, with a message
  telling you to run it through Studio. It is a 1:2 portrait Bayer mosaic, not a
  panorama, and decoding one would produce something that wraps to garbage on a
  sphere.
- **Studio stamps its own export time into the exported DNG** and drops
  `DateTimeOriginal`, so the file's timestamp says when it was converted, not
  when it was shot. Grouping falls back to the capture time in the *filename*
  (`IMG_<date>_<time>_…`), which Insta360 stamps once per tripod position and
  therefore shares across all the frames of one bracket.

If you hand it raw `.insp` dual-fisheye files instead, it notices, fuses the
brackets anyway, and writes `merged_NN.insp` files for you to stitch in Studio
afterwards — see [Raw .insp files](#raw-insp-files) below for the caveat.

---

## Normal run

**1. Check the grouping** (reads only, writes nothing):

```bash
python tools/pano-hdr/pano_hdr.py scan "D:/shoots/1234-oak-st/export"
```

```
15 files -> 3 panorama(s)

  pano_01  (5 frames)
      IMG_20260805_143022_00_001.jpg
      ...
```

Frames are grouped by capture time — the five in one bracket land within a
couple of seconds of each other, and there is a long gap while you walk to the
next position. If a group comes out the wrong size, adjust `--bracket` (frames
per position) or `--gap` (seconds that start a new position) and scan again.

**2. Build:**

```bash
python tools/pano-hdr/pano_hdr.py build "D:/shoots/1234-oak-st/export" "D:/shoots/1234-oak-st/360"
```

Writes `pano_01.jpg …`, a `_previews/` folder, and `manifest.json`.

**3. Name the rooms.** Write a `labels.json`:

```json
{
  "pano_01.jpg": "Living Room",
  "pano_02.jpg": "Kitchen",
  "pano_03.jpg": "Upstairs Primary Bath"
}
```

```bash
python tools/pano-hdr/pano_hdr.py label "D:/shoots/1234-oak-st/360" --map labels.json
```

```
pano_01.jpg  ->  01-living-room.jpg
pano_02.jpg  ->  02-kitchen.jpg
pano_03.jpg  ->  03-upstairs-primary-bath.jpg
```

The number prefix keeps shooting order, so the files still sort the way you
walked the house. The room name also goes into the file's own title metadata.
This step re-splices metadata only — the pixels come out byte-identical, so
naming a room costs nothing in quality.

Or just ask Claude: **"label the 360s in D:/shoots/1234-oak-st/360"** — it
reads the previews, works out which room each one is, and runs the command.
That is what the `pano-tour` skill does.

---

## What the grade does

The defaults are deliberately light — the goal is a panorama that cuts
together with the stills you shot on the same job, not an HDR look.

| Step | Default | What it is for |
|---|---|---|
| White balance | `--wb 0.5` | Half-strength pull toward neutral. Interiors mix daylight from the windows with tungsten from the fixtures; full correction kills the warmth, none of it leaves an orange cast. |
| Exposure | `--ev 0.12` | A slight lift. |
| Highlights | `--highlights 0.08` | A slight lift in the bright end. |
| Shadows | `--shadows 0.10` | Masked gamma lift — opens dark corners without touching mid-tones. |
| Soft shoulder | `--shoulder 0.9` | Rolls the top end off asymptotically so window panes keep a trace of detail instead of clipping to paper white. Nothing in the output reaches pure white. |
| Contrast | `--contrast 0.05` | Gentle S-curve that cannot clip. |
| Vibrance | `--vibrance 0.06` | Weighted toward flat colours, so wood and skin stay put. |
| Clarity | `--clarity 0.08` | Wide-radius local contrast. |
| Sharpening | `--sharpen 0.35` | Applied after the final resize. |

Presets: `--preset natural` (default), `--preset bright` for dim or
north-facing rooms, `--preset flat` to fuse with no colour or tone changes at
all — use that when the panorama is going into Lightroom afterwards.

Any single value overrides the preset:

```bash
python tools/pano-hdr/pano_hdr.py build in/ out/ --preset bright --shadows 0.25
```

### Output size

`--max-width 8192` by default, quality 90. That is the CloudPano sweet spot:
sharp on desktop and in a headset, roughly 4–8 MB, and quick to load in a tour.
`--max-width 0` keeps the camera's native resolution.

---

## Two things worth knowing

**The wrap seam.** The left and right edges of an equirectangular image are the
same place in the room. Any blur or sharpen that treats them as edges leaves a
vertical line straight down the panorama once CloudPano wraps it onto a sphere.
Every spatial filter here pads horizontally by wrapping the image around itself
first. The seam is measured in the test suite, not assumed.

**Fusion engine.** `--engine mertens` (default) uses OpenCV's Mertens exposure
fusion. `--engine luminosity` blends through smoothed luminosity masks instead —
the same thing a retoucher does by hand in Photoshop — and is the low-memory
fallback.

Luminosity was the original default and it halos. Blurring a weight map smears
the boundary between two regions that want opposite exposures, so a dark object
on a bright wall gets lifted toward mid-tone *and* leaves a glow on the wall
around it. Measured on the guitar room at 2719 Fort Worth, where a black TV
hangs on a pale blue wall:

| | TV screen | wall beside TV vs. wall further off |
|---|---|---|
| source frame (ground truth) | 0.019 | −0.016 (wall is *darker* by the TV) |
| luminosity | 0.182 | **+0.016** (glow — sign is inverted) |
| luminosity, 8× wider blur | 0.157 | +0.022 (wider blur does not fix the sign) |
| **mertens** | **0.068** | **−0.037** (correct direction) |

Luminosity lifted the screen to 0.182 — the exact luminance the *wall* had in
the source — which is why it read as grey plastic rather than a black TV. No
blur radius fixes it, because the artefact is the blur.

Two consequences of the switch, both handled:

- Mertens' Laplacian pyramid lays a seam down the wrap edge, so it gets 25% wrap
  padding before it runs. The seam is measured in the test suite, not assumed.
- Holding darks down means the shadow lift in the grade is now stretching real
  sensor noise that the washed-out blend used to bury (high-frequency energy in
  the TV went 0.0095 → 0.0322). `--denoise` handles it; see below.

Mertens needs the whole stack plus its pyramids in memory at once. `build`
prints the estimated peak before it starts; drop to `--engine luminosity` if a
machine cannot hold it.

**Shadow denoise.** `--denoise 0.9` (default, `0` disables) runs a guided filter
over the fused frame, mixed in proportional to how dark each pixel is and doing
nothing at all above ~0.22 luminance. Because it is edge-aware it cleans a flat
black screen without softening the edge of it. Wall texture, fabric and timber
grain measure bit-identical before and after; the TV came back to 0.013, in line
with the 0.0095 the old blend produced.

---

## Raw .insp files

If the input is raw dual-fisheye, the tool detects it, fuses the brackets in
fisheye space (the five frames are geometrically identical, so this is sound),
and writes `merged_NN.insp` — no 360 tags, since the pixels are not a panorama
yet. It copies the Insta360 metadata block off the end of the source file so
Studio has what it needs.

**This path is untested against real camera files** — it was built against
synthetic fixtures, since no `.insp` files were available. If Studio refuses
the merged file, fall back to the normal route: export the brackets to
equirectangular first, then run this on those.

---

## Options

```
scan  <input_dir>                    show how files group into bracket sets
build <input_dir> <output_dir>       fuse, grade and tag
label <output_dir> --map FILE.json   rename to room names

  --bracket N        frames per position (default 5)
  --gap SECONDS      separation that starts a new position (default 6)
  --preset NAME      natural | bright | flat
  --engine NAME      mertens (default) | luminosity
  --denoise N        shadow-only denoise strength, 0 disables (default 0.9)
  --align            align frames first — handheld captures only; brackets
                     shot on a tripod are already pixel-aligned
  --allow-partial    also process groups without a full bracket set
  --max-width PX     downscale wider panoramas; 0 keeps native (default 8192)
  --quality N        JPEG quality (default 90)
  --nadir DEGREES    patch the tripod out of the bottom, e.g. 25
  --nadir-logo FILE  PNG to centre in that patch
```

---

## Tests

```bash
python tools/pano-hdr/test_pano_hdr.py
```

Builds synthetic bracketed panoramas with a blown window and a dark corner,
runs the pipeline, and checks the 360 metadata CloudPano reads, seam
continuity across the wrap, that highlights are recovered and nothing clips to
white, that shadows actually lift, that labelling is byte-identical on pixels,
and the fisheye and missing-EXIF fallbacks.
