const walk = new Set([
  "footway",
  "path",
  "pedestrian",
  "steps",
  "cycleway",
  "bridleway",
]);
export function roadStyle(tags) {
  const walking = walk.has(tags.highway),
    lanes = Math.min(
      6,
      parseInt(tags.lanes) ||
        (["trunk", "primary", "secondary"].includes(tags.highway) ? 4 : 2),
    );
  return {
    walking,
    width: walking
      ? 0.005
      : Math.max(0.009, (parseFloat(tags.width) || lanes * 3.1) * 0.002),
  };
}
export function roadNetwork(features, project) {
  const nodes = new Map(),
    edges = [];
  const node = (c) => {
    const key = c.map((v) => v.toFixed(7)).join(",");
    if (!nodes.has(key)) {
      const [x, z] = project(c);
      nodes.set(key, { key, x, z, out: [] });
    }
    return nodes.get(key);
  };
  const add = (a, b, width, id) => {
    const length = Math.hypot(b.x - a.x, b.z - a.z);
    if (length < 0.00001) return;
    const e = {
      a,
      b,
      width,
      length,
      id,
      dx: (b.x - a.x) / length,
      dz: (b.z - a.z) / length,
    };
    a.out.push(e);
    edges.push(e);
  };
  for (const f of features) {
    const p = f.properties,
      { walking, width } = roadStyle(p);
    if (walking || p.access === "private" || p.motor_vehicle === "no") continue;
    const c = f.geometry.coordinates;
    for (let i = 1; i < c.length; i++) {
      const a = node(c[i - 1]),
        b = node(c[i]);
      if (p.oneway !== "-1") add(a, b, width, f.id);
      if (!["yes", "1"].includes(p.oneway)) add(b, a, width, f.id);
    }
  }
  return { nodes, edges };
}
export function vehicleState(network, index, edgeIndex = null) {
  const edge = network.edges[edgeIndex ?? (index * 131) % network.edges.length];
  return {
    edge,
    distance: edge.length * ((index * 0.618) % 1),
    speed: 0.008 + (index % 7) * 0.001,
    seed: index + 37,
    stopped: false,
  };
}
export function advanceVehicle(state, dt) {
  if (state.stopped) return;
  state.distance += dt * state.speed;
  while (state.distance > state.edge.length) {
    const edge = state.edge;
    state.distance -= edge.length;
    let choices = edge.b.out.filter((next) => next.b !== edge.a);
    if (!choices.length) choices = edge.b.out;
    if (!choices.length) {
      state.distance = edge.length;
      state.stopped = true;
      break;
    }
    state.seed = (state.seed * 1664525 + 1013904223) >>> 0;
    // Mostly follow a straight continuation; occasionally choose an available turn.
    choices = [...choices].sort(
      (a, b) =>
        b.dx * edge.dx + b.dz * edge.dz - (a.dx * edge.dx + a.dz * edge.dz),
    );
    state.edge =
      choices[state.seed % 5 === 0 ? state.seed % choices.length : 0];
  }
}
export function vehiclePosition(state) {
  const e = state.edge,
    t = Math.min(1, state.distance / e.length),
    offset = e.width * 0.22;
  return {
    x: e.a.x + (e.b.x - e.a.x) * t - e.dz * offset,
    z: e.a.z + (e.b.z - e.a.z) * t + e.dx * offset,
    dx: e.dx,
    dz: e.dz,
    rotation: Math.atan2(e.dx, e.dz),
  };
}

// Same-direction headway for the miniature fleet; not a traffic-signal model.
export function advanceTraffic(states, dt, gap = 0.023) {
  if (dt <= 0) return;
  const positions = states.map(vehiclePosition),
    cells = new Map();
  positions.forEach((p, i) => {
    const key = `${Math.floor(p.x / gap)},${Math.floor(p.z / gap)}`;
    if (!cells.has(key)) cells.set(key, []);
    cells.get(key).push(i);
  });
  states.forEach((s, i) => {
    const p = positions[i];
    let step = s.speed * dt;
    const cx = Math.floor(p.x / gap),
      cz = Math.floor(p.z / gap);
    for (let x = cx - 1; x <= cx + 1; x++)
      for (let z = cz - 1; z <= cz + 1; z++)
        for (const j of cells.get(`${x},${z}`) || []) {
          if (i === j) continue;
          const q = positions[j],
            dx = q.x - p.x,
            dz = q.z - p.z;
          const ahead = dx * p.dx + dz * p.dz,
            lateral = Math.abs(dx * p.dz - dz * p.dx);
          if (
            ahead > 0 &&
            ahead < gap &&
            lateral < 0.0045 &&
            p.dx * q.dx + p.dz * q.dz > 0.5
          )
            step = Math.min(step, Math.max(0, ahead - gap));
        }
    advanceVehicle(s, step / s.speed);
  });
}
