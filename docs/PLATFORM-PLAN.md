# Platform plan — multi-tenant tours

Status: **draft for approval**. Nothing here is built. Written 2026-08-06.

The goal is a service where a realtor (or their photographer) drops raw 360
brackets somewhere, LF processes and grades them, and a finished tour is
published under a link that works in the MLS — with each realtor able to fix
their own hotspots behind a login, and the public seeing a clean viewer.

---

## 1. What already exists

| Piece | State |
|---|---|
| Bracket fusion + real-estate grade (`tools/pano-hdr/`) | Works. 6080×3040 native, Mertens fusion, 16° nadir. |
| Tour viewer (`tours/<slug>/index.html`) | Works. PSV 5, horizontal-FOV zoom model, hotspot editor. |
| Hotspot authoring in 3D | Works, drafts saved per browser. |
| Floor-plan authoring (`tools/floor-plan.html`) | Works. Places rooms, draws the web, derives hotspot yaw from plan geometry. |
| Publishing | Manual. Download `tour.json`, commit, push, Pages rebuilds. |
| Multi-tenancy | **None.** One property, hard-coded paths, panoramas in git. |
| Auth | **None.** The editor is visible to every visitor. |

The expensive parts — the pipeline, the grade, the viewer — are done. What is
missing is tenancy, storage and intake.

## 2. The finding that decides hosting

Tours reach Zillow through the **MLS "Virtual Tour URL" field**, which Zillow
ingests from the MLS feed. Any publicly reachable unbranded URL qualifies —
a self-hosted `lfpropertymedia.org` tour works today with no partnership.

The caveat is placement. A plain MLS tour URL appears as a **hyperlink in Facts
and Features**. Zillow's own 3D Home tours and a short list of partner providers
appear **in the photo carousel**, which is worth far more attention. That list is
Zillow's discretion and has changed before (Matterport was dropped).

**Blocking experiment, before any of the below:** put the existing tour URL in
the MLS virtual tour field on one real listing and observe how it renders. If
self-hosting loses carousel placement and that matters commercially, the answer
may be to keep a paid provider as the delivery layer and sell processing on top.
Everything in section 4 assumes self-hosting is acceptable.

## 3. Target architecture

Cloudflare throughout, because the site is already there and the economics fit.

```
intake (dropbox / upload)  ->  job queue  ->  processing box  ->  R2
                                                                   |
realtor browser  <->  Pages Functions (API + auth)  <->  D1  <------+
public browser   <->  Pages (static viewer)  <->  R2 (panoramas via CDN)
```

- **R2** for panoramas. A tour is ~77 MB; zero egress is the whole argument, and
  it gets bulk media out of git, which does not survive past a handful of jobs.
- **D1** for tenants, users, properties, tours, links, audit.
- **Pages Functions** for the API, session auth and signed upload URLs.
- **Processing stays on real hardware.** Mertens fusion peaks at ~4.3 GB per
  panorama against a Worker's 128 MB. This cannot be serverless. It runs on the
  owner's machine today; at volume it becomes a queue worker on a rented box.
  Design the intake around "a job is picked up by a machine with real RAM".

### Multi-tenant layout

URLs — public tour stays flat and pretty, because it goes in the MLS:

```
/t/<tour-slug>/                 public viewer      (unbranded, MLS-safe)
/app/                           realtor console    (auth required)
/app/tours/<tour-slug>/edit     hotspot + plan editor
/api/*                          Pages Functions
```

Storage:

```
r2://tours/<tenant>/<tour>/panos/NN-room.jpg
r2://tours/<tenant>/<tour>/thumbs/NN-room.jpg
r2://tours/<tenant>/<tour>/floorplan.jpg
```

`tour.json` stops being a file and becomes a D1-backed API response. The viewer
already fetches it over HTTP, so this is a URL change, not a rewrite.

### Roles

Mirrors the CRM model: shared resources, capability varies by who is holding it.

| Role | Can |
|---|---|
| `owner` (LF) | Everything, all tenants, run/re-run processing |
| `agent` | View + edit their own tenant's tours; cannot publish new media |
| `public` | View published tours only; no editor bundle served at all |

