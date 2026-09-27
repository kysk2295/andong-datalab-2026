// Bridge decks are elevated surfaces, not terrain or water. Heights are a
// miniature approximation from their banks; OSM does not supply deck elevations.
export function bridgeSurfaces(features, elevation) {
  const surfaces = new Map();
  const moon = features.find((f) => f.properties["bridge:name"] === "월영교");
  const moonHeight = moon
    ? Math.max(
        elevation(moon.geometry.coordinates[0]),
        elevation(moon.geometry.coordinates.at(-1)),
      ) + 0.043
    : null;
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
    surfaces.set(String(f.id), () => height);
  }
  return surfaces;
}
