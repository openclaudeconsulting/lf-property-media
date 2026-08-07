import { destroySession, clearCookie, json } from '../../_lib/session.js';

export const onRequestPost = async ({ request, env }) => {
  await destroySession(env.DB, request);
  return json({ ok: true }, 200, { 'set-cookie': clearCookie() });
};
