import { requireUser, json } from '../../_lib/session.js';

/** Load a job the caller is allowed to touch. Tenant is in the WHERE clause, not
 *  checked afterwards, so there is no path where a wrong id returns a row. */
async function load(env, user, id, requested) {
  const tenant = requested && user.role === 'owner' ? requested : user.tenant_id;
  if (requested && requested !== tenant) return null;
  return env.DB.prepare(
    `SELECT * FROM jobs WHERE id = ? AND tenant_id = ?`).bind(id, tenant).first();
}

export const onRequestGet = requireUser(async ({ params, request, env, data }) => {
  const job = await load(env, data.user, params.id,
    new URL(request.url).searchParams.get('tenant'));
  // 404 rather than 403 for a job in another tenant: a 403 confirms the id is
  // real, which is a slow way to enumerate every job on the platform.
  if (!job) return json({ error: 'not_found' }, 404);

  const { results } = await env.DB.prepare(
    `SELECT id, filename, size, kind, status, created_at
       FROM job_files WHERE job_id = ? ORDER BY kind, filename`).bind(job.id).all();

  return json({ job, files: results ?? [] });
});

/** Submit for processing, or edit the details while it is still a draft. */
export const onRequestPatch = requireUser(async ({ params, request, env, data }) => {
  let body = {};
  try { body = await request.json(); } catch { return json({ error: 'bad_request' }, 400); }

  const job = await load(env, data.user, params.id, body?.tenant);
  if (!job) return json({ error: 'not_found' }, 404);

  const now = Math.floor(Date.now() / 1000);

  if (body.action === 'submit') {
    if (job.status !== 'draft') return json({ error: 'not_a_draft', status: job.status }, 409);
    const ready = await env.DB.prepare(
      `SELECT count(*) AS n FROM job_files
        WHERE job_id = ? AND kind = 'raw' AND status = 'stored'`).bind(job.id).first();
    // Submitting nothing would hand the runner a job it can only fail.
    if ((ready?.n ?? 0) === 0) return json({ error: 'no_files' }, 400);

    // Guarded on status so two clicks cannot both submit.
    const r = await env.DB.prepare(
      `UPDATE jobs SET status='queued', submitted_at=? WHERE id=? AND status='draft'`)
      .bind(now, job.id).run();
    if ((r.meta?.changes ?? 0) !== 1) return json({ error: 'not_a_draft' }, 409);

    await env.DB.prepare(
      `INSERT INTO audit (id, tenant_id, user_id, action, subject, created_at)
       VALUES (?, ?, ?, 'job.submit', ?, ?)`)
      .bind(crypto.randomUUID(), job.tenant_id, data.user.id, job.id, now).run();

    return json({ job: { ...job, status: 'queued', submitted_at: now }, files: ready?.n ?? 0 });
  }

  if (body.action === 'update') {
    if (job.status !== 'draft') return json({ error: 'not_a_draft', status: job.status }, 409);
    const address = String(body?.address ?? '').trim().slice(0, 200) || null;
    const note = String(body?.note ?? '').trim().slice(0, 2000) || null;
    await env.DB.prepare(`UPDATE jobs SET address=?, note=? WHERE id=?`)
      .bind(address, note, job.id).run();
    return json({ job: { ...job, address, note } });
  }

  return json({ error: 'unknown_action' }, 400);
});
