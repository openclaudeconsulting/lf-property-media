import { requireUser, scopeTenant, json } from '../_lib/session.js';

/* Tours visible to the caller.
 *
 * Every row is filtered by tenant. LF staff may inspect another tenant by
 * passing ?tenant=, which is what makes support possible; anyone else asking for
 * a tenant that is not theirs gets 403 rather than a silent fallback to their
 * own, because a fallback turns a broken client into a leak that looks fine.
 */
export const onRequestGet = requireUser(async ({ request, env, data }) => {
  const requested = new URL(request.url).searchParams.get('tenant');
  const tenant = scopeTenant(data.user, requested);
  if (!tenant) return json({ error: 'forbidden' }, 403);

  const { results } = await env.DB.prepare(
    `SELECT t.id, t.slug, t.status, t.created_at, t.published_at,
            p.address, p.city, p.state, p.beds, p.baths, p.sqft,
            (SELECT count(*) FROM scenes s WHERE s.tour_id = t.id) AS scenes
       FROM tours t
       JOIN properties p ON p.id = t.property_id
      WHERE t.tenant_id = ?
      ORDER BY t.created_at DESC`).bind(tenant).all();

  return json({ tenant, tours: results ?? [] });
});
