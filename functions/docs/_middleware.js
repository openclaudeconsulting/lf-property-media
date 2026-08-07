/* Blocks /docs/* on the live site.
 *
 * Cloudflare Pages deploys the entire repo root and honours no ignore file for a
 * git build: .assetsignore is a Workers Assets feature, and a _redirects rule
 * loses to an existing static asset (both were tried, both served 200). A Pages
 * Function does take precedence over static assets, so this is the only
 * mechanism that actually works without changing the project's build settings.
 *
 * Scoped to this directory rather than the site root so ordinary traffic --
 * pages, images, the 3.5 MB panoramas -- never invokes a Worker.
 */
export const onRequest = () => new Response('Not found', {
  status: 404,
  headers: { 'content-type': 'text/plain; charset=utf-8' },
});
