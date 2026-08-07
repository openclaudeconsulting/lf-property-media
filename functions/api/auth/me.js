import { currentUser, json } from '../../_lib/session.js';

/* The console calls this on load to decide whether to render itself. 401 rather
   than an empty body so a fetch wrapper can treat it like any other auth error. */
export const onRequestGet = async ({ request, env }) => {
  const user = await currentUser(env.DB, request);
  return user ? json({ user }) : json({ error: 'not_authenticated' }, 401);
};
