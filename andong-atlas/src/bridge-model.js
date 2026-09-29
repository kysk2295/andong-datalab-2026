import * as THREE from "three";

// Illustrative timber structure. Deck elevation matches bridge-surface.js;
// posts and the open pavilion leave the centre walking corridor unobstructed.
export function createWalkingBridge(
  points = [
    [-0.39, 0],
    [0.39, 0],
  ],
  { heights = points.map(() => 0), pavilion: withPavilion = true } = {},
) {
  const group = new THREE.Group();
  const wood = new THREE.MeshStandardMaterial({
    color: "#ac8055",
    emissive: "#facf81",
    emissiveIntensity: 0,
  });
  const rail = new THREE.MeshStandardMaterial({ color: "#876440" });
  const box = (name, size, pos, material = wood) => {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size), material);
    mesh.name = name;
    mesh.position.set(...pos);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    group.add(mesh);
    return mesh;
  };
  const lengths = points
    .slice(1)
    .map((b, i) => Math.hypot(b[0] - points[i][0], b[1] - points[i][1]));
  const half = lengths.reduce((a, b) => a + b, 0) / 2;
  let travelled = 0,
    pavilion = { x: 0, z: 0, rotation: 0 };
  for (let i = 1; i < points.length; i++) {
    const a = points[i - 1],
      b = points[i],
      length = lengths[i - 1];
    if (length < 1e-10) continue;
    const rise = heights[i] - heights[i-1];
    const dx = (b[0] - a[0]) / length,
      dz = (b[1] - a[1]) / length;
    const segmentBox = (name, size, t, side, y, mat = wood) => {
      const mesh = box(
        name,
        size,
        [
          a[0] + dx * length * t - dz * side,
          y + heights[i-1] + rise*t,
          a[1] + dz * length * t + dx * side,
        ],
        mat,
      );
      mesh.rotation.y = -Math.atan2(dz, dx);
      return mesh;
    };
    const deck=segmentBox("deck", [length + 0.001, 0.016, 0.008], 0.5, 0, 0);
    const vertices=deck.geometry.attributes.position;
    for(let n=0;n<vertices.count;n++)vertices.setY(n,vertices.getY(n)+vertices.getX(n)*rise/length);
    deck.geometry.computeVertexNormals();
    const supportCount = Math.max(1, Math.ceil(length / 0.15));
    for (let k = 0; k < supportCount; k++)
      segmentBox(
        "support",
        [0.008, 0.2, 0.006],
        (k + 0.5) / supportCount,
        0,
        -0.108,
        rail,
      );
    for (const side of [-0.0046, 0.0046]) {
      const handrail=segmentBox("handrail", [Math.hypot(length,rise), 0.0012, 0.0009], 0.5, side, 0.017, rail);
      handrail.rotation.z=Math.atan2(rise,length);
      const posts = Math.ceil(length / 0.0095);
      for (let k = 0; k <= posts; k++)
        segmentBox(
          "post",
          [0.0009, 0.009, 0.0009],
          k / posts,
          side,
          0.0125,
          rail,
        );
    }
    if (travelled <= half && travelled + length >= half) {
      const offset = half - travelled;
      pavilion = {
        x: a[0] + dx * offset,
        z: a[1] + dz * offset,
        y: heights[i-1] + rise*offset/length,
        rotation: -Math.atan2(dz, dx),
      };
    }
    travelled += length;
  }
  // Fill the outside of each bend, where two rotated rectangular spans leave a
  // triangular opening. Duplicate points are skipped above without producing NaNs.
  for (let i=1;i<points.length-1;i++) {
    const joint=new THREE.Mesh(new THREE.CylinderGeometry(.0048,.0048,.016,12),wood);
    joint.name='deck-joint';joint.position.set(points[i][0],heights[i],points[i][1]);
    joint.castShadow=true;joint.receiveShadow=true;group.add(joint);
  }
  if (!withPavilion) return {group,wood};
  const pavilionStart = group.children.length;
  box("pavilion-floor", [0.028, 0.0012, 0.018], [0, 0.0074, 0]);
  for (const x of [-0.012, 0, 0.012])
    for (const z of [-0.0075, 0.0075])
      box("pavilion-column", [0.0015, 0.027, 0.0015], [x, 0.0215, z], rail);
  const roof = new THREE.Mesh(
    new THREE.ConeGeometry(0.023, 0.012, 4),
    new THREE.MeshStandardMaterial({ color: "#596c69" }),
  );
  roof.name = "pavilion-roof";
  roof.rotation.y = Math.PI / 4;
  roof.scale.z = 0.72;
  roof.position.y = 0.0405;
  group.add(roof);
  const pavilionGroup = new THREE.Group();
  for (const child of group.children.slice(pavilionStart))
    pavilionGroup.add(child);
  pavilionGroup.position.set(pavilion.x, pavilion.y || 0, pavilion.z);
  pavilionGroup.rotation.y = pavilion.rotation;
  group.add(pavilionGroup);
  return { group, wood };
}
