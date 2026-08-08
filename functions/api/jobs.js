import { requireUser, scopeTenant, json } from '../_lib/session.js';

/* Jobs: the unit of work between "the realtor has files" and "there is a tour". */

export const onRequestGet = requireUser(async ({ request, env, data }) => {
  const tenant = scopeTenant(data.user, new URL(request.url).searchParams.get('tenant'));
  if (!tenant) return json({ error: 'forbidden' }, 403);

  const { results } = await env.DB.prepare(
    `SELECT j.id, j.address, j.note, j.status, j.error,
            j.created_at, j.submitted_at, j.finished_at, j.tour_id,
            count(f.id) FILTER (WHERE f.kind = 'raw' AND f.status = 'stored') AS raw_files,
            coalesce(sum(f.size) FILTER (WHERE f.kind = 'raw' AND f.status = 'stored'), 0) AS raw_bytes
       FROM jobs j
       LEFT JOIN job_files f ON f.job_id = j.id
      WHERE j.tenant_id = ?
      GROUP BY j.id
      ORDER BY j.created_at DESC`).bind(tenant).all();

  return json({ tenant, jobs: results ?? [] });
});

export const onRequestPost = requireUser(async ({ request, env, data }) => {
  let body = {};
  try { body = await request.json(); } catch { /* an empty job is legitimate */ }

  const tenant = scopeTenant(data.user, body?.tenant);
  if (!tenant) return json({ error: 'forbidden' }, 403);

  // Address is free text and optional. The realtor knows it long before there is
  // a properties row, and demanding one up front puts a form in front of a
  // drag-and-drop, which is the one thing this screen is for.
  const address = String(body?.address ?? '').trim().slice(0, 200) || null;
  const note = String(body?.note ?? '').trim().slice(0, 2000) || null;

  const id = crypto.randomUUID();
  const now = Math.floor(Date.now() / 1000);
  await env.DB.prepare(
    `INSERT INTO jobs (id, tenant_id, created_by, address, note, status, created_at)
     VALUES (?, ?, ?, ?, ?, 'draft', ?)`)
    .bind(id, tenant, data.user.id, address, note, now).run();

  return json({ job: { id, tenant_id: tenant, address, note, status: 'draft', created_at: now } }, 201);
});
