import { hashPassword, sha256Hex } from '../../_lib/crypto.js';
import { createSession, cookieHeader, json } from '../../_lib/session.js';

/* Redeem a single-use invite and set a password.
 *
 * The same shape serves account setup and password reset, which is why it lives
 * in auth/ rather than in a bootstrap script: the only difference between the
 * two is who created the token.
 *
 * The link carries a 256-bit token; only its SHA-256 is stored, so the invite
 * rows are worthless to anyone who reads the table. Redemption is a compare-and-
 * set on used_at, so two clicks on the same link cannot both win -- a link
 * forwarded, or fetched by a mail scanner, is spent exactly once.
 */

// Length is the only password rule worth enforcing. Composition rules push
// people toward Password1! and NIST stopped recommending them years ago.
const MIN_PASSWORD = 12;

export const onRequestPost = async ({ request, env }) => {
  let body;
  try { body = await request.json(); } catch { return json({ error: 'bad_request' }, 400); }

  const token = String(body?.token ?? '');
  const password = String(body?.password ?? '');
  if (!token) return json({ error: 'bad_request' }, 400);
  if (password.length < MIN_PASSWORD) {
    return json({ error: 'weak_password', min: MIN_PASSWORD }, 400);
  }

  const now = Math.floor(Date.now() / 1000);
  const hashed = await sha256Hex(token);

  const invite = await env.DB.prepare(
    `SELECT c.id, c.user_id, c.expires_at, c.used_at,
            u.tenant_id, u.email, u.name, u.role, u.status,
            t.status AS tenant_status
       FROM credentials c
       JOIN users u   ON u.id = c.user_id
       JOIN tenants t ON t.id = u.tenant_id
      WHERE c.secret = ? AND c.kind = 'magiclink'`).bind(hashed).first();

  // One error for every reason a link will not work -- unknown, expired, already
  // used, disabled account. Distinguishing them tells a stranger holding a stale
  // link which accounts exist and which invites are still outstanding.
  const dead = !invite
    || invite.used_at !== null
    || invite.expires_at < now
    || invite.status !== 'active'
    || invite.tenant_status !== 'active';
  if (dead) return json({ error: 'invalid_or_expired' }, 400);

  // Compare-and-set: whoever flips used_at from NULL owns this redemption. A
  // second request finds changes === 0 and is turned away, so a forwarded link
  // cannot set the password twice.
  const claim = await env.DB.prepare(
    `UPDATE credentials SET used_at = ? WHERE id = ? AND used_at IS NULL`)
    .bind(now, invite.id).run();
  if ((claim.meta?.changes ?? 0) !== 1) return json({ error: 'invalid_or_expired' }, 400);

  const secret = await hashPassword(password);
  await env.DB.batch([
    // A partial unique index allows one password per user, so the old one goes
    // first. This also makes the endpoint idempotent for password *reset*.
    env.DB.prepare(`DELETE FROM credentials WHERE user_id = ? AND kind = 'password'`)
      .bind(invite.user_id),
    env.DB.prepare(
      `INSERT INTO credentials (id, user_id, kind, secret, created_at)
       VALUES (?, ?, 'password', ?, ?)`)
      .bind(crypto.randomUUID(), invite.user_id, secret, now),
    // Setting a password invalidates existing sessions. If the invite was used
    // because someone lost control of the account, leaving old sessions alive
    // would defeat the point.
    env.DB.prepare(`DELETE FROM sessions WHERE user_id = ?`).bind(invite.user_id),
    env.DB.prepare(
      `INSERT INTO audit (id, tenant_id, user_id, action, subject, created_at)
       VALUES (?, ?, ?, 'auth.password_set', ?, ?)`)
      .bind(crypto.randomUUID(), invite.tenant_id, invite.user_id, invite.id, now),
  ]);

  const sessionToken = await createSession(
    env.DB, { id: invite.user_id, tenant_id: invite.tenant_id }, request);

  return json(
    { user: { id: invite.user_id, email: invite.email, name: invite.name, role: invite.role } },
    200, { 'set-cookie': cookieHeader(sessionToken) });
};
