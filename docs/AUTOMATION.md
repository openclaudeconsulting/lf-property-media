# LF Property Media — Automation Guide

How the backend of the business is automated, what's still manual (and why), and
how to run each tool. Written for the owner + whoever maintains the systems.

The work splits into three buckets:

- 🟢 **Website tools we built** — code in this repo, ours to change, no subscription.
- 🔵 **HoneyBook-native** — configure once inside HoneyBook; it runs the booking,
  payments, and scheduling. We deliberately did **not** rebuild these in code —
  HoneyBook already does deposits, payment schedules, and self-scheduling well, and
  its API is closed. Feeding it cleanly beats fighting it.
- ⚪ **Manual** — creative or tool-locked steps with no real automation surface.

---

## The 10 phases at a glance

| # | Phase | Status | How it's handled |
|---|-------|--------|------------------|
| 1 | Client intake | 🟢🔵 | Instant-quote calculator on the site → HoneyBook smart file captures the booking |
| 2 | Scheduling | 🔵 | HoneyBook scheduler (self-book open slots) |
| 3 | Invoicing & 50% deposit | 🔵 | HoneyBook payment schedule + on-booking automation |
| 4 | On-site shoot | ⚪ | Manual (shooting); floor plan auto-emailed by the phone app |
| 5 | File organization | 🟢 | `tools/new-job.py` scaffolds the raw + final folder trees |
| 6 | Photo editing | ⚪ | RealtyAI + Pixieset (no API); folders are pre-made by Phase 5 |
| 7 | 360 / virtual tour | ⚪ | Fiverr editor + CloudPano (manual stitching) |
| 8 | Video editing | ⚪ | Editor via Drive (manual) |
| 9 | Delivery | 🟢 | `tools/delivery-email.html` builds one branded email with every link |
| 10 | Final payment | 🔵 | HoneyBook balance invoice (on-delivery automation or set date) |

Plus: 🟢 **Listing websites** — `tools/build-property.py` generates a branded
property tour page per listing.

---

## 🟢 The tools we built

### 1. Instant-quote calculator
**Where:** [`packages.html`](../packages.html) → the "Build your quote" section
(anchor `#build-quote`). Also linked from the homepage and contact page.

A realtor enters square footage, picks a package, and adds à-la-carte items; the
price updates live using your published rates (sq-ft brackets, the $100/5 drone
bundle, and the Premier/Platinum 50%-off virtual tour are all built in). They then
**Continue to booking** (your HoneyBook form) or **Copy quote summary** to paste the
itemized lines into a message — or into a HoneyBook invoice.

Nothing to run; it's part of the live site. Prices live in this section's markup —
if pricing ever changes, update them here *and* in HoneyBook so they match.

### 2. New-job folder generator (Phase 5)
**File:** [`tools/new-job.py`](../tools/new-job.py) (double-click `tools/new-job.bat` on Windows)

Builds the standard folder structure for a shoot so you never hand-make folders:

```
<base>/Real Estate/<Realtor Name>/<Month-Day> <Address>/   Photos  Drone  360  Video
<base>/Final/<Realtor Name>/<Month-Day> <Address>/         Home  Aerial  Amenities  Video  360  Floorplan
```

The Final sub-folders mirror the Pixieset galleries (Home / Aerial / Amenities).

```bash
python tools/new-job.py --realtor "John Smith" --address "2719 Fort Worth Street, Sarasota"
python tools/new-job.py --realtor "John Smith" --address "2719 Fort Worth St" --date 2026-06-26
python tools/new-job.py                 # interactive — prompts for everything
python tools/new-job.py ... --open      # open the raw folder when done
python tools/new-job.py ... --dry-run   # preview only
```

Set your base folder once so you never pass `--base`:
```powershell
setx LF_JOBS_BASE "D:\LF Property Media"
```
New jobs then land under `D:\LF Property Media\Real Estate\...` and `...\Final\...`.
Re-running for an existing job is safe — it never deletes or overwrites.

### 3. Delivery email builder (Phase 9)
**File:** [`tools/delivery-email.html`](../tools/delivery-email.html) — open it in any browser.

Consolidates every deliverable into **one branded email**. Fill in the realtor name,
property, and whatever links you have (Pixieset gallery, video, 360 tour, 2D floor
plan, listing website) — blanks are skipped automatically. Then:

- **Copy email (paste into Gmail)** — pastes as a formatted, branded email.
- **Copy as plain text** — for anywhere rich formatting won't paste.
- **Open in mail app** — opens your mail client pre-filled (subject, body, recipient).

Your sign-off name is remembered on that computer.

### 4. Property listing-tour generator
**File:** [`tools/build-property.py`](../tools/build-property.py)

Generates a branded full-screen tour page per listing from a `listing.json` +
photos, and keeps the `/properties/` hub in sync.

```bash
python tools/build-property.py --new 123-bay-shore-road   # scaffold a new listing (draft)
python tools/build-property.py 123-bay-shore-road         # build it after adding photos
python tools/build-property.py --all                      # rebuild everything + hub
```

New listings scaffold as a **draft** (hidden from the public hub) until you add
photos, fill in `listing.json`, and set `"status":"active"` + `"unlisted":false`.

---

## 🔵 HoneyBook setup checklist (the booking spine)

These are configured inside HoneyBook, not in code. One-time setup, then automatic:

- [ ] **Service-selection smart file** — already live (the contact page links to it).
      Keep its services/prices matched to the website calculator.
- [ ] **Payment schedule** — set every invoice to **50% deposit due at booking,
      50% balance** due on/after delivery. This is a built-in HoneyBook feature.
- [ ] **Scheduler** — publish your open time slots so realtors self-book (Phase 2).
      Optionally embed the scheduler link on the contact page.
- [ ] **On-booking automation** — when a client books: create the project and send
      the 50% deposit invoice automatically (Phase 3).
- [ ] **On-delivery automation** — send the remaining 50% balance invoice on delivery
      or on a set date (Phase 10).

> Why HoneyBook and not custom code: it already does deposits, payment schedules, and
> self-scheduling natively, and has no open API to build against. Configuring it is
> faster and far less fragile than rebuilding payments on the website.

---

## ⚪ What stays manual (and why)

- **Shooting** (Phase 4) — the actual photography/drone/360/video capture.
- **Photo editing** (Phase 6) — RealtyAI processes the images; no automation API.
  (The destination folders are already made by `new-job.py`.)
- **Virtual tours** (Phase 7) — Fiverr 360 editing + CloudPano room-linking are
  hands-on and tool-locked.
- **Video editing** (Phase 8) — handed to an editor via Drive.

The 2D floor plan is effectively automated already — the phone app emails the
finished plan back with no editing.

---

## Connecting the pieces

Glue between apps is kept lean — **no paid Zapier/Make**. Preference is HoneyBook's
own automations for the booking spine, plus small custom scripts/Cloudflare Workers
where needed. Note one real limit: cloud services (HoneyBook, Zapier) can't create
folders on the local computer — that's exactly why the folder generator is a local
script you run (or trigger) yourself.
