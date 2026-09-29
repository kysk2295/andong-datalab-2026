export const escapeHtml = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
export function placeLinks(place) {
  const [lon, lat] = place.coordinates;
  if (
    ![lon, lat].every(Number.isFinite) ||
    Math.abs(lat) > 90 ||
    Math.abs(lon) > 180
  )
    return null;
  const query = place.name.startsWith("안동")
    ? place.name
    : `안동 ${place.name}`;
  return {
    roadview: `https://map.kakao.com/link/roadview/${lat},${lon}`,
    map: `https://map.kakao.com/link/map/${encodeURIComponent(place.name)},${lat},${lon}`,
    reviews: place.proposed
      ? null
      : `https://map.kakao.com/link/search/${encodeURIComponent(query)}`,
  };
}
export function photosFor(place, data) {
  if (place.proposed) return [];
  return (data.records[place.id]?.photos || [])
    .map((id) => data.photos[id])
    .filter(
      (p) =>
        p?.view === "photo" &&
        p.src.startsWith("https://") &&
        p.credit &&
        p.license &&
        p.sourceUrl.startsWith("https://"),
    ).map(photo=>data.records[place.id]?.photoScope==='region'?{...photo,caption:`${photo.caption} · 선택한 개별 건물의 사진은 아닙니다`}:photo);
}
export function photoDate(photo) {
  return photo.capturedAt
    ? `촬영 ${photo.capturedAt}`
    : `촬영일 미확인${photo.updatedAt ? ` · 자료 갱신 ${photo.updatedAt}` : ""}`;
}
