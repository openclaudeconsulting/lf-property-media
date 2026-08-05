# pano-hdr — bracketed 360s → CloudPano

Turns the bracketed exposures an Insta360 shoots at each tripod position into
one finished, room-named 360 photo ready to upload to CloudPano.

```
5 bracketed frames  ->  fuse  ->  grade  ->  tag as 360  ->  01-living-room.jpg
```

No install step: it runs on Python 3 with `opencv-python`, `numpy` and
`Pillow`, all of which are already on this machine.

---

## The input it wants

**Stitched equirectangular frames** — a 2:1 image that already looks like an
unrolled sphere. Export them out of Insta360 Studio first:

1. Load the shoot into Insta360 Studio.
2. Select all the bracketed frames.
3. Export as JPEG (or 16-bit TIFF for a little more latitude), **equirectangular**.
4. Point this tool at that export folder.

Studio's stitching uses Insta360's own lens calibration. Nothing open-source
matches it, so it is worth doing that pass rather than trying to skip it.

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

**Fusion engine.** `--engine luminosity` (default) blends the frames through
smoothed luminosity masks — the same thing a retoucher does by hand with
luminosity masks in Photoshop. `--engine mertens` uses OpenCV's Mertens
exposure fusion instead.

Measured on the test scene, the two are equivalent on retained detail
(0.0089 vs 0.0092), but Mertens crushes deep shadows — it rendered a dark
corner at 0.017 where the frames actually held detail at 0.087 — and its
Laplacian pyramid lays a seam down the wrap edge, which is why it gets 25%
wrap padding before it runs. The luminosity engine also holds peak memory
roughly flat instead of needing the whole stack plus its pyramids at once,
which matters at 72 MP. Hence the default.

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
  --engine NAME      luminosity | mertens
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
