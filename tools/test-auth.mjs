/* Auth test suite.  Run:  node tools/test-auth.mjs
 *
 * Drives the real route handlers in functions/api/auth/ against an in-memory
 * SQLite database through a D1-shaped shim. It is not a substitute for
 * `wrangler pages dev` -- it does not exercise routing, bindings or the actual
 * Workers runtime -- but it does exercise the handler code, and it runs in a
 * second with no account, no network and no local server.
 *
 * It exists because `wrangler pages dev` cannot reach the local D1 on a checkout
 * whose path contains spaces: wrangler splices its state directory into the
 * middle of the path, every query lands on an empty database, and --persist-to
 * does not correct it. See docs/PLATFORM-PLAN.md, "Known environment traps".
 *
 * Note what this suite cannot catch, and did not: it runs on Node, where PBKDF2
 * has no iteration ceiling. The Workers ceiling was only visible on a deployed
 * preview. Anything touching WebCrypto limits needs testing there too.
 */
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import { onRequestPost as login } from '../functions/api/auth/login.js';
import { onRequestPost as logout } from '../functions/api/auth/logout.js';
import { onRequestGet as me } from '../functions/api/auth/me.js';
import { hashPassword, verifyPassword, MAX_ITERATIONS } from '../functions/_lib/crypto.js';

const sql = new DatabaseSync(':memory:');
sql.exec(readFileSync(new URL('../migrations/0001_init.sql', import.meta.url), 'utf8'));

/** Minimal D1 surface: prepare().bind().first()/.run()/.all(), plus batch(). */
const shim = {
  prepare(q) {
    let args = [];
    const api = {
      bind(...a) { args = a; return api; },
      // D1 returns null for no match; node:sqlite throws on some malformed
      // reads, and a throw here would become a 500 that leaks intent.
      first() { try { return sql.prepare(q).get(...args) ?? null; } catch { return null; } },
      // D1 reports affected rows under meta.changes, node:sqlite under changes.
      // The compare-and-set that makes an invite single-use reads meta.changes,
      // so the shape has to match or the test proves nothing.
      run() { const r = sql.prepare(q).run(...args); return { meta: { changes: r.changes } }; },
      all() { return { results: sql.prepare(q).all(...args) }; },
      _run() { return api.run(); },
    };
    return api;
  },
  batch(statements) { return statements.map((s) => s._run()); },
};

const now = Math.floor(Date.now() / 1000);
const H = await hashPassword('hunter2', MAX_ITERATIONS);
sql.exec(`INSERT INTO tenants VALUES ('t1','Preferred Shore','preferred-shore','active',${now})`);
sql.prepare(`INSERT INTO users VALUES ('u1','t1','Agent@Example.com','Test Agent','agent','active',?,NULL)`).run(now);
sql.prepare(`INSERT INTO credentials VALUES ('c1','u1','password',?,NULL,NULL,?)`).run(H, now);
sql.exec(`INSERT INTO tenants VALUES ('t2','Suspended Co','susp','suspended',${now})`);
sql.prepare(`INSERT INTO users VALUES ('u3','t2','sus@x.com','S','agent','active',?,NULL)`).run(now);
sql.prepare(`INSERT INTO credentials VALUES ('c3','u3','password',?,NULL,NULL,?)`).run(H, now);

const req = (b, c) => new Request('https://x/api', {
  method: b ? 'POST' : 'GET',
  headers: { 'content-type': 'application/json', ...(c ? { cookie: c } : {}) },
  ...(b ? { body: JSON.stringify(b) } : {}),
});
const call = (fn, b, c) => fn({ request: req(b, c), env: { DB: shim }, data: {} });
const ck = (r) => (r.headers.get('set-cookie') || '').split(';')[0];

let pass = 0, fail = 0;
const P = (n, ok) => { ok ? pass++ : fail++; console.log(`${ok ? 'PASS' : 'FAIL'}  ${n}`); };

P('me without cookie -> 401', (await call(me)).status === 401);

let r = await call(login, { email: 'agent@example.com', password: 'nope' });
const wrongBody = await r.clone().text();
P('wrong password -> 401', r.status === 401);

r = await call(login, { email: 'ghost@nowhere.com', password: 'nope' });
// The anti-enumeration property: an unknown address must be indistinguishable
// from a known one with the wrong password.
P('unknown user response identical to wrong password',
  r.status === 401 && (await r.text()) === wrongBody);

P('missing password -> 400', (await call(login, { email: 'agent@example.com' })).status === 400);
P('suspended tenant cannot log in',
  (await call(login, { email: 'sus@x.com', password: 'hunter2' })).status === 401);

