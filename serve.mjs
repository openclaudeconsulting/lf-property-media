// Static dev server for the LF Property Media site.
// Serves the project root at http://localhost:3000 -- CLAUDE.md requires that
// screenshots come from localhost, never a file:// URL.
//
//   node serve.mjs            # port 3000
//   node serve.mjs 4000       # explicit port
//   PORT=4000 node serve.mjs  # explicit port, for tooling that assigns one
//                             # (a worktree cannot have 3000 too)
import { createServer } from 'node:http';
import { createReadStream } from 'node:fs';
import { stat } from 'node:fs/promises';
import { extname, join, normalize, sep } from 'node:path';

const ROOT = import.meta.dirname;
const PORT = Number(process.argv[2]) || Number(process.env.PORT) || 3000;

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.png': 'image/png',
  '.webp': 'image/webp',
  '.avif': 'image/avif',
  '.mp4': 'video/mp4',
  '.woff2': 'font/woff2',
  '.txt': 'text/plain; charset=utf-8',
  '.xml': 'application/xml; charset=utf-8',
};

async function resolve(urlPath) {
  // decodeURIComponent so folders with spaces resolve; normalize + prefix check
  // so ../ cannot escape the project root.
  let rel = normalize(decodeURIComponent(urlPath.split('?')[0])).replace(/^([/\\])+/, '');
  let full = join(ROOT, rel);
  if (!(full + sep).startsWith(ROOT + sep) && full !== ROOT) return null;

  try {
    const info = await stat(full);
    if (info.isDirectory()) {
      full = join(full, 'index.html');
      await stat(full);
    }
    return full;
  } catch {
    // Extensionless URLs fall back to .html, matching Cloudflare Pages.
    if (!extname(full)) {
      try {
        await stat(full + '.html');
        return full + '.html';
      } catch { /* fall through */ }
    }
    return null;
  }
}

createServer(async (req, res) => {
  const file = await resolve(req.url || '/');
  if (!file) {
    res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' });
    res.end('404 Not Found');
    console.log(`404  ${req.url}`);
    return;
  }
  res.writeHead(200, {
    'content-type': TYPES[extname(file).toLowerCase()] || 'application/octet-stream',
    'cache-control': 'no-cache',
  });
  createReadStream(file).pipe(res);
  console.log(`200  ${req.url}`);
}).listen(PORT, () => {
  console.log(`LF Property Media dev server -> http://localhost:${PORT}`);
});
