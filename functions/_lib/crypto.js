/* Password hashing and token handling.
 *
 * PBKDF2-HMAC-SHA256, because it is the only password KDF in the WebCrypto API
 * that Workers expose natively. Argon2id and scrypt are better and are what you
 * would reach for on a normal server, but both need a WASM build shipped with
 * the Worker; that is a worthwhile upgrade later and the stored format below is
 * designed so it can happen without a migration.
 *
 * Hashes are self-describing:
 *
 *     pbkdf2$sha256$<iterations>$<salt-b64>$<derived-b64>
 *
 * so the cost can be raised over time and old hashes still verify against the
 * parameters they were written with. Verify reads the iteration count out of
 * the stored string rather than assuming today's constant.
 */

const enc = new TextEncoder();

// OWASP's floor for PBKDF2-HMAC-SHA256. Costs real CPU time per login -- see
// docs/PLATFORM-PLAN.md on the Workers CPU budget before lowering it.
export const ITERATIONS = 600_000;
const KEY_LEN = 32;         // bytes
const SALT_LEN = 16;

const b64 = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf)));
const unb64 = (s) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0));

async function derive(password, salt, iterations) {
  const key = await crypto.subtle.importKey(
    'raw', enc.encode(password), 'PBKDF2', false, ['deriveBits']);
  return crypto.subtle.deriveBits(
    { name: 'PBKDF2', hash: 'SHA-256', salt, iterations }, key, KEY_LEN * 8);
}

export async function hashPassword(password, iterations = ITERATIONS) {
  const salt = crypto.getRandomValues(new Uint8Array(SALT_LEN));
  const bits = await derive(password, salt, iterations);
  return `pbkdf2$sha256$${iterations}$${b64(salt)}$${b64(bits)}`;
}

export async function verifyPassword(password, stored) {
  // A malformed or missing hash must fail closed, never throw -- an exception
  // here would be a 500 that tells an attacker the account exists.
  try {
    const [scheme, hash, iters, salt, expected] = String(stored).split('$');
    if (scheme !== 'pbkdf2' || hash !== 'sha256') return false;
    const bits = await derive(password, unb64(salt), Number(iters));
    return timingSafeEqual(new Uint8Array(bits), unb64(expected));
  } catch {
    return false;
  }
}

/** Comparison whose duration does not depend on where the first difference is. */
export function timingSafeEqual(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i] ^ b[i];
  return diff === 0;
}

/** 256 bits of CSPRNG, url-safe. Used for session cookies and magic links. */
export function newToken() {
  const raw = crypto.getRandomValues(new Uint8Array(32));
  return btoa(String.fromCharCode(...raw))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

/** Sessions and magic links are stored hashed, so a table dump is not a login. */
export async function sha256Hex(text) {
  const buf = await crypto.subtle.digest('SHA-256', enc.encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
}
