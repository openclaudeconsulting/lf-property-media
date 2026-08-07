import { currentUser } from '../_lib/session.js';

/* Gate on /app/*.
 *
 * Two paths have to stay open or the gate locks out the people it exists for:
 * the sign-in page itself, and the invite-redemption page, which is reached by
 * someone who by definition has no session yet.
 *
 * Everything else redirects to sign-in carrying ?next=, so a bookmarked deep
 * link lands where it was pointed instead of dumping the visitor at the top.
 * The login page only honours same-origin paths, so this cannot be bent into an
 * open redirect by asking for /app/../../evil.
 */
const PUBLIC = [/^\/app\/login\/?$/, /^\/app\/setup\/?$/];

export const onRequest = async (context) => {
  const path = new URL(context.request.url).pathname;
  if (PUBLIC.some((re) => re.test(path))) return context.next();

  const user = await currentUser(context.env.DB, context.request);
  if (!user) {
    const next = encodeURIComponent(path);
    return new Response(null, {
      status: 302,
      headers: { location: `/app/login/?next=${next}`, 'cache-control': 'no-store' },
    });
  }

  context.data.user = user;
  const res = await context.next();
  // Never let a CDN or a shared browser cache hold a page rendered for one
  // signed-in tenant and hand it to the next visitor.
  const out = new Response(res.body, res);
  out.headers.set('cache-control', 'private, no-store');
  return out;
};