The editor must be a **separate bundle**, not a hidden button. A public viewer
should not ship editing code.

## 4. Phases

Ordered by dependency. Phase 0 gates everything.

### Phase 0 — Prove the channel *(blocking, no code)*
- One real listing, our URL in the MLS field, observe the Zillow result.
- Decide: self-host, or paid provider as delivery layer.

### Phase 1 — Get media out of git *(independent, can start now)*
- R2 bucket, upload script, viewer reads panoramas from R2.
- Remove `tours/*/panos` from the repo; keep a pointer.
- **Parallelisable with Phase 2.**

### Phase 2 — Tenancy model *(independent, can start now)*
- D1 schema: `tenants, users, properties, tours, scenes, links`.
- `tour.json` shape becomes the API contract; viewer switches to the new endpoint.
- Migration: today's single tour becomes tenant #1, tour #1.
- **Parallelisable with Phase 1.**

### Phase 3 — Auth + split bundles *(needs 2)*
- Session auth, per-tenant scoping, `owner`/`agent` roles.
- Public viewer bundle vs editor bundle; editor served only to an authorised session.
- Save writes through the API instead of localStorage. Drafts stay as the offline
  fallback — they are the only thing that survives a dropped connection.

### Phase 4 — Intake *(needs 1)*
- Upload endpoint issuing signed R2 URLs; job row in D1.
- Queue + worker on a real box running the existing `pano_hdr` pipeline.
- Status visible to the realtor: received → processing → ready → published.

### Phase 5 — Console *(needs 3, 4)*
- Realtor-facing list of properties, job status, tour editing, publish button.
- Reuse the existing 3D hotspot editor and floor-plan editor as panels.

## 5. Decisions still needed

1. **Zillow result** (Phase 0) — self-host or outsource delivery.
2. **Auth**: roll our own sessions on D1, or buy (Clerk/Auth0/Cloudflare Access)?
   Buying is faster and safer; per-seat cost matters if every agent needs a login.
3. **Custom domains per realtor?** Branded tours on the agent's own domain is a
   common upsell, and it changes the routing design if it comes later.
4. **Who owns the media** — is a tour deleted when a realtor leaves?
5. **Processing box**: owner's desktop indefinitely, or rented hardware, and at
   what job volume does that flip?

## 5a. Known environment traps

**`wrangler pages dev` cannot reach the local D1 on this machine.** It splices
its state directory into the middle of a path containing spaces — the checkout
lives under `C:\Project Claude\LF Propery Media\…`, and wrangler resolves module
and persistence paths to `C:\Project Claude\.wrangler\LF Propery Media\…`. The
server starts and routing works, but every D1 query hits an empty database and
returns `no such table: users`. `--persist-to` does not correct it, and
`pages dev` has no `--remote`.

Consequences:

- Handler logic is covered by `tools/test-auth.mjs`, which drives the real route
  code against SQLite through a D1-shaped shim. 16 checks.
- The D1 **binding** — the integration point between the Workers runtime and the
  database — is therefore only provable on a deployed preview, not locally.
- Anyone picking this up on a path without spaces should try `pages dev` again
  first; it is likely to just work, and it is the fastest way to close that gap.

**Bindings are not in this repo.** A Pages *git* deployment ignores
`wrangler.jsonc`; production bindings (`DB` → `lf-tours`, `MEDIA` →
`lf-tour-media`) live on the project in the dashboard. The file is still the
source of truth for local dev and for `wrangler d1 execute`.

## 6. Notes for whoever builds this

- Do not put the pipeline behind a Worker. It will not fit. See section 3.
- Panoramas are immutable once graded; treat them as content-addressed and cache
  hard. Only `tour.json` changes after publish.
- Hotspot links are reciprocal everywhere in the existing code. Any schema must
  keep that invariant or half the graph rots — see `unlink`/`ensureReturn`.
- Every scene currently has a return link (verified, 44/44). The viewer's arrival
  orientation depends on it; a schema that allows one-way links must handle the
  fallback.
- The unbranded requirement is not cosmetic. MLSs fine agents for branded links
  in unbranded fields, so the public tour must stay free of agent contact detail.
