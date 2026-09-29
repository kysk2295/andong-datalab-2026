let sdk;
export function roadviewConfigured() {
  return Boolean(import.meta.env.VITE_KAKAO_MAP_KEY);
}
function loadSdk() {
  if (window.kakao?.maps?.Roadview) return Promise.resolve(window.kakao.maps);
  if (sdk) return sdk;
  sdk = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    const timer = setTimeout(() => {
      script.remove();
      reject(Error("timeout"));
    }, 12000);
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?autoload=false&appkey=${encodeURIComponent(import.meta.env.VITE_KAKAO_MAP_KEY)}`;
    script.onerror = () => {
      clearTimeout(timer);
      script.remove();
      reject(Error("unavailable"));
    };
    script.onload = () => {
      if (!window.kakao?.maps?.load) {
        clearTimeout(timer);
        reject(Error("unavailable"));
        return;
      }
      window.kakao.maps.load(() => {
        clearTimeout(timer);
        resolve(window.kakao.maps);
      });
    };
    document.head.append(script);
  }).catch((error) => {
    sdk = null;
    throw error;
  });
  return sdk;
}
export async function showRoadview(container, coordinates, isCurrent) {
  if (!roadviewConfigured()) return "external";
  try {
    const maps = await loadSdk();
    if (!isCurrent()) return "cancelled";
    const position = new maps.LatLng(coordinates[1], coordinates[0]);
    const pano = await new Promise((resolve) => {
      const timer = setTimeout(() => resolve(null), 8000);
      new maps.RoadviewClient().getNearestPanoId(position, 80, (id) => {
        clearTimeout(timer);
        resolve(id);
      });
    });
    if (!isCurrent()) return "cancelled";
    if (!pano) return "missing";
    container.hidden = false;
    const view = new maps.Roadview(container);
    view.setPanoId(pano, position);
    return "ready";
  } catch {
    return "unavailable";
  }
}
