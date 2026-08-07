import { verifyPassword } from '../../_lib/crypto.js';
import { createSession, cookieHeader, json } from '../../_lib/session.js';

/* Deliberately uniform failures.
 *
 * Wrong email and wrong password return the same body, the same status, and --
 * because the dummy verify below burns the same PBKDF2 cost as a real one --
 * close to the same duration. Skipping the hash for an unknown address is the
 * classic account-enumeration leak: the "no such user" path returns in 2ms and
 * the "wrong password" path in 70ms, so anyone can map who has an account. */
const DUMMY = 'pbkdf2$sha256$600000$AAAAAAAAAAAAAAAAAAAAAA==$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=';

export const onRequestPost = async ({ request, env }) => {
  let body;
  try { body = await request.json(); } catch { return json({ error: 'bad_request' }, 400); }

  const email = String(body?.email ?? '').trim().toLowerCase();
  const password = String(body?.password ?? '');
  if (!email || !password) return json({ error: 'missing_credentials' }, 400);

  const row = await env.DB.prepare(
    `SELECT u.id, u.tenant_id, u.email, u.name, u.role, u.status,
            t.status AS tenant_status, c.secret
       FROM users u
       JOIN tenants t ON t.id = u.tenant_id
       LEFT JOIN credentials c ON c.user_id = u.id AND c.kind = 'password'
      WHERE lower(u.email) = ?`).bind(email).first();

  const ok = await verifyPassword(password, row?.secret ?? DUMMY);
  if (!row || !ok || row.status !== 'active' || row.tenant_status !== 'active') {
    return json({ error: 'invalid_credentials' }, 401);
  }

  const token = await createSession(env.DB, row, request);
  await env.DB.prepare('UPDATE users SET last_seen = ? WHERE id = ?')
    .bind(Math.floor(Date.now() / 1000), row.id).run();

  return json(
    { user: { id: row.id, email: row.email, name: row.name, role: row.role } },
    200, { 'set-cookie': cookieHeader(token) });
};
