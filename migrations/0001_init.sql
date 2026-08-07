-- LF Property Media — multi-tenant tours, initial schema.
--
-- Conventions:
--   * ids are text uuids, generated in the Worker (crypto.randomUUID)
--   * timestamps are unix seconds (INTEGER) — SQLite has no date type and
--     storing text dates makes every comparison a string comparison
--   * every tenant-scoped row carries tenant_id directly, even where it could be
--     reached by a join. Authorisation filters run on every request and a missing
--     WHERE tenant_id is the bug that leaks one realtor's listings to another;
--     having the column on the row makes that filter impossible to forget.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------- tenancy

-- A brokerage, a team, or a single independent agent.
CREATE TABLE tenants (
  id          TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  slug        TEXT NOT NULL UNIQUE,      -- reserved for per-tenant subdomains later
  status      TEXT NOT NULL DEFAULT 'active'
              CHECK (status IN ('active','suspended')),
  created_at  INTEGER NOT NULL
);

CREATE TABLE users (
  id          TEXT PRIMARY KEY,
  tenant_id   TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  email       TEXT NOT NULL,
  name        TEXT,
  -- 'owner' is LF staff and crosses tenants; the check is enforced in code
  -- because SQLite cannot express "owner may ignore tenant_id".
  role        TEXT NOT NULL DEFAULT 'agent'
              CHECK (role IN ('owner','agent')),
  status      TEXT NOT NULL DEFAULT 'active'
              CHECK (status IN ('active','disabled')),
  created_at  INTEGER NOT NULL,
  last_seen   INTEGER
);

-- Emails are compared case-insensitively, so uniqueness has to be too, or
-- Josh@x.com and josh@x.com become two accounts that both look correct.
CREATE UNIQUE INDEX idx_users_email ON users(lower(email));
CREATE INDEX idx_users_tenant ON users(tenant_id);

-- ------------------------------------------------------------ credentials
--
-- Split from `users` so a person can hold more than one way of proving who they
-- are, and so adding magic links later is an INSERT rather than a migration.
-- `secret` means whatever `kind` says it means:
--   password  -> PBKDF2 hash, self-describing (see functions/_lib/crypto.js)
--   magiclink -> SHA-256 of a single-use token, with expires_at set
CREATE TABLE credentials (
  id          TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  kind        TEXT NOT NULL CHECK (kind IN ('password','magiclink')),
  secret      TEXT NOT NULL,
  expires_at  INTEGER,                   -- null for passwords
  used_at     INTEGER,                   -- single-use kinds only
  created_at  INTEGER NOT NULL
);

CREATE INDEX idx_credentials_user ON credentials(user_id, kind);

-- A password is replaced, never accumulated; one row per user enforces it.
CREATE UNIQUE INDEX idx_credentials_password
  ON credentials(user_id) WHERE kind = 'password';

-- --------------------------------------------------------------- sessions
--
-- Only the SHA-256 of the cookie value is stored. A dump of this table cannot
-- be replayed as a login, which is the entire point of not storing the token.
CREATE TABLE sessions (
  id          TEXT PRIMARY KEY,          -- sha256(token), hex
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  tenant_id   TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  created_at  INTEGER NOT NULL,
  expires_at  INTEGER NOT NULL,
  user_agent  TEXT,
  ip          TEXT
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_expiry ON sessions(expires_at);

-- ------------------------------------------------------------- properties

CREATE TABLE properties (
  id          TEXT PRIMARY KEY,
  tenant_id   TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  address     TEXT NOT NULL,
  city        TEXT,
  state       TEXT,
  beds        REAL,
  baths       REAL,
  sqft        INTEGER,
  year_built  INTEGER,
  mls         TEXT,
  price       TEXT,                      -- text: "$725,000", "Call for price"
  created_at  INTEGER NOT NULL
);

CREATE INDEX idx_properties_tenant ON properties(tenant_id);

-- ------------------------------------------------------------------ tours

CREATE TABLE tours (
  id            TEXT PRIMARY KEY,
  tenant_id     TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  property_id   TEXT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  -- The public URL is /t/<slug>. Unique across every tenant because that URL
  -- goes in the MLS virtual tour field and has to resolve on its own.
  slug          TEXT NOT NULL UNIQUE,
  status        TEXT NOT NULL DEFAULT 'draft'
                CHECK (status IN ('draft','published','archived')),
  default_scene TEXT,                    -- scenes.id; set once scenes exist
  floor_plan    TEXT,                    -- R2 key, null until one is uploaded
  created_at    INTEGER NOT NULL,
  published_at  INTEGER
);

CREATE INDEX idx_tours_tenant ON tours(tenant_id);
CREATE INDEX idx_tours_property ON tours(property_id);

-- ----------------------------------------------------------------- scenes

CREATE TABLE scenes (
  id          TEXT PRIMARY KEY,
  tour_id     TEXT NOT NULL REFERENCES tours(id) ON DELETE CASCADE,
  tenant_id   TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,             -- "Dining Room"
  ordinal     INTEGER NOT NULL,          -- rail order, 1-based
  pano_key    TEXT NOT NULL,             -- R2 key for the 6080x3040 panorama
  thumb_key   TEXT NOT NULL,
  initial_yaw REAL NOT NULL DEFAULT 0,
  -- Position on the floor plan, normalised 0..1. Null until placed; the plan
  -- editor uses these to derive hotspot bearings.
  plan_x      REAL,
  plan_y      REAL
);

CREATE INDEX idx_scenes_tour ON scenes(tour_id, ordinal);

-- ------------------------------------------------------------------ links
--
-- Hotspots. Stored as directed rows, but the application maintains them in
-- pairs: every A->B has a B->A. A one-way door strands the visitor in a room
-- with no way back, and the viewer's arrival orientation reads the return link
-- to decide which way to face -- so a missing pair breaks navigation twice.
-- Enforced in code (see the tour API); SQLite cannot express it.
CREATE TABLE links (
  id          TEXT PRIMARY KEY,
  tour_id     TEXT NOT NULL REFERENCES tours(id) ON DELETE CASCADE,
  tenant_id   TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  from_scene  TEXT NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
  to_scene    TEXT NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
  yaw         REAL NOT NULL DEFAULT 0,   -- degrees, -180..180
  pitch       REAL NOT NULL DEFAULT -8,
  -- false once a human has aimed it. The plan editor only overwrites estimated
  -- ones, so this flag is what protects hand-aimed work.
  estimated   INTEGER NOT NULL DEFAULT 1 CHECK (estimated IN (0,1))
);

CREATE UNIQUE INDEX idx_links_pair ON links(from_scene, to_scene);
CREATE INDEX idx_links_tour ON links(tour_id);

-- ------------------------------------------------------------------ audit
--
-- Who moved that arrow. Cheap to write, and the first question asked when a
-- realtor says the tour changed on its own.
CREATE TABLE audit (
  id          TEXT PRIMARY KEY,
  tenant_id   TEXT,
  user_id     TEXT,
  action      TEXT NOT NULL,             -- 'tour.publish', 'links.save', ...
  subject     TEXT,                      -- id of the thing acted on
  detail      TEXT,                      -- JSON blob, small
  created_at  INTEGER NOT NULL
);

CREATE INDEX idx_audit_tenant ON audit(tenant_id, created_at);
