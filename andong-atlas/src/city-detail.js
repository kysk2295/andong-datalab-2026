import * as THREE from "three";
import { inRing, polygons } from "./geo.js";

export function detailedFacade(material) {
  material.onBeforeCompile = (shader) => {
    shader.vertexShader = shader.vertexShader
      .replace(
        "#include <common>",
        "#include <common>\nvarying vec3 atlasPosition; varying vec3 atlasNormal;",
      )
      .replace(
        "#include <begin_vertex>",
        "#include <begin_vertex>\natlasPosition=position; atlasNormal=normal;",
      );
    shader.fragmentShader = shader.fragmentShader.replace(
      "#include <common>",
      "#include <common>\nvarying vec3 atlasPosition; varying vec3 atlasNormal;",
    );
    shader.fragmentShader = shader.fragmentShader.replace(
      "#include <color_fragment>",
      `#include <color_fragment>
   float side=1.0-step(0.5,abs(atlasNormal.y));
   float along=abs(atlasNormal.x)>abs(atlasNormal.z)?atlasPosition.z:atlasPosition.x;
   vec2 facade=vec2(along/.014,atlasPosition.y/.015);
   vec2 cell=fract(facade), aa=max(fwidth(facade),vec2(.018));
   float glass=side*smoothstep(.15,.15+aa.x,cell.x)*(1.0-smoothstep(.85-aa.x,.85,cell.x))*smoothstep(.19,.19+aa.y,cell.y)*(1.0-smoothstep(.84-aa.y,.84,cell.y));
   float mullion=1.0-smoothstep(.025,.055,abs(cell.x-.5));
   float lit=step(.88,fract(sin(dot(floor(facade),vec2(12.9898,78.233)))*43758.5453));
   vec3 pane=mix(vec3(.045,.105,.14),vec3(.17,.28,.32),step(.6,cell.x));
   pane=mix(pane,vec3(.78,.74,.61),mullion*.7);
   diffuseColor.rgb=mix(diffuseColor.rgb,pane,glass*.97);
  `,
    );
    shader.fragmentShader = shader.fragmentShader.replace(
      "#include <emissivemap_fragment>",
      "#include <emissivemap_fragment>\ntotalEmissiveRadiance *= glass * lit;",
    );
  };
  material.customProgramCacheKey = () => "andong-facade-v3";
}
export class CityDetail {
  constructor(atlas) {
    this.atlas = atlas;
    this.group = new THREE.Group();
    atlas.world.add(this.group);
    this.time = 0;
    this.running = true;
    this.boats = [];
    this.cars = [];
    const waters = atlas.data.map.water.flatMap((f) => polygons(f.geometry));
    const inside = (c) =>
      waters.some(
        (p) => inRing(c, p[0]) && !p.slice(1).some((r) => inRing(c, r)),
      );
    this.waterRoute = [];
    for (const center of [
      [128.7614, 36.5754],
      [128.7607, 36.575],
      [128.762, 36.576],
    ]) {
      const ring = Array.from({ length: 65 }, (_, i) => [
        center[0] + Math.cos((i / 64) * Math.PI * 2) * 0.00036,
        center[1] + Math.sin((i / 64) * Math.PI * 2) * 0.00055,
      ]);
      if (ring.every(inside)) {
        this.waterRoute = ring;
        break;
      }
    }
    if (this.waterRoute.length) {
      this.waterPath = new THREE.CatmullRomCurve3(
        this.waterRoute.slice(0, -1).map((c) => atlas.point(c, 0.022)),
        true,
        "centripetal",
      );
      for (let i = 0; i < 4; i++) {
        const g = new THREE.Group();
        g.userData.boat = true;
        g.scale.set(0.18, 0.4, 0.18);
        this.group.add(g);
        const hull = new THREE.Mesh(
          new THREE.SphereGeometry(1, 12, 8),
          new THREE.MeshStandardMaterial({
            color: i % 2 ? "#d9bc85" : "#f0e6cc",
            roughness: 0.5,
          }),
        );
        hull.scale.set(0.025, 0.01, 0.06);
        g.add(hull);
        this.box(g, 0.035, 0.008, 0.064, 0, 0.012, 0, "#987654");
        for (const z of [-0.018, 0.018]) {
          this.box(g, 0.025, 0.012, 0.011, 0, 0.02, z, "#e6d4a7");
          const head = new THREE.Mesh(
            new THREE.SphereGeometry(0.005, 8, 6),
            new THREE.MeshStandardMaterial({ color: "#cba17e" }),
          );
          head.position.set(0, 0.037, z);
          g.add(head);
          this.box(g, 0.01, 0.016, 0.009, 0, 0.026, z, "#527669");
        }
        const arc = new THREE.Mesh(
          new THREE.TorusGeometry(0.032, 0.003, 6, 20, Math.PI * 1.4),
          new THREE.MeshStandardMaterial({
            color: "#f5dfad",
            emissive: "#ffc15c",
            emissiveIntensity: 0.35,
          }),
        );
        arc.position.y = 0.04;
        arc.rotation.y = Math.PI / 2;
        g.add(arc);
        const wake = new THREE.Line(
          new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(-0.026, -0.003, -0.06),
            new THREE.Vector3(0, -0.003, -0.04),
            new THREE.Vector3(0.026, -0.003, -0.06),
          ]),
          new THREE.LineBasicMaterial({
            color: "#e3f3ee",
            transparent: true,
            opacity: 0.7,
          }),
        );
        g.add(wake);
        this.boats.push(g);
      }
    }
    this.roadPath = new THREE.CurvePath();
    const ps = atlas.data.solution.route.map((c) => atlas.point(c, 0.012));
    for (let i = 1; i < ps.length; i++)
      this.roadPath.add(new THREE.LineCurve3(ps[i - 1], ps[i]));
    for (let i = 0; i < 6; i++) {
      const g = new THREE.Group();
      this.group.add(g);
      this.box(
        g,
        0.022,
        0.014,
        0.046,
        0,
        0.012,
        0,
        ["#e4d8bc", "#7faaa4", "#bb865f"][i % 3],
      );
      this.box(g, 0.019, 0.012, 0.023, 0, 0.024, 0, "#587780");
      for (const x of [-0.012, 0.012])
        for (const z of [-0.014, 0.014]) {
          const w = new THREE.Mesh(
            new THREE.CylinderGeometry(0.006, 0.006, 0.004, 8),
            new THREE.MeshStandardMaterial({ color: "#37413e" }),
          );
          w.rotation.z = Math.PI / 2;
          w.position.set(x, 0.006, z);
          g.add(w);
        }
      this.cars.push(g);
    }
  }
  box(g, w, h, d, x, y, z, color) {
    const m = new THREE.Mesh(
      new THREE.BoxGeometry(w, h, d),
      new THREE.MeshStandardMaterial({ color }),
    );
    m.position.set(x, y, z);
    g.add(m);
  }
  update(delta) {
    if (this.running && !this.atlas.reduced) this.time += delta;
    this.cars.forEach((g, i) => {
      g.visible =
        !this.atlas.solution.group.visible &&
        !this.atlas.district?.group.visible;
      const p = (this.time / 95 + i / 6) % 1,
        u = p < 0.5 ? p * 2 : 2 - p * 2;
      this.move(g, this.roadPath, u, p < 0.5 ? 0 : Math.PI);
    });
    this.boats.forEach((g, i) => {
      this.move(g, this.waterPath, (this.time / 70 + i / 4) % 1, 0);
      g.rotation.z = Math.sin(this.time * 1.4 + i) * 0.035;
    });
  }
  move(g, path, t, reverse) {
    t = Math.max(0.001, Math.min(0.999, t));
    g.position.copy(path.getPointAt(t));
    g.position.y =
      this.atlas.elevation(
        this.atlas.project.toGeo(g.position.x, g.position.z),
      ) + (g.userData?.boat ? 0.008 : 0.012);
    const d = path.getTangentAt(t);
    g.rotation.y = Math.atan2(d.x, d.z) + reverse;
  }
  focusBoats() {
    if (this.waterRoute.length)
      this.atlas.fly(
        this.waterRoute[0],
        0.95,
        false,
        new THREE.Vector3(-0.65, 1, 0.15),
      );
  }
}
