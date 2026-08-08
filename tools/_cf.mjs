/* Cloudflare access for machine-side tooling.
 *
 * D1 goes over the HTTP API because it takes bound parameters; the wrangler CLI
 * only accepts a SQL string, which would mean hand-escaping job ids and
 * filenames into statements. R2 goes over the CLI because objects here are
 * hundreds of megabytes and the CLI already streams them to disk.
 *
 * Both authenticate with the OAuth token wrangler already holds, so the runner
 * needs no credential of its own. That is the whole reason this can live on the
 * owner's desktop without minting a machine token and finding somewhere safe to
 * keep it. If the runner ever moves to rented hardware, this is the file that
 * changes -- swap the token source for a scoped API token in the environment.
 */
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

export const ACCOUNT_ID = '7eb35ea8e7185bea52a1202faab6c769';
export const DATABASE_ID = '5c2d1f69-2cac-470f-bb4c-e455ad71a918';
export const BUCKET = 'lf-tour-media';

const CONFIG = join(homedir(), 'AppData/Roaming/xdg.config/.wrangler/config/default.toml');

function readToken() {
  const m = /oauth_token\s*=\s*"([^"]+)"/.exec(readFileSync(CONFIG, 'utf8'));
  if (!m) throw new Error(`no oauth_token in ${CONFIG} — run: npx wrangler login`);
  return m[1];
}

/** Wrangler refreshes the stored token as a side effect of any API call. */
function refreshToken() {
  try {
    execFileSync('npx', ['wrangler', 'd1', 'list'],
      { stdio: 'ignore', shell: process.platform === 'win32' });
  } catch { /* the retry below will surface it */ }
  return readToken();
}

let token = null;

/**
 * Run SQL against the remote D1 with bound parameters.
 * @param {string} sql
 * @param {unknown[]} params
 * @returns {Promise<{results: any[], meta: any}>}
 */
export async function d1(sql, params = []) {
  token ??= readToken();
  const url = `https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}`
            + `/d1/database/${DATABASE_ID}/query`;

  const send = async () => fetch(url, {
    method: 'POST',
    headers: { authorization: `Bearer ${token}`, 'content-type': 'application/json' },
    body: JSON.stringify({ sql, params }),
  });

  let res = await send();
  // The stored token expires on its own schedule; one silent refresh beats
  // making a long-running runner die overnight.
  if (res.status === 401) { token = refreshToken(); res = await send(); }

  const body = await res.json().catch(() => ({}));
  if (!res.ok || !body.success) {
    throw new Error(`D1 ${res.status}: ${JSON.stringify(body.errors ?? body).slice(0, 400)}`);
  }
  const first = body.result?.[0] ?? {};
  return { results: first.results ?? [], meta: first.meta ?? {} };
}

/* Windows needs shell:true to run npx (a .cmd), and shell:true concatenates
 * arguments without escaping them -- which is exactly what DEP0190 warns about.
 * This project lives under "C:\Project Claude\LF Propery Media", so every path
 * argument contains spaces and arrives at wrangler split into pieces. Quoting
 * here is not cosmetic: without it, every R2 transfer fails with a usage error.
 */
const quote = (a) => (process.platform === 'win32' ? `"${String(a).replace(/"/g, '\\"')}"` : a);

const wrangler = (args) => execFileSync('npx', ['wrangler', ...args].map(quote), {
  encoding: 'utf8', shell: process.platform === 'win32', stdio: ['ignore', 'pipe', 'pipe'],
});

/** Download an object to a local path. */
export function r2get(key, dest) {
  wrangler(['r2', 'object', 'get', `${BUCKET}/${key}`, '--remote', `--file=${dest}`]);
}

/** Upload a local file. */
export function r2put(key, src, contentType) {
  const args = ['r2', 'object', 'put', `${BUCKET}/${key}`, '--remote', `--file=${src}`];
  if (contentType) args.push(`--content-type=${contentType}`);
  wrangler(args);
}

export function r2delete(key) {
  try { wrangler(['r2', 'object', 'delete', `${BUCKET}/${key}`, '--remote']); }
  catch { /* already gone is fine */ }
}
