/* Horizontal-FOV zoom model for the tour viewer.
 *
 * Photo Sphere Viewer expresses zoom as a *vertical* field of view. That is the
 * wrong anchor for a room: hold vFov constant and a 16:9 laptop takes in a whole
 * living room while a phone held upright sees a letterbox slit of the same shot.
 * Measured on this tour, one fixed setting handed out anywhere from 33deg to
 * 108deg horizontal depending on nothing but window shape.
 *
 * So every number a human tunes here is *horizontal* FOV -- "how much of the room
 * is on screen" -- and gets converted to PSV's vertical FOV against the live
 * viewport aspect. The limits are re-derived per shape too, not just the opening
 * view; without that a phone could zoom to a 6deg slit of mush while a laptop
 * bottomed out at a sane 21deg.
 *
 * This module is the single source of truth, imported by both the tour
 * (index.html) and the tuning harness (/tools/fov-tuner.html). Keep it that way:
 * a tuner running its own copy of this maths would happily recommend numbers the
 * tour does not actually produce.
 */

export const D = Math.PI / 180;

export const clamp = (x, lo, hi) => Math.min(Math.max(x, lo), hi);

/** Horizontal FOV -> vertical, for a viewport of the given width/height ratio. */
export const hToV = (h, a) => Math.atan(Math.tan(h * D / 2) / a) * 2 / D;

/** Vertical FOV -> horizontal. */
export const vToH = (v, a) => Math.atan(Math.tan(v * D / 2) * a) * 2 / D;

export const DEFAULTS = {
  /** Horizontal FOV the tour opens at. Wide enough to read a room at a glance
   *  rather than dropping the visitor nose-first into the furniture. */
  hStart: 130,
  /** Closest the visitor can zoom, horizontally. */
  hIn: 110,
  /** Widest they can pull back, horizontally. */
  hOut: 142,
  /** A tall viewport can only reach a wide horizontal FOV by going very wide
   *  vertically, and past this the equirect stops reading as a room and starts
   *  reading as a fisheye. A phone held upright is what hits these, so it opens
   *  a little tighter than a laptop rather than opening bulged.
   *
   *  125 is chosen, not rounded to: it is exactly what puts a 390x750 phone's
   *  opening view on 90deg horizontal. Move it and the phone moves with it. */
  vCeilStart: 125,
  vCeilOut: 145,
};

/**
 * Build the zoom model for a set of horizontal targets.
 * @param {Partial<typeof DEFAULTS>} cfg
 */
export function fovModel(cfg) {
  const c = { ...DEFAULTS, ...cfg };

  const startVFov = (a) => Math.min(hToV(c.hStart, a), c.vCeilStart);

  /** PSV's minFov/maxFov for a given viewport shape. */
  const boundsFor = (a) => {
    // The opening view has to be reachable. On a tall viewport the ceiling can
    // pull the opening *closer* than hIn allows -- a phone opening at 90deg
    // under a 110deg zoom-in limit -- and PSV would silently clamp the landing
    // view out to the limit. Letting the floor follow the opening keeps the
    // number you asked for on screen; that shape simply cannot zoom in past it.
    const minFov = clamp(Math.min(hToV(c.hIn, a), startVFov(a)), 1, 179);
    const maxFov = clamp(Math.min(hToV(c.hOut, a), c.vCeilOut), minFov, 179);
    return { minFov, maxFov };
  };

  /** PSV maps zoom level 0..100 linearly onto maxFov..minFov. */
  const zoomFor = (v, b) => clamp(100 * (b.maxFov - v) / (b.maxFov - b.minFov), 0, 100);
  const vFovOf = (lvl, b) => b.maxFov + lvl / 100 * (b.minFov - b.maxFov);

  const startZoom = (a) => zoomFor(startVFov(a), boundsFor(a));

  /** What this config actually delivers on a given viewport shape. */
  const report = (a) => {
    const b = boundsFor(a);
    return {
      aspect: a,
      open: vToH(startVFov(a), a),
      closest: vToH(b.minFov, a),
      widest: vToH(b.maxFov, a),
      minFov: b.minFov,
      maxFov: b.maxFov,
    };
  };

  return { config: c, boundsFor, zoomFor, vFovOf, startVFov, startZoom, report };
}

/** The viewport shapes worth checking a config against before shipping it. */
export const SHAPES = [
  { name: 'Desktop 16:9', w: 1600, h: 900 },
  { name: 'Laptop, tour stage', w: 1280, h: 616 },
  { name: 'Half-width window', w: 960, h: 1000 },
  { name: 'Phone portrait', w: 390, h: 750 },
  { name: 'Phone landscape', w: 844, h: 390 },
];
