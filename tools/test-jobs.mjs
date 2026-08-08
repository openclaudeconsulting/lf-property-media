/* Intake test suite.  Run:  node tools/test-jobs.mjs
 *
 * Drives the real job and upload handlers against in-memory SQLite plus a fake
 * R2 binding. The fake records what the real binding would have been asked to
 * do, which is the part worth pinning: multipart state is invisible in D1, so a
 * bug there surfaces as a corrupt object rather than a failing query.
 */
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import { hashPassword } from '../functions/_lib/crypto.js';
import { onRequestPost as login } from '../functions/api/auth/login.js';
import { onRequestGet as listJobs, onRequestPost as createJob } from '../functions/api/jobs.js';
import { onRequestGet as getJob, onRequestPatch as patchJob } from '../functions/api/jobs/[id].js';
import { onRequestPost as uploadPost, onRequestPut as uploadPut } from '../functions/api/upload.js';

const sql = new DatabaseSync(':memory:');
for (const f of ['0001_init.sql', '0002_jobs.sql']) {
  sql.exec(readFileSync(new URL(`../migrations/${f}`, import.meta.url), 'utf8'));
}

const shim = {
  prepare(q) {
    let a = [];
    const api = {
      bind(...x) { a = x; return api; },
      first() { try { return sql.prepare(q).get(...a) ?? null; } catch { return null; } },
      run() { const r = sql.prepare(q).run(...a); return { meta: { changes: r.changes } }; },
      all() { return { results: sql.prepare(q).all(...a) }; },
      _run() { return api.run(); },
    };
    return api;
  },
  batch(s) { return s.map((x) => x._run()); },
};

/* Fake R2 with enough multipart surface to prove the handler drives it right. */
const r2 = { uploads: new Map(), objects: new Map(), aborted: [] };
const MEDIA = {
  createMultipartUpload(key) {
    const uploadId = `up-${r2.uploads.size + 1}`;
    r2.uploads.set(uploadId, { key, parts: new Map() });
    return { uploadId, key };
  },
  resumeMultipartUpload(key, uploadId) {
    return {
      async uploadPart(n, body) {
        const u = r2.uploads.get(uploadId);
        if (!u) throw new Error('no such upload');
        u.parts.set(n, body);
        return { partNumber: n, etag: `etag-${n}` };
      },
      async complete(parts) {
        const u = r2.uploads.get(uploadId);
        if (!u) throw new Error('no such upload');
        for (const p of parts) {
          if (!u.parts.has(p.partNumber)) throw new Error(`missing part ${p.partNumber}`);
        }
        r2.objects.set(key, parts.length);
        r2.uploads.delete(uploadId);
      },
      async abort() { r2.aborted.push(uploadId); r2.uploads.delete(uploadId); },
    };
  },
};

const now = Math.floor(Date.now() / 1000);
const H = await hashPassword('hunter2', 100_000);
sql.exec(`INSERT INTO tenants VALUES ('t1','A','a','active',${now})`);
sql.exec(`INSERT INTO tenants VALUES ('t2','B','b','active',${now})`);
sql.prepare(`INSERT INTO users VALUES ('u1','t1','a@x.com','A','agent','active',?,NULL)`).run(now);
sql.prepare(`INSERT INTO credentials VALUES ('c1','u1','password',?,NULL,NULL,?)`).run(H, now);
sql.prepare(`INSERT INTO users VALUES ('u2','t2','b@x.com','B','agent','active',?,NULL)`).run(now);
sql.prepare(`INSERT INTO credentials VALUES ('c2','u2','password',?,NULL,NULL,?)`).run(H, now);

const env = { DB: shim, MEDIA };
const req = (url, { method = 'GET', body, cookie, raw } = {}) => new Request(url, {
  method,
  headers: { 'content-type': 'application/json', ...(cookie ? { cookie } : {}) },
  ...(raw !== undefined ? { body: raw } : body ? { body: JSON.stringify(body) } : {}),
});
const call = (fn, url, opts = {}, params = {}) =>
  fn({ request: req(url, opts), env, data: {}, params });
const ck = (r) => (r.headers.get('set-cookie') || '').split(';')[0];
const signIn = async (email) => ck(await login({
  request: req('https://x', { method: 'POST', body: { email, password: 'hunter2' } }),
  env, data: {},
}));

let pass = 0, fail = 0;
const P = (n, ok) => { ok ? pass++ : fail++; console.log(`${ok ? 'PASS' : 'FAIL'}  ${n}`); };

const A = await signIn('a@x.com');
const B = await signIn('b@x.com');

P('creating a job requires a session', (await call(createJob, 'https://x/api/jobs')).status === 401);

let r = await call(createJob, 'https://x/api/jobs',
  { method: 'POST', body: { address: '2719 Fort Worth' }, cookie: A });
const job = (await r.json()).job;
P('create job -> 201 draft', r.status === 201 && job.status === 'draft');

P('another tenant cannot read the job (404, not 403)',
  (await call(getJob, 'https://x/api/jobs/x', { cookie: B }, { id: job.id })).status === 404);

