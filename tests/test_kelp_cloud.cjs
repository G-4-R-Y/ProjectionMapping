'use strict';
// Run: node tests/test_kelp_cloud.cjs
const { buildKelp, encodePly, parseArgs, POINT_COUNT, DEFAULT_SEED } =
  require('../scripts/generate_kelp_cloud.cjs');

function check(condition, message) {
  if (!condition) throw new Error(message);
}
function rejects(fn) {
  try { fn(); } catch (_) { return true; }
  return false;
}

const points = buildKelp();
check(points.length === POINT_COUNT && POINT_COUNT === 70128, 'fixed point budget');
check(POINT_COUNT < 130000, 'fits the existing Studio point cap');
check(points.every(p => p.length === 6 && p.every(Number.isFinite)), 'finite XYZRGB');
check(points.every(p => p.slice(3).every(v => Number.isInteger(v) && v >= 0 && v <= 255)), 'RGB byte range');
check(points.every(p => Math.abs(p[0]) < 7 && p[1] >= -3 && p[1] < 5 && Math.abs(p[2]) < 8),
  'asset has bounded coordinates');
const stemAndBlades = points.slice(0, 66528);
check(stemAndBlades.every(p => Math.abs(p[0]) > 0.5), 'keeps the central passage open');
const ply = encodePly(points, DEFAULT_SEED, 'ghost');
check(ply === encodePly(buildKelp(), DEFAULT_SEED, 'ghost'), 'same-seed reproducibility');
check(ply !== encodePly(buildKelp(42), 42, 'ghost'), 'seed changes geometry');
const lagoon = buildKelp(DEFAULT_SEED, 'lagoon');
check(points.every((p, i) => p.slice(0, 3).every((v, k) => v === lagoon[i][k])), 'palette preserves geometry');
check(points[0][3] !== lagoon[0][3], 'palette changes color');
check(ply.length < 40 * 1024 * 1024, 'fits the existing Studio byte cap');
const [header, body] = ply.split('end_header\n');
check(header.includes('format ascii 1.0') && header.includes('element vertex ' + POINT_COUNT), 'PLY header');
const rows = body.trim().split('\n');
check(rows.length === POINT_COUNT && rows.every(r => r.split(' ').length === 6), 'PLY row count and stride');
check(parseArgs(['out.ply']).seed === DEFAULT_SEED, 'CLI defaults');
check(parseArgs(['out.ply', '--seed', '0', '--palette', 'lagoon']).seed === 0, 'CLI explicit zero seed');
check(rejects(() => buildKelp(-1)) && rejects(() => buildKelp(1, 'invalid')), 'invalid API inputs');
check(rejects(() => parseArgs(['out.ply', '--seed', '4294967296'])) &&
  rejects(() => parseArgs(['out.ply', '--seed'])) && rejects(() => parseArgs(['out.ply', '--palette', 'oops'])) &&
  rejects(() => parseArgs(['out.xyz'])), 'invalid CLI inputs');
console.log('Kelp cloud geometry, determinism, palette, PLY and CLI contract: PASS');
