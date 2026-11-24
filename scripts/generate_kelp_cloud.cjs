// Original procedural point asset, inspired by Codevember 2026 day 17 (Kelp).
// No upstream source, assets, shader or runtime dependency is used.
'use strict';

const STALKS = 28;
const STEM_STEPS = 72;
const BLADES = 18;
const BLADE_STEPS = 24;
const BLADE_WIDTH_STEPS = 5;
const FLOOR_POINTS = 1600;
const SNOW_POINTS = 2000;
const POINT_COUNT = STALKS * (STEM_STEPS * 3 + BLADES * BLADE_STEPS * BLADE_WIDTH_STEPS)
  + FLOOR_POINTS + SNOW_POINTS;
const DEFAULT_SEED = 20261124;
const TAU = 2 * Math.PI;

function rng(seed) {
  let state = seed >>> 0;
  if (!state) state = 0x6d2b79f5;
  return () => {
    state ^= state << 13;
    state ^= state >>> 17;
    state ^= state << 5;
    return (state >>> 0) / 4294967296;
  };
}

function buildKelp(seed = DEFAULT_SEED, palette = 'ghost') {
  if (!Number.isInteger(seed) || seed < 0 || seed > 0xffffffff) {
    throw new RangeError('seed must be an unsigned 32-bit integer');
  }
  if (!['ghost', 'lagoon'].includes(palette)) throw new RangeError('unknown palette');
  const rand = rng(seed);
  const points = [];
  // Color is baked into ordinary RGB vertices; the viewer may override it.
  function add(x, y, z, light, kind) {
    const gain = Math.max(0.08, Math.min(1, light));
    const base = palette === 'ghost' ? [234, 242, 255]
      : kind === 'snow' ? [180, 233, 255]
      : kind === 'stem' ? [77, 214, 183]
      : kind === 'floor' ? [63, 124, 161] : [98, 249, 225];
    points.push([x, y, z, ...base.map(v => Math.round(v * gain))]);
  }
  // A central open passage, framed by staggered tall stalks on both sides.
  for (let j = 0; j < STALKS; j++) {
    const side = j % 2 ? 1 : -1;
    const depth = Math.floor(j / 2);
    const x0 = side * (2.6 + 1.35 * rand());
    const z0 = -6.3 + depth * 0.97 + (rand() - 0.5) * 0.7;
    const height = 4.2 + 2.2 * rand();
    const phase = TAU * rand();
    const lean = 0.35 + 0.45 * rand();
    function stem(t) {
      return [
        x0 + lean * t * t * Math.sin(phase + 4.2 * t),
        -2.8 + height * t,
        z0 + lean * t * Math.cos(phase + 3.1 * t),
      ];
    }
    for (let k = 0; k < STEM_STEPS; k++) {
      const t = k / (STEM_STEPS - 1);
      const [x, y, z] = stem(t);
      const radius = 0.045 * (1 - 0.6 * t);
      for (let a = 0; a < 3; a++) {
        const angle = phase + TAU * a / 3 + t * 9;
        add(x + radius * Math.cos(angle), y, z + radius * Math.sin(angle),
          0.48 + 0.3 * t, 'stem');
      }
    }
    // Alternating tapered, curved blades; fixed sampling of a continuous surface.
    for (let b = 0; b < BLADES; b++) {
      const t = 0.12 + 0.84 * b / (BLADES - 1);
      const [x, y, z] = stem(t);
      const theta = phase + b * 2.399963229728653;
      const dx = Math.cos(theta), dz = Math.sin(theta);
      const length = (0.52 + 0.48 * rand()) * (0.75 + 0.32 * Math.sin(Math.PI * t));
      const width = 0.11 + 0.12 * rand();
      for (let k = 0; k < BLADE_STEPS; k++) {
        const u = k / (BLADE_STEPS - 1);
        const taper = Math.pow(Math.sin(Math.PI * u), 0.85);
        const curl = 0.14 * Math.sin(2.7 * u + phase) * u;
        for (let w = 0; w < BLADE_WIDTH_STEPS; w++) {
          const v = 2 * w / (BLADE_WIDTH_STEPS - 1) - 1;
          const offset = width * taper * v + curl;
          const tip = 0.32 * Math.sin(Math.PI * u) - 0.24 * u * u;
          const ripple = 0.08 * v * taper * Math.sin(10 * u + phase);
          add(x + dx * length * u - dz * offset,
            y + tip + ripple, z + dz * length * u + dx * offset,
            0.34 + 0.39 * t + 0.19 * Math.abs(v), 'blade');
        }
      }
    }
  }
  // Sparse substrate and drifting-particle reference positions, not animated physics.
  for (let i = 0; i < FLOOR_POINTS; i++) {
    const x = (rand() - 0.5) * 9.8;
    const z = (rand() - 0.5) * 14;
    add(x, -2.8 + 0.08 * Math.sin(x * 3 + z), z, 0.12 + 0.17 * rand(), 'floor');
  }
  for (let i = 0; i < SNOW_POINTS; i++) {
    add((rand() - 0.5) * 10, -2.5 + 6.4 * rand(), (rand() - 0.5) * 14,
      0.15 + 0.42 * rand() ** 3, 'snow');
  }
  return points;
}

function encodePly(points, seed, palette) {
  const lines = [
    'ply', 'format ascii 1.0',
    'comment original procedural kelp cloud; synthetic geometry, not a scan',
    'comment seed ' + seed + ' palette ' + palette,
    'element vertex ' + points.length,
    'property float x', 'property float y', 'property float z',
    'property uchar red', 'property uchar green', 'property uchar blue', 'end_header',
  ];
  for (const p of points) {
    lines.push(p.slice(0, 3).map(v => v.toFixed(5)).concat(p.slice(3)).join(' '));
  }
  return lines.join('\n') + '\n';
}

function parseArgs(args) {
  const result = { seed: DEFAULT_SEED, palette: 'ghost', output: null };
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--seed') {
      const value = args[++i];
      if (!/^\d+$/.test(value || '') || Number(value) > 0xffffffff) {
        throw new Error('--seed must be an unsigned 32-bit integer');
      }
      result.seed = Number(value);
    } else if (arg === '--palette') {
      const value = args[++i];
      if (!['ghost', 'lagoon'].includes(value)) throw new Error('--palette: ghost or lagoon');
      result.palette = value;
    } else if (!arg.startsWith('-') && !result.output) {
      result.output = arg;
    } else {
      throw new Error('unknown or duplicate argument: ' + arg);
    }
  }
  if (!result.output || !/\.ply$/i.test(result.output)) throw new Error('output must be a .ply file');
  return result;
}

function main(args) {
  const usage = 'node scripts/generate_kelp_cloud.cjs <new-file.ply> [--seed N] [--palette ghost|lagoon]';
  if (args.includes('--help')) {
    console.log(usage);
    return;
  }
  try {
    const options = parseArgs(args);
    const data = encodePly(buildKelp(options.seed, options.palette), options.seed, options.palette);
    require('node:fs').writeFileSync(options.output, data, { encoding: 'ascii', flag: 'wx' });
    console.log('Wrote ' + POINT_COUNT + ' synthetic points to ' + options.output);
  } catch (error) {
    console.error(error.message + '\n' + usage);
    process.exitCode = 1;
  }
}

module.exports = { buildKelp, encodePly, parseArgs, POINT_COUNT, DEFAULT_SEED };
if (require.main === module) main(process.argv.slice(2));