/* --- upload lifecycle ---------------------------------------------------- */
r = await call(uploadPost, 'https://x/api/upload', {
  method: 'POST', cookie: A,
  body: { action: 'start', job: job.id, filename: 'IMG_001.dng', size: 110e6 },
});
const started = await r.json();
P('start upload -> 201 with a file id', r.status === 201 && !!started.fileId);
P('an r2 multipart upload was created', r2.uploads.size === 1);
P('key is namespaced by tenant and job',
  started.key === `tenants/t1/jobs/${job.id}/raw/IMG_001.dng`);

P('another tenant cannot push parts into that file',
  (await call(uploadPut, `https://x/api/upload?file=${started.fileId}&part=1`,
    { method: 'PUT', raw: 'x', cookie: B })).status === 404);

for (const n of [1, 2]) {
  r = await call(uploadPut, `https://x/api/upload?file=${started.fileId}&part=${n}`,
    { method: 'PUT', raw: `chunk-${n}`, cookie: A });
  P(`part ${n} accepted`, r.status === 200 && (await r.json()).etag === `etag-${n}`);
}
P('rejects part number 0',
  (await call(uploadPut, `https://x/api/upload?file=${started.fileId}&part=0`,
    { method: 'PUT', raw: 'x', cookie: A })).status === 400);

r = await call(uploadPost, 'https://x/api/upload', {
  method: 'POST', cookie: A,
  body: { action: 'complete', file: started.fileId,
          parts: [{ partNumber: 1, etag: 'etag-1' }, { partNumber: 2, etag: 'etag-2' }] },
});
P('complete -> 200 and the object exists', r.status === 200 && r2.objects.size === 1);
const stored = sql.prepare('SELECT status, upload_id FROM job_files WHERE id=?').get(started.fileId);
P('row is stored with no dangling upload id',
  stored.status === 'stored' && stored.upload_id === null);

/* A part list R2 rejects must not leave the row claiming to be stored. */
r = await call(uploadPost, 'https://x/api/upload', {
  method: 'POST', cookie: A,
  body: { action: 'start', job: job.id, filename: 'IMG_002.dng', size: 1e6 },
});
const badFile = (await r.json()).fileId;
r = await call(uploadPost, 'https://x/api/upload', {
  method: 'POST', cookie: A,
  body: { action: 'complete', file: badFile, parts: [{ partNumber: 9, etag: 'nope' }] },
});
P('a rejected complete -> 400 and the row is failed, not stored',
  r.status === 400
  && sql.prepare('SELECT status FROM job_files WHERE id=?').get(badFile).status === 'failed');

/* Re-dropping a filename replaces it: two copies of one frame would land in the
   same bracket set and fuse into a ghosted panorama. */
await call(uploadPost, 'https://x/api/upload', {
  method: 'POST', cookie: A,
  body: { action: 'start', job: job.id, filename: 'IMG_002.dng', size: 1e6 },
});
P('re-dropping a filename supersedes the old row',
  sql.prepare("SELECT count(*) c FROM job_files WHERE job_id=? AND filename='IMG_002.dng'")
    .get(job.id).c === 1);

/* --- path traversal ------------------------------------------------------ */
for (const name of ['../../escape.dng', 'a/b.dng', '', '.', '..']) {
  const res = await call(uploadPost, 'https://x/api/upload', {
    method: 'POST', cookie: A, body: { action: 'start', job: job.id, filename: name, size: 100 },
  });
  const j = res.status === 201 ? await res.json() : null;
  const escaped = j !== null && !j.key.startsWith(`tenants/t1/jobs/${job.id}/raw/`);
  P(`filename ${JSON.stringify(name)} cannot escape the job prefix`, !escaped);
}

/* --- submit -------------------------------------------------------------- */
r = await call(patchJob, 'https://x/api/jobs/x',
  { method: 'PATCH', body: { action: 'submit' }, cookie: A }, { id: job.id });
P('submit -> 200 queued', r.status === 200 && (await r.json()).job.status === 'queued');

r = await call(patchJob, 'https://x/api/jobs/x',
  { method: 'PATCH', body: { action: 'submit' }, cookie: A }, { id: job.id });
P('submitting twice -> 409', r.status === 409);

r = await call(uploadPost, 'https://x/api/upload', {
  method: 'POST', cookie: A, body: { action: 'start', job: job.id, filename: 'late.dng', size: 100 },
});
P('no new files once queued -> 409', r.status === 409);

const empty = (await (await call(createJob, 'https://x/api/jobs',
  { method: 'POST', body: {}, cookie: A })).json()).job;
r = await call(patchJob, 'https://x/api/jobs/x',
  { method: 'PATCH', body: { action: 'submit' }, cookie: A }, { id: empty.id });
P('submitting a job with no files -> 400', r.status === 400);

/* --- listing ------------------------------------------------------------- */
const listed = await (await call(listJobs, 'https://x/api/jobs', { cookie: A })).json();
P('list shows this tenant only', listed.jobs.length === 2);
P('list reports stored raw file counts',
  listed.jobs.find((j) => j.id === job.id).raw_files >= 1);
const other = await (await call(listJobs, 'https://x/api/jobs', { cookie: B })).json();
P('the other tenant sees none of them', other.jobs.length === 0);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
