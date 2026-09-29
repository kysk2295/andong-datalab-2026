import * as THREE from "three";

// Symbol sizes are exaggerated for legibility; positions remain geographic.
export class SolutionScene {
  constructor(atlas, data, onPick) {
    this.atlas = atlas;
    this.data = data;
    this.onPick = onPick;
    this.group = new THREE.Group();
    atlas.world.add(this.group);
    this.group.visible = false;
    this.time = 0;
    this.running = true;
    this.materials = new Map();
    this.pickables = [];
    this.people = [];
    this.vehicles = [];
    this.sites = data.sites.map((s) => ({ ...s, group: new THREE.Group() }));
    for (const s of this.sites) {
      s.group.position.copy(atlas.point(s.coordinates, 0.025));
      s.group.scale.set(
        s.id === "popup" ? 0.06 : 0.12,
        s.id === "popup" ? 0.2 : 0.3,
        s.id === "popup" ? 0.06 : 0.12,
      );
      this.group.add(s.group);
    }
    atlas.controls.addEventListener("start", () => {
      this.follow = false;
    });
    this.buildMarket();
    this.buildPopup();
    this.buildTransport();
    this.buildPeople();
    this.positionSites();
    const canvas = atlas.renderer.domElement;
    canvas.addEventListener("pointerdown", (e) => {
      this.down = [e.clientX, e.clientY];
    });
    canvas.addEventListener("pointerup", (e) => {
      if (
        !this.group.visible ||
        this.atlas.journey?.group.visible ||
        !this.down ||
        Math.hypot(e.clientX - this.down[0], e.clientY - this.down[1]) > 5
      )
        return;
      const rect = canvas.getBoundingClientRect(),
        ray = new THREE.Raycaster();
      ray.setFromCamera(
        new THREE.Vector2(
          ((e.clientX - rect.left) / rect.width) * 2 - 1,
          (-(e.clientY - rect.top) / rect.height) * 2 + 1,
        ),
        atlas.camera,
      );
      const hit = ray.intersectObjects(this.pickables, true)[0];
      if (hit) {
        let obj = hit.object;
        while (obj && !obj.userData.site) obj = obj.parent;
        if (obj) this.onPick(obj.userData.site);
      }
    });
  }
  positionSites() {
    // A level display plinth keeps proposal models readable on the exaggerated terrain.
    // This is presentation geometry, not a construction/earthworks proposal.
    for (const site of this.sites) {
      const center = this.atlas.point(site.coordinates),
        width = site.id === "popup" ? 0.84 : 0.7,
        depth = site.id === "popup" ? 0.6 : 0.42,
        scale = site.group.scale.x,
        verticalScale = site.group.scale.y,
        ground = (x, z) =>
          this.atlas.elevation(
            this.atlas.project.toGeo(
              center.x + x * scale,
              center.z + z * scale,
            ),
          );
      let top = -Infinity;
      for (let x = 0; x <= 8; x++)
        for (let z = 0; z <= 8; z++)
          top = Math.max(
            top,
            ground((x / 8 - 0.5) * width, (z / 8 - 0.5) * depth),
          );
      site.group.position.set(center.x, top + 0.001, center.z);
      const vertices = [],
        corners = [
          [-width / 2, -depth / 2],
          [width / 2, -depth / 2],
          [width / 2, depth / 2],
          [-width / 2, depth / 2],
        ];
      for (let side = 0; side < 4; side++) {
        const a = corners[side],
          b = corners[(side + 1) % 4];
        for (let step = 0; step < 8; step++) {
          const x1 = a[0] + ((b[0] - a[0]) * step) / 8,
            z1 = a[1] + ((b[1] - a[1]) * step) / 8,
            x2 = a[0] + ((b[0] - a[0]) * (step + 1)) / 8,
            z2 = a[1] + ((b[1] - a[1]) * (step + 1)) / 8,
            y1 =
              (ground(x1, z1) - site.group.position.y) / verticalScale - 0.01,
            y2 =
              (ground(x2, z2) - site.group.position.y) / verticalScale - 0.01;
          vertices.push(
            x1,
            -0.01,
            z1,
            x1,
            y1,
            z1,
            x2,
            -0.01,
            z2,
            x2,
            -0.01,
            z2,
            x1,
            y1,
            z1,
            x2,
            y2,
            z2,
          );
        }
      }
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute(
        "position",
        new THREE.Float32BufferAttribute(vertices, 3),
      );
      geometry.computeVertexNormals();
      if (site.plinth) {
        site.plinth.geometry.dispose();
        site.plinth.geometry = geometry;
      } else {
        const material = this.material("#c2c3ad");
        material.side = THREE.DoubleSide;
        site.plinth = new THREE.Mesh(geometry, material);
        site.group.add(site.plinth);
      }
    }
  }
  material(color) {
    if (!this.materials.has(color))
      this.materials.set(
        color,
        new THREE.MeshStandardMaterial({ color, roughness: 0.75 }),
      );
    return this.materials.get(color);
  }
  box(parent, w, h, d, x, y, z, color) {
    const o = new THREE.Mesh(
      new THREE.BoxGeometry(w, h, d),
      this.material(color),
    );
    o.position.set(x, y, z);
    parent.add(o);
    return o;
  }
  sign(parent, text, x, y, z, width = 0.24) {
    const c = document.createElement("canvas");
    c.width = 768;
    c.height = 160;
    const ctx = c.getContext("2d");
    ctx.fillStyle = "#244b43";
    ctx.fillRect(0, 0, 768, 160);
    ctx.fillStyle = "#fff9e8";
    ctx.font = "bold 52px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(text, 384, 99);
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    const m = new THREE.Mesh(
      new THREE.PlaneGeometry(width, (width * 160) / 768),
      new THREE.MeshBasicMaterial({ map: t, side: THREE.DoubleSide }),
    );
    m.position.set(x, y, z);
    parent.add(m);
  }
  building(parent, x, z, name, color) {
    const g = new THREE.Group();
    g.position.set(x, 0, z);
    parent.add(g);
    this.box(g, 0.13, 0.09, 0.1, 0, 0.045, 0, "#ece2c9");
    this.box(g, 0.15, 0.014, 0.12, 0, 0.097, 0, color);
    this.box(g, 0.1, 0.032, 0.004, 0, 0.046, 0.052, "#6d9694");
    this.box(g, 0.028, 0.057, 0.007, 0, 0.029, 0.055, "#304f48");
    this.box(g, 0.15, 0.008, 0.05, 0, 0.068, 0.065, color);
    this.sign(g, name, 0, 0.09, 0.078, 0.145);
    return g;
  }
  buildMarket() {
    const site = this.sites[0],
      g = site.group;
    g.userData.site = "market";
    this.pickables.push(g);
    this.box(g, 0.7, 0.012, 0.42, 0, -0.006, 0, "#d4cbb7");
    ["식음 · QR 인증", "체험 10% 할인", "관광주민증 안내"].forEach((s, i) =>
      this.building(
        g,
        (i - 1) * 0.19,
        -0.09,
        s,
        i === 1 ? "#bf8156" : "#426e62",
      ),
    );
    this.expandedMarket = new THREE.Group();
    g.add(this.expandedMarket);
    for (let i = 0; i < 3; i++)
      this.building(
        this.expandedMarket,
        (i - 1) * 0.19,
        0.13,
        "참여 확대",
        "#a47651",
      );
  }
  buildPopup() {
    const site = this.sites[1],
      g = site.group;
    g.userData.site = "popup";
    this.pickables.push(g);
    this.box(g, 0.84, 0.014, 0.6, 0, -0.008, 0, "#d3c7af");
    for (let i = 0; i < 8; i++) {
      const x = ((i % 4) - 1.5) * 0.185,
        z = i < 4 ? -0.21 : 0.21;
      const stall = new THREE.Group();
      stall.position.set(x, 0, z);
      if (i >= 4) stall.rotation.y = Math.PI;
      g.add(stall);
      this.box(stall, 0.14, 0.065, 0.1, 0, 0.033, 0, "#f2e6ce");
      this.box(
        stall,
        0.155,
        0.017,
        0.13,
        0,
        0.078,
        0,
        i % 2 ? "#c18458" : "#477466",
      );
      this.box(stall, 0.125, 0.025, 0.036, 0, 0.035, 0.056, "#b48d66");
      this.box(stall, 0.12, 0.027, 0.006, 0, 0.061, 0.054, "#304f48");
      for (let j = 0; j < 3; j++)
        this.box(
          stall,
          0.018,
          0.012,
          0.016,
          (j - 1) * 0.03,
          0.055,
          0.07,
          ["#d68f56", "#e2bc74", "#6e9564"][j],
        );
      this.sign(
        stall,
        ["로컬 푸드", "안동 공예", "야간 체험", "관광 안내"][i % 4],
        0,
        0.093,
        0.071,
        0.14,
      );
    }
    for (const x of [-0.39, 0.39]) {
      this.box(g, 0.009, 0.18, 0.009, x, 0.09, 0, "#78694e");
      const lamp = new THREE.Mesh(
        new THREE.SphereGeometry(0.021, 8, 6),
        new THREE.MeshBasicMaterial({ color: "#ffe8a6" }),
      );
      lamp.position.set(x, 0.185, 0);
      g.add(lamp);
    }
    for (let i = 0; i < 3; i++) {
      this.box(g, 0.07, 0.007, 0.045, (i - 1) * 0.17, 0.04, 0, "#aa835c");
      this.box(g, 0.01, 0.04, 0.01, (i - 1) * 0.17, 0.02, 0, "#60513c");
    }
  }
  buildTransport() {
    const a = this.atlas;
    const points = this.data.route.map((c) => a.point(c, 0.032));
    this.path = new THREE.CurvePath();
    for (let i = 1; i < points.length; i++)
      this.path.add(new THREE.LineCurve3(points[i - 1], points[i]));
    const line = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(points),
      new THREE.LineBasicMaterial({ color: "#c08b53" }),
    );
    this.group.add(line);
    this.routeLine = line;
    for (let i = 0; i < 2; i++) {
      const g = new THREE.Group();
      g.userData.site = "transport";
      g.scale.set(0.12, 0.35, 0.18);
      this.pickables.push(g);
      this.group.add(g);
      this.box(g, 0.055, 0.034, 0.13, 0, 0.03, 0, i ? "#bc8956" : "#3d756b");
      this.box(g, 0.05, 0.025, 0.083, 0, 0.06, 0, "#f4e6c7");
      this.box(g, 0.052, 0.019, 0.055, 0, 0.061, 0, "#527b86");
      for (const x of [-0.028, 0.028])
        for (let j = 0; j < 4; j++)
          this.box(
            g,
            0.003,
            0.017,
            0.02,
            x,
            0.043,
            (j - 1.5) * 0.028,
            "#9cc0c3",
          );
      for (const x of [-0.018, 0.018])
        this.box(g, 0.01, 0.008, 0.004, x, 0.024, 0.068, "#ffe7ab");
      this.box(g, 0.043, 0.018, 0.004, 0, 0.036, 0.068, "#b3d2cd");
      for (const x of [-0.028, 0.028])
        for (const z of [-0.042, 0.042]) {
          const w = new THREE.Mesh(
            new THREE.CylinderGeometry(0.014, 0.014, 0.01, 10),
            this.material("#303b39"),
          );
          w.rotation.z = Math.PI / 2;
          w.position.set(x, 0.014, z);
          g.add(w);
        }
      this.sign(g, "이어드림", 0, 0.09, 0, 0.12);
      this.vehicles.push(g);
    }
  }
  buildPeople() {
    for (let i = 0; i < 56; i++) {
      const g = new THREE.Group(),
        site = this.sites[i % 2];
      site.group.add(g);
      const body = new THREE.Mesh(
        new THREE.CylinderGeometry(0.008, 0.01, 0.026, 7),
        this.material(["#c37c51", "#355e56", "#7c8eae", "#cfb576"][i % 4]),
      );
      body.position.y = 0.032;
      g.add(body);
      const head = new THREE.Mesh(
        new THREE.SphereGeometry(0.008, 8, 6),
        this.material("#d7b090"),
      );
      head.position.y = 0.055;
      g.add(head);
      const legs = [];
      for (const x of [-0.005, 0.005])
        legs.push(this.box(g, 0.006, 0.02, 0.006, x, 0.01, 0, "#414b49"));
      this.people.push({ g, legs, site: i % 2, seed: i * 0.731 });
    }
  }
  configure({ visible, expanded, minutes }) {
    this.atlas.controls.minDistance = 0.25;
    this.group.visible = visible;
    if (!visible) this.follow = false;
    this.expanded = expanded;
    this.active = minutes >= 1110 && minutes <= 1260;
    this.expandedMarket.visible = expanded;
    this.people.forEach(
      (p, i) => (p.g.visible = this.active && (expanded || i < 18)),
    );
    this.vehicles.forEach(
      (v, i) => (v.visible = this.active && (expanded || i === 0)),
    );
    this.atlas.container.dataset.solution = visible
      ? expanded
        ? "expanded"
        : "basic"
      : "off";
  }
  update(delta) {
    if (!this.group.visible) return;
    if (this.running && this.active && !this.atlas.reduced) this.time += delta;
    this.vehicles.forEach((v, i) => {
      const t = (this.time / 420 + i * 0.5) % 1;
      const u = t < 0.5 ? t * 2 : 2 - t * 2;
      v.position.copy(
        this.path.getPointAt(Math.min(0.999, Math.max(0.001, u))),
      );
      v.position.y =
        this.atlas.elevation(
          this.atlas.project.toGeo(v.position.x, v.position.z),
        ) + 0.0017;
      const tangent = this.path.getTangentAt(
        Math.min(0.999, Math.max(0.001, u)),
      );
      v.rotation.y = Math.atan2(tangent.x, tangent.z) + (t < 0.5 ? 0 : Math.PI);
    });
    if (this.follow && this.active) {
      const target = this.vehicles[0].position;
      this.atlas.flight = null;
      this.atlas.controls.target.copy(target);
      this.atlas.camera.position
        .copy(target)
        .add(new THREE.Vector3(0.02, 0.55, 0.02));
    }
    this.people.forEach((p) => {
      const phase = this.time * 0.5 + p.seed;
      p.g.position.set(Math.sin(phase) * 0.3, 0, Math.cos(phase * 0.71) * 0.1);
      p.g.rotation.y = Math.cos(phase) > 0 ? Math.PI / 2 : -Math.PI / 2;
      p.legs.forEach(
        (leg, i) =>
          (leg.rotation.x =
            Math.sin(this.time * 7 + p.seed + i * Math.PI) * 0.42),
      );
    });
  }
  focus(id) {
    this.follow = false;
    if (id === "transport") this.atlas.fly([128.744, 36.572], 9);
    else
      this.atlas.fly(
        this.sites.find((s) => s.id === id).coordinates,
        id === "popup"
          ? this.atlas.mobile
            ? 0.85
            : 0.65
          : this.atlas.mobile
            ? 1.0
            : 0.65,
        false,
        null,
        this.sites.find((s) => s.id === id).group.position.y,
      );
  }
}
