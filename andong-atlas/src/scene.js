import { buildingGeometry } from "./building-geometry.js";
import { DistrictScene } from "./district-scene.js";
import { detailedFacade, CityDetail } from "./city-detail.js";
import { SolutionScene } from "./solution-scene.js";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { mergeGeometries } from "three/addons/utils/BufferGeometryUtils.js";
import {
  projection,
  sampleHeight,
  polygons,
  lines,
  geometryBounds,
  closingState,
  terrainSafeEye,
} from "./geo.js";

export class AtlasScene {
  constructor(container, data, places, onSelect, onInterrupt) {
    this.data = data;
    this.places = places;
    this.container = container;
    this.project = projection(data.terrain.bbox);
    this.reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    this.mobile = innerWidth <= 700;
    this.mode = "day";
    this.season = "summer";
    this.onSelect = onSelect;
    this.labelsVisible = true;
    this.selected = null;
    this.flat = false;
    this.flight = null;
    this.destroyed = false;
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color("#e2e6de");
    this.camera = new THREE.PerspectiveCamera(
      36,
      innerWidth / innerHeight,
      0.03,
      1000,
    );
    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false,
      powerPreference: "high-performance",
    });
    this.renderer.setPixelRatio(
      Math.min(devicePixelRatio, this.mobile ? 1.5 : 2),
    );
    this.renderer.setSize(innerWidth, innerHeight);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.shadowMap.autoUpdate = false;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.05;
    container.append(this.renderer.domElement);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.minDistance = 0.7;
    this.controls.maxDistance = 400;
    this.controls.maxPolarAngle = Math.PI * 0.465;
    this.controls.mouseButtons = {
      LEFT: THREE.MOUSE.ROTATE,
      MIDDLE: THREE.MOUSE.DOLLY,
      RIGHT: THREE.MOUSE.PAN,
    };
    this.controls.touches = {
      ONE: THREE.TOUCH.ROTATE,
      TWO: THREE.TOUCH.DOLLY_PAN,
    };
    this.controls.addEventListener("start", () => {
      this.flight = null;
      onInterrupt();
    });
    this.hemi = new THREE.HemisphereLight("#ffffff", "#a6ae96", 1.9);
    this.sun = new THREE.DirectionalLight("#fff5dc", 2.4);
    this.sun.position.set(-60, 100, 35);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(
      this.mobile ? 1024 : 2048,
      this.mobile ? 1024 : 2048,
    );
    this.sun.shadow.bias = -0.00015;
    this.sun.shadow.normalBias = 0.001;
    this.scene.add(this.hemi, this.sun, this.sun.target);
    this.shadowCenter = new THREE.Vector3(Infinity, Infinity, Infinity);
    this.world = new THREE.Group();
    this.scene.add(this.world);
    this.routeGroup = new THREE.Group();
    this.boundaryGroup = new THREE.Group();
    this.trailGroup = new THREE.Group();
    this.highlight = new THREE.Group();
    this.world.add(
      this.routeGroup,
      this.boundaryGroup,
      this.trailGroup,
      this.highlight,
    );
    const groundBefore = new Set(this.world.children);
    this.createTerrain();
    this.overviewGround = this.world.children.filter(
      (x) => !groundBefore.has(x),
    );
    this.createBuildings();
    this.createTrees();
    this.createBoundaries();
    this.createLandmarks();
    this.createWeather();
    this.createLabels();
    this.solution = new SolutionScene(this, data.solution, () => {});
    this.cityDetail = new CityDetail(this);
    this.district = new DistrictScene(this, data.district);
    this.home(true);
    this.resize = () => {
      this.mobile = innerWidth <= 700;
      this.camera.aspect = innerWidth / innerHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(innerWidth, innerHeight);
      this.renderer.setPixelRatio(
        Math.min(devicePixelRatio, this.mobile ? 1.5 : 2),
      );
    };
    window.addEventListener("resize", this.resize);
    this.clock = new THREE.Clock();
    this.frames = 0;
    this.fpsStart = performance.now();
    this.fps = 0;
    this.animate();
  }
  elevation(coordinates) {
    const terrain =
      this.district?.group.visible && this.inDetail(coordinates)
        ? this.district.renderTerrain || this.data.district.terrain
        : this.data.terrain;
    return sampleHeight(terrain, ...coordinates) * 0.008;
  }
  point(coordinates, lift = 0) {
    const [x, z] = this.project.toWorld(coordinates);
    return new THREE.Vector3(x, this.elevation(coordinates) + lift, z);
  }
  createTerrain() {
    const { bbox, cols, rows, heights } = this.data.terrain,
      { width, depth } = this.project;
    const canvas = document.createElement("canvas");
    canvas.width = 4096;
    canvas.height = 4096;
    const ctx = canvas.getContext("2d");
    const pixel = ([lon, lat]) => [
      ((lon - bbox[0]) / (bbox[2] - bbox[0])) * 4096,
      ((bbox[3] - lat) / (bbox[3] - bbox[1])) * 4096,
    ];
    const drawPolygon = (geometry, color) => {
      ctx.fillStyle = color;
      for (const polygon of polygons(geometry)) {
        ctx.beginPath();
        for (const ring of polygon) {
          ring.forEach((p, i) => {
            const [x, y] = pixel(p);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
          });
          ctx.closePath();
        }
        ctx.fill("evenodd");
      }
    };
    ctx.fillStyle = "#dce0c8";
    ctx.fillRect(0, 0, 4096, 4096);
    for (const f of this.data.map.landcover) {
      const c = f.properties.class;
      drawPolygon(
        f.geometry,
        c === "wood"
          ? "#b4c4a0"
          : c === "grass"
            ? "#c9d3ad"
            : c === "farmland"
              ? "#d6d9b8"
              : "#d2dbc0",
      );
    }
    for (const f of this.data.map.water) drawPolygon(f.geometry, "#669cba");
    const treePixels = ctx.getImageData(0, 0, 4096, 4096).data;
    this.treePixels = treePixels;
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    for (const f of this.data.map.transportation) {
      const c = f.properties.class;
      if (c === "path" || c === "track") continue;
      ctx.strokeStyle = c === "rail" ? "#9da99c" : "#faf7e7";
      ctx.lineWidth = ["motorway", "trunk"].includes(c)
        ? 2.5
        : ["primary", "secondary"].includes(c)
          ? 1.7
          : 0.8;
      for (const line of lines(f.geometry)) {
        ctx.beginPath();
        line.forEach((p, i) => {
          const [x, y] = pixel(p);
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        });
        ctx.stroke();
      }
    }
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.anisotropy = Math.min(
      8,
      this.renderer.capabilities.getMaxAnisotropy(),
    );
    const g = new THREE.PlaneGeometry(width, depth, cols - 1, rows - 1);
    g.rotateX(-Math.PI / 2);
    const p = g.attributes.position;
    for (let i = 0; i < p.count; i++) p.setY(i, heights[i] * 0.008);
    g.computeVertexNormals();
    this.terrainMaterial = new THREE.MeshStandardMaterial({
      map: texture,
      roughness: 0.92,
      metalness: 0,
    });
    this.terrainMesh = new THREE.Mesh(g, this.terrainMaterial);
    this.world.add(this.terrainMesh);
    const edges = [];
    for (let i = 0; i < cols; i++) edges.push(i);
    for (let j = 1; j < rows; j++) edges.push(j * cols + cols - 1);
    for (let i = cols - 2; i >= 0; i--) edges.push((rows - 1) * cols + i);
    for (let j = rows - 2; j > 0; j--) edges.push(j * cols);
    const positions = [],
      colors = [],
      earth = new THREE.Color("#b9c2a5");
    for (let i = 0; i < edges.length; i++) {
      const a = edges[i],
        b = edges[(i + 1) % edges.length];
      for (const idx of [a, b, b, a, b, a]) {
        const n = (positions.length / 3) % 6;
        positions.push(
          p.getX(idx),
          [2, 4, 5].includes(n) ? -1.8 : p.getY(idx),
          p.getZ(idx),
        );
        colors.push(earth.r, earth.g, earth.b);
      }
    }
    const skirt = new THREE.BufferGeometry();
    skirt.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(positions, 3),
    );
    skirt.computeVertexNormals();
    this.world.add(
      new THREE.Mesh(
        skirt,
        new THREE.MeshStandardMaterial({
          color: "#bbc5aa",
          roughness: 1,
          side: THREE.DoubleSide,
        }),
      ),
    );
    const base = new THREE.Mesh(
      new THREE.BoxGeometry(width + 0.2, 0.35, depth + 0.2),
      new THREE.MeshStandardMaterial({ color: "#c7cfb9", roughness: 1 }),
    );
    base.position.y = -1.98;
    this.world.add(base);
  }
  createBuildings() {
    const { geometry, count } = buildingGeometry(
      [...this.data.map.building, ...this.data.buildings.features],
      (c) => this.project.toWorld(c),
      (c) => this.elevation(c),
    );
    this.buildingCount = count;
    this.buildingMaterial = new THREE.MeshStandardMaterial({
      color: "#ffffff",
      vertexColors: true,
      roughness: 0.78,
      emissive: "#cbdff2",
      emissiveIntensity: 0,
      side: THREE.DoubleSide,
    });
    detailedFacade(this.buildingMaterial);
    this.buildingMesh = new THREE.Mesh(geometry, this.buildingMaterial);
    this.world.add(this.buildingMesh);
  }
  createTrees() {
    let seed = 719;
    const rand = () => {
      seed = (seed * 1664525 + 1013904223) >>> 0;
      return seed / 4294967296;
    };
    const count = this.mobile ? 40000 : 90000,
      positions = [];
    const { width, depth } = this.project;
    for (let i = 0; i < count * 4 && positions.length < count; i++) {
      const u = rand(),
        v = rand(),
        pi = (Math.floor(v * 4095) * 4096 + Math.floor(u * 4095)) * 4;
      const r = this.treePixels[pi],
        g = this.treePixels[pi + 1],
        b = this.treePixels[pi + 2];
      if (g <= r || b > r || r > 200) continue;
      const x = (u - 0.5) * width,
        z = (v - 0.5) * depth,
        c = this.project.toGeo(x, z);
      positions.push({
        x,
        z,
        y: this.elevation(c),
        size: 0.035 + rand() * 0.04,
        tint: rand(),
      });
    }
    this.treeMaterial = new THREE.MeshStandardMaterial({
      color: "#75916c",
      roughness: 1,
    });
    this.trees = new THREE.InstancedMesh(
      new THREE.IcosahedronGeometry(1, 0),
      this.treeMaterial,
      positions.length,
    );
    this.trunks = new THREE.InstancedMesh(
      new THREE.CylinderGeometry(0.12, 0.17, 1.6, 4),
      new THREE.MeshStandardMaterial({ color: "#8e8c7b" }),
      positions.length,
    );
    const dummy = new THREE.Object3D(),
      color = new THREE.Color();
    positions.forEach((p, i) => {
      dummy.position.set(p.x, p.y + p.size * 0.8, p.z);
      dummy.scale.setScalar(p.size);
      dummy.rotation.y = p.tint * Math.PI;
      dummy.updateMatrix();
      this.trunks.setMatrixAt(i, dummy.matrix);
      dummy.position.y = p.y + p.size * 1.8;
      dummy.scale.set(p.size, p.size * 1.2, p.size);
      dummy.updateMatrix();
      this.trees.setMatrixAt(i, dummy.matrix);
      color.setHSL(0.27 + p.tint * 0.07, 0.36, 0.23 + p.tint * 0.16);
      this.trees.setColorAt(i, color);
    });
    this.trees.instanceMatrix.needsUpdate = true;
    this.world.add(this.trunks, this.trees);
    this.treePositions = positions;
    this.treePixels = null;
  }
  lineObject(coordinates, color, width = 0.06, lift = 0.1, dashed = false) {
    const points = [];
    for (let i = 0; i < coordinates.length - 1; i++) {
      const a = this.point(coordinates[i], lift),
        b = this.point(coordinates[i + 1], lift),
        segments = Math.max(1, Math.ceil(a.distanceTo(b) / 0.15));
      for (let j = 0; j < segments; j++) {
        const t = j / segments,
          c = [
            coordinates[i][0] * (1 - t) + coordinates[i + 1][0] * t,
            coordinates[i][1] * (1 - t) + coordinates[i + 1][1] * t,
          ];
        points.push(this.point(c, lift));
      }
    }
    points.push(this.point(coordinates.at(-1), lift));
    if (dashed) {
      const l = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(points),
        new THREE.LineDashedMaterial({
          color,
          dashSize: 0.18,
          gapSize: 0.1,
          depthTest: false,
        }),
      );
      l.computeLineDistances();
      l.renderOrder = 5;
      return l;
    }
    if (points.length < 2) return new THREE.Group();
    const curve = new THREE.CatmullRomCurve3(points);
    return new THREE.Mesh(
      new THREE.TubeGeometry(
        curve,
        Math.min(1800, points.length),
        width,
        5,
        false,
      ),
      new THREE.MeshBasicMaterial({ color }),
    );
  }
  createBoundaries() {
    for (const f of this.data.boundaries.features) {
      const group = new THREE.Group();
      for (const p of polygons(f.geometry))
        for (const ring of p) {
          const points = ring.map((c) => this.point(c, 0.08));
          group.add(
            new THREE.Line(
              new THREE.BufferGeometry().setFromPoints(points),
              new THREE.LineBasicMaterial({
                color: "#829b76",
                transparent: true,
                opacity: 0.7,
                depthTest: false,
              }),
            ),
          );
        }
      group.userData.code = f.properties.adm_cd2;
      this.boundaryGroup.add(group);
    }
    this.boundaryGroup.visible = false;
  }
  createLandmarks() {
    this.landmarkGroup = new THREE.Group();
    this.world.add(this.landmarkGroup);
    this.landmarkMaterials = [];
    for (const place of this.places) {
      const group = new THREE.Group();
      group.userData.place = place;
      group.position.copy(this.point(place.coordinates, 0.05));
      if (place.kind === "bridge") {
        const deck = new THREE.Mesh(
          new THREE.BoxGeometry(0.78, 0.016, 0.026),
          new THREE.MeshStandardMaterial({
            color: "#ac8055",
            emissive: "#facf81",
            emissiveIntensity: 0,
          }),
        );
        group.add(deck);
        this.landmarkMaterials.push(deck.material);
        this.positionBridge(group);
        for (const x of [-0.35, -0.2, 0, 0.2, 0.35]) {
          const support = new THREE.Mesh(
            new THREE.BoxGeometry(0.012, 0.2, 0.02),
            new THREE.MeshStandardMaterial({ color: "#887757" }),
          );
          support.position.set(x, -0.08, 0);
          group.add(support);
        }
        for (const z of [-0.018, 0.018]) {
          const rail = new THREE.Mesh(
            new THREE.BoxGeometry(0.78, 0.004, 0.003),
            new THREE.MeshStandardMaterial({ color: "#a07a4f" }),
          );
          rail.position.set(0, 0.028, z);
          group.add(rail);
          for (let i = 0; i < 17; i++) {
            const post = new THREE.Mesh(
              new THREE.BoxGeometry(0.003, 0.025, 0.003),
              rail.material,
            );
            post.position.set(-0.38 + i * 0.0475, 0.018, z);
            group.add(post);
          }
        }
        this.pavilion(group, 0, 0.014, 0, 0.055);
      } else if (place.kind === "heritage") {
        this.pavilion(group, 0, 0, 0, 0.15);
        this.pavilion(group, 0.2, 0, 0.08, 0.08);
        this.pavilion(group, -0.18, 0, 0.04, 0.08);
      } else if (place.kind === "station") {
        const body = new THREE.Mesh(
          new THREE.BoxGeometry(0.35, 0.09, 0.13),
          new THREE.MeshStandardMaterial({ color: "#dedfd4" }),
        );
        body.position.y = 0.045;
        group.add(body);
        const roof = new THREE.Mesh(
          new THREE.BoxGeometry(0.39, 0.02, 0.16),
          new THREE.MeshStandardMaterial({ color: "#9ba8aa" }),
        );
        roof.position.y = 0.1;
        group.add(roof);
      }
      this.landmarkGroup.add(group);
    }
  }
  positionBridge(group) {
    const feature = this.data.district.roads.find(
      (f) => f.properties["bridge:name"] === "월영교",
    );
    if (!feature) return;
    const coordinates = feature.geometry.coordinates,
      a = this.project.toWorld(coordinates[0]),
      b = this.project.toWorld(coordinates.at(-1)),
      dx = b[0] - a[0],
      dz = b[1] - a[1];
    group.position.set(
      (a[0] + b[0]) / 2,
      Math.max(
        this.elevation(coordinates[0]),
        this.elevation(coordinates.at(-1)),
      ) + 0.035,
      (a[1] + b[1]) / 2,
    );
    group.rotation.y = -Math.atan2(dz, dx);
    group.scale.x = Math.hypot(dx, dz) / 0.78;
  }
  pavilion(group, x, y, z, size) {
    const body = new THREE.Mesh(
      new THREE.BoxGeometry(size, size * 0.55, size * 0.72),
      new THREE.MeshStandardMaterial({ color: "#d1b691" }),
    );
    body.position.set(x, y + size * 0.27, z);
    group.add(body);
    const roof = new THREE.Mesh(
      new THREE.ConeGeometry(size * 0.9, size * 0.45, 4),
      new THREE.MeshStandardMaterial({ color: "#596c69" }),
    );
    roof.rotation.y = Math.PI / 4;
    roof.position.set(x, y + size * 0.72, z);
    roof.scale.z = 0.78;
    group.add(roof);
  }
  createWeather() {
    const count = this.mobile ? 700 : 1400,
      p = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      p[i * 3] = (Math.random() - 0.5) * this.project.width;
      p[i * 3 + 1] = Math.random() * 35 + 5;
      p[i * 3 + 2] = (Math.random() - 0.5) * this.project.depth;
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(p, 3));
    this.particles = new THREE.Points(
      g,
      new THREE.PointsMaterial({
        color: "#d8e5e6",
        size: 0.16,
        transparent: true,
        opacity: 0.65,
        depthWrite: false,
      }),
    );
    this.particles.visible = false;
    this.scene.add(this.particles);
  }
  createLabels() {
    this.labelElements = this.places.map((p) => {
      const button = document.createElement("button");
      button.className = "map-label";
      button.textContent = p.name;
      button.setAttribute("aria-label", `${p.name} 위치로 이동`);
      const pin = document.createElement("span");
      pin.className = "pin";
      button.append(pin);
      button.addEventListener("click", () => this.onSelect(p));
      document.querySelector("#labels").append(button);
      return { p, button, position: this.point(p.coordinates, 0.3) };
    });
  }
  clearGroup(group) {
    for (const obj of [...group.children]) {
      obj.traverse((child) => {
        child.geometry?.dispose();
        if (child.material) {
          const mats = Array.isArray(child.material)
            ? child.material
            : [child.material];
          mats.forEach((m) => m.dispose());
        }
      });
      group.remove(obj);
    }
  }
  setDistrict(feature) {
    this.clearGroup(this.highlight);
    if (!feature) return;
    for (const p of polygons(feature.geometry))
      for (const ring of p)
        this.highlight.add(this.lineObject(ring, "#376c62", 0.04, 0.13));
    const b = geometryBounds(feature.geometry),
      c = [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2];
    const a = this.project.toWorld([b[0], b[1]]),
      d = this.project.toWorld([b[2], b[3]]);
    this.fly(c, Math.max(8, Math.hypot(a[0] - d[0], a[1] - d[1]) * 1.4));
  }
  setRelay(visible, proposal) {
    this.clearGroup(this.routeGroup);
    if (!visible) return;
    const market = this.places.find((p) => p.id === "market"),
      bridge = this.places.find((p) => p.id === "woryeong");
    if (!market || !bridge) return;
    const c = [market.coordinates, bridge.coordinates];
    this.routeGroup.add(
      this.lineObject(c, proposal ? "#ad7450" : "#376c62", 0.04, 0.18, true),
    );
    for (const p of c) {
      const ring = new THREE.Mesh(
        new THREE.RingGeometry(0.13, 0.18, 32),
        new THREE.MeshBasicMaterial({
          color: proposal ? "#ad7450" : "#376c62",
          side: THREE.DoubleSide,
        }),
      );
      ring.rotation.x = -Math.PI / 2;
      ring.position.copy(this.point(p, 0.2));
      this.routeGroup.add(ring);
    }
  }
  setFacilities(features, minutes, visible) {
    if (!this.facilityGroup) {
      this.facilityGroup = new THREE.Group();
      this.world.add(this.facilityGroup);
    }
    this.clearGroup(this.facilityGroup);
    this.facilityGroup.visible = visible;
    for (const f of features) {
      const state = closingState(f.properties, minutes),
        color =
          state === "조사 기준 종료" || state === "폐업"
            ? "#8f9993"
            : "#376c62";
      const marker = new THREE.Mesh(
        new THREE.CylinderGeometry(0.035, 0.035, 0.12, 10),
        new THREE.MeshBasicMaterial({ color }),
      );
      marker.position.copy(this.point(f.geometry.coordinates, 0.1));
      this.facilityGroup.add(marker);
    }
  }
  setTrail(feature, visible = true, endpoints = true) {
    this.clearGroup(this.trailGroup);
    if (!feature || !visible) return;
    for (const line of lines(feature.geometry)) {
      this.trailGroup.add(this.lineObject(line, "#a76d45", 0.035, 0.12));
      for (const [i, c] of [line[0], line.at(-1)].entries()) {
        const m = new THREE.Mesh(
          new THREE.SphereGeometry(0.08, 10, 8),
          new THREE.MeshBasicMaterial({ color: i ? "#a76d45" : "#376c62" }),
        );
        m.userData.endpoint = true;
        m.visible = endpoints;
        m.position.copy(this.point(c, 0.2));
        this.trailGroup.add(m);
      }
    }
  }
  fitFeature(feature) {
    const b = geometryBounds(feature.geometry),
      a = this.project.toWorld([b[0], b[1]]),
      d = this.project.toWorld([b[2], b[3]]);
    this.fly(
      [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2],
      Math.max(3, Math.hypot(a[0] - d[0], a[1] - d[1]) * 2.2),
    );
  }
  setMode(mode) {
    this.mode = mode;
    const night = mode === "night",
      sunset = mode === "sunset",
      rain = mode === "rain",
      snow = mode === "snow";
    this.scene.background.set(
      night
        ? "#0c151c"
        : sunset
          ? "#e6d3c3"
          : rain
            ? "#bac8c7"
            : snow
              ? "#e4e9e8"
              : "#e2e6de",
    );
    this.hemi.intensity = night ? 0.7 : rain ? 1.7 : 1.9;
    this.hemi.color.set(night ? "#91b1e2" : "#ffffff");
    this.hemi.groundColor.set(night ? "#344c72" : "#a6ae96");
    this.sun.intensity = night ? 0.42 : sunset ? 2.3 : rain ? 1.4 : 2.4;
    this.sun.color.set(sunset ? "#ffcf9b" : night ? "#a6bad2" : "#fff5dc");
    this.terrainMaterial.color.set(
      night ? "#789098" : snow ? "#f2f5ee" : "#ffffff",
    );
    this.buildingMaterial.emissiveIntensity = night ? 0.32 : 0;
    this.landmarkMaterials.forEach(
      (m) => (m.emissiveIntensity = night ? 0.18 : 0),
    );
    this.particles.visible = rain || snow;
    this.particles.material.size = snow ? 0.23 : 0.11;
    this.particles.material.opacity = snow ? 0.8 : 0.55;
    document.body.classList.toggle("night", night);
  }
  setSeason(season) {
    this.season = season;
    const color = new THREE.Color(),
      dummy = new THREE.Object3D();
    this.treePositions.forEach((p, i) => {
      if (season === "spring")
        color.setHSL(0.9 + p.tint * 0.07, 0.28, 0.62 + p.tint * 0.15);
      else if (season === "autumn")
        color.setHSL(0.04 + p.tint * 0.11, 0.42, 0.32 + p.tint * 0.22);
      else if (season === "winter")
        color.setHSL(0.13, 0.1, 0.43 + p.tint * 0.17);
      else color.setHSL(0.27 + p.tint * 0.07, 0.36, 0.23 + p.tint * 0.16);
      this.trees.setColorAt(i, color);
      const winterScale = season === "winter" ? 0.36 : 1;
      dummy.position.set(p.x, p.y + p.size * 1.8, p.z);
      dummy.scale.set(
        p.size * winterScale,
        p.size * 1.2 * winterScale,
        p.size * winterScale,
      );
      dummy.rotation.y = p.tint * Math.PI;
      dummy.updateMatrix();
      this.trees.setMatrixAt(i, dummy.matrix);
    });
    this.trees.instanceColor.needsUpdate = true;
    this.trees.instanceMatrix.needsUpdate = true;
  }
  inDetail([x, y]) {
    const b = this.data.district.bbox;
    return x >= b[0] && x <= b[2] && y >= b[1] && y <= b[3];
  }
  setDetailed(enabled, area = "popup") {
    this.district.group.visible = enabled;
    this.renderer.shadowMap.enabled = enabled;
    this.renderer.shadowMap.needsUpdate = true;
    this.shadowCenter.set(Infinity, Infinity, Infinity);
    this.solution.positionSites();
    this.solution.routeLine.visible = !enabled;
    for (const object of [
      ...this.overviewGround,
      this.buildingMesh,
      this.trees,
      this.trunks,
    ])
      if (object) object.visible = !enabled;
    for (const landmark of this.landmarkGroup.children) {
      const place = landmark.userData.place;
      if (!place) continue;
      landmark.visible =
        !enabled ||
        (place.kind === "bridge" && this.inDetail(place.coordinates));
      if (place.kind === "bridge") this.positionBridge(landmark);
    }
    document.body.dataset.view = enabled ? "district" : "overview";
    document
      .querySelectorAll("[data-district-view]")
      .forEach((b) =>
        b.setAttribute(
          "aria-pressed",
          String(b.dataset.districtView === (enabled ? area : "overview")),
        ),
      );
    document.getElementById("district-note").hidden = !enabled;
  }
  home(immediate = false) {
    if (this.district) this.setDetailed(false);
    const c = this.project.toGeo(0, 0),
      dist = this.mobile ? 240 : 190;
    this.selected = null;
    this.fly(c, dist, immediate);
  }
  fly(
    coordinates,
    distance = 15,
    immediate = false,
    viewDirection = null,
    targetHeight = null,
  ) {
    if (this.solution) this.solution.follow = false;
    const target = this.point(coordinates, 0),
      direction = this.flat
        ? new THREE.Vector3(0, 1, 0.001)
        : (viewDirection || new THREE.Vector3(0.48, 0.75, 1)).normalize();
    if (targetHeight !== null) target.y = targetHeight;
    const position = target.clone().addScaledVector(direction, distance);
    if (immediate || this.reduced) {
      this.camera.position.copy(position);
      this.controls.target.copy(target);
      this.controls.update();
      this.flight = null;
    } else
      this.flight = {
        from: this.camera.position.clone(),
        to: position,
        fromTarget: this.controls.target.clone(),
        target,
        start: performance.now(),
        duration: 1100,
      };
  }
  select(place) {
    if (this.inDetail(place.coordinates))
      this.setDetailed(true, place.kind === "bridge" ? "popup" : "market");
    this.selected = place.id;
    this.fly(
      place.coordinates,
      this.inDetail(place.coordinates)
        ? place.kind === "bridge"
          ? 2
          : 2.7
        : place.kind === "heritage"
          ? 8
          : 7,
      false,
      place.kind === "bridge" ? new THREE.Vector3(-0.65, 1.2, 0.15) : null,
    );
  }
  setFlat(flat) {
    this.flat = flat;
    this.fly(
      this.project.toGeo(this.controls.target.x, this.controls.target.z),
      this.camera.position.distanceTo(this.controls.target),
    );
  }
  zoom(factor) {
    this.flight = null;
    const offset = this.camera.position
      .clone()
      .sub(this.controls.target)
      .multiplyScalar(factor);
    offset.clampLength(this.controls.minDistance, this.controls.maxDistance);
    this.camera.position.copy(this.controls.target).add(offset);
    this.controls.update();
  }
  north() {
    this.flight = null;
    const dist = this.camera.position.distanceTo(this.controls.target);
    this.camera.position
      .copy(this.controls.target)
      .add(
        new THREE.Vector3(
          0,
          this.flat ? dist : dist * 0.65,
          this.flat ? 0.001 : dist * 0.76,
        ),
      );
    this.controls.update();
  }
  updateLabels() {
    const occupied = [],
      max = this.mobile ? 4 : 8,
      w = innerWidth,
      h = innerHeight;
    let shown = 0;
    const ordered = [...this.labelElements].sort(
      (a, b) => (b.p.id === this.selected) - (a.p.id === this.selected),
    );
    for (const { p, button, position } of ordered) {
      position.copy(this.point(p.coordinates, 0.09));
      const v = position.clone().project(this.camera),
        x = (v.x * 0.5 + 0.5) * w,
        y = (-v.y * 0.5 + 0.5) * h;
      let visible =
        this.labelsVisible &&
        v.z < 1 &&
        x > 25 &&
        x < w - 25 &&
        y > 210 &&
        y < h - 175 &&
        shown < max;
      const bw = button.offsetWidth || 110,
        bh = 34;
      const rect = { x: x - bw / 2, y: y - 42, w: bw, h: bh };
      if (!this.mobile && x < 355 && y > 150) visible = false;
      if (!this.mobile && x > w - 310 && y > h - 300) visible = false;
      if (
        occupied.some(
          (r) =>
            Math.abs(r.x - rect.x) < Math.max(r.w, rect.w) + 6 &&
            Math.abs(r.y - rect.y) < 42,
        )
      )
        visible = false;
      button.hidden = !visible;
      if (visible) {
        button.style.transform = `translate(${Math.round(rect.x)}px,${Math.round(rect.y)}px)`;
        button.classList.toggle("selected", p.id === this.selected);
        occupied.push(rect);
        shown++;
      }
    }
  }
  animate() {
    if (this.destroyed) return;
    this.frame = requestAnimationFrame(() => this.animate());
    if (document.hidden) return;
    const now = performance.now(),
      delta = Math.min(this.clock.getDelta(), 0.05);
    if (this.flight) {
      const f = this.flight,
        t = Math.min(1, (now - f.start) / f.duration),
        e = t * t * (3 - 2 * t);
      this.camera.position.lerpVectors(f.from, f.to, e);
      this.controls.target.lerpVectors(f.fromTarget, f.target, e);
      if (t === 1) this.flight = null;
    }
    this.controls.update();
    if (this.particles.visible) {
      const span = this.camera.position.distanceTo(this.controls.target) * 1.4;
      this.particles.position.copy(this.controls.target);
      this.particles.scale.set(
        span / this.project.width,
        span / 35,
        span / this.project.depth,
      );
      this.particles.material.size =
        (this.mode === "snow" ? 0.0035 : 0.0018) * span;
    }
    if (this.particles.visible && !this.reduced) {
      const p = this.particles.geometry.attributes.position;
      for (let i = 0; i < p.count; i++) {
        let y = p.getY(i) - delta * (this.mode === "snow" ? 1.5 : 17);
        if (y < 0) y = 35;
        p.setY(i, y);
      }
      p.needsUpdate = true;
    }
    this.solution.update(delta);
    this.cityDetail.update(delta);
    this.district.update(delta);
    if (this.district.group.visible) {
      this.camera.position.y = terrainSafeEye(
        this.controls.target,
        this.camera.position,
        (x, z) => {
          const c = this.project.toGeo(x, z);
          return this.inDetail(c) ? this.elevation(c) : null;
        },
      );
    }
    if (this.district.group.visible) {
      const target = this.controls.target,
        span = Math.max(
          2,
          Math.min(12, this.camera.position.distanceTo(target)),
        );
      if (
        this.shadowCenter.distanceTo(target) > 0.08 ||
        Math.abs((this.shadowSpan || 0) - span) > 0.3
      ) {
        this.shadowCenter.copy(target);
        this.shadowSpan = span;
        this.sun.position
          .copy(target)
          .add(new THREE.Vector3(-span, span * 1.7, span * 0.7));
        this.sun.target.position.copy(target);
        Object.assign(this.sun.shadow.camera, {
          left: -span,
          right: span,
          top: span,
          bottom: -span,
          near: 0.01,
          far: span * 5,
        });
        this.sun.shadow.camera.updateProjectionMatrix();
        this.renderer.shadowMap.needsUpdate = true;
      }
    }
    this.renderer.render(this.scene, this.camera);
    this.updateLabels();
    this.frames++;
    if (now - this.fpsStart > 2000) {
      this.fps = Math.round((this.frames * 1000) / (now - this.fpsStart));
      this.frames = 0;
      this.fpsStart = now;
      this.container.dataset.fps = String(this.fps);
    }
    this.container.dataset.rendered = "true";
  }
}
