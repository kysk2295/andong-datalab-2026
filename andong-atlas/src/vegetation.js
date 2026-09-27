import * as THREE from "three";
// Stylized trees inside mapped woodland. Positions are decorative, not a tree survey.
export class Vegetation {
  constructor(parent, points) {
    this.points = points;
    this.group = new THREE.Group();
    parent.add(this.group);
    this.leaves = new THREE.InstancedMesh(
      new THREE.IcosahedronGeometry(1, 0),
      new THREE.MeshStandardMaterial({
        color: "#ffffff",
        roughness: 1,
        flatShading: true,
      }),
      points.length * 2,
    );
    this.wood = new THREE.InstancedMesh(
      new THREE.CylinderGeometry(0.08, 0.12, 1, 5),
      new THREE.MeshStandardMaterial({ color: "#786e4d", roughness: 1 }),
      points.length * 3,
    );
    this.twigs = new THREE.InstancedMesh(
      new THREE.CylinderGeometry(0.035, 0.055, 1, 4),
      this.wood.material,
      points.length * 4,
    );
    this.group.add(this.twigs);
    this.twigs.castShadow = true;
    this.leaves.castShadow = true;
    this.wood.castShadow = true;
    this.group.add(this.wood, this.leaves);
    this.setSeason("summer");
  }
  setSeason(season) {
    if (this.season === season) return;
    this.season = season;
    this.twigs.visible = season === "winter";
    const dummy = new THREE.Object3D(),
      color = new THREE.Color();
    this.points.forEach((p, i) => {
      const s = p.size,
        t = p.tint;
      for (let j = 0; j < 3; j++) {
        dummy.position.set(
          p.x + (j ? (j === 1 ? -s * 0.24 : s * 0.24) : 0),
          p.y + s * (j ? 1.1 : 0.7),
          p.z,
        );
        dummy.scale.set(s, s * (j ? 1 : 1.4), s);
        dummy.rotation.set(0, t * 6, 0);
        dummy.rotation.z = j ? (j === 1 ? 0.55 : -0.55) : 0;
        dummy.updateMatrix();
        this.wood.setMatrixAt(i * 3 + j, dummy.matrix);
      }
      if (season === "winter")
        for (let j = 0; j < 4; j++) {
          const side = j % 2 ? 1 : -1;
          dummy.position.set(
            p.x + side * s * (j < 2 ? 0.4 : 0.2),
            p.y + s * (j < 2 ? 1.5 : 1.9),
            p.z + side * s * 0.14,
          );
          dummy.rotation.set(j < 2 ? 0.2 : -0.3, t * 6, side * 0.8);
          dummy.scale.set(s, s * 0.7, s);
          dummy.updateMatrix();
          this.twigs.setMatrixAt(i * 4 + j, dummy.matrix);
        }
      for (let j = 0; j < 2; j++) {
        dummy.position.set(
          p.x + (j ? s * 0.3 : 0),
          p.y + s * (j ? 1.65 : 2),
          p.z + (j ? s * 0.15 : 0),
        );
        dummy.rotation.set(t * 0.4, t * 6, j * 0.3);
        const winter = season === "winter",
          scale = winter ? (t > 0.7 ? 0.55 : 0) : 1;
        dummy.scale.set(
          s * (j ? 0.65 : 0.9) * scale,
          s * (j ? 0.8 : 1.2) * scale,
          s * (j ? 0.65 : 0.85) * scale,
        );
        dummy.updateMatrix();
        this.leaves.setMatrixAt(i * 2 + j, dummy.matrix);
        if (season === "autumn")
          color.setHSL(0.045 + t * 0.09, 0.5, 0.31 + t * 0.15);
        else if (season === "spring" && t > 0.68)
          color.setHSL(0.94, 0.26, 0.65 + t * 0.15);
        else
          color.setHSL(
            0.27 + t * 0.08,
            season === "winter" ? 0.19 : 0.36,
            0.07 + t * 0.12,
          );
        this.leaves.setColorAt(i * 2 + j, color);
      }
    });
    this.leaves.instanceMatrix.needsUpdate = true;
    this.leaves.instanceColor.needsUpdate = true;
    this.wood.instanceMatrix.needsUpdate = true;
    this.twigs.instanceMatrix.needsUpdate = true;
  }
}
