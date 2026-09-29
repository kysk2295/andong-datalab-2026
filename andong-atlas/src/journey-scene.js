import {createBusCabin, BUS_SEAT, BUS_AISLE_SEAT} from "./transit-cabin.js";
import { MapPoints } from "./map-points.js";
import { terrainSafeEye } from "./geo.js";
import { roadStyle } from "./traffic.js";
import { clearCameraPath } from "./journey-clearance.js";
import { arrivalAnchor, sampleTravel, transitPhase } from "./journey-position.js";
import * as THREE from "three";
import { meters } from "./journey-model.js";
export class JourneyScene {
  constructor(atlas, network, onPlace, onTick) {
    this.a = atlas;
    this.network = network;
    this.onPlace = onPlace;
    this.onTick = onTick;
    this.group = new THREE.Group();
    atlas.world.add(this.group);
    this.group.visible = false;
    this.active = false;
    this.playing = false;
    this.view = "first";
    this.preferredView = "first";
    this.speed = 1;
    this.index = 0;
    this.elapsed = 0;
    this.yaw = 0;
    this.pitch = 0;
    this.mapPointsVisible = true;
    this.routeGroup = new THREE.Group();
    this.benefitGroup = new THREE.Group();
    this.decor = new THREE.Group();
    this.group.add(this.routeGroup, this.decor, this.benefitGroup);
    this.person = this.makePerson();
    this.bus = this.makeBus();
    this.car = this.makeCar();
    this.group.add(this.person, this.bus, this.car);
    this.ray = new THREE.Raycaster();
    this.pointer = new THREE.Vector2();
    this.mapPoints = new MapPoints(atlas, place => {
      this.playing = false;
      this.onPlace(place, !this.active);
      this.onTick();
    });
    let down = null;
    const canvas = atlas.renderer.domElement;
    canvas.addEventListener("pointerdown", (e) => {
      if (!this.group.visible) return;
      down = { x: e.clientX, y: e.clientY, px: e.clientX, py: e.clientY };
    });
    canvas.addEventListener("pointermove", (e) => {
      if (!down || !this.active || this.view !== "first") return;
      this.yaw -= (e.clientX - down.px) * 0.004;
      this.pitch = THREE.MathUtils.clamp(
        this.pitch - (e.clientY - down.py) * 0.003,
        -0.5,
        0.5,
      );
      down.px = e.clientX;
      down.py = e.clientY;
    });
    canvas.addEventListener("pointerup", (e) => {
      if (!down) return;
      const click = Math.hypot(e.clientX - down.x, e.clientY - down.y) < 5;
      down = null;
      if (!click || !this.group.visible) return;
      const rect = canvas.getBoundingClientRect();
      this.pointer.set(
        ((e.clientX - rect.left) / rect.width) * 2 - 1,
        (-(e.clientY - rect.top) / rect.height) * 2 + 1,
      );
      this.ray.setFromCamera(this.pointer, atlas.camera);
      const pickables = this.decor.visible
        ? this.decor.children.map(s => s.userData.board).filter(Boolean) : [];
      const hit = this.ray.intersectObjects(pickables, false)[0];
      if (hit?.object.userData.place) {
        this.playing = false;
        this.onPlace(hit.object.userData.place, !this.active);
        this.onTick();
      }
    });
    canvas.addEventListener("pointercancel", () => {
      down = null;
    });
    window.addEventListener("keydown", (e) => {
      if (!this.active || /INPUT|SELECT|TEXTAREA|BUTTON/.test(e.target.tagName) || document.querySelector('dialog[open]'))
        return;
      if (e.key === "Escape") {
        this.stop();
        this.onTick();
        this.onExit?.();
      }
      if (e.key === "ArrowLeft") this.yaw += 0.15;
      if (e.key === "ArrowRight") this.yaw -= 0.15;
    });
  }
  box(parent, size, pos, color) {
    const m = new THREE.Mesh(
      new THREE.BoxGeometry(...size),
      new THREE.MeshStandardMaterial({ color, roughness: 0.78 }),
    );
    m.position.set(...pos);
    m.castShadow = true;
    parent.add(m);
    return m;
  }
  makePerson() {
    const g = new THREE.Group();
    g.scale.set(.26,1,.26);
    this.box(g, [0.004, 0.007, 0.003], [0, 0.009, 0], "#d88d50");
    this.box(g, [0.0036, 0.004, 0.0036], [0, 0.0145, 0], "#edc5a4");
    g.userData.limbs=[];
    for (const x of [-0.0014, 0.0014]) {
      const leg=new THREE.Group();leg.position.set(x,.006,0);g.add(leg);
      this.box(leg,[.0015,.005,.002],[0,-.0025,0],'#354e5b');g.userData.limbs.push(leg);
    }
    this.box(g,[.003,.005,.0015],[0,.009,-.0024],'#b9ab83');
    for(const part of g.children)part.position.y-=.001;
    return g;
  }
  makeBus() {
    this.cabin=createBusCabin();this.busSeat='window';
    const g=this.cabin.group;
    // Map XY metres use .002 units; the atlas vertically exaggerates terrain 4×.
    // Its travel view flattens Y by 1/4, so compensate here exactly once.
    g.scale.set(.002,.008,.002);
    this.cabin.light.intensity*=.002*.002;this.cabin.light.distance*=.002;
    return g;
  }
  setBusSeat(){this.busSeat=this.busSeat==='window'?'aisle':'window';this.yaw=0;this.pitch=0;this.onTick();}
  requestBusStop(){if(this.cabin.requestStop())this.onTick();}
  makeCar(){
    const g=new THREE.Group();
    this.box(g,[.0038,.005,.009],[0,.004,0],'#e7d4a1');
    this.box(g,[.0033,.005,.005],[0,.008,0],'#80a5ad');
    this.box(g,[.0034,.001,.0047],[0,.0108,0],'#eee7d8');
    for(const x of [-.0019,.0019])for(const z of [-.0028,.0028])this.box(g,[.0007,.003,.0018],[x,.0015,z],'#344442');
    return g;
  }
  clear(group) {
    for (const o of [...group.children]) {
      o.traverse((x) => {
        x.geometry?.dispose();
        if (x.material) {
          for (const m of Array.isArray(x.material)
            ? x.material
            : [x.material]) {
            m.map?.dispose();
            m.dispose();
          }
        }
      });
      group.remove(o);
    }
  }
  point(c, bridge = "") {
    const a = this.a,
      p = a.point(c, 0.002);
    const surface = a.district.bridgeSurfaces.get(String(bridge));
    if (surface) p.y = surface() + 0.003;
    return p;
  }
  showPlaces(places, additions, selected) {
    this.clear(this.decor);
    this.placeRecords = places;
    this.mapPoints.setPlaces(places, additions, selected);
    for (const p of places) {
      const color =
        p.id === selected
          ? "#c66332"
          : additions.some((x) => x.id === p.id)
            ? "#c98a3a"
            : p.benefit
              ? "#37836b"
              : p.kind === "experience"
                ? "#8174a6"
                : p.proposed
                  ? "#c98a3a"
                  : "#496e7e";
      // A small wayfinding sign on the nearest mapped approach, not a fabricated building facade.
      const snap = this.network.snap(p.coordinates, "walk");
      if (!snap || snap.offset > 150) continue;
      const pos = this.a.point(this.network.nodes[snap.id], 0.004),
        sign = new THREE.Group();
      sign.position.copy(pos);
      if (p.kind === "stop") {
        this.box(sign, [0.025, 0.0015, 0.012], [0.016, 0.018, 0], "#406d66");
        this.box(sign, [0.019, 0.004, 0.005], [0.016, 0.005, 0.002], "#bb986c");
        for (const x of [0.005, 0.027])
          this.box(sign, [0.001, 0.018, 0.001], [x, 0.009, 0.004], "#6a8177");
      }
      this.box(sign, [0.0008, 0.016, 0.0008], [0.008, 0.008, 0], "#6b6e5d");
      const cv = document.createElement("canvas");
      cv.width = 512;
      cv.height = 160;
      const ctx = cv.getContext("2d");
      ctx.fillStyle = "#fff9e8";
      ctx.fillRect(0, 0, 512, 160);
      ctx.fillStyle = color;
      ctx.fillRect(0, 0, 12, 160);
      ctx.font = "bold 36px sans-serif";
      ctx.fillText(p.name.slice(0, 14), 28, 65);
      ctx.font = "23px sans-serif";
      ctx.fillText(
        p.proposed ? "이어드림 제안 장소" : "장소 안내 · 정보 보기",
        28,
        113,
      );
      const texture = new THREE.CanvasTexture(cv);
      texture.colorSpace = THREE.SRGBColorSpace;
      const board = new THREE.Mesh(
        new THREE.PlaneGeometry(0.008, 0.01),
        new THREE.MeshBasicMaterial({ map: texture, side: THREE.DoubleSide }),
      );
      board.position.set(0.008, 0.018, 0);
      sign.add(board);
      sign.userData.board = board;
      board.userData.place = p;
      this.decor.add(sign);
    }
  }
  cameraBlocked(x,z,margin=0){
    const d=this.a.district;
    return d.buildingBlocked(x,z,margin)||(d.wallBlocked?.(x,z,margin)??false);
  }
  pathPoints(stage) {
    const cs = stage.path?.coordinates;
    if (!cs) return [];
    const points = [],
      profiles = [];
    for (let i = 0; i < cs.length; i++) {
      if (i) {
        const a = cs[i - 1],
          b = cs[i],
          steps = Math.max(1, Math.ceil(meters(a, b) / 2));
        for (let j = 1; j < steps; j++) {
          const t = j / steps;
          profiles.push({
            kind: stage.path.kinds?.[i],
            bridge: stage.path.bridges[i],
          });
          points.push(
            this.point(
              [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t],
              stage.path.bridges[i],
            ),
          );
        }
      }
      profiles.push({
        kind: stage.path.kinds?.[i] || stage.path.kinds?.[i + 1],
        bridge: stage.path.bridges[i] || stage.path.bridges[i + 1],
      });
      points.push(
        this.point(cs[i], stage.path.bridges[i] || stage.path.bridges[i + 1]),
      );
    }
    const centre = points.map((p) => p.clone());
    if (stage.kind === "walk") {
      const shifted = points.map((p, i) => {
        if (
          profiles[i].bridge ||
          ["footway", "path", "pedestrian", "steps", "cycleway"].includes(
            profiles[i].kind,
          )
        )
          return p;
        const a = points[Math.max(0, i - 1)],
          b = points[Math.min(points.length - 1, i + 1)],
          dx = b.x - a.x,
          dz = b.z - a.z,
          len = Math.hypot(dx, dz) || 1;
        const off =
          roadStyle({ highway: profiles[i].kind || "residential" }).width / 2 +
          0.001;
        for (const side of [1, -1]) {
          const x = p.x - (dz / len) * off * side,
            z = p.z + (dx / len) * off * side;
          if (
            !this.a.district.buildingBlocked(x, z, 0.001) &&
            !this.a.district.waterBlocked(x, z)
          ) {
            const geo = this.a.project.toGeo(x, z);
            return new THREE.Vector3(x, this.a.elevation(geo) + 0.003, z);
          }
        }
        return p;
      });
      points.splice(0, points.length, ...shifted);
    }
    let clear = clearCameraPath(
      points.map((p) => ({ x: p.x, y: p.y, z: p.z })),
      (x, z, margin) => this.cameraBlocked(x,z,margin),
    );
    if (!clear && stage.kind === "walk") {
      points.splice(0, points.length, ...centre);
      clear = clearCameraPath(
        points.map((p) => ({ x: p.x, y: p.y, z: p.z })),
        (x, z, margin) => this.cameraBlocked(x,z,margin),
      );
    }
    stage.cameraClear = !!clear;
    if (!clear) return points;
    return clear.map((p, i) => {
      const geo = this.a.project.toGeo(p.x, p.z);
      const unchanged = Math.hypot(p.x - points[i].x, p.z - points[i].z) < 1e-8;
      return new THREE.Vector3(
        p.x,
        unchanged ? p.y : this.a.elevation(geo) + 0.003,
        p.z,
      );
    });
  }
  setJourney(journey) {
    this.stop();
    this.journey = journey;
    this.refreshTerrain();
    this.index = 0;
    this.elapsed = 0;
    this.person.visible = false;
    this.bus.visible = false;
    if(this.car)this.car.visible=false;
  }
  refreshTerrain() {
    if(!this.journey)return;
    this.clear(this.routeGroup);
    this.paths = this.journey.stages.map((s) => {delete s._length;delete s._lengths;return this.pathPoints(s);});
    this.paths.forEach((points, i) => {
      if (points.length < 2) return;
      const line = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(
          points.map((p) => p.clone().add(new THREE.Vector3(0, 0.005, 0))),
        ),
        this.journey.stages[i].kind === "walk"
          ? new THREE.LineDashedMaterial({color:"#97734f",dashSize:.025,gapSize:.016,transparent:true,opacity:.8,depthTest:false,depthWrite:false})
          : new THREE.LineBasicMaterial({color:"#466f68",transparent:true,opacity:.8,depthTest:false,depthWrite:false}),
      );
      line.computeLineDistances();
      line.renderOrder = 6;
      this.routeGroup.add(line);
    });
    if(this.active)this.restorePreferredView();
  }
  setVisible(value) {
    this.group.visible = value;
    if (!value) {this.stop();this.mapPoints.update(false);}
  }
  showBenefitPaths(rows) {
    this.clear(this.benefitGroup);
    for(const row of rows){
      const points=[];
      for(let i=1;i<row.path.coordinates.length;i++){
        const a=row.path.coordinates[i-1],b=row.path.coordinates[i],n=Math.max(1,Math.ceil(meters(a,b)/4));
        for(let k=0;k<n;k++)points.push(this.point([a[0]+(b[0]-a[0])*k/n,a[1]+(b[1]-a[1])*k/n],row.path.bridges[i]).add(new THREE.Vector3(0,.006,0)));
      }
      points.push(this.point(row.path.coordinates.at(-1),row.path.bridges.at(-1)).add(new THREE.Vector3(0,.006,0)));
      const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(points),new THREE.LineBasicMaterial({color:row.added?'#b17b40':'#397267',depthTest:false,depthWrite:false}));line.renderOrder=8;this.benefitGroup.add(line);
    }
    this.benefitGroup.userData.rows=rows;
    this.a.container.dataset.benefitRoutes=String(rows.length);
  }
  setView(view, { automatic = false } = {}) {
    if(!automatic)this.preferredView=view;
    if (
      this.active &&
      view !== "map" &&
      this.journey.stages[this.index].cameraClear === false
    )
      view = "map";
    this.view = view;
    this.a.world.scale.y = this.active && view !== "map" ? 0.25 : 1;
    this.a.renderer.shadowMap.needsUpdate = true;
    this.a.solution.sites.find((s) => s.id === "market").group.visible =
      !this.active || view === "map";
    this.mapPointsVisible = !this.active || view === "map";
    this.routeGroup.visible = !this.active || view === "map";
    if(this.benefitGroup)this.benefitGroup.visible=!this.active;
    this.yaw = 0;
    this.pitch = 0;
    this.cameraDirection=null;
    const a = this.a;
    a.controls.enabled = !this.active || view === "map";
    a.resize?.();
    a.camera.fov = view === "first" ? (this.journey?.kind==='heritage-inspection'?Math.min(100,Math.max(68,THREE.MathUtils.radToDeg(2*Math.atan(Math.tan(Math.PI/6)/a.camera.aspect)))):68) : 40;
    a.camera.near = view === "first" ? 0.00008 : 0.002;
    a.camera.updateProjectionMatrix();
    if (view === "map" && this.active) {
      a.setDetailed(false);
      const coordinates = this.journey.stages.flatMap(
        (s) => s.path?.coordinates || [s.place.coordinates],
      );
      const xs = coordinates.map((c) => c[0]),
        ys = coordinates.map((c) => c[1]);
      const low = [Math.min(...xs), Math.min(...ys)],
        high = [Math.max(...xs), Math.max(...ys)];
      a.fly(
        [(low[0] + high[0]) / 2, (low[1] + high[1]) / 2],
        Math.max(5, meters(low, high) * 0.0036),
        true,
      );
    }
  }
  restorePreferredView() {
    const desired=this.journey.stages[this.index]?.cameraClear===false?'map':this.preferredView;
    if(desired!==this.view)this.setView(desired,{automatic:true});
  }
  start(index = 0) {
    if (!this.journey?.stages.length) return;
    this.saved = {
      position: this.a.camera.position.clone(),
      target: this.a.controls.target.clone(),
      fov: this.a.camera.fov,
      near: this.a.camera.near,
      detail: this.a.district.group.visible,
      region: this.a.activeRegion,
    };
    this.active = true;
    this.mapPointsVisible = false;
    this.routeGroup.visible = false;
    this.index = Math.min(index, this.journey.stages.length - 1);
    this.elapsed = 0;
    this.playing = !this.a.reduced;
    this.a.flight = null;
    this.a.solution.follow = false;
    this.a.solution.running = false;
    document.body.classList.add("journey-playing");
    this.setView(this.preferredView);
    this.enterStage();
    this.onTick();
  }
  stop() {
    if (!this.active) return;
    this.active = false;
    this.playing = false;
    this.mapPointsVisible = true;
    this.routeGroup.visible = true;
    if(this.benefitGroup)this.benefitGroup.visible=true;
    this.a.controls.enabled = true;
    this.a.world.scale.y = 1;
    this.a.solution.sites.find((s) => s.id === "market").group.visible = true;
    this.a.solution.running = true;
    if (this.saved) {
      this.a.camera.position.copy(this.saved.position);
      this.a.controls.target.copy(this.saved.target);
      this.a.camera.fov = this.saved.fov;
      this.a.camera.near = this.saved.near;
      this.a.camera.updateProjectionMatrix();
      this.a.setDetailed(this.saved.detail, this.saved.region || "city");
    }
    this.person.visible = false;
    this.bus.visible = false;
    if(this.car)this.car.visible=false;
    document.body.classList.remove("journey-playing");
    this.a.resize?.();
  }
  seek(index) {
    this.index = Math.max(0, Math.min(index, this.journey.stages.length - 1));
    this.elapsed = 0;
    this.yaw = 0;
    this.pitch = 0;
    this.cameraDirection=null;
    this.enterStage();
    this.onTick();
  }
  enterStage() {
    const stage = this.journey.stages[this.index];
    this.a.flight = null;

    if (!stage.path) {
      this.playing = false;
      this.onPlace(stage.place, false);
    }
    this.cabin?.reset();
    if(['bus','return'].includes(stage.kind))this.cabin?.setDestination(stage.place?.name);
    this.restorePreferredView();
    this.onTick();
  }
  duration(stage) {
    // Road distance at ~32 km/h keeps scenery at street scale. Faster playback
    // and Next remain available; a multi-kilometre ride no longer flies by in 15s.
    if(stage.path&&['bus','return'].includes(stage.kind))return Math.max(18,(stage.path.distance||0)/9);
    return stage.path
      ? Math.max(9, Math.min(55, (stage.end - stage.start) * 1.5))
      : Math.max(5, Math.min(12, (stage.end - stage.start) * 0.4));
  }
  syncMapPoints() {
    this.mapPoints.update(this.group.visible && this.mapPointsVisible);
  }
  update(delta) {
    if (!this.group.visible) return;
    this.decor.visible = this.active && this.view !== "map";
    for (const sign of this.decor.children) {
      sign.userData.board?.lookAt(this.a.camera.position);
      // Small illustrative signs must not cover the visitor's eyes at arrival.
      sign.visible=this.view==='map'||Math.hypot(sign.position.x-this.a.camera.position.x,sign.position.z-this.a.camera.position.z)>(this.view==='first'?.035:.06);
    }
    if (!this.active) return;
    const stage = this.journey.stages[this.index];
    if (!stage) return;
    if (this.playing) this.elapsed += delta * this.speed;
    const duration = this.duration(stage),
      t = Math.min(1, this.elapsed / duration),
      points = this.paths[this.index];
    const vehicle=["bus","return"].includes(stage.kind),car=stage.vehicleType==='car',motion=transitPhase(t,vehicle,duration);
    this.phase=stage.path?motion.phase:'arrival';
    let p, next, onBridge=!!stage.path?.bridges?.some(Boolean);
    if(stage.viewpoint){
      p=this.a.point(stage.viewpoint.coordinates,.0014);
      next=this.a.point(stage.viewpoint.lookAt,.0014);
    } else if (points.length > 1) {
      const pose=sampleTravel(points,motion.progress,vehicle?.025:.012);
      p=pose.point;next=pose.next;
    } else {
      const snap = this.network.snap(stage.place.coordinates, "walk");
      p = this.a.point(
        snap ? this.network.nodes[snap.id] : stage.place.coordinates,
        0.003,
      );
      next = this.a.point(stage.place.coordinates, 0.003);
      const forward = this.paths
        .slice(this.index + 1)
        .find((ps) => ps.length > 1);
      const backward = this.paths
        .slice(0, this.index)
        .reverse()
        .find((ps) => ps.length > 1);
      const approach=arrivalAnchor(this.journey.stages,this.paths,this.index);
      if(approach){p.copy(approach.point);onBridge=approach.bridge;}
      if (backward)
        next=p.clone().add(backward.at(-1).clone().sub(backward[Math.max(0,backward.length-3)]));
      else if (forward)
        next = p
          .clone()
          .add(
            forward[Math.min(3, forward.length - 1)].clone().sub(forward[0]),
          );
      else if (backward)
        next = p.clone().add(
          backward
            .at(-1)
            .clone()
            .sub(backward[Math.max(0, backward.length - 3)]),
        );
      if (p.distanceTo(next) < 0.005) next.x += 0.03;
    }
    const geo = this.a.project.toGeo(p.x, p.z);
    if(this.view!=='map') this.a.focusDetail(geo);
    // Follow the currently loaded terrain even across region boundaries.
    if(!onBridge)p.y=this.a.elevation(geo)+.0014;
    const direction = next.clone().sub(p);
    direction.y = 0;
    if (direction.lengthSq() < 1e-8) direction.z = -1;
    direction.normalize();
    const heading = Math.atan2(direction.x, direction.z);
    this.person.visible = !stage.viewpoint && (!vehicle||motion.phase!=='riding') && this.view !== "first";
    this.bus.visible = vehicle && !car;
    if(this.car)this.car.visible=vehicle&&car&&this.view!=='first';
    const actor = vehicle ? (car&&this.car?this.car:this.bus) : this.person;
    actor.position.copy(p);
    actor.rotation.y = heading+(vehicle&&!car?Math.PI:0);
    if(vehicle&&!car)this.cabin?.update(this.elapsed,{moving:this.playing&&motion.phase==='riding'?1:0,doorOpen:1-motion.boarding,reduced:this.a.reduced});
    if(vehicle){
      const side=new THREE.Vector3(direction.z,0,-direction.x),offset=(car?.0025:.003)+(1-motion.boarding)*.005;
      const candidate=p.clone().addScaledVector(side,offset).addScaledVector(direction,car?0:.0064);
      const safe=!this.a.district.buildingBlocked(candidate.x,candidate.z,.001)&&!this.a.district.waterBlocked(candidate.x,candidate.z);
      this.transitAccess=safe;
      this.person.position.copy(safe?candidate:p);this.person.rotation.y=heading-Math.PI/2;
      this.person.visible&&=safe&&motion.boarding<.92;

    }
    this.person.userData.limbs?.forEach((leg,i)=>{leg.rotation.x=stage.path&&this.playing?Math.sin(this.elapsed*8+i*Math.PI)*.45:0;});
    if (this.view !== "map") {
      const heightScale = 0.25;
      const eye = p.clone();
      eye.y *= heightScale;
      eye.y += (vehicle ? .014+(car?-.004:.004)*motion.boarding : 0.014) * heightScale;
      if(vehicle&&motion.phase!=='riding'&&this.transitAccess){eye.x+=(this.person.position.x-p.x)*(1-motion.boarding);eye.z+=(this.person.position.z-p.z)*(1-motion.boarding);}
      if (this.view === "follow") {
        let behind = vehicle?.06:.022;
        for (let d = 0.005; d <= behind; d += 0.005) {
          if (
            this.cameraBlocked(
              p.x - direction.x * d,
              p.z - direction.z * d,
              0.002,
            )
          ) {
            behind = Math.max(0, d - 0.005);
            break;
          }
        }
        eye
          .addScaledVector(direction, -behind)
          .add(new THREE.Vector3(0, vehicle?(behind<.01?.045:.016):.006, 0));
        const anchor=p.clone();anchor.y*=heightScale;
        eye.y = terrainSafeEye(anchor, eye, (x, z) =>
          this.a.elevation(this.a.project.toGeo(x, z))*heightScale,
          {clearance:.001,rise:.003},
        );
      }
      if(!this.cameraDirection)this.cameraDirection=direction.clone();
      this.cameraDirection.lerp(direction,1-Math.exp(-delta*7)).normalize();
      if(vehicle&&!car&&this.cabin&&this.view==='first'){
        // Seat, shell and viewing direction share one smoothed heading through bends.
        this.bus.rotation.y=Math.atan2(this.cameraDirection.x,this.cameraDirection.z)+Math.PI;
        this.bus.updateWorldMatrix(true,false);
        const seat=new THREE.Vector3(...(this.busSeat==='aisle'?BUS_AISLE_SEAT:BUS_SEAT));
        eye.copy(this.bus.localToWorld(seat));
        // A seated ride: no hovering outside the shell during boarding transitions.
        if(this.playing&&!this.a.reduced&&motion.phase==='riding')eye.y+=Math.sin(this.elapsed*9)*.000008;
      }
      const dir = this.cameraDirection
        .clone()
        .applyAxisAngle(new THREE.Vector3(0, 1, 0), this.yaw);
      dir.y = Math.sin(this.pitch);
      if(stage.viewpoint){
        const targetY=(this.a.elevation(stage.viewpoint.lookAt)+.012)*heightScale;
        dir.y=(targetY-eye.y)/Math.max(.005,p.distanceTo(next))+Math.sin(this.pitch);
      }
      const target =
        this.view === "first"
          ? eye.clone().addScaledVector(dir, 0.1)
          : new THREE.Vector3(p.x,(p.y+.010)*heightScale,p.z);
      this.a.camera.position.copy(eye);
      this.a.controls.target.copy(target);
      this.a.camera.lookAt(target);
    }
    this.a.container.dataset.journeyStage = String(this.index);
    this.a.container.dataset.journeyView = this.view;
    this.a.container.dataset.journeyProgress = t.toFixed(3);
    this.a.container.dataset.journeyPhase=this.phase;
    if (!this.tickAt || performance.now() - this.tickAt > 300) {
      this.tickAt = performance.now();
      this.onTick(t);
    }
    if (t >= 1 && this.playing) {
      if (this.index < this.journey.stages.length - 1)
        this.seek(this.index + 1);
      else {
        this.playing = false;
        this.onTick(1);
      }
    }
  }
}
