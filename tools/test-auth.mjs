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

/** Minimal D1 surface: prepare().bind().first()/.run()/.all() */
const shim = {
  prepare(q) {
    let args = [];
    const api = {
      bind(...a) { args = a; return api; },
      // D1 returns null for no match; node:sqlite throws on some malformed
      // reads, and a throw here would become a 500 that leaks intent.
      first() { try { return sql.prepare(q).get(...args) ?? null; } catch { return null; } },
      run() { return sql.prepare(q).run(...args); },
      all() { return { results: sql.prepare(q).all(...args) }; },
    };
    return api;
  },
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

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
