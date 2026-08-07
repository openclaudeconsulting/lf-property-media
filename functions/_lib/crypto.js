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

/* Cloudflare Workers refuses PBKDF2 above 100,000 iterations: deriveBits throws
 * rather than returning, and it is a hard platform ceiling, not a budget.
 * Measured against a deployed preview -- 100k logs in, 250k and 600k both throw.
 *
 * That is below OWASP's 600k recommendation for PBKDF2-HMAC-SHA256, and it is
 * the strongest reason to move to Argon2id via WASM once this carries real
 * accounts. The stored format is self-describing precisely so that swap can
 * happen without invalidating anyone: verify reads the scheme and cost out of
 * the hash it is checking.
 */
export const MAX_ITERATIONS = 100_000;
export const ITERATIONS = MAX_ITERATIONS;
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
  // Refuse to write a hash this platform cannot read back. Without this the
  // failure surfaces at the victim's next login, not at the point of the mistake.
  if (iterations > MAX_ITERATIONS) {
    throw new RangeError(
      `PBKDF2 iterations ${iterations} exceeds the Workers ceiling of ${MAX_ITERATIONS}`);
  }
  const salt = crypto.getRandomValues(new Uint8Array(SALT_LEN));
  const bits = await derive(password, salt, iterations);
  return `pbkdf2$sha256$${iterations}$${b64(salt)}$${b64(bits)}`;
}

export async function verifyPassword(password, stored) {
  // A hash that is missing or the wrong shape means "no usable credential", so
  // it fails closed and says nothing about whether the account exists.
  const parts = String(stored ?? '').split('$');
  if (parts.length !== 5) return false;
  const [scheme, hash, iters, salt, expected] = parts;
  if (scheme !== 'pbkdf2' || hash !== 'sha256') return false;
  const n = Number(iters);
  if (!Number.isInteger(n) || n < 1) return false;

  // Corrupt base64 is a damaged stored credential -- one account's problem, and
  // it fails closed like any other unusable hash.
  let saltBytes, expectedBytes;
  try {
    saltBytes = unb64(salt);
    expectedBytes = unb64(expected);
  } catch {
    return false;
  }

  let bits;
  try {
    bits = await derive(password, saltBytes, n);
  } catch (cause) {
    // A failure of the crypto engine itself is everyone's problem: a bad cost
    // parameter, a missing algorithm, a platform limit. Returning false here is
    // exactly what hid the 100k iteration ceiling -- every login came back
    // "invalid credentials" with clean logs. Surface it.
    throw new Error(`password verification failed at ${n} iterations: ${cause.message}`,
      { cause });
  }
  return timingSafeEqual(new Uint8Array(bits), expectedBytes);
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
