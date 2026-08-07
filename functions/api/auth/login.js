import { verifyPassword, ITERATIONS } from '../../_lib/crypto.js';
import { createSession, cookieHeader, json } from '../../_lib/session.js';

/* Deliberately uniform failures.
 *
 * Wrong email and wrong password return the same body, the same status, and --
 * because the dummy verify below burns the same PBKDF2 cost as a real one --
 * close to the same duration. Skipping the hash for an unknown address is the
 * classic account-enumeration leak: the "no such user" path returns in 2ms and
 * the "wrong password" path in 70ms, so anyone can map who has an account.
 *
 * Built from ITERATIONS rather than written out, for two reasons. It has to be a
 * cost this platform can actually run -- a hardcoded 600k here threw on Workers
 * and turned every unknown-email login into a 500. And it has to match what real
 * hashes cost, or the timing it exists to equalise diverges the moment the
 * constant changes. Padding is valid base64 for a 16-byte salt and a 32-byte
 * digest, so it parses and derives exactly like a real credential. */
const DUMMY = `pbkdf2$sha256$${ITERATIONS}$${'A'.repeat(22)}==$${'A'.repeat(43)}=`;

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
