/* Create an account and print a single-use setup link.
 *
 *   node tools/invite.mjs --email you@example.com --name "Your Name" \
 *        --tenant "LF Property Media" --role owner [--local] [--base https://…]
 *
 * Bootstrap only. There is no admin API yet, and there cannot be one that
 * creates the first owner — nobody exists to authorise it. Once the console can
 * invite people, this stays useful for recovering an account nobody can log into.
 *
 * The password is never involved here. This writes a user row and a hashed,
 * expiring, single-use token; the person clicking the link chooses the password
 * themselves at /app/setup. Nothing secret passes through whoever runs this.
 */
import { execFileSync } from 'node:child_process';
import { writeFileSync, unlinkSync } from 'node:fs';
import { newToken, sha256Hex } from '../functions/_lib/crypto.js';

const TTL_DAYS = 7;

function arg(name, fallback) {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}
const has = (name) => process.argv.includes(`--${name}`);

const email = arg('email');
const name = arg('name', null);
const tenantName = arg('tenant', 'LF Property Media');
const role = arg('role', 'agent');
const base = arg('base', 'https://lfpropertymedia.org');
const local = has('local');

if (!email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
  console.error('usage: node tools/invite.mjs --email you@example.com [--name "Your Name"]');
  console.error('       [--tenant "Brokerage"] [--role owner|agent] [--base URL] [--local]');
  process.exit(1);
}
if (!['owner', 'agent'].includes(role)) {
  console.error(`role must be owner or agent, got ${role}`);
  process.exit(1);
}

const sql = (statements) => {
  const file = `.tmp-invite-${Date.now()}.sql`;
  writeFileSync(file, statements);
  try {
    return execFileSync('npx', ['wrangler', 'd1', 'execute', 'lf-tours',
      local ? '--local' : '--remote', '--json', `--file=${file}`],
      { encoding: 'utf8', shell: true, stdio: ['ignore', 'pipe', 'pipe'] });
  } finally {
    unlinkSync(file);
  }
};
const q = (s) => `'${String(s).replace(/'/g, "''")}'`;

const now = Math.floor(Date.now() / 1000);
const token = newToken();
const tokenHash = await sha256Hex(token);
const tenantId = crypto.randomUUID();
const userId = crypto.randomUUID();

// Reuse the tenant if one with this name already exists, so inviting a second
// agent into a brokerage does not silently create a parallel empty tenant.
const slug = tenantName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

sql(`
INSERT INTO tenants (id, name, slug, created_at)
  SELECT ${q(tenantId)}, ${q(tenantName)}, ${q(slug)}, ${now}
  WHERE NOT EXISTS (SELECT 1 FROM tenants WHERE slug = ${q(slug)});

INSERT INTO users (id, tenant_id, email, name, role, created_at)
  SELECT ${q(userId)}, (SELECT id FROM tenants WHERE slug = ${q(slug)}),
         ${q(email)}, ${name ? q(name) : 'NULL'}, ${q(role)}, ${now}
  WHERE NOT EXISTS (SELECT 1 FROM users WHERE lower(email) = lower(${q(email)}));

-- Supersede any outstanding invite for this person: an older link left live
-- would be a second, forgotten way into the account.
DELETE FROM credentials
  WHERE kind = 'magiclink'
    AND user_id = (SELECT id FROM users WHERE lower(email) = lower(${q(email)}));

INSERT INTO credentials (id, user_id, kind, secret, expires_at, created_at)
  SELECT ${q(crypto.randomUUID())},
         (SELECT id FROM users WHERE lower(email) = lower(${q(email)})),
         'magiclink', ${q(tokenHash)}, ${now + TTL_DAYS * 86400}, ${now};
`.trim());

const out = sql(`SELECT u.id, u.email, u.role, t.name AS tenant
                   FROM users u JOIN tenants t ON t.id = u.tenant_id
                  WHERE lower(u.email) = lower(${q(email)});`);
let who = {};
try { who = JSON.parse(out)[0].results[0] ?? {}; } catch { /* fall back to echoing input */ }

console.log(`
Account ready${local ? ' (local database)' : ''}
  email   ${who.email ?? email}
  name    ${name ?? '(not set)'}
  role    ${who.role ?? role}
  tenant  ${who.tenant ?? tenantName}

Send this link. It expires in ${TTL_DAYS} days and works exactly once:

  ${base}/app/setup/?token=${token}

The token is stored hashed, so this is the only time it can be read. If it is
lost, run this again -- that supersedes the old link rather than adding a second.
`);
