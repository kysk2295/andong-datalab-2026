// These choices style a miniature, not a surveyed material/visitor inventory.
export function heritageAppearance(feature, region) {
  const p = feature.properties, traditional = p.visualRoof === 'traditional';
  let seed = 0;
  for (const c of String(feature.id)) seed = (seed * 31 + c.charCodeAt(0)) >>> 0;
  const thatch = traditional && region === 'hahoe' && (!p.name || p.name.includes('초가')) && seed % 5 < 3;
  return { traditional, thatch,
    roof: thatch ? ['#ac915e','#b7a174','#a58f68'][seed % 3] : ['#556163','#657073','#4c595d'][seed % 3],
    wall: ['#e1d4b9','#e9ddc6','#d9c9aa'][seed % 3], rise: thatch ? .010 : .012 };
}

export function heritageLane(tags, heritage) {
  if (!heritage) return false;
  return ['path','footway','pedestrian','steps','track'].includes(tags.highway)
    || (['service','residential'].includes(tags.highway) && !['asphalt','concrete'].includes(tags.surface));
}

export function visitorWeight(x, z, center, foot) {
  const distance2 = (x-center[0])**2 + (z-center[1])**2;
  return (1 + 65 * Math.exp(-distance2 / .14)) * (foot ? 2.4 : 1);
}

// Alternating walks with short rests are continuous at the phase boundaries.
// Every member of a small party uses the same travel clock.
export function visitorProgress(time, index, length) {
  const party = Math.floor(index / 3), speed = .0015 + (party % 5) * .00016;
  const travel = Math.max(.001, length) / speed, rest = 2 + party % 5;
  const leg = travel + rest, cycle = ((time + party * 11.71) % (2 * leg) + 2 * leg) % (2 * leg);
  const forward = cycle < leg, local = forward ? cycle : cycle - leg;
  const t = Math.min(1, local / travel);
  return {t:forward?t:1-t,direction:forward?1:-1,moving:local<travel};
}
