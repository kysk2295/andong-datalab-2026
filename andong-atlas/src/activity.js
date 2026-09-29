// Deterministic stratified sampling: populate paths by length, with a denser town centre.
// These are presentation densities, not observed traffic or population statistics.
export function distributedIndices(items, count, weight) {
  const cumulative = [];
  let total = 0;
  for (const item of items) {
    total += Math.max(0, weight(item));
    cumulative.push(total);
  }
  if (!items.length || !total) return [];
  return Array.from({ length: count }, (_, i) => {
    const t = ((i + 0.5) / count) * total;
    let lo = 0,
      hi = items.length - 1;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (cumulative[mid] < t) lo = mid + 1;
      else hi = mid;
    }
    return lo;
  });
}
export function urbanWeight(x, z, center) {
  return 1 + 8 * Math.exp(-((x - center[0]) ** 2 + (z - center[1]) ** 2) / 1.2);
}

// Split a sampled walkway at obstacles. A person reverses at each end rather than
// wrapping from one end to the other or passing through a mapped building.
export function clearRuns(points, blocked, margin = 0.002) {
  const runs = [];
  let run = [];
  const flush = () => {
    if (run.length > 1) runs.push(run);
    run = [];
  };
  for (const p of points) {
    if (blocked(p.x, p.z, margin)) flush();
    else {
      const previous=run.at(-1);
      if(previous){
        const steps=Math.ceil(Math.hypot(p.x-previous.x,p.z-previous.z)/.0005);
        for(let i=1;i<steps;i++)if(blocked(previous.x+(p.x-previous.x)*i/steps,previous.z+(p.z-previous.z)*i/steps,margin)){flush();break;}
      }
      run.push(p);
    }
  }
  flush();
  return runs;
}
export function walkingProgress(time, phase, length) {
  const cycle =
    ((((time * 0.002) / Math.max(0.001, length) + phase) % 2) + 2) % 2;
  return { t: cycle <= 1 ? cycle : 2 - cycle, direction: cycle <= 1 ? 1 : -1 };
}
