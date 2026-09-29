import { timeLabel } from "./geo.js";
export const PLANS = ["현재", "기본안", "확대안"];
export const meters = (a, b) =>
  Math.hypot((a[0] - b[0]) * 89300, (a[1] - b[1]) * 111320);
export function parseTime(value) {
  if (!/^\d{2}:\d{2}$/.test(value)) return null;
  const [h, m] = value.split(":").map(Number);
  return h < 24 && m < 60 ? h * 60 + m : null;
}
export function clockTime(minutes) {
  return Number.isFinite(minutes)
    ? `${minutes >= 1440 ? "다음 날 " : ""}${timeLabel(Math.round(minutes) % 1440)}`
    : "계산 불가";
}
class Heap {
  a = [];
  push(v) {
    let i = this.a.length;
    this.a.push(v);
    while (i) {
      const p = (i - 1) >> 1;
      if (this.a[p][0] <= v[0]) break;
      this.a[i] = this.a[p];
      i = p;
    }
    this.a[i] = v;
  }
  pop() {
    const top = this.a[0],
      end = this.a.pop();
    if (this.a.length) {
      let i = 0;
      while (i * 2 + 1 < this.a.length) {
        let c = i * 2 + 1;
        if (c + 1 < this.a.length && this.a[c + 1][0] < this.a[c][0]) c++;
        if (this.a[c][0] >= end[0]) break;
        this.a[i] = this.a[c];
        i = c;
      }
      this.a[i] = end;
    }
    return top;
  }
}
export class JourneyNetwork {
  constructor(network, blocked = null) {
    this.nodes = network.nodes;
    this.edges = network.edges;
    this.cache = new Map();
    this.graph = {
      walk: this.nodes.map(() => []),
      drive: this.nodes.map(() => []),
    };
    this.edges.forEach((e, index) => {
      const [u, v, d, w, f, b] = e;
      if (w) {
        this.graph.walk[u].push([v, d, index]);
        this.graph.walk[v].push([u, d, index]);
      }
      let cost = d;
      if (blocked && (f || b)) {
        const a = this.nodes[u],
          z = this.nodes[v],
          samples = Math.ceil(d / 3);
        for (let i = 0; i <= samples; i++) {
          const t = i / (samples || 1);
          if (blocked([a[0] + (z[0] - a[0]) * t, a[1] + (z[1] - a[1]) * t])) {
            cost += 10000;
            break;
          }
        }
      }
      if (f) this.graph.drive[u].push([v, cost, index]);
      if (b) this.graph.drive[v].push([u, cost, index]);
    });
    // Keep real connected networks; never create a straight line across missing roads.
    this.valid = {};
    for (const mode of ["walk", "drive"]) {
      const und = this.nodes.map(() => []);
      this.graph[mode].forEach((es, u) =>
        es.forEach(([v]) => {
          und[u].push(v);
          und[v].push(u);
        }),
      );
      const seen = new Set();
      let largest = [];
      for (let i = 0; i < und.length; i++) {
        if (seen.has(i) || !und[i].length) continue;
        const group = [i];
        seen.add(i);
        for (let j = 0; j < group.length; j++)
          for (const v of und[group[j]])
            if (!seen.has(v)) {
              seen.add(v);
              group.push(v);
            }
        if (group.length > largest.length) largest = group;
      }
      this.valid[mode] = largest;
    }
  }
  snap(c, mode = "walk") {
    let best = null,
      d = Infinity;
    for (const i of this.valid[mode]) {
      const n = meters(c, this.nodes[i]);
      if (n < d) {
        d = n;
        best = i;
      }
    }
    return d <= 220 ? { id: best, offset: d } : null;
  }
  route(a, b, mode = "walk") {
    const key = JSON.stringify([a, b, mode]);
    if (this.cache.has(key)) return this.cache.get(key);
    const start = this.snap(a, mode),
      end = this.snap(b, mode);
    if (!start || !end) return null;
    const costs = new Float64Array(this.nodes.length).fill(Infinity),
      prev = new Int32Array(this.nodes.length).fill(-1),
      via = new Int32Array(this.nodes.length).fill(-1),
      heap = new Heap();
    costs[start.id] = 0;
    heap.push([0, start.id]);
    while (heap.a.length) {
      const [d, u] = heap.pop();
      if (d !== costs[u]) continue;
      if (u === end.id) break;
      for (const [v, w, e] of this.graph[mode][u])
        if (d + w < costs[v]) {
          costs[v] = d + w;
          prev[v] = u;
          via[v] = e;
          heap.push([d + w, v]);
        }
    }
    if (!Number.isFinite(costs[end.id])) {
      this.cache.set(key, null);
      return null;
    }
    const ids = [end.id];
    while (ids.at(-1) !== start.id) ids.push(prev[ids.at(-1)]);
    ids.reverse();
    const route = {
      coordinates: ids.map((i) => this.nodes[i]),
      kinds: ids.map((i) => (via[i] < 0 ? "" : this.edges[via[i]][7] || "")),
      bridges: ids.map((i) => (via[i] < 0 ? "" : this.edges[via[i]][6])),
      distance:
        ids.slice(1).reduce((sum, id) => sum + this.edges[via[id]][2], 0) +
        start.offset +
        end.offset,
      accessMeters: start.offset + end.offset,
    };
    this.cache.set(key, route);
    return route;
  }
}
export function benefitAt(place, additions, minute) {
  const addition = additions.find((a) => a.id === place.id);
  const available =
    (!Number.isFinite(place.open) || minute >= place.open) &&
    (!Number.isFinite(place.close) || minute < place.close);
  if (!available) return null;
  if (addition && minute >= addition.start && minute < addition.end)
    return {
      type: "추가 제안",
      text: `${addition.discount}% 할인 · ${clockTime(addition.start)}–${clockTime(addition.end)}`,
      discount: addition.discount,
    };
  if (place.benefit)
    return { type: "기존 주민증", text: place.benefit, discount: null };
  return null;
}
export function placementComparison(
  places,
  additions,
  origin,
  minute,
  network,
  limit = 10,
) {
  const rows = [];
  for (const place of places) {
    const before = benefitAt(place, [], minute),
      after = benefitAt(place, additions, minute);
    if (!before && !after) continue;
    if (meters(origin, place.coordinates) > limit * 75 + 450) continue;
    const path = network.route(origin, place.coordinates, "walk");
    if (!path) continue;
    const walk = Math.ceil(path.distance / 75);
    if (walk > limit) continue;
    rows.push({
      place,
      walk,
      before,
      after,
      uncertain: !Number.isFinite(place.open) || !Number.isFinite(place.close),
    });
  }
  rows.sort((a, b) => a.walk - b.walk);
  return {
    before: rows.filter((r) => r.before).length,
    after: rows.filter((r) => r.after).length,
    rows,
  };
}
export function returnDeadline({
  train,
  buffer = 20,
  drive = 35,
  transfer = 15,
  walk = 8,
  mode = "car",
  departures = [],
  timetableBasis = "boarding-departure",
}) {
  if (
    ![train, buffer, drive, transfer, walk].every(Number.isFinite) ||
    train < 0 ||
    train > 1439 ||
    [buffer, drive, transfer, walk].some((x) => x < 0)
  )
    return { valid: false, error: "시각과 이동 조건을 확인하세요." };
  const deadline = train - buffer;
  if (mode === "bus") {
    if (timetableBasis !== 'boarding-departure')
      return {valid:false,error:'월영교 승차 시각·역 연결편 확인 필요',reason:'origin-times-only'};
    const times = departures
      .map(parseTime)
      .filter(Number.isFinite)
      .filter((t) => t + drive + transfer <= deadline);
    if (!times.length)
      return {
        valid: false,
        error: "입력한 귀가 시각에 맞는 조사 시간표 출발편이 없습니다.",
      };
    const departure = Math.max(...times);
    return {
      valid: true,
      leave: departure - walk,
      departure,
      arrival: departure + drive + transfer,
      deadline,
      source: "확인한 승차 시각 + 역 환승·이동 시간 가정",
    };
  }
  if (mode === "proposal") {
    const departure = Math.min(deadline - drive - transfer, 1260);
    if (departure < 1110)
      return {
        valid: false,
        error: "제안 저녁 이동 시간(18:30–21:00)에 맞는 귀가 연결이 없습니다.",
      };
    return {
      valid: true,
      leave: departure - walk,
      departure,
      arrival: departure + drive + transfer,
      deadline,
      source: "18:30–21:00 제안 시간창 내 차량·환승 시간 가정",
    };
  }
  if (deadline - drive - transfer - walk < 0)
    return {
      valid: false,
      error: "전날 출발이 필요한 조건입니다. 같은 날 귀가 시각을 입력하세요.",
    };
  return {
    valid: true,
    leave: deadline - drive - transfer - walk,
    departure: deadline - drive - transfer,
    arrival: deadline,
    deadline,
    source:
      mode === "proposal"
        ? "제안 차량의 대기·이동 시간 가정"
        : "택시·차량의 대기·이동 시간 가정",
  };
}
export function makeJourney({
  catalog,
  network,
  analysis,
  origin = "downtown",
  restaurant,
  experience = "workshop",
  plan = "기본안",
  start = 1020,
  additions = [],
  extra = [],
  transportWait = 10,
  stops = [],
}) {
  const byId = new Map(catalog.map((p) => [p.id, p])),
    stages = [],
    issues = [];
  let time = start,
    current = byId.get(origin),
    totalDistance = 0;
  if (!current)
    return {
      stages,
      issues: ["출발지를 찾을 수 없습니다."],
      start,
      end: start,
    };
  function stay(place, kind = "visit", duration = place.duration || 5) {
    const closed =
      (Number.isFinite(place.open) && time < place.open) ||
      (Number.isFinite(place.close) && time + duration > place.close);
    if (closed) {
      issues.push(`${place.name}: 방문 구간이 수집/제안 운영 시간 밖입니다.`);
    }
    stages.push({
      kind,
      place,
      title: place.name,
      start: time,
      end: time + duration,
      coordinates: place.coordinates,
      closed,
      benefit: benefitAt(place, additions, time),
    });
    time += duration;
    current = place;
  }
  function move(place, mode, title) {
    const path = network.route(
      current.coordinates,
      place.coordinates,
      mode === "walk" ? "walk" : "drive",
    );
    if (!path) {
      issues.push(
        `${current.name} → ${place.name}: 연결 도로가 없어 재생에서 제외됩니다.`,
      );
      return false;
    }
    const duration = Math.max(
      1,
      Math.ceil(path.distance / (mode === "walk" ? 75 : 420)),
    );
    stages.push({
      kind: mode,
      title: title || `${place.name}까지 ${mode === "walk" ? "걷기" : "이동"}`,
      place,
      from: current,
      start: time,
      end: time + duration,
      path,
    });
    time += duration;
    totalDistance += path.distance;
    current = place;
    return true;
  }
  stay(current, "arrival", 3);
  const food = byId.get(restaurant),
    exp = byId.get(experience),
    bridge = byId.get("bridge"),
    popup = byId.get("popup");
  function nearbyStop(place) {
    const candidates = stops
      .map((s) => ({
        ...s,
        id: "stop-" + s.id,
        kind: "stop",
        source: "안동 BIS 정류장 위치 · 2026.09 수집",
        description:
          "가까운 실제 정류장 위치를 이용한 여행 시연입니다. 이 경로의 실제 운행 노선은 확인이 필요합니다.",
        hours: "운행일·노선별 확인 필요",
        distance: meters(s.coordinates, place.coordinates),
      }))
      .filter((s) => s.distance < 450)
      .sort((a, b) => a.distance - b.distance)
      .slice(0, 5);
    // The closest stop across a road can require a long detour. Compare the
    // mapped walking approaches, while retaining the same nearby-stop limit.
    return candidates.map(s=>({stop:s,path:network.route(place.coordinates,s.coordinates,'walk')}))
      .filter(item=>item.path).sort((a,b)=>a.path.distance-b.path.distance)[0]?.stop;
  }
  if (food) {
    if (origin !== "downtown") {
      const board = nearbyStop(current),
        alight = nearbyStop(food);
      if (board) move(board, "walk", "정류장까지 걸어가기");
      stay(current, "wait", transportWait);
      if (
        move(
          alight || food,
          "bus",
          origin === "station"
            ? "KTX 하차 후 원도심으로"
            : "원도심으로 · 차량 이동",
        )
      ) {
        if (alight) {
          stay(alight, "alight", 1);
          move(food, "walk", "하차 후 식당까지 걷기");
        }
        stay(food, "food", 45);
      }
    } else if (move(food, "walk", "식당으로 이동")) stay(food, "food", 45);
  }
  if (exp && (!exp.proposed || plan !== "현재")) {
    if (
      move(
        exp,
        meters(current.coordinates, exp.coordinates) > 1500 ? "bus" : "walk",
      )
    )
      stay(exp, "experience", exp.duration || 30);
  }
  for (const id of [...new Set(extra)]) {
    const p = byId.get(id);
    if (
      !p ||
      ["popup", "bridge", "bridge-east"].includes(p.id) ||
      p.id === food?.id ||
      p.id === exp?.id ||
      (p.proposed && plan === "현재")
    )
      continue;
    if (
      move(
        p,
        meters(current.coordinates, p.coordinates) > 1500 ? "bus" : "walk",
      )
    )
      stay(p, "visit", 15);
  }
  if (meters(current.coordinates, bridge.coordinates) > 1200) {
    const board = nearbyStop(current);
    if (board) move(board, "walk", "월영교행 승차 지점까지 걷기");
    if (plan === "현재") {
      stay(current, "wait", transportWait);
      issues.push("현재 코스의 대기·차량 이동은 시연 가정입니다. 기점 시간표로 중간 정류장 승차 시각을 추정하지 않습니다.");
    } else {
      if (time < 1110) stay(current, "wait", 1110 - time);
      else stay(current, "wait", transportWait);
      if (time > 1260)
        issues.push("제안 저녁 이동 운영 시간(18:30–21:00) 밖입니다.");
    }
    if (
      !move(
        bridge,
        "bus",
        plan === "현재"
          ? "월영교로 · 공개 도로망 이동"
          : "월영교로 · 제안 저녁 이동",
      )
    )
      return {
        stages,
        issues,
        start,
        end: time,
        distance: totalDistance,
        plan,
      };
  } else if (!move(bridge, "walk"))
    return { stages, issues, start, end: time, distance: totalDistance, plan };
  stay(bridge, "sight", 3);
  const east = byId.get("bridge-east");
  if (move(east, "walk", "월영교 위를 걷기")) stay(east, "sight", 5);
  move(bridge, "walk", "월영교 서측으로 돌아오기");
  if (plan !== "현재" && move(popup, "walk", "야간 팝업으로"))
    stay(popup, "popup", 25);
  return { stages, issues, start, end: time, distance: totalDistance, plan };
}
export function appendReturn(
  journey,
  { catalog, network, deadline, mode = "car" },
) {
  const stages = [...journey.stages],
    issues = [...journey.issues];
  if (!deadline.valid)
    return { ...journey, issues: [...issues, deadline.error] };
  const last = stages.at(-1)?.place,
    station = catalog.find((p) => p.id === "station");
  if (!last) return journey;
  const route = network.route(last.coordinates, station.coordinates, "drive");
  if (!route)
    return {
      ...journey,
      issues: [...issues, "안동역 복귀 경로를 연결하지 못했습니다."],
    };
  const time = Math.max(journey.end, deadline.leave),
    late = journey.end > deadline.leave;
  if (late && mode === "bus")
    return {
      ...journey,
      late: true,
      issues: [
        ...issues,
        "귀가 버스 출발을 놓치는 코스입니다. 이후 버스 탑승은 재생하지 않습니다.",
      ],
    };
  if (late)
    issues.push(
      `귀가 권장 출발보다 ${Math.ceil(journey.end - deadline.leave)}분 늦습니다. 방문을 줄이거나 귀가 조건을 바꾸세요.`,
    );
  if (time > journey.end)
    stages.push({
      kind: "wait",
      title: "귀가 출발 전 자유 시간",
      place: last,
      start: journey.end,
      end: time,
      coordinates: last.coordinates,
    });
  stages.push({
    kind: mode === "bus" ? "bus" : "return",
    vehicleType: mode === 'car' ? 'car' : 'bus',
    title:
      mode === "bus"
        ? "안동역 복귀 · 환승 시간 포함"
        : "안동역 복귀 · 가정한 차량 이동",
    place: station,
    from: last,
    start: time,
    end: time + (deadline.arrival - deadline.leave),
    path: route,
  });
  stages.push({
    kind: "arrival",
    title: "안동역 도착 · 귀가편 준비",
    place: station,
    start: stages.at(-1).end,
    end: stages.at(-1).end + 1,
    coordinates: station.coordinates,
  });
  return {
    ...journey,
    stages,
    issues,
    distance: journey.distance + route.distance,
    end: stages.at(-1).end,
    late,
  };
}
