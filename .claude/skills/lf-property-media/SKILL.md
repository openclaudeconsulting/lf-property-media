---
name: lf-property-media
description: >-
  Operational front door for the LF Property Media real-estate-photography studio's
  job pipeline. Use this whenever the user is running a shoot job and references the
  workflow without naming an exact tool — setting up the raw/final folder structure
  for a new booking ("set up folders for John Smith's shoot at 2719 Fort Worth on the
  27th", "new job for the Henderson listing"), filing a dump of photos into a shoot's
  subfolders ("file these photos for 2719 Fort Worth", "sort the edited shots into the
  final folders"), assembling the single branded delivery
  email of gallery/video/tour/floor-plan/listing links ("send the delivery email for
  Fort Worth"), or asking where they are in the process ("what's next on this job",
  "how does my pipeline work"). It also recognizes listing-tour requests (publishing
  from an MLS link, or editing an existing tour) and routes them to the dedicated
  new-property and update-property skills. Trigger generously for anything about LFPM
  / LF Property Media jobs, shoot folders, job intake, client delivery, or "what step
  comes next" — even when the user doesn't say the word "skill" or name a script.
---

# LF Property Media — pipeline dispatcher

This is the operational hub for a real-estate-photography studio. A job moves through
the same stages every time, and different stages are handled by different tools. Your
job is to figure out **which stage the user is on**, then either route to the
specialized skill or run the right local tool — without making the user remember which
script does what.

## The pipeline (the map you're dispatching against)

| Stage | What the user wants | Where it goes |
|---|---|---|
| Intake / quote | A price for a realtor | HoneyBook + the site calculator (no action here — see "Where am I") |
| **New booking** | Make the shoot's folder structure | **Run `tools/new-job.py`** (this skill) |
| **File photos** | Sort a dump of photos into the job's subfolders | **Run `tools/file-photos.py`** (this skill) |
| Listing tour — new | Publish a property page from an MLS link + photos | **Route to the `new-property` skill** |
| Listing tour — edit | Change photos/status/facts on an existing tour | **Route to the `update-property` skill** |
| **Delivery** | One branded email with every deliverable link | **Assemble it** (this skill) |
| Final payment | Remaining balance invoice | HoneyBook (no action here) |

## Step 0 — Route the request

Read what the user actually asked and pick the lane. Don't over-ask; infer from the
phrasing and only confirm what's genuinely missing.

- Mentions an **MLS/IDX link, "publish", "new listing tour", "add this to properties"**
  → this is a listing publish. **Use the `new-property` skill** (it scrapes the MLS,
  organizes photos, builds the page). Hand off rather than reinventing it.
- Mentions **"modify / update / change / mark sold / pull down" an existing property**
  → **Use the `update-property` skill**.
- Mentions **a new shoot, a booking, "set up folders", a realtor + address**, with no
  listing-page intent → **folder setup** (below).
- Mentions **filing / sorting a pile of photos** for a shoot ("file these for 2719 Fort
  Worth", "sort the edited ones into final") → **file photos** (below).
- Mentions **delivering, sending links, "the gallery is ready", Pixieset/tour/video
  links to send** → **delivery email** (below).
- Asks **how the process works / what's next / "where am I"** → **explain the
  pipeline** using the map above and the [reference](references/pipeline.md).

If a request spans stages ("the Smith gallery is done, send it and mark the listing
sold"), handle them in order and route each part to its lane.

## Set up shoot folders (new booking)

When a job is booked, create the standard raw + final folder trees so the owner never
hand-builds folders. The generator already exists — your job is to pull the three
inputs from natural language and run it.

**Extract from the request:**
- **Realtor** — first & last name (e.g. "John Smith").
- **Address** — the property address; the folder uses the first ~3 words
  ("2719 Fort Worth Street, Sarasota" → "2719 Fort Worth").
- **Shoot date** — parse what they say ("the 27th", "June 27", "6/27") into the
  generator's format. If they don't give one, it defaults to today.

Run it from the repo root:

```bash
python tools/new-job.py --realtor "<name>" --address "<address>" --date <YYYY-MM-DD>
```

Notes that matter:
- It writes under `LF_JOBS_BASE` (currently `C:\Project Claude\LFPM Jobs`). Don't pass
  `--base` unless the user names a different location.
- Each shoot is **one folder** named `<Month-Day> <Address>`, e.g.
  `06-27 2719 Fort Worth`, under both `Real Estate\<Realtor>\` (raw) and
  `Final\<Realtor>\` (edited). Raw subfolders: Photos, Drone, 360, Video. Final
  subfolders mirror the Pixieset galleries: Home, Aerial, Amenities, Video, 360,
  Floorplan.
- Re-running for the same job is safe (it never deletes or overwrites).
- If you want to show the structure before creating anything, add `--dry-run`.

Always tell the user the exact paths it created so they can find them.

## File photos into the job folders

When the owner dumps a pile of photos and wants them sorted, run the filer. It finds the
job by **address alone** (no need for the realtor or date), classifies each file by its
name/type, and drops it in the right subfolder.

1. **Which stage?** Raw camera files / "the photos" → `raw`. Edited / "finals" / "the
   edited ones" → `final`. Default to `raw` if unsaid — raw comes first in the pipeline.
2. **Where are the files?** By default the owner dumps them straight into the job folder,
   so the filer sorts them in place. If they point at another folder (Downloads, the SD
   card), pass `--source "<that folder>"`.
3. **Preview, then commit.** Run `--dry-run` first and show the plan (what lands where).
   Once the owner confirms, run it for real — it *moves* the files, so the dry-run check
   matters.

```bash
python tools/file-photos.py --address "2719 Fort Worth" --dry-run        # preview (raw)
python tools/file-photos.py --address "2719 Fort Worth"                  # do it (raw)
python tools/file-photos.py --address "2719 Fort Worth" --stage final    # edited photos
```

How it classifies: drone (`DJI_*` or "drone") → Drone (raw) / Aerial (final); video →
Video; Insta360 `.insp`/`.insv` or "360"/"pano" → 360; PDFs or "floor" → Floorplan
(final); everything else that's a photo → Photos (raw) / Home (final).

Flag these to the owner when relevant:
- **Amenity shots read the same as interior shots by filename**, so on `final` they land
  in Home/. Mention it so they can move any amenity shots into Amenities/.
- **If no job folder matches the address**, the job hasn't been set up yet — create it
  first with `new-job.py` (you'll need the realtor and shoot date), then file.

## Publish or update a listing tour — route, don't reinvent

These already have dedicated, well-built skills. Read and follow them rather than
duplicating their logic here:

- **New tour from an MLS link / folder of photos → the `new-property` skill.**
- **Edit an existing tour (photos, sections, hero, MLS facts, status) → the
  `update-property` skill.**

Hand off cleanly: confirm the one or two things that skill needs (MLS URL, photo
folder path, or which property + what change) and let it run.

## Send the delivery email

At delivery, consolidate everything into one branded email instead of texting links
separately. Gather the realtor's name, the property, and whichever links exist, then
produce a ready-to-send email. **Blank deliverables are simply omitted** — never
invent a link or leave a placeholder.

Deliverables to ask for (only what's relevant to this job):
Pixieset photo gallery · video · 360° virtual tour · 2D floor plan · listing website.

Build the email from the template and rules in
[references/pipeline.md](references/pipeline.md) (subject line, branded body, the exact
contact block, and the plain-text version). Output a **subject line + a clean,
paste-ready body** the owner can drop into Gmail or a text. If the user wants the fully
styled HTML email, point them to the browser tool at `tools/delivery-email.html`, which
renders and copies the branded version.

## Where am I / what's next

When the user asks how the system works or what to do next, walk them through the
pipeline map above in plain language, grounded in where their current job is. The full
narrative version — including what HoneyBook handles vs. what's manual — lives in
[references/pipeline.md](references/pipeline.md) and in the repo's `docs/AUTOMATION.md`.

## Fixed facts (don't change without the owner's say-so)

- Jobs base: `C:\Project Claude\LF Propery Media\Filing System` (env var `LF_JOBS_BASE`);
  job folders live under `Real Estate\` and `Final\` there, excluded from deploy via `.assetsignore`
- Repo root for the tools: `C:\Users\joshu\Downloads\LF Gallery`
- Contact block for client emails: **(941) 387-5399** · **l.f.gallery03@gmail.com** ·
  **@lfpropertymedia** · Sarasota, FL
- Tone for anything client-facing: confident, minimal, warm. No exclamation points,
  no hype.
