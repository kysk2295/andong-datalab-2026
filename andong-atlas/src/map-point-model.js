// Cartographic symbols stay in screen pixels. Never move geographic anchors
// to make a cluster look less crowded: hide lower-priority overlaps instead.
export function mapPointStyle(place, { selected = false, added = false } = {}) {
  const type = place.popupSite ? 'popup' : place.relayStage ? 'relay' : added ? 'added' : place.benefit ? 'benefit'
    : place.kind === 'heritage' ? 'heritage'
    : place.kind === 'experience' ? 'experience'
    : place.kind === 'stop' ? 'stop'
    : place.kind === 'restaurant' ? 'food' : 'place';
  const names = {popup:'야간 팝업 · 9개 부스',relay:`${place.relayStage}단계`,heritage:'관광지 명소',added:'추가 혜택',benefit:'주민증 혜택',experience:'체험·관람',stop:'정류장',food:'식당·카페',place:'여행 장소'};
  return { type, label: names[type] + (place.proposed ? " · 제안" : ""), selected,
    priority: selected ? 100 : place.popupSite ? 95 : place.relayStage ? 90 : added ? 80 : place.benefit ? 60 : place.kind === 'stop' ? 40 : type === 'experience' ? 30 : 10 };
}

export function declutterMapPoints(points, { width, height, obstacles = [], gap = 26 } = {}) {
  const chosen = [];
  for (const p of [...points].sort((a,b) => b.priority - a.priority)) {
    if (![p.x,p.y,p.z].every(Number.isFinite) || p.z < -1 || p.z > 1
      || p.x < 14 || p.x > width - 14 || p.y < 14 || p.y > height - 14) continue;
    if (obstacles.some(r => p.x >= r.left - 12 && p.x <= r.right + 12 && p.y >= r.top - 12 && p.y <= r.bottom + 12)) continue;
    if (chosen.some(q => Math.hypot(q.x-p.x, q.y-p.y) < gap)) continue;
    chosen.push(p);
  }
  return chosen;
}
