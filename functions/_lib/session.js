/* Sessions, and the authorisation helpers every API route leans on.
 *
 * The cookie carries a 256-bit random token. Only its SHA-256 lands in D1, so a
 * dump of the sessions table cannot be replayed as a login. Cookie is
 * HttpOnly + Secure + SameSite=Lax: Lax rather than Strict so that following a
 * link into the console from an email still arrives signed in.
 */
import { newToken, sha256Hex } from './crypto.js';

export const COOKIE = 'lf_session';
const TTL = 60 * 60 * 24 * 14;          // 14 days
const now = () => Math.floor(Date.now() / 1000);

export async function createSession(db, user, req) {
  const token = newToken();
  const id = await sha256Hex(token);
  await db.prepare(
    `INSERT INTO sessions (id, user_id, tenant_id, created_at, expires_at, user_agent, ip)
     VALUES (?, ?, ?, ?, ?, ?, ?)`)
    .bind(id, user.id, user.tenant_id, now(), now() + TTL,
          req.headers.get('user-agent')?.slice(0, 256) ?? null,
          req.headers.get('cf-connecting-ip') ?? null)
    .run();
  return token;
}

export function cookieHeader(token, maxAge = TTL) {
  return `${COOKIE}=${token}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${maxAge}`;
}
export const clearCookie = () => cookieHeader('', 0);

function readCookie(req) {
  const raw = req.headers.get('cookie');
  if (!raw) return null;
  for (const part of raw.split(';')) {
    const [k, ...v] = part.trim().split('=');
    if (k === COOKIE) return v.join('=') || null;
  }
  return null;
}

/** The signed-in user, or null. Expired rows are deleted as they are found. */
export async function currentUser(db, req) {
  const token = readCookie(req);
  if (!token) return null;
  const id = await sha256Hex(token);
  const row = await db.prepare(
    `SELECT s.id AS sid, s.expires_at, u.id, u.tenant_id, u.email, u.name, u.role, u.status,
            t.name AS tenant_name, t.status AS tenant_status
       FROM sessions s
       JOIN users u   ON u.id = s.user_id
       JOIN tenants t ON t.id = u.tenant_id
      WHERE s.id = ?`).bind(id).first();

  if (!row) return null;
  if (row.expires_at < now()) {
    await db.prepare('DELETE FROM sessions WHERE id = ?').bind(id).run();
    return null;
  }
  // A disabled user or a suspended tenant keeps a valid cookie until it expires,
  // so both are checked on every request rather than only at login.
  if (row.status !== 'active' || row.tenant_status !== 'active') return null;

  return {
    id: row.id, tenant_id: row.tenant_id, email: row.email, name: row.name,
    role: row.role, tenant_name: row.tenant_name, sessionId: row.sid,
  };
}

export async function destroySession(db, req) {
  const token = readCookie(req);
  if (token) await db.prepare('DELETE FROM sessions WHERE id = ?')
    .bind(await sha256Hex(token)).run();
}

/* ------------------------------------------------------------ responses */

export const json = (body, status = 200, headers = {}) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', ...headers },
  });

/**
 * Wrap a handler so it only runs for a signed-in user.
 * `role: 'owner'` restricts to LF staff.
 */
export function requireUser(handler, { role } = {}) {
  return async (context) => {
    const user = await currentUser(context.env.DB, context.request);
    if (!user) return json({ error: 'not_authenticated' }, 401);
    if (role === 'owner' && user.role !== 'owner') return json({ error: 'forbidden' }, 403);
    context.data.user = user;
    return handler(context);
  };
}

/**
 * The tenant a request is allowed to touch.
 *
 * LF staff ('owner') may act on any tenant by passing ?tenant=, which is what
 * makes support possible. Everyone else is pinned to their own, and passing
 * someone else's id is a 403 rather than a silent fallback -- a fallback would
 * turn a broken client into a data leak that looks like it worked.
 */
export function scopeTenant(user, requested) {
  if (!requested || requested === user.tenant_id) return user.tenant_id;
  if (user.role === 'owner') return requested;
  return null;
}