r = await call(login, { email: 'AGENT@Example.COM', password: 'hunter2' });
const cookie = ck(r), sc = r.headers.get('set-cookie') || '';
P('correct login, mixed-case email -> 200', r.status === 200);
P('cookie HttpOnly + Secure + SameSite=Lax',
  /HttpOnly/.test(sc) && /Secure/.test(sc) && /SameSite=Lax/.test(sc));

const stored = sql.prepare('SELECT id FROM sessions').get().id;
P('session stored as sha256, not the raw token',
  !cookie.includes(stored) && stored.length === 64);

r = await call(me, null, cookie);
const body = await r.json();
P('me with cookie -> 200', r.status === 200);
P('me is tenant-scoped', body.user?.tenant_id === 't1' && body.user?.role === 'agent');
P('forged cookie -> 401', (await call(me, null, 'lf_session=forged')).status === 401);

sql.exec(`UPDATE users SET status='disabled' WHERE id='u1'`);
P('disabled user rejected mid-session', (await call(me, null, cookie)).status === 401);
sql.exec(`UPDATE users SET status='active' WHERE id='u1'`);

sql.exec(`UPDATE sessions SET expires_at=${now - 1}`);
P('expired session -> 401', (await call(me, null, cookie)).status === 401);
P('expired row cleaned up', sql.prepare('SELECT count(*) c FROM sessions').get().c === 0);

const c2 = ck(await call(login, { email: 'agent@example.com', password: 'hunter2' }));
r = await call(logout, {}, c2);
P('logout -> 200 and clears cookie',
  r.status === 200 && /Max-Age=0/.test(r.headers.get('set-cookie')));
P('cookie dead after logout', (await call(me, null, c2)).status === 401);

/* Regression guards for the ceiling that cost an afternoon.
 *
 * Cloudflare Workers refuses PBKDF2 above 100k iterations -- deriveBits throws.
 * verifyPassword used to catch everything and return false, so a hash written at
 * the recommended 600k made every account on the service unloggable-into while
 * reporting "invalid credentials" and leaving the logs clean. Node happily does
 * 600k, so it only appeared on a deployed preview. */
let threw = false;
try { await hashPassword('x', MAX_ITERATIONS + 1); } catch { threw = true; }
P('hashPassword refuses to exceed the Workers ceiling', threw);
P('MAX_ITERATIONS is the measured platform ceiling', MAX_ITERATIONS === 100_000);

// Unusable *stored credentials* fail closed -- one account affected, and saying
// more would leak whether the account exists.
P('malformed hash fails closed', (await verifyPassword('x', 'nonsense')) === false);
P('null hash fails closed', (await verifyPassword('x', null)) === false);
P('wrong scheme fails closed', (await verifyPassword('x', 'bcrypt$2b$12$aa$bb')) === false);
P('non-numeric cost fails closed', (await verifyPassword('x', 'pbkdf2$sha256$abc$AAAA$AAAA')) === false);
P('corrupt base64 salt fails closed', (await verifyPassword('x', 'pbkdf2$sha256$1000$!!!!$AAAA')) === false);

// The other branch -- a failure of the crypto engine -- must throw instead, and
// cannot be exercised here: Node has no PBKDF2 ceiling, so the 600k call that
// throws on Workers simply returns a non-matching hash. Only a deployed preview
// catches that, which is the whole lesson from this one.
P('high cost verifies (no ceiling on Node) rather than throwing',
  (await verifyPassword('x', 'pbkdf2$sha256$600000$AAAAAAAAAAAAAAAAAAAAAA==$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=')) === false);

/* The login handler's dummy hash, rebuilt here from the same constant. It must
   parse and derive like a real credential: when it was hardcoded at 600k it
   threw on Workers, so every login with an unknown email returned 500 -- which
   both broke the endpoint and blew the anti-enumeration property wide open. */
const DUMMY = `pbkdf2$sha256$${MAX_ITERATIONS}$${'A'.repeat(22)}==$${'A'.repeat(43)}=`;
let dummyOk = true;
try { await verifyPassword('anything', DUMMY); } catch { dummyOk = false; }
P('login dummy hash is usable at the platform ceiling', dummyOk);
P('login dummy hash never matches a password', (await verifyPassword('anything', DUMMY)) === false);

/* ------------------------------------------------- invite redemption ----- */

const { onRequestPost: setup } = await import('../functions/api/auth/setup.js');
const { sha256Hex, newToken } = await import('../functions/_lib/crypto.js');

sql.exec(`INSERT INTO tenants VALUES ('t3','Invite Co','invite-co','active',${now})`);
sql.prepare(`INSERT INTO users VALUES ('u4','t3','invitee@example.com','Invitee','agent','active',?,NULL)`).run(now);

