-- Intake: a client drops raw brackets, LF processes them into a tour.
--
-- A job is the unit of work between "the realtor has files" and "there is a
-- tour". It exists so both sides can see the same state: the client watches it
-- move, and the processing box has a queue to pull from.
--
-- The fusion itself never runs in a Worker -- 4.3 GB peak per panorama against a
-- 128 MB limit -- so `status` is the contract between the API and a machine with
-- real memory, not a description of something happening inside Cloudflare.

PRAGMA foreign_keys = ON;

CREATE TABLE jobs (
  id           TEXT PRIMARY KEY,
  tenant_id    TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  created_by   TEXT REFERENCES users(id) ON DELETE SET NULL,
  -- Free text at intake. The realtor knows the address long before there is a
  -- properties row, and forcing them to create one first would put a form in
  -- front of a drag-and-drop.
  address      TEXT,
  note         TEXT,
  -- Set once processing produces a tour.
  property_id  TEXT REFERENCES properties(id) ON DELETE SET NULL,
  tour_id      TEXT REFERENCES tours(id) ON DELETE SET NULL,

  --   draft      files still arriving; the client can add or remove
  --   queued     client pressed submit; waiting for the processing box
  --   processing claimed by a runner
  --   ready      panoramas built, awaiting review
  --   published  tour is live
  --   failed     runner gave up; `error` says why
  status       TEXT NOT NULL DEFAULT 'draft'
               CHECK (status IN ('draft','queued','processing','ready','published','failed')),
  error        TEXT,
  -- Which runner holds it, and since when. A job claimed by a machine that then
  -- died has to be reclaimable, and that needs a timestamp to age out.
  claimed_by   TEXT,
  claimed_at   INTEGER,

  created_at   INTEGER NOT NULL,
  submitted_at INTEGER,
  finished_at  INTEGER
);

CREATE INDEX idx_jobs_tenant ON jobs(tenant_id, created_at);
-- The runner's query: oldest queued job first.
CREATE INDEX idx_jobs_queue ON jobs(status, submitted_at);

CREATE TABLE job_files (
  id           TEXT PRIMARY KEY,
  job_id       TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  tenant_id    TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  filename     TEXT NOT NULL,
  r2_key       TEXT NOT NULL UNIQUE,
  size         INTEGER,
  -- Raw brackets in, finished panoramas out. Keeping both on one table means a
  -- job's whole file history is one query, and derived files can be re-made
  -- without touching the originals.
  kind         TEXT NOT NULL DEFAULT 'raw' CHECK (kind IN ('raw','pano','thumb','floorplan')),
  -- R2 multipart state. Cleared on completion; a row still carrying an upload_id
  -- is an abandoned upload and can be aborted.
  upload_id    TEXT,
  status       TEXT NOT NULL DEFAULT 'uploading'
               CHECK (status IN ('uploading','stored','failed')),
  created_at   INTEGER NOT NULL
);

CREATE INDEX idx_job_files_job ON job_files(job_id, kind);
-- One name per job: re-dropping the same file replaces it rather than
-- silently storing two copies that later fuse into the wrong bracket set.
CREATE UNIQUE INDEX idx_job_files_name ON job_files(job_id, filename, kind);
