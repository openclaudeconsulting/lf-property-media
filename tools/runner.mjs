/* The processing workhorse.
 *
 *   node tools/runner.mjs            # claim one job, process it, exit
 *   node tools/runner.mjs --watch    # keep polling
 *   node tools/runner.mjs --once --dry-run
 *
 * Claims a queued job, pulls its raw brackets out of R2, runs the pano_hdr
 * pipeline, pushes the finished panoramas back, writes the tour into D1 and
 * marks the job ready for review.
 *
 * This runs here rather than in a Worker because it cannot run in a Worker:
 * Mertens fusion peaks around 4.3 GB per panorama against a 128 MB limit. The
 * `status` column is the contract between the two halves -- Cloudflare receives
 * and queues, this machine does the work.
 *
 * Work happens under Filing System/_runner/, inside the project, and is removed
 * on success. Nothing is written to the system temp directory.
 */
import { execFileSync } from 'node:child_process';
import { mkdirSync, rmSync, readdirSync, statSync, existsSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { hostname } from 'node:os';
import { d1, r2get, r2put } from './_cf.mjs';

// fileURLToPath, not url.pathname: the project lives under "C:\Project Claude\
// LF Propery Media", and pathname hands back percent-encoded spaces plus a
// leading slash before the drive letter.
const ROOT = resolve(fileURLToPath(new URL('..', import.meta.url)));
const WORK = join(ROOT, 'Filing System', '_runner');
const PANO = join(ROOT, 'tools', 'pano-hdr', 'pano_hdr.py');

const args = process.argv.slice(2);
const has = (f) => args.includes(`--${f}`);
const WATCH = has('watch');
const DRY = has('dry-run');
const POLL_MS = 20_000;
// A runner that dies mid-job leaves the row claimed. After this long another
// runner (or the same one restarted) may take it back.
const STALE_CLAIM_S = 45 * 60;
const ME = `${hostname()}:${process.pid}`;

const now = () => Math.floor(Date.now() / 1000);
const log = (...m) => console.log(new Date().toISOString().slice(11, 19), ...m);
const uuid = () => crypto.randomUUID();
const slugify = (s) => String(s ?? '').toLowerCase()
  .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 60) || 'property';

/* ------------------------------------------------------------------ claim */

async function reclaimStale() {
  const { meta } = await d1(
    `UPDATE jobs SET status='queued', claimed_by=NULL, claimed_at=NULL
      WHERE status='processing' AND claimed_at < ?`, [now() - STALE_CLAIM_S]);
  if (meta.changes) log(`reclaimed ${meta.changes} stale job(s)`);
}

/** Atomic claim: the UPDATE is guarded on status, so two runners cannot both win. */
async function claim() {
  const { results } = await d1(
    `UPDATE jobs SET status='processing', claimed_by=?, claimed_at=?
      WHERE id = (SELECT id FROM jobs WHERE status='queued'
                   ORDER BY submitted_at LIMIT 1)
        AND status='queued'
      RETURNING id, tenant_id, address, note`, [ME, now()]);
  return results[0] ?? null;
}

async function fail(job, message) {
  log(`FAILED ${job.id}: ${message}`);
  await d1(`UPDATE jobs SET status='failed', error=?, finished_at=?, claimed_by=NULL WHERE id=?`,
    [String(message).slice(0, 1000), now(), job.id]);
}

/* ------------------------------------------------------------- processing */

/* No shell. python is a real executable, so execFileSync can invoke it directly
 * and pass arguments as a proper argv -- which matters because every path here
 * contains spaces ("C:\Project Claude\LF Propery Media"). Going through a shell
 * would concatenate them unescaped and python would be handed "C:\Project". */
function run(cmd, cmdArgs, opts = {}) {
  return execFileSync(cmd, cmdArgs, {
    encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'],
    maxBuffer: 64 * 1024 * 1024, ...opts,
  });
}

async function process_(job) {
  const dir = join(WORK, job.id);
  const rawDir = join(dir, 'raw');
  const outDir = join(dir, 'out');
  rmSync(dir, { recursive: true, force: true });
  mkdirSync(rawDir, { recursive: true });
  mkdirSync(outDir, { recursive: true });

  const { results: files } = await d1(
    `SELECT filename, r2_key FROM job_files
      WHERE job_id=? AND kind='raw' AND status='stored' ORDER BY filename`, [job.id]);
  if (!files.length) throw new Error('no stored raw files');

  log(`  pulling ${files.length} file(s) from R2`);
  for (const f of files) r2get(f.r2_key, join(rawDir, f.filename));

  // Bracket size is inferred, not assumed: a shoot is N positions x B exposures,
  // and guessing B wrong fuses frames from two different rooms into one image.
  const scan = run('python', [PANO, 'scan', rawDir, '--bracket', String(bracketSize(files.length))]);
  const positions = Number(/->\s*(\d+)\s*panorama/.exec(scan)?.[1] ?? 0);
  if (!positions) throw new Error(`scan found no bracket sets:\n${scan.slice(-500)}`);
  log(`  ${positions} tripod position(s)`);

  log('  fusing — this is the slow part');
  run('python', [PANO, 'build', rawDir, outDir,
    '--bracket', String(bracketSize(files.length)),
    '--preset', 'natural', '--engine', 'mertens',
    '--nadir', '16', '--max-width', '0', '--quality', '90']);

  const panos = readdirSync(outDir).filter((f) => /^pano_\d+\.jpg$/.test(f)).sort();
  if (!panos.length) throw new Error('build produced no panoramas');
  return { dir, outDir, panos };
}

