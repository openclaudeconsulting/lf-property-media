/* Recovering panorama yaw from floor-plan geometry.
 *
 * A bearing measured on a floor plan is not a panorama yaw. Every 360 has its
 * own north, fixed by whichever way the camera body happened to face on the
 * tripod, so each scene carries an unknown constant offset between the two.
 *
 * Those offsets are recoverable. Any hotspot already aimed by hand pins one
 * known plan bearing against one known yaw, which is one equation for that
 * scene's offset. Average over a scene's aimed hotspots and the offset falls
 * out; apply it to the scene's remaining links and they point the right way.
 *
 * Handedness has to be solved too, not assumed. Plan bearings and panorama yaw
 * may run in opposite directions, and no constant offset can undo a mirror --
 * so both hypotheses are scored across the whole tour and the better one wins.
 * That also means this never has to be re-derived if a convention changes
 * upstream: it measures what is actually there.
 *
 * Split out of floor-plan.html so it can be tested directly. Angles are degrees
 * throughout; bearings are 0 = up the plan, increasing clockwise.
 */

const D = Math.PI / 180;

export const norm180 = (a) => ((a % 360) + 540) % 360 - 180;

/** Mean of angles, done on the unit circle so 179 and -179 average to 180. */
export const circMean = (degs) => norm180(Math.atan2(
  degs.reduce((t, a) => t + Math.sin(a * D), 0),
  degs.reduce((t, a) => t + Math.cos(a * D), 0)) / D);

/** Bearing from p to q, both {x, y} with y increasing downward as in an image. */
export const bearing = (p, q) => Math.atan2(q.x - p.x, -(q.y - p.y)) / D;

/**
 * @param {Array<{from:string, yaw:number, bearing:number}>} samples hand-aimed hotspots
 * @returns {{ok:boolean, reason?:string, samples:number, sign?:number,
 *            offsets?:Map<string,number>, mean?:number, worst?:number}}
 */
export function fit(samples) {
  if (samples.length < 3) {
    return { ok: false, samples: samples.length,
             reason: 'need at least 3 aimed hotspots between placed rooms' };
  }

  let best = null;
  for (const sign of [1, -1]) {
    const offsets = new Map();
    for (const s of samples) {
      if (offsets.has(s.from)) continue;
      offsets.set(s.from, circMean(samples.filter(x => x.from === s.from)
        .map(x => norm180(x.yaw - sign * x.bearing))));
    }
    const resid = samples.map(x =>
      Math.abs(norm180(x.yaw - (sign * x.bearing + offsets.get(x.from)))));
    const mean = resid.reduce((a, b) => a + b, 0) / resid.length;
    if (!best || mean < best.mean) {
      best = { sign, offsets, mean, worst: Math.max(...resid) };
    }
  }
  return { ok: true, samples: samples.length, ...best };
}

/** Yaw for a link the plan knows the geometry of but nobody has aimed. */
export const predict = (sign, offset, planBearing) => norm180(sign * planBearing + offset);
