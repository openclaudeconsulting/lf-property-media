---
name: pano-tour
description: Turn a folder of bracketed Insta360 exposures into finished, room-named 360 photos ready to upload to CloudPano. Fuses each bracket set into one panorama, applies the LF real-estate grade, tags it as a 360, and names each file by the room it shows by looking at the previews. Use when the user has 360 brackets to process, mentions CloudPano, .insp files, an Insta360 shoot, or asks to combine/edit/label bracketed 360 photos.
---

# pano-tour

**Use this when the user has bracketed 360 photos to turn into a tour.** They
will say things like "process the 360s from the Oak St shoot", "combine these
brackets for CloudPano", "I've got five exposures per room, edit them", or just
point at a folder of Insta360 exports.

The heavy lifting is done by `tools/pano-hdr/pano_hdr.py`. Your job is to drive
it and — the part the script cannot do — **work out which room each panorama
shows** by looking at the previews.

Read `tools/pano-hdr/README.md` if you need the details of any flag.

## 1. Find the input

Ask for the folder if the user has not named one. What you want is a folder of
**stitched equirectangular** frames exported from Insta360 Studio — 2:1 images,
five per tripod position by default.

If they only have raw `.insp` files, tell them plainly: the tool can merge the
brackets but Insta360 Studio still has to stitch them, and that path is untested
against real camera files. Better route is to export equirectangular from Studio
first and then run this. Do not promise the `.insp` path will work.

## 2. Check the grouping before processing anything

```bash
python tools/pano-hdr/pano_hdr.py scan "<input folder>"
```

This writes nothing. Read the output back to the user as a count — "15 frames,
3 positions" — and only flag detail if something is off.

If any group is not the expected size, **stop and sort it out** rather than
processing. Usually one of:

- The camera shot 3 brackets, not 5 → add `--bracket 3`.
- Two positions shot close together got merged → lower `--gap`.
- One position took longer than the gap → raise `--gap`.
- Files have no EXIF timestamps → it falls back to filename order, which is
  fine as long as the filenames are in shooting order. Say so.

## 3. Build

```bash
python tools/pano-hdr/pano_hdr.py build "<input folder>" "<output folder>"
```

Default output folder: a `360/` sibling of the input folder.

Defaults are the light real-estate grade — a slight exposure and highlight
lift, dark corners opened, windows held off pure white. Reach for a preset only
if the user asks or the previews clearly call for it:

- `--preset bright` — dim or north-facing rooms.
- `--preset flat` — the user wants to grade in Lightroom afterwards.
- Single overrides like `--shadows 0.25` work on top of any preset.

This takes a couple of minutes for a full house at full resolution. Run it in
the background if it is a big shoot.

## 4. Name the rooms — this is the part that needs you

The build writes a `_previews/` folder: one wide strip per panorama showing the
full 360° horizon of that position. **Read those images.** Each one is a whole
room unrolled, which is plenty to tell a kitchen from a primary bath.

Then write a `labels.json` next to the output:

```json
{
  "pano_01.jpg": "Living Room",
  "pano_02.jpg": "Kitchen",
  "pano_03.jpg": "Upstairs Primary Bath"
}
```

Naming that works for the user:

- Plain room names as a buyer would say them — "Living Room", "Primary
  Bedroom", "Guest Bath", "Lanai", "Two-Car Garage".
- **Disambiguate repeats by floor or position**, since that is the whole
  problem being solved: "Upstairs Bath" and "Downstairs Half Bath", not
  "Bath 1" and "Bath 2". Use the preview to tell them apart — a half bath has
  no tub, an upstairs hallway shows a stair rail.
- Only number them when they are genuinely interchangeable: "Guest Bedroom 1",
  "Guest Bedroom 2".
- Exteriors get their side: "Front Exterior", "Back Yard", "Pool Deck".

If a preview is genuinely ambiguous — two similar bedrooms, an unclear hallway
— **say which ones you were unsure about and what you guessed**. Do not quietly
pick one. The user shot the house and can correct it in a second.

Then apply:

```bash
python tools/pano-hdr/pano_hdr.py label "<output folder>" --map labels.json
```

Files come out as `01-living-room.jpg`, `02-kitchen.jpg` — shooting order kept
as a prefix so they still sort the way the house was walked. This step only
rewrites metadata; the pixels are untouched.

## 5. Hand off

Tell the user the folder is ready to drag into CloudPano, and list the finished
names so they can spot a wrong room immediately. Mention anything worth knowing:
positions that failed, groups you skipped, rooms you guessed at.

If they then want these on the website as a listing tour, that is the
**new-property** or **update-property** skill — those handle flat listing
photos, so do not try to feed 360s into them without asking.

## Don't

- Don't process a shoot whose groups came out the wrong size — fix the grouping
  first, or you will silently produce garbage panoramas.
- Don't invent room names to fill in gaps. Ask, or flag the guess.
- Don't crank the grade to make a dark room look bright. The point is that these
  cut together with the stills shot on the same job. `--preset bright` is as far
  as it should normally go.
- Don't re-run `build` over an output folder that has already been labelled —
  it writes `pano_NN.jpg` afresh and you will end up with both sets.
