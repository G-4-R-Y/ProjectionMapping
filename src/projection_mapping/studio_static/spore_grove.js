/* Original, dependency-free Spatial Studio Spore Grove generator (2026-11-17).
 * Point layout: [x,y,z,r,g,b,seed]. Seed >= 0.75 identifies drifting spores.
 * All geometry is deterministic and uploaded once; animation stays on WebGL2.
 */
(function (root) {
  'use strict';
  function generateSporeGrove() {
  // An original deterministic point sculpture, not third-party asset or shader code.
  let s = 0x5B0AE >>> 0;
  const rand = () => ((s = (Math.imul(s, 1664525) + 1013904223) >>> 0) / 4294967296);
  const points = [];
  const put = (x, y, z, r, g, b, seed) => points.push(x, y, z, r, g, b, seed);
  const tau = Math.PI * 2;
  // Thin ground gives perspective without filling the projected black floor.
  for (let z = -4; z > -120; z -= 0.65) {
    for (const x of [-7.0, -4.2, -2.4, 2.4, 4.2, 7.0]) {
      put(x + (rand() - 0.5) * 0.18, -2.53, z, 0.11, 0.24, 0.26, rand() * 0.72);
    }
    for (let k = 0; k < 12; k++) {
      const x = (rand() - .5) * 20;
      if (Math.abs(x) < 1.55) continue;
      put(x, -2.5 + rand() * 0.08, z + rand() * .5, .07, .13, .16, rand() * .72);
    }
  }
  // Repeated recognizable domes and stalks; no geometry regeneration per frame.
  for (let i = 0; i < 158; i++) {
    const side = i % 2 ? 1 : -1;
    const x = side * (2.1 + rand() * 6.1);
    const z = -5 - rand() * 113;
    const base = -2.48;
    const height = .7 + rand() * 2.05;
    const radius = .3 + rand() * .62;
    const dome = .16 + radius * .48;
    const hue = rand();
    const r = .34 + .48 * hue, g = .40 + .35 * (1 - hue), b = .73 + .24 * rand();
    for (let j = 0; j < 38; j++) {
      const t = j / 37, a = rand() * tau;
      const width = radius * (.12 + .10 * t) * Math.sqrt(rand());
      put(x + Math.cos(a) * width, base + height * t,
          z + Math.sin(a) * width, r * .64, g * .65, b * .65, rand() * .72);
    }
    for (let ring = 0; ring < 9; ring++) {
      const a = (ring + .2) / 8.2 * Math.PI * .5;
      const rim = radius * Math.sin(a), y = base + height + dome * Math.cos(a);
      for (let j = 0; j < 25; j++) {
        const angle = tau * (j + (ring % 2) * .5) / 25;
        const jitter = (rand() - .5) * .024;
        const glow = .72 + .28 * Math.cos(a);
        put(x + (rim + jitter) * Math.cos(angle), y,
            z + (rim + jitter) * Math.sin(angle),
            Math.min(1, r * glow), Math.min(1, g * glow), Math.min(1, b * glow),
            rand() * .72);
      }
    }
    // Underside gills create a readable cap silhouette when viewed from below.
    for (let spoke = 0; spoke < 18; spoke++) {
      const a = tau * spoke / 18;
      for (let j = 0; j < 5; j++) {
        const f = (j + 1) / 5;
        put(x + Math.cos(a) * radius * f, base + height - .035,
            z + Math.sin(a) * radius * f, .22, .45, .65, rand() * .72);
      }
    }
    for (let j = 0; j < 30; j++) {
      const a = rand() * tau, rr = Math.sqrt(rand()) * radius * 2.5;
      put(x + Math.cos(a) * rr, base + rand() * 1.1,
          z + Math.sin(a) * rr, .42 + .4 * hue, .66, .9, .75 + .25 * rand());
    }
  }
  // Sparse airborne light; seed >= 0.75 marks spores for animated vertex drift.
  for (let i = 0; i < 4100; i++) {
    const x = (rand() - .5) * 18, z = -4 - rand() * 116;
    const y = -2.25 + rand() * 5.9, bright = .24 + .75 * Math.pow(rand(), 3);
    put(x, y, z, bright * .6, bright * .85, bright, .75 + .25 * rand());
  }
  return new Float32Array(points);
}
  root.ProjectionSporeGrove = Object.freeze({ generate: generateSporeGrove });
})(globalThis);