const mkInvite = async (id, { expires = now + 3600, used = null, user = 'u4' } = {}) => {
  const tok = newToken();
  sql.prepare(`INSERT INTO credentials VALUES (?,?,'magiclink',?,?,?,?)`)
    .run(id, user, await sha256Hex(tok), expires, used, now);
  return tok;
};

P('setup rejects a token that does not exist',
  (await call(setup, { token: 'nope', password: 'a-long-enough-password' })).status === 400);

let tok = await mkInvite('i-weak');
r = await call(setup, { token: tok, password: 'short' });
P('setup rejects a short password', r.status === 400 && (await r.json()).error === 'weak_password');
P('a rejected attempt does not spend the invite',
  sql.prepare(`SELECT used_at FROM credentials WHERE id='i-weak'`).get().used_at === null);

tok = await mkInvite('i-expired', { expires: now - 1 });
P('setup rejects an expired invite',
  (await call(setup, { token: tok, password: 'a-long-enough-password' })).status === 400);

tok = await mkInvite('i-good');
// A live session that must not survive a password being set.
sql.prepare(`INSERT INTO sessions VALUES ('stale','u4','t3',?,?,NULL,NULL)`).run(now, now + 9999);

r = await call(setup, { token: tok, password: 'a-long-enough-password' });
const setupCookie = ck(r);
P('setup accepts a valid invite -> 200', r.status === 200);
P('setup signs the user straight in', /HttpOnly/.test(r.headers.get('set-cookie') || ''));
P('setup session works', (await call(me, null, setupCookie)).status === 200);
P('the new password actually logs in',
  (await call(login, { email: 'invitee@example.com', password: 'a-long-enough-password' })).status === 200);
P('exactly one password credential exists',
  sql.prepare(`SELECT count(*) c FROM credentials WHERE user_id='u4' AND kind='password'`).get().c === 1);
P('older sessions are invalidated',
  sql.prepare(`SELECT count(*) c FROM sessions WHERE id='stale'`).get().c === 0);
P('the redemption is audited',
  sql.prepare(`SELECT count(*) c FROM audit WHERE action='auth.password_set'`).get().c === 1);

// The property the whole design rests on: a forwarded link is spent once.
P('the same invite cannot be redeemed twice',
  (await call(setup, { token: tok, password: 'another-long-password' })).status === 400);
P('a second attempt did not change the password',
  (await call(login, { email: 'invitee@example.com', password: 'another-long-password' })).status === 401);

/* --------------------------------------------------- tenant isolation ---- */

const { onRequestGet: tours } = await import('../functions/api/tours.js');

// Two tenants with a listing each. t1 is the agent's; t3 belongs to someone else.
for (const [tid, pid, toid, addr] of [
  ['t1', 'p1', 'to1', '2719 Fort Worth Street'],
  ['t3', 'p2', 'to2', 'Someone Elses House'],
]) {
  sql.prepare(`INSERT INTO properties (id,tenant_id,address,created_at) VALUES (?,?,?,?)`)
    .run(pid, tid, addr, now);
  sql.prepare(`INSERT INTO tours (id,tenant_id,property_id,slug,status,created_at) VALUES (?,?,?,?,'published',?)`)
    .run(toid, tid, pid, toid, now);
}

const asUser = (u, url = 'https://x/api/tours') =>
  tours({ request: new Request(url, { headers: { cookie: u } }), env: { DB: shim }, data: {} });

P('tours requires a session', (await asUser('')).status === 401);

// Sign the agent (tenant t1) back in for the scoping checks.
const agentCookie = ck(await call(login, { email: 'agent@example.com', password: 'hunter2' }));
r = await asUser(agentCookie);
let payload = await r.json();
P('tours returns 200 for a signed-in agent', r.status === 200);
P('agent sees only their own tenant',
  payload.tours.length === 1 && payload.tours[0].address === '2719 Fort Worth Street');
P('tour row carries its scene count', 'scenes' in payload.tours[0]);

// The leak that matters: asking for a tenant you do not belong to.
r = await asUser(agentCookie, 'https://x/api/tours?tenant=t3');
P('agent asking for another tenant -> 403, not a silent fallback', r.status === 403);

// LF staff cross tenants on purpose; that is what makes support possible.
sql.exec(`UPDATE users SET role='owner' WHERE id='u1'`);
const ownerCookie = ck(await call(login, { email: 'agent@example.com', password: 'hunter2' }));
r = await asUser(ownerCookie, 'https://x/api/tours?tenant=t3');
payload = await r.json();
P('owner may inspect another tenant',
  r.status === 200 && payload.tours.length === 1 && payload.tours[0].address === 'Someone Elses House');
r = await asUser(ownerCookie);
payload = await r.json();
P('owner without ?tenant still defaults to their own',
  payload.tours.length === 1 && payload.tours[0].address === '2719 Fort Worth Street');

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
