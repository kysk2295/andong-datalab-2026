// Follow the mapped corridor while keeping the camera outside building shells.
// Returns null when no continuous clear corridor exists; callers must not fly through it.
export function clearCameraPath(points, blocked, margin = 0.001) {
  if (points.length < 2) return points;
  const safe = (a, b) => {
    const n = Math.max(1, Math.ceil(Math.hypot(a.x - b.x, a.z - b.z) / 0.001));
    for (let k = 0; k <= n; k++) {
      const t = k / n;
      if (blocked(a.x + (b.x - a.x) * t, a.z + (b.z - a.z) * t, margin))
        return false;
    }
    return true;
  };
  if (points.every((p, i) => !i || safe(points[i - 1], p))) return points;
  // Resolve only a short envelope around the mapped path, with continuity checked at 0.5 m.
  let states = [{ point: points[0], cost: 0, prev: null }],
    layers = [];
  for (let i = 0; i < points.length; i++) {
    const p = points[i],
      a = points[Math.max(0, i - 1)],
      b = points[Math.min(points.length - 1, i + 1)],
      dx = b.x - a.x,
      dz = b.z - a.z,
      len = Math.hypot(dx, dz) || 1,
      candidates = [];
    for (const offset of [
      0, 0.002, -0.002, 0.004, -0.004, 0.006, -0.006, 0.009, -0.009, 0.012,
      -0.012, 0.016, -0.016, 0.022, -0.022, 0.03, -0.03,
    ]) {
      const q = {
        ...p,
        x: p.x - (dz / len) * offset,
        z: p.z + (dx / len) * offset,
      };
      if (blocked(q.x, q.z, margin)) continue;
      if (!i) {
        candidates.push({ point: q, cost: Math.abs(offset) * 2, prev: null });
        continue;
      }
      let best = null;
      for (const s of states) {
        const jump = Math.hypot(q.x - s.point.x, q.z - s.point.z);
        if (jump > 0.014 || !safe(s.point, q)) continue;
        const cost = s.cost + Math.abs(offset) * 0.25 + jump;
        if (!best || cost < best.cost) best = { point: q, cost, prev: s };
      }
      if (best) candidates.push(best);
    }
    if (!candidates.length) return null;
    states = candidates;
    layers.push(states);
  }
  let best = states.reduce((a, b) => (a.cost < b.cost ? a : b)),
    out = [];
  while (best) {
    out.push(best.point);
    best = best.prev;
  }
  return out.reverse();
}
