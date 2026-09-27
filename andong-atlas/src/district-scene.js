import { terrainGrid, drapePolygon } from "./terrain-ribbon.js";
import { bridgeSurfaces } from "./bridge-surface.js";
import { ParkScene } from "./parks.js";
import {
  distributedIndices,
  urbanWeight,
  clearRuns,
  walkingProgress,
} from "./activity.js";
import { footprintMask, corridorMask } from "./footprints.js";
import {
  buildingAppearance,
  paintGeometry,
  terrainSkirt,
} from "./building-style.js";
import {
  roadNetwork,
  roadStyle,
  vehicleState,
  advanceTraffic,
  vehiclePosition,
} from "./traffic.js";
import { Vegetation } from "./vegetation.js";
import * as THREE from "three";
import { mergeGeometries } from "three/addons/utils/BufferGeometryUtils.js";
import { polygons, sampleHeight } from "./geo.js";
import { detailedFacade } from "./city-detail.js";
export class DistrictScene {
  constructor(atlas, data) {
    this.a = atlas;
    this.data = data;
    this.group = new THREE.Group();
    atlas.world.add(this.group);
    this.group.visible = false;
    this.time = 0;
    this.running = true;
    this.materials = [];
    this.paths = [];
    this.walks = [];
    this.buildGround();
    this.buildWater();
    this.bridgeSurfaces = bridgeSurfaces(data.roads, (c) => this.point(c).y);
    this.waterBlocked = footprintMask(data.water || [], (c) =>
      this.a.project.toWorld(c),
    );
    this.buildingBlocked = footprintMask(this.data.buildings, (c) =>
      this.a.project.toWorld(c),
    );
    this.roadBlocked = corridorMask(
      data.roads,
      (c) => this.a.project.toWorld(c),
      (f) => roadStyle(f.properties).width + 0.008,
    );
    this.buildForest();
    this.buildBuildings();
    this.buildStreets();
    this.parks = new ParkScene(this);
    this.buildLife();
    this.buildStreetAssets();
  }
  point(c, lift = 0) {
    const [x, z] = this.a.project.toWorld(c);
    return new THREE.Vector3(
      x,
      sampleHeight(this.renderTerrain || this.data.terrain, ...c) * 0.008 +
        lift,
      z,
    );
  }
  buildGround() {
    const t = this.data.terrain,
      b = t.bbox,
      a = this.a.project.toWorld([b[0], b[3]]),
      v = this.a.project.toWorld([b[2], b[1]]),
      geo = new THREE.PlaneGeometry(
        v[0] - a[0],
        v[1] - a[1],
        t.cols - 1,
        t.rows - 1,
      );
    geo.rotateX(-Math.PI / 2);
    geo.translate((a[0] + v[0]) / 2, 0, (a[1] + v[1]) / 2);
    for (let i = 0; i < t.heights.length; i++)
      geo.attributes.position.setY(i, t.heights[i] * 0.008);
    geo.computeVertexNormals();
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = 2048;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#e0e3cc";
    ctx.fillRect(0, 0, 2048, 2048);
    const draw = (f, color) => {
      ctx.fillStyle = color;
      for (const p of polygons(f.geometry)) {
        ctx.beginPath();
        for (const r of p) {
          r.forEach((c, i) => {
            const x = ((c[0] - b[0]) / (b[2] - b[0])) * 2048,
              y = ((b[3] - c[1]) / (b[3] - b[1])) * 2048;
            i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
          });
          ctx.closePath();
        }
        ctx.fill("evenodd");
      }
    };
    for (const f of this.a.data.map.landcover)
      draw(f, f.properties.class === "wood" ? "#bbc8a1" : "#c5d0ac");
    for (const f of this.data.parks || [])
      draw(
        f,
        f.properties.leisure === "pitch"
          ? f.properties.sport === "tennis" ||
            f.properties.sport === "basketball"
            ? "#b48165"
            : "#83a671"
          : "#94b77d",
      );
    for (const f of this.a.data.map.water) draw(f, "#5e9db4");
    this.groundPixels = ctx.getImageData(0, 0, 2048, 2048).data;
    // Flatten connected mapped water surfaces for the diorama, retaining the raw DEM.
    this.renderTerrain = { ...t, heights: [...t.heights] };
    const wet = new Uint8Array(t.heights.length),
      seen = new Uint8Array(t.heights.length);
    for (let j = 0; j < t.rows; j++)
      for (let i = 0; i < t.cols; i++) {
        const pixel =
          (Math.round((j / (t.rows - 1)) * 2047) * 2048 +
            Math.round((i / (t.cols - 1)) * 2047)) *
          4;
        wet[j * t.cols + i] =
          this.groundPixels[pixel + 2] > this.groundPixels[pixel + 1] + 10 &&
          this.groundPixels[pixel + 2] > this.groundPixels[pixel] + 20
            ? 1
            : 0;
      }
    for (let k = 0; k < wet.length; k++)
      if (wet[k] && !seen[k]) {
        const queue = [k];
        seen[k] = 1;
        for (let q = 0; q < queue.length; q++) {
          const n = queue[q],
            x = n % t.cols,
            y = Math.floor(n / t.cols);
          for (const v of [
            x > 0 ? n - 1 : -1,
            x < t.cols - 1 ? n + 1 : -1,
            y > 0 ? n - t.cols : -1,
            y < t.rows - 1 ? n + t.cols : -1,
          ])
            if (v >= 0 && wet[v] && !seen[v]) {
              seen[v] = 1;
              queue.push(v);
            }
        }
        if (queue.length < 6) continue;
        const heights = queue.map((i) => t.heights[i]).sort((a, b) => a - b),
          level = heights[Math.floor(heights.length * 0.25)];
        for (const index of queue) this.renderTerrain.heights[index] = level;
      }
    for (let i = 0; i < t.heights.length; i++)
      geo.attributes.position.setY(i, this.renderTerrain.heights[i] * 0.008);
    geo.computeVertexNormals();
    for (const f of this.a.data.map.water) draw(f, "#e0e3cc");
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 8;
    this.ground = new THREE.MeshStandardMaterial({ map: tex, roughness: 1 });
    this.waterUniform = { value: 0 };
    this.ground.onBeforeCompile = (shader) => {
      shader.uniforms.flowTime = this.waterUniform;
      shader.fragmentShader = shader.fragmentShader.replace(
        "#include <common>",
        "#include <common>\nuniform float flowTime;",
      );
      shader.fragmentShader = shader.fragmentShader.replace(
        "#include <map_fragment>",
        `#include <map_fragment>
        float water=step(diffuseColor.r+.035,diffuseColor.b)*step(diffuseColor.g+.025,diffuseColor.b);
        float wave=pow(max(0.,sin(vMapUv.y*1400.+sin(vMapUv.x*250.)*2.+flowTime*.4)),18.);
        diffuseColor.rgb=mix(diffuseColor.rgb,diffuseColor.rgb+vec3(.07)*wave,water*.08);
      `,
      );
    };
    const mesh = new THREE.Mesh(geo, this.ground);
    mesh.receiveShadow = true;
    this.group.add(mesh);
    this.buildTerrainEdge(t);
  }
  buildWater() {
    const parts = [];
    for (const f of this.data.water || []) {
      const poly = f.geometry.coordinates,
        shape = new THREE.Shape(
          poly[0].map((c) => {
            const [x, z] = this.a.project.toWorld(c);
            return new THREE.Vector2(x, -z);
          }),
        );
      for (const ring of poly.slice(1))
        shape.holes.push(
          new THREE.Path(
            ring.map((c) => {
              const [x, z] = this.a.project.toWorld(c);
              return new THREE.Vector2(x, -z);
            }),
          ),
        );
      const level = this.point(f.properties.center).y + 0.005,
        g = new THREE.ShapeGeometry(shape);
      g.rotateX(-Math.PI / 2);
      g.translate(0, level, 0);
      parts.push(g);
    }
    this.waterMaterial = new THREE.MeshStandardMaterial({
      color: "#66a3b5",
      roughness: 0.65,
      metalness: 0.03,
    });
    if (parts.length) {
      const g = mergeGeometries(parts);
      const mesh = new THREE.Mesh(g, this.waterMaterial);
      mesh.receiveShadow = true;
      this.group.add(mesh);
      parts.forEach((p) => p.dispose());
    }
  }
  buildTerrainEdge(t) {
    const positions = [],
      edge = [];
    for (let x = 0; x < t.cols; x++) edge.push(x);
    for (let y = 1; y < t.rows; y++) edge.push(y * t.cols + t.cols - 1);
    for (let x = t.cols - 2; x >= 0; x--) edge.push((t.rows - 1) * t.cols + x);
    for (let y = t.rows - 2; y > 0; y--) edge.push(y * t.cols);
    const point = (i) =>
      this.point([
        t.bbox[0] + ((i % t.cols) / (t.cols - 1)) * (t.bbox[2] - t.bbox[0]),
        t.bbox[3] -
          (Math.floor(i / t.cols) / (t.rows - 1)) * (t.bbox[3] - t.bbox[1]),
      ]);
    for (let i = 0; i < edge.length; i++) {
      const a = point(edge[i]),
        b = point(edge[(i + 1) % edge.length]);
      for (const p of [
        [a.x, a.y, a.z],
        [a.x, 0.15, a.z],
        [b.x, b.y, b.z],
        [b.x, b.y, b.z],
        [a.x, 0.15, a.z],
        [b.x, 0.15, b.z],
      ])
        positions.push(...p);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    g.computeVertexNormals();
    this.group.add(
      new THREE.Mesh(
        g,
        new THREE.MeshStandardMaterial({
          color: "#b0bc9e",
          side: THREE.DoubleSide,
        }),
      ),
    );
  }
  buildForest() {
    const points = [],
      b = this.data.bbox;
    let seed = 8127;
    const rand = () => {
      seed = (seed * 1664525 + 1013904223) >>> 0;
      return seed / 4294967296;
    };
    // Leave space around the explanatory proposal models; these are decorative trees.
    const clearings = this.a.data.solution.sites.map((site) => ({
      point: this.point(site.coordinates),
      halfWidth: site.id === "popup" ? 0.11 : 0.21,
      halfDepth: site.id === "popup" ? 0.1 : 0.16,
    }));
    const count = this.a.mobile ? 7000 : 18000;
    for (let i = 0; i < count * 14 && points.length < count; i++) {
      const u = rand(),
        v = rand(),
        pixel = (Math.floor(v * 2047) * 2048 + Math.floor(u * 2047)) * 4;
      if (this.groundPixels[pixel] !== 187) continue;
      const c = [b[0] + u * (b[2] - b[0]), b[3] - v * (b[3] - b[1])],
        p = this.point(c),
        size = 0.012 + rand() * 0.018;
      if (
        this.roadBlocked(p.x, p.z, size * 1.2) ||
        this.buildingBlocked(p.x, p.z, size * 1.2)
      )
        continue;
      if (
        clearings.some(
          ({ point, halfWidth, halfDepth }) =>
            Math.abs(p.x - point.x) < halfWidth &&
            Math.abs(p.z - point.z) < halfDepth,
        )
      )
        continue;
      points.push({
        x: p.x,
        y: p.y,
        z: p.z,
        size,
        tint: rand(),
      });
    }
    this.forest = new Vegetation(this.group, points);
    this.groundPixels = null;
  }
  buildBuildings() {
    const sets = [[]],
      foundations = [],
      roofs = [],
      fittings = [],
      trims = [];
    for (const [index, f] of this.data.buildings.entries()) {
      for (const poly of polygons(f.geometry)) {
        const ring = poly[0];
        if (ring.length < 4) continue;
        const shape = new THREE.Shape(
          ring.map((c) => {
            const p = this.point(c);
            return new THREE.Vector2(p.x, -p.z);
          }),
        );
        for (const hole of poly.slice(1))
          shape.holes.push(
            new THREE.Path(
              hole.map((c) => {
                const p = this.point(c);
                return new THREE.Vector2(p.x, -p.z);
              }),
            ),
          );
        const parsed = parseFloat(f.properties.height),
          levels = parseFloat(f.properties["building:levels"]),
          h = Math.max(3, Math.min(90, parsed || levels * 3 || 6)) * 0.008;
        const y = Math.max(...ring.map((c) => this.point(c).y)) + 0.004;
        const g = new THREE.ExtrudeGeometry(shape, {
          depth: h,
          bevelEnabled: false,
        });
        g.rotateX(-Math.PI / 2);
        g.translate(0, y, 0);
        const appearance = buildingAppearance(f);
        paintGeometry(g, appearance.facade);
        sets[0].push(g);
        foundations.push(
          paintGeometry(
            terrainSkirt(poly, (c) => this.point(c), y),
            appearance.facade,
          ),
        );
        const roof = new THREE.ShapeGeometry(shape);
        roof.rotateX(-Math.PI / 2);
        roof.translate(0, y + h + 0.001, 0);
        roofs.push(paintGeometry(roof, appearance.roof));
        const pts = ring.map((c) => this.point(c)),
          xs = pts.map((p) => p.x),
          zs = pts.map((p) => p.z),
          cx = (Math.min(...xs) + Math.max(...xs)) / 2,
          cz = (Math.min(...zs) + Math.max(...zs)) / 2,
          w = Math.max(...xs) - Math.min(...xs),
          dep = Math.max(...zs) - Math.min(...zs);
        if (w > 0.025 && dep > 0.025) {
          // Generic rooftop equipment; not surveyed architecture.
          const shapePts = ring.map((c) => {
            const p = this.point(c);
            return [p.x, p.z];
          });
          let inside = false;
          for (
            let i = 0, j = shapePts.length - 1;
            i < shapePts.length;
            j = i++
          ) {
            const a = shapePts[i],
              b = shapePts[j];
            if (
              a[1] > cz !== b[1] > cz &&
              cx < ((b[0] - a[0]) * (cz - a[1])) / (b[1] - a[1]) + a[0]
            )
              inside = !inside;
          }
          if (inside) {
            const unit = new THREE.BoxGeometry(
              Math.min(0.018, w * 0.22),
              0.008,
              Math.min(0.02, dep * 0.24),
            );
            unit.translate(cx, y + h + 0.005, cz);
            fittings.push(unit);
          }
          for (let j = 1; j < pts.length; j++) {
            const p = pts[j - 1],
              q = pts[j],
              length = Math.hypot(q.x - p.x, q.z - p.z);
            const g = new THREE.BoxGeometry(0.0015, 0.003, length);
            g.rotateY(Math.atan2(q.x - p.x, q.z - p.z));
            g.translate((p.x + q.x) / 2, y + h + 0.002, (p.z + q.z) / 2);
            trims.push(g);
          }
        }
      }
    }
    this.merge(
      fittings,
      new THREE.MeshStandardMaterial({ color: "#a4b5ad", roughness: 0.9 }),
    );
    this.merge(
      trims,
      new THREE.MeshStandardMaterial({ color: "#eff0e4", roughness: 0.8 }),
    );
    this.merge(
      foundations,
      new THREE.MeshStandardMaterial({
        vertexColors: true,
        side: THREE.DoubleSide,
        roughness: 1,
      }),
    );
    for (let i = 0; i < sets.length; i++) {
      const mat = new THREE.MeshStandardMaterial({
        color: "#ffffff",
        vertexColors: true,
        roughness: 0.85,
        emissive: "#cbdff2",
        emissiveIntensity: 0,
      });
      detailedFacade(mat);
      this.materials.push(mat);
      this.merge(sets[i], mat);
    }
    this.merge(
      roofs,
      new THREE.MeshStandardMaterial({
        color: "#ffffff",
        vertexColors: true,
        roughness: 0.9,
        side: THREE.DoubleSide,
      }),
    );
  }
  merge(gs, material) {
    if (!gs.length) return;
    const merged = mergeGeometries(gs);
    const mesh = new THREE.Mesh(merged, material);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    this.group.add(mesh);
    gs.forEach((g) => g.dispose());
  }
  ribbon(coords, width, lift, offset = 0, surface = null) {
    const pos = [];
    this.drapeGrid ||= terrainGrid(this.data.terrain, this.a.project);
    for (let i = 1; i < coords.length; i++) {
      const c = coords[i - 1],
        d = coords[i],
        length = this.point(c).distanceTo(this.point(d));
      const count = Math.max(1, Math.ceil(length / 0.025));
      for (let j = 0; j < count; j++) {
        const lerp = (t) => c.map((v, k) => v + (d[k] - v) * t),
          p = this.point(lerp(j / count), lift),
          q = this.point(lerp((j + 1) / count), lift),
          dir = q.clone().sub(p).setY(0).normalize(),
          n = new THREE.Vector3(-dir.z, 0, dir.x);
        const l = p.clone().addScaledVector(n, offset - width / 2),
          r = p.clone().addScaledVector(n, offset + width / 2),
          L = q.clone().addScaledVector(n, offset - width / 2),
          R = q.clone().addScaledVector(n, offset + width / 2);
        if (surface) {
          for (const v of [l, r, L, r, R, L])
            pos.push(v.x, surface(v.x, v.z) + lift, v.z);
        } else
          pos.push(
            ...drapePolygon(
              [l, r, R, L].map((v) => [v.x, v.z]),
              this.drapeGrid,
              (x, z) => this.point(this.a.project.toGeo(x, z)).y,
              lift,
            ),
          );
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.computeVertexNormals();
    return g;
  }
  buildStreets() {
    const road = [],
      paving = [],
      marks = [];
    for (const f of this.data.roads) {
      const tags = f.properties,
        c = f.geometry.coordinates,
        walk = ["footway", "path", "pedestrian", "steps", "cycleway"].includes(
          tags.highway,
        );
      if (c.length < 2) continue;
      const surface = this.bridgeSurfaces.get(String(f.id));
      const ribbon = (c, width, lift) =>
        this.ribbon(c, width, lift, 0, surface);
      const lanes = Math.min(
        6,
        parseInt(tags.lanes) ||
          (["trunk", "primary", "secondary"].includes(tags.highway) ? 4 : 2),
      );
      const width = walk
        ? 0.005
        : Math.max(0.009, (parseFloat(tags.width) || lanes * 3.1) * 0.002);
      if (!walk) {
        paving.push(ribbon(c, width + 0.008, 0.001));
        road.push(ribbon(c, width, 0.0015));
        if (width >= 0.012) {
          for (let i = 1; i < c.length; i++) {
            const a = this.point(c[i - 1]),
              b = this.point(c[i]);
            if (a.distanceTo(b) < 0.015) continue;
            for (let t = 0.1; t < 0.9; t += 0.2) {
              const p = c[i - 1].map((v, k) => v + (c[i][k] - v) * t),
                q = c[i - 1].map(
                  (v, k) => v + (c[i][k] - v) * Math.min(0.95, t + 0.08),
                );
              marks.push(ribbon([p, q], 0.00065, 0.0018));
            }
          }
        }
      } else paving.push(ribbon(c, width, 0.0012));
      const curve = new THREE.CurvePath();
      for (let i = 1; i < c.length; i++)
        curve.add(
          new THREE.LineCurve3(
            this.point(c[i - 1], 0.015),
            this.point(c[i], 0.015),
          ),
        );
      const len = curve.getLength();
      if (len > 0.04) {
        const item = {
          curve,
          width,
          oneway:
            tags.oneway === "yes" ||
            tags.oneway === "1" ||
            tags.oneway === "-1",
          reverse: tags.oneway === "-1",
          coordinates: c,
          surface,
        };
        if (walk) this.walks.push(item);
        else this.paths.push(item);
      }
    }
    this.merge(
      paving,
      new THREE.MeshStandardMaterial({
        color: "#c6c4b7",
        side: THREE.DoubleSide,
        roughness: 1,
      }),
    );
    this.merge(
      road,
      new THREE.MeshStandardMaterial({
        color: "#78827c",
        side: THREE.DoubleSide,
        roughness: 1,
      }),
    );
    this.merge(
      marks,
      new THREE.MeshBasicMaterial({ color: "#eee4af", side: THREE.DoubleSide }),
    );
  }
  buildStreetAssets() {
    const white = [],
      poles = [],
      signs = [];
    for (const asset of this.data.streetAssets || []) {
      const center = this.point(asset.coordinates, 0.002);
      let nearest = null,
        dist = Infinity;
      for (const e of this.network.edges) {
        const vx = center.x - e.a.x,
          vz = center.z - e.a.z,
          t = Math.max(0, Math.min(1, (vx * e.dx + vz * e.dz) / e.length)),
          dx = center.x - e.a.x - e.dx * e.length * t,
          dz = center.z - e.a.z - e.dz * e.length * t,
          d = dx * dx + dz * dz;
        if (d < dist) {
          dist = d;
          nearest = e;
        }
      }
      if (!nearest) continue;
      const angle = Math.atan2(nearest.dx, nearest.dz);
      if (asset.kind === "crossing") {
        for (let i = -3; i <= 3; i++) {
          const g = new THREE.BoxGeometry(nearest.width * 0.92, 0.0007, 0.0012);
          g.rotateY(angle);
          g.translate(
            center.x + nearest.dx * i * 0.002,
            center.y,
            center.z + nearest.dz * i * 0.002,
          );
          white.push(g);
        }
      } else {
        const p = new THREE.CylinderGeometry(0.0005, 0.0006, 0.018, 6);
        p.translate(center.x, center.y + 0.009, center.z);
        poles.push(p);
        const sign = new THREE.BoxGeometry(0.006, 0.006, 0.001);
        sign.rotateY(angle);
        sign.translate(center.x, center.y + 0.02, center.z);
        signs.push(sign);
        const bench = new THREE.BoxGeometry(0.008, 0.002, 0.003);
        bench.rotateY(angle);
        bench.translate(
          center.x - nearest.dz * 0.005,
          center.y + 0.003,
          center.z + nearest.dx * 0.005,
        );
        poles.push(bench);
      }
    }
    this.merge(white, new THREE.MeshStandardMaterial({ color: "#f5f1df" }));
    this.merge(poles, new THREE.MeshStandardMaterial({ color: "#58736a" }));
    this.merge(signs, new THREE.MeshStandardMaterial({ color: "#387a92" }));
  }
  instance(geometry, color, n) {
    const m = new THREE.InstancedMesh(
      geometry,
      new THREE.MeshStandardMaterial({ color, roughness: 0.75 }),
      n,
    );
    m.frustumCulled = false;
    m.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    this.group.add(m);
    return m;
  }
  buildLife() {
    this.carCount = this.a.mobile ? 280 : 720;
    this.peopleCount = this.a.mobile ? 480 : 1400;
    this.dummy = new THREE.Object3D();
    this.network = roadNetwork(this.data.roads, (c) =>
      this.a.project.toWorld(c),
    );
    const center = this.a.project.toWorld([128.731, 36.566]);
    const seeds = distributedIndices(
      this.network.edges,
      this.carCount,
      (e) =>
        e.length *
        urbanWeight((e.a.x + e.b.x) / 2, (e.a.z + e.b.z) / 2, center),
    );
    this.traffic = seeds
      .map((edge, i) => vehicleState(this.network, i, edge))
      .filter(
        (s, i, all) =>
          !all
            .slice(0, i)
            .some(
              (other) =>
                other.edge === s.edge &&
                Math.abs(other.distance - s.distance) < 0.022,
            ),
      );
    this.carCount = this.traffic.length;
    this.pedestrianPaths = [];
    for (const source of [
      ...this.walks.map((p) => ({ ...p, foot: true })),
      ...this.paths.map((p) => ({ ...p, foot: false })),
    ]) {
      const length = source.curve.getLength();
      for (const side of source.foot ? [0] : [-1, 1]) {
        const samples = Math.max(2, Math.ceil(length / 0.004));
        const points = Array.from({ length: samples + 1 }, (_, i) => {
          const t = i / samples,
            v = source.curve.getPointAt(t),
            dir = source.curve.getTangentAt(t);
          const off = side * (source.width / 2 + 0.002);
          v.x -= dir.z * off;
          v.z += dir.x * off;
          return v;
        });
        for (const run of clearRuns(
          points,
          (x, z, margin) =>
            this.buildingBlocked(x, z, margin) ||
            (!source.surface && this.waterBlocked(x, z)),
        )) {
          const curve = new THREE.CurvePath();
          for (let j = 1; j < run.length; j++)
            curve.add(new THREE.LineCurve3(run[j - 1], run[j]));
          if (curve.getLength() > 0.025)
            this.pedestrianPaths.push({
              curve,
              foot: source.foot,
              surface: source.surface,
            });
        }
      }
    }
    const pedestrians = distributedIndices(
      this.pedestrianPaths,
      this.peopleCount,
      (p) => {
        const c = p.curve.getPointAt(0.5);
        return (
          p.curve.getLength() * urbanWeight(c.x, c.z, center) * (p.foot ? 3 : 1)
        );
      },
    );
    this.pedestrianAssignments = pedestrians.map(
      (i) => this.pedestrianPaths[i],
    );
    this.cars = this.instance(
      new THREE.BoxGeometry(0.0063, 0.005, 0.014),
      "#ffffff",
      this.carCount,
    );
    this.glass = this.instance(
      new THREE.BoxGeometry(0.0049, 0.0035, 0.007),
      "#3c636a",
      this.carCount,
    );
    this.wheels = this.instance(
      new THREE.BoxGeometry(0.0077, 0.003, 0.0028),
      "#33413b",
      this.carCount * 2,
    );
    this.headlights = this.instance(
      new THREE.BoxGeometry(0.0042, 0.0016, 0.0007),
      "#fff0b1",
      this.carCount,
    );
    const palette = [
      "#eee8d6",
      "#23778d",
      "#cc6344",
      "#4674aa",
      "#e5b848",
      "#465950",
      "#a64b50",
    ];
    this.cars.instanceColor = null;
    for (let i = 0; i < this.carCount; i++)
      this.cars.setColorAt(i, new THREE.Color(palette[i % palette.length]));
    this.people = this.instance(
      new THREE.CylinderGeometry(0.0014, 0.0016, 0.0065, 7),
      "#ffffff",
      this.peopleCount,
    );
    this.heads = this.instance(
      new THREE.SphereGeometry(0.0016, 8, 6),
      "#c9a589",
      this.peopleCount,
    );
    for (let i = 0; i < this.peopleCount; i++)
      this.people.setColorAt(i, new THREE.Color(palette[i % palette.length]));
    this.legs = this.instance(
      new THREE.BoxGeometry(0.0012, 0.0044, 0.0013),
      "#3c4e50",
      this.peopleCount * 2,
    );
    this.arms = this.instance(
      new THREE.BoxGeometry(0.001, 0.0051, 0.001),
      "#b99a78",
      this.peopleCount * 2,
    );
    const fixtures = Math.min(180, this.paths.length * 2);
    this.poles = this.instance(
      new THREE.CylinderGeometry(0.0005, 0.0007, 0.023, 5),
      "#536c63",
      fixtures,
    );
    this.lamps = this.instance(
      new THREE.BoxGeometry(0.004, 0.002, 0.004),
      "#ece6b3",
      fixtures,
    );
    this.lamps.material.emissive = new THREE.Color("#ffcb72");
    for (let i = 0; i < fixtures; i++) {
      const p = this.paths[i % this.paths.length],
        t = ((i % 3) + 1) / 4,
        v = p.curve.getPointAt(t),
        n = p.curve.getTangentAt(t);
      v.x += -n.z * (p.width / 2 + 0.003);
      v.z += n.x * (p.width / 2 + 0.003);
      this.place(this.poles, i, v, 0.0115, 0, 0.001, p.surface);
      this.place(this.lamps, i, v, 0.024, 0, 0.001, p.surface);
    }
    const streetTrees = [];
    for (let i = 0; i < fixtures; i++) {
      const p = this.paths[i % this.paths.length],
        v = p.curve.getPointAt(0.65),
        n = p.curve.getTangentAt(0.65);
      v.x -= n.z * (p.width / 2 + 0.009);
      v.z += n.x * (p.width / 2 + 0.009);
      if (
        p.surface ||
        this.waterBlocked(v.x, v.z) ||
        this.buildingBlocked(v.x, v.z, 0.008)
      )
        continue;
      streetTrees.push({
        x: v.x,
        y: this.point(this.a.project.toGeo(v.x, v.z)).y,
        z: v.z,
        size: 0.007,
        tint: (i * 0.618) % 1,
      });
    }
    this.streetTrees = new Vegetation(this.group, streetTrees);
  }

  place(mesh, i, v, y, rotation, lift = 0.0017, surface = null) {
    const ground = surface
      ? surface(v.x, v.z) + lift
      : this.point(this.a.project.toGeo(v.x, v.z), lift).y;
    this.dummy.position.set(v.x, ground + y, v.z);
    this.dummy.rotation.set(0, rotation, 0);
    this.dummy.updateMatrix();
    mesh.setMatrixAt(i, this.dummy.matrix);
  }
  update(dt) {
    if (!this.group.visible) return;
    if (this.running && !this.a.reduced) this.time += dt;
    if (this.forest.season !== this.a.season) {
      this.forest.setSeason(this.a.season);
      this.a.renderer.shadowMap.needsUpdate = true;
    }
    this.parks.update();
    this.streetTrees.setSeason(this.a.season);
    this.waterUniform.value = this.time;
    this.waterMaterial.color.set(
      this.a.mode === "night"
        ? "#3f6685"
        : this.a.mode === "sunset"
          ? "#739ba1"
          : "#66a3b5",
    );
    const night = this.a.mode === "night";
    this.materials.forEach((m) => (m.emissiveIntensity = night ? 0.32 : 0));
    this.lamps.material.emissiveIntensity = night ? 1.6 : 0;
    this.headlights.material.emissive.set("#fff0ae");
    this.headlights.material.emissiveIntensity = night ? 2 : 0;
    this.ground.color.set(
      night ? "#9aafce" : this.a.mode === "snow" ? "#f4f8fc" : "#ffffff",
    );
    advanceTraffic(this.traffic, this.running && !this.a.reduced ? dt : 0);
    for (let i = 0; i < this.carCount; i++) {
      const state = this.traffic[i],
        surface = this.bridgeSurfaces.get(String(state.edge.id));
      const pose = vehiclePosition(state),
        v = new THREE.Vector3(pose.x, 0, pose.z),
        direction = new THREE.Vector3(pose.dx, 0, pose.dz),
        rotation = pose.rotation;
      this.place(this.cars, i, v, 0.004, rotation, 0.0017, surface);
      this.place(this.glass, i, v, 0.008, rotation, 0.0017, surface);
      for (let j = 0; j < 2; j++)
        this.place(
          this.wheels,
          i * 2 + j,
          v.clone().addScaledVector(direction, (j ? 1 : -1) * 0.0042),
          0.0018,
          rotation,
          0.0017,
          surface,
        );
      this.place(
        this.headlights,
        i,
        v.clone().addScaledVector(direction, 0.007),
        0.004,
        rotation,
        0.0017,
        surface,
      );
    }
    for (let i = 0; i < this.peopleCount; i++) {
      const p = this.pedestrianAssignments[i],
        progress = walkingProgress(this.time, i * 0.381, p.curve.getLength()),
        v = p.curve.getPointAt(progress.t),
        d = p.curve.getTangentAt(progress.t).multiplyScalar(progress.direction),
        lift = p.foot ? 0.0014 : 0.0012,
        rot = Math.atan2(d.x, d.z),
        bob = Math.sin(this.time * 5 + i) * 0.00015;
      this.place(this.people, i, v, 0.0065 + bob, rot, lift, p.surface);
      this.place(this.heads, i, v, 0.0116 + bob, rot, lift, p.surface);
      for (let j = 0; j < 2; j++) {
        const side = j ? 1 : -1,
          limb = v.clone();
        limb.x += d.z * side * 0.001;
        limb.z -= d.x * side * 0.001;
        this.place(this.legs, i * 2 + j, limb, 0.0022, rot, lift, p.surface);
        this.dummy.rotation.x =
          Math.sin(this.time * 5 + i + j * Math.PI) * 0.35;
        this.dummy.updateMatrix();
        this.legs.setMatrixAt(i * 2 + j, this.dummy.matrix);
        limb.x += d.z * side * 0.0007;
        limb.z -= d.x * side * 0.0007;
        this.place(this.arms, i * 2 + j, limb, 0.0065, rot, lift, p.surface);
        this.dummy.rotation.x =
          -Math.sin(this.time * 5 + i + j * Math.PI) * 0.3;
        this.dummy.updateMatrix();
        this.arms.setMatrixAt(i * 2 + j, this.dummy.matrix);
      }
    }
    for (const m of [
      this.cars,
      this.glass,
      this.wheels,
      this.headlights,
      this.people,
      this.heads,
      this.legs,
      this.arms,
    ])
      m.instanceMatrix.needsUpdate = true;
  }
}
