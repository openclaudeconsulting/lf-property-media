# LF Property Media — pipeline reference

Detail that backs the dispatcher in `SKILL.md`. Read this when explaining the process
or building a delivery email.

## The full job pipeline

Two halves meet in the middle: **HoneyBook** runs the money side (quote → deposit →
schedule → final invoice) and the **local tools** run the production side (folders →
listing page → delivery). The owner runs the local tools by hand, per job.

1. **Quote** — realtor picks services + square footage on the site calculator
   (`packages.html#build-quote`) and sees a price, or the owner quotes them. The
   calculator hands off to HoneyBook to book.
2. **Book + 50% deposit** — HoneyBook (automatic once configured).
3. **Folders** — `tools/new-job.py` builds the raw + final trees. ← skill runs this
4. **Shoot** — on-site capture. Manual.
5. **Offload + edit** — camera → raw folders → RealtyAI → final folders. Dumped photos
   get sorted into subfolders by `tools/file-photos.py`; the editing itself is manual.
6. **Galleries / tour / video** — Pixieset (Home/Aerial/Amenities), CloudPano 360
   tour, video editor. Manual.
7. **Listing tour (optional)** — `new-property` skill builds the property page from an
   MLS link + photos; `update-property` edits it later.
8. **Delivery** — one branded email with every link. ← skill assembles this
9. **Final payment** — HoneyBook sends the remaining 50%.

What's manual and stays manual: the shoot itself, RealtyAI photo editing, CloudPano
tour stitching, and video editing — these are creative/tool-locked with no automation
surface. The 2D floor plan is auto-emailed by the on-site phone app.

## Delivery email template

Goal: one clean, branded message to the realtor with everything at once. Only include
deliverables that actually exist for this job — omit the rest silently.

**Subject:** `Your listing media is ready — <property address>`

**Body (paste-ready plain text — the default output):**

```
Hi <Realtor first name>,

Everything for <property address> is edited and ready to go live. Here's the full set:

- Photo Gallery: <pixieset url>
- Listing Video: <video url>
- 360° Virtual Tour: <cloudpano url>
- 2D Floor Plan: <floor plan url>
- Listing Website: <listing url>

<optional one-line personal note>

Thank you,
<Sender name>
LF Property Media
(941) 387-5399 · l.f.gallery03@gmail.com · @lfpropertymedia
```

Rules:
- Drop any line whose link wasn't provided. If only a gallery and a tour exist, the
  list has two bullets — no empty "Video:" line, no "(coming soon)".
- Keep the tone confident and minimal. No exclamation points, no "Hope you love them!!"
- Use the realtor's first name if known; otherwise open with "Hi there,".
- Default to the plain-text version above — it pastes cleanly into Gmail, a text, or
  any mail app. Offer the fully styled HTML version only if asked; that lives in the
  browser tool `tools/delivery-email.html` (fill the fields, click "Copy email").

**Example**

Input: "Send the delivery email for the Fort Worth job to John — gallery is
https://lfgallery.pixieset.com/2719fortworth/, 360 tour is
https://app.cloudpano.com/tours/abc. No video on this one."

Output:
```
Subject: Your listing media is ready — 2719 Fort Worth Street

Hi John,

Everything for 2719 Fort Worth Street is edited and ready to go live. Here's the full set:

- Photo Gallery: https://lfgallery.pixieset.com/2719fortworth/
- 360° Virtual Tour: https://app.cloudpano.com/tours/abc

Thank you,
LF Property Media
(941) 387-5399 · l.f.gallery03@gmail.com · @lfpropertymedia
```
(Video and floor-plan lines omitted because no link was given. Sender name left as the
studio when the owner didn't specify one.)

## Folder structure produced by new-job.py

```
<LF_JOBS_BASE>/Real Estate/<Realtor>/<Month-Day> <Address>/   Photos  Drone  360  Video
<LF_JOBS_BASE>/Final/<Realtor>/<Month-Day> <Address>/         Home  Aerial  Amenities  Video  360  Floorplan
```

The Final subfolders mirror the Pixieset galleries (Home / Aerial / Amenities) plus
homes for the video, 360s, and the 2D floor plan. `LF_JOBS_BASE` is currently
`C:\Project Claude\LF Propery Media\Filing System` (job folders under `Real Estate\` and `Final\`).
