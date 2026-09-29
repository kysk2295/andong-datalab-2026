// Bridge decks are elevated surfaces, not terrain or water. Heights are a
// miniature approximation from their banks; OSM does not supply deck elevations.
export function bridgeDeckProfile(feature, elevation, project) {
  const coordinates = feature.geometry.coordinates;
  const points = coordinates.map(c => project.toWorld(c));
  const level = Math.max(elevation(coordinates[0]), elevation(coordinates.at(-1))) + .043;
  // Both banks meet their paved path. The first and last spans rise to the
  // central crossing instead of leaving the lower bank suspended in mid-air.
  const heights = points.map((_, i) => i === 0 || i === points.length - 1
    ? elevation(coordinates[i]) + .0012 : level);
  const at = (x, z) => {
    if (!Number.isFinite(x) || !Number.isFinite(z)) return level;
    let nearest = Infinity, height = level;
    for (let i = 1; i < points.length; i++) {
      const a = points[i-1], b = points[i], dx=b[0]-a[0], dz=b[1]-a[1];
      const t=Math.max(0,Math.min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz||1)));
      const distance=Math.hypot(x-a[0]-dx*t,z-a[1]-dz*t);
      if (distance < nearest) { nearest=distance; height=heights[i-1]+(heights[i]-heights[i-1])*t; }
    }
    return height;
  };
  return { points, heights, at };
}

export function bridgeSurfaces(features, elevation, project) {
  const surfaces = new Map();
  const moon = features.find((f) => f.properties["bridge:name"] === "월영교");
  const moonHeight = moon
    ? Math.max(
        elevation(moon.geometry.coordinates[0]),
        elevation(moon.geometry.coordinates.at(-1)),
      ) + 0.043
    : null;
  const profile = moon && project ? bridgeDeckProfile(moon, elevation, project) : null;
  for (const f of features) {
    if (!f.properties.bridge || f.properties.bridge === "no") continue;
    const c = f.geometry.coordinates,
      named =
        f.properties["bridge:name"] === "월영교" ||
        f.properties.name === "Moonlight Bridge";
    const height =
      named && moonHeight !== null
        ? moonHeight
        : Math.max(elevation(c[0]), elevation(c.at(-1))) + 0.008;
    surfaces.set(String(f.id), named && profile ? profile.at : () => height);
  }
  return surfaces;
}