/** Largest plausible bracket count that divides the frame count exactly. */
function bracketSize(total) {
  for (const b of [9, 7, 5, 3]) if (total % b === 0) return b;
  return 1;
}

/* ----------------------------------------------------------------- publish */

async function publish(job, { outDir, panos }) {
  const address = job.address || 'Untitled property';
  const propertyId = uuid();
  const tourId = uuid();
  let slug = slugify(address);

  // Slugs are the public tour URL and must be unique across every tenant,
  // because that URL goes in the MLS field and has to resolve on its own.
  const { results: clash } = await d1(`SELECT 1 FROM tours WHERE slug=?`, [slug]);
  if (clash.length) slug = `${slug}-${tourId.slice(0, 6)}`;

  await d1(`INSERT INTO properties (id, tenant_id, address, created_at) VALUES (?,?,?,?)`,
    [propertyId, job.tenant_id, address, now()]);
  await d1(`INSERT INTO tours (id, tenant_id, property_id, slug, status, created_at)
            VALUES (?,?,?,?,'draft',?)`, [tourId, job.tenant_id, propertyId, slug, now()]);

  const sceneIds = [];
  for (const [i, name] of panos.entries()) {
    const n = i + 1;
    const sceneId = uuid();
    const base = `tenants/${job.tenant_id}/tours/${tourId}`;
    const panoKey = `${base}/panos/${name}`;
    const thumbKey = `${base}/thumbs/${name}`;

    r2put(panoKey, join(outDir, name), 'image/jpeg');
    const thumb = join(outDir, '_previews', name);
    if (existsSync(thumb)) r2put(thumbKey, thumb, 'image/jpeg');

    await d1(
      `INSERT INTO scenes (id, tour_id, tenant_id, name, ordinal, pano_key, thumb_key)
       VALUES (?,?,?,?,?,?,?)`,
      // Rooms are named by a human later; a number beats a wrong guess.
      [sceneId, tourId, job.tenant_id, `Room ${n}`, n, panoKey, thumbKey]);
    sceneIds.push(sceneId);
    if (n % 5 === 0 || n === panos.length) log(`  uploaded ${n}/${panos.length}`);
  }

  // A walkable chain so the tour is navigable before anyone opens the editor.
  // Reciprocal, because a one-way door strands the visitor and the viewer reads
  // the return link to decide which way to face on arrival.
  for (let i = 0; i < sceneIds.length - 1; i++) {
    const [a, b] = [sceneIds[i], sceneIds[i + 1]];
    await d1(`INSERT INTO links (id,tour_id,tenant_id,from_scene,to_scene,yaw,pitch,estimated)
              VALUES (?,?,?,?,?,0,-8,1),(?,?,?,?,?,180,-8,1)`,
      [uuid(), tourId, job.tenant_id, a, b, uuid(), tourId, job.tenant_id, b, a]);
  }

  await d1(`UPDATE tours SET default_scene=? WHERE id=?`, [sceneIds[0], tourId]);
  await d1(`UPDATE jobs SET status='ready', tour_id=?, property_id=?, finished_at=?,
                            claimed_by=NULL, error=NULL WHERE id=?`,
    [tourId, propertyId, now(), job.id]);
  await d1(`INSERT INTO audit (id,tenant_id,user_id,action,subject,detail,created_at)
            VALUES (?,?,NULL,'job.processed',?,?,?)`,
    [uuid(), job.tenant_id, job.id, JSON.stringify({ tourId, scenes: panos.length }), now()]);

  return { tourId, slug, scenes: panos.length };
}

/* -------------------------------------------------------------------- loop */

async function tick() {
  await reclaimStale();
  const job = await claim();
  if (!job) return false;

  log(`claimed ${job.id} — ${job.address ?? '(no address)'}`);
  if (DRY) {
    await d1(`UPDATE jobs SET status='queued', claimed_by=NULL, claimed_at=NULL WHERE id=?`, [job.id]);
    log('  dry run — released');
    return true;
  }

  try {
    const built = await process_(job);
    const out = await publish(job, built);
    rmSync(built.dir, { recursive: true, force: true });
    log(`done ${job.id} -> tour ${out.slug} (${out.scenes} scenes)`);
  } catch (e) {
    // The work directory is deliberately left behind on failure: it holds the
    // raw files and whatever the build managed, which is what anyone diagnosing
    // this will want. Success is what cleans up.
    await fail(job, e.stdout ? `${e.message}\n${String(e.stdout).slice(-800)}` : e.message);
  }
  return true;
}

mkdirSync(WORK, { recursive: true });
if (!existsSync(PANO)) { console.error(`pano_hdr.py not found at ${PANO}`); process.exit(1); }

log(`runner ${ME}${WATCH ? ' (watching)' : ''}${DRY ? ' (dry run)' : ''}`);
if (WATCH) {
  for (;;) {
    try { if (!await tick()) await new Promise((r) => setTimeout(r, POLL_MS)); }
    catch (e) { log(`poll error: ${e.message}`); await new Promise((r) => setTimeout(r, POLL_MS)); }
  }
} else {
  const did = await tick();
  if (!did) log('nothing queued');
}
