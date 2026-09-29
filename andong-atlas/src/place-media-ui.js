import {relayEntryHTML} from './relay-entry.js';
import {restaurantInfo, restaurantFactsHTML} from "./restaurant-info.js";
import "./place-media.css";
import {heritageVisit} from "./heritage-visit.js";
import {
  escapeHtml as esc,
  placeLinks,
  photosFor,
  photoDate,
} from "./place-media-model.js";
import { roadviewConfigured, showRoadview } from "./roadview.js";
const $ = (id) => document.getElementById(id);
const link = (url, text, cls = "") =>
  `<a class="${cls}" href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(text)} ↗</a>`;
export function initPlaceMedia(atlas, catalog, data) {
  const places = new Map(catalog.map((p) => [p.id, p]));
  let selected = catalog.find((p) => p.id === "bridge"),
    mode = "photos",
    photoIndex = 0,
    photoTimer,
    generation = 0;
  document.body.insertAdjacentHTML(
    "beforeend",
    `<dialog id="place-media-dialog" class="place-media-dialog" aria-labelledby="media-title">
    <div class="media-top"><span>ANDONG · 실제 모습으로 만나는 여행</span><button id="media-close" aria-label="실제 모습 닫기">닫기 ×</button></div>
    <div class="media-heading"><div><p id="media-eyebrow">사진과 거리</p><h2 id="media-title"></h2></div><label>둘러볼 장소<select id="media-place">${catalog.map((p) => `<option value="${esc(p.id)}">${esc(p.name)}${photosFor(p, data).length ? " · 사진" : ""}</option>`).join("")}</select></label></div>
    <div class="media-featured" aria-label="사진이 있는 주요 장소">${[
      "bridge",
      "hahoe",
      "station",
      ...catalog
        .filter((p) => p.kind === "restaurant" && photosFor(p, data).length)
        .map((p) => p.id),
    ]
      .map((id) => {
        const p = catalog.find((p) => p.id === id);
        return `<button data-photo-place="${id}">${esc(p.name.replace(" · KTX 하차", "").replace(" 서측 입구", ""))}</button>`;
      })
      .join("")}</div>
    <div class="media-tabs" role="tablist" aria-label="장소 정보 보기"><button role="tab" id="media-tab-photos" data-media-tab="photos" aria-controls="media-content">실제 사진</button><button role="tab" id="media-tab-street" data-media-tab="street" aria-controls="media-content">거리 둘러보기</button><button role="tab" id="media-tab-reviews" data-media-tab="reviews" aria-controls="media-content">후기·방문 팁</button></div>
    <div id="media-content" role="tabpanel"></div>
    <div id="media-relay-entry"></div><div class="media-footer"><span id="media-footnote"></span><button id="media-back">3D 지도로 돌아가기</button></div>
  </dialog>`,
  );
  const dialog = $("place-media-dialog");
  const fallback = (message) =>
    `<div class="media-empty"><span>실제 장소를 확인해 보세요</span><h3>${esc(message)}</h3><p>사진이 없는 곳은 현재 위치의 거리 모습이나 공식 안내에서 확인할 수 있습니다.</p></div>`;
  function renderPhoto(p) {
    return `<figure class="media-photo"><div class="media-photo-frame"><img id="media-photo-img" src="${esc(p.src)}" alt="${esc(p.caption)}" referrerpolicy="no-referrer"><p id="media-photo-loading" role="status">실제 사진을 불러오는 중…</p><div id="media-photo-error" hidden><p>원 제공처의 사진을 불러오지 못했습니다.</p>${link(p.sourceUrl, "원본에서 사진 보기")}</div></div><figcaption><strong>${esc(p.caption)}</strong><span>${esc(photoDate(p))} · 일반 사진</span><span>© ${esc(p.credit)} · ${link(p.sourceUrl, p.provider)} · ${link(p.licenseUrl, p.license)}</span></figcaption></figure>`;
  }
  async function render() {
    clearTimeout(photoTimer);
    const token = ++generation,
      photos = photosFor(selected, data),
      urls = placeLinks(selected),
      record = data.records[selected.id],
      visit = heritageVisit(selected);
    $("media-title").textContent = selected.name;
    $("media-relay-entry").innerHTML=relayEntryHTML(selected);
    $("media-place").value = selected.id;
    $("media-eyebrow").textContent = selected.proposed
      ? "이어드림 제안 위치 · 아직 조성되지 않은 장소"
      : selected.kind === "restaurant"
        ? "식당 · 실사진과 방문 정보"
        : "안동의 장소 · 실사진과 거리";
    $("media-footnote").textContent =
      mode === "reviews"
        ? "공식 안내와 방문자 후기를 구분해 확인하세요."
        : "촬영 당시 모습입니다. 현재 현장·영업 상태와 다를 수 있습니다.";
    document.querySelectorAll("[data-media-tab]").forEach((b) => {
      b.setAttribute("aria-selected", String(b.dataset.mediaTab === mode));
      b.tabIndex = b.dataset.mediaTab === mode ? 0 : -1;
    });
    $("media-content").setAttribute("aria-labelledby", "media-tab-" + mode);
    document
      .querySelectorAll("[data-photo-place]")
      .forEach((b) =>
        b.setAttribute(
          "aria-pressed",
          String(b.dataset.photoPlace === selected.id),
        ),
      );
    const external = urls
      ? `<div class="media-links">${link(urls.roadview, selected.proposed ? "제안 부지 주변 로드뷰" : "카카오맵 로드뷰 열기", "media-primary")}${link(urls.map, "지도에서 위치 확인")}</div>`
      : "";
    if (mode === "photos") {
      $("media-content").innerHTML =
        (photos.length
          ? renderPhoto(photos[Math.min(photoIndex, photos.length - 1)])
          : fallback(
              selected.proposed
                ? "제안 시설의 실제 사진은 아직 없습니다."
                : "이 장소에 연결된 사진은 아직 없습니다.",
            )) + external;
    } else if (mode === "street" && visit?.vr) {
      const vr=visit.vr;
      $("media-content").innerHTML=`<div class="street-intro"><div><h3>${esc(vr.title)}</h3><p>실제로 촬영한 공간을 직접 이동하며 둘러보세요.</p></div></div><div class="media-links">${link(vr.url,"공식 VR 새 탭으로 열기","media-primary")}</div><div id="media-vr" class="media-vr"><div class="media-vr-start"><span>360° · 실제 공간</span><h3>도산서원 안으로</h3><p>서원 전체 VR의 시작 지점에서 열립니다.<br>선택한 건물로 바로 이동하는 화면은 아닙니다.</p><button id="media-vr-load" class="media-primary">실사 VR 시작</button></div></div><p class="media-vr-credit">${esc(vr.provider)} · 연결 확인 ${esc(visit.checkedAt)}</p><div class="media-links">${link(vr.url,'VR을 새 탭에서 열기')}${link(vr.source,'공식 제공 페이지')}</div>${external}`;
      $("media-vr-load").onclick=()=>{
        const frame=document.createElement('iframe');
        frame.src=vr.url+'&play=1';frame.title=vr.title;frame.allowFullscreen=true;frame.allow='autoplay; fullscreen; xr-spatial-tracking';
        frame.referrerPolicy='strict-origin-when-cross-origin';
        $("media-vr").replaceChildren(frame);
        const notice=document.createElement('p');notice.className='media-vr-credit';notice.setAttribute('role','status');notice.textContent='공식 제공처의 외부 VR 화면입니다. 재생되지 않으면 위의 새 탭 열기를 이용하세요.';
        $("media-vr").before(notice);
      };
    } else if (mode === "street") {
      $("media-content").innerHTML =
        `<div class="street-intro"><div><h3>거리에서 바라보기</h3><p>${roadviewConfigured() ? "주변 80m 안의 촬영 지점을 찾고 있습니다." : "이 위치의 거리 사진은 카카오맵에서 둘러볼 수 있습니다."}</p></div><span class="media-coordinate">${selected.coordinates[1].toFixed(5)}° N<br>${selected.coordinates[0].toFixed(5)}° E</span></div><div id="media-roadview" hidden></div><p id="media-street-status" role="status">${roadviewConfigured() ? "거리 사진을 불러오는 중…" : "아래 버튼을 누르면 새 탭에서 로드뷰가 열립니다. 촬영 지점이 없는 구간은 제공되지 않을 수 있습니다."}</p>${external}${photos.length ? renderPhoto(photos[0]) : ""}`;
      const result = await showRoadview(
        $("media-roadview"),
        selected.coordinates,
        () => token === generation && dialog.open,
      );
      if (token !== generation || !dialog.open) return;
      if (result === "ready") {
        $("media-street-status").textContent =
          "가장 가까운 촬영 지점입니다. 표시된 장소와 촬영 위치가 다를 수 있습니다.";
        $("media-content").querySelector(".media-photo")?.remove();
      }
      if (result === "missing" || result === "unavailable")
        $("media-street-status").textContent =
          "이 화면에서 거리 사진을 불러오지 못했습니다. 카카오맵에서 해당 위치를 확인해 주세요.";
    } else {
      const official = record?.official, practical=restaurantInfo(selected);
      $("media-content").innerHTML =
        `<div class="review-intro"><h3>방문 전에 알고 싶은 네 가지</h3><p>대기·가격·주차·아이 동반을 중심으로 확인합니다. 공식 안내와 확인이 필요한 항목을 구분합니다. 실제 방문자 후기·별점은 원 서비스에서 확인하세요.</p></div><div class="review-facts"><article><span>01 · 대기</span><h3>줄 서는 시간</h3><p>실시간 대기 미연결 · 방문 시각·인원을 정해 업소에 문의하세요.</p></article><article><span>02 · 가격</span><h3>${selected.kind === "restaurant" ? "메뉴와 실제 결제" : "이용 비용과 할인"}</h3><p>${esc(visit?.price || selected.priceText || "가격 정보 확인 필요")}</p></article><article><span>03 · 주차</span><h3>주차와 마지막 도보</h3><p>전용 주차·요금 지원 미확인. 주변 주차장 검색 후 업소에 지원 여부를 확인하세요.</p></article><article><span>04 · 아이 동반</span><h3>${selected.kind === "restaurant" ? "유아의자·유모차" : "유모차와 보행 동선"}</h3><p>${selected.kind === "restaurant" ? "유아의자·맵기 조절·유모차 진입 미확인. 전화로 확인할 수 있습니다." : "유모차 진입·계단·쉼터 정보 미확인"}</p></article></div><div class="review-source"><h3>확인된 안내</h3><p>${esc(visit?.address || selected.address || "주소 상세 미확인")}</p><p>${esc(visit?.hours || practical?.hours || official?.hours || selected.hours || "운영 시간 확인 필요")}${official?.restDays ? `<br>휴무 · ${esc(official.restDays)}` : ""}${(visit?.phone || official?.phone) ? `<br>문의 · ${esc(visit?.phone || official.phone)}` : ""}</p><small>${esc(visit ? `${visit.provider} · 확인 ${visit.checkedAt}` : official ? `${official.provider} · 자료 갱신 ${official.updatedAt} · 수집 ${official.collectedAt}` : selected.source)}</small></div>${restaurantFactsHTML(selected)}<div class="media-links">${urls?.reviews ? link(urls.reviews, "카카오맵에서 장소·후기 찾기", "media-primary") : "<p>제안 장소에는 실제 영업 후기나 별점이 없습니다.</p>"}${visit ? link(visit.source, "공식 관람 안내") : ""}${selected.url?.startsWith("https://") ? link(selected.url, "공식 안내 보기") : ""}</div><p class="media-review-note">상호와 주소가 같은 곳인지 확인하세요. 다른 서비스의 별점·후기 수는 이 화면에서 합치지 않습니다.</p>`;
    }
    const img = $("media-photo-img");
    if (img) {
      const loading = $("media-photo-loading"), errorBox = $("media-photo-error");
      const error = () => {
        if (token !== generation || !img.isConnected) return;
        clearTimeout(photoTimer);
        loading.hidden = true;
        img.hidden = true;
        errorBox.hidden = false;
      };
      const loaded = () => {
        if (token !== generation || !img.isConnected) return;
        clearTimeout(photoTimer);
        loading.hidden = true;
        errorBox.hidden = true;
        img.hidden = false;
      };
      img.onerror = error;
      img.onload = loaded;
      if (img.complete) img.naturalWidth ? loaded() : error();
      else photoTimer = setTimeout(error, 10000);
    }
  }
  function open(place = selected, tab = "photos") {
    selected =
      places.get(place?.id) ||
      place ||
      catalog.find((p) => p.id === "bridge");
    if (!places.has(selected.id)) {
      places.set(selected.id, selected);
      const option = document.createElement("option");
      option.value = selected.id;
      option.textContent = selected.name;
      $("media-place").append(option);
    }
    mode = tab;
    photoIndex = 0;
    if (atlas.journey?.active) {
      atlas.journey.playing = false;
      atlas.journey.onTick();
    }
    if (!dialog.open) dialog.showModal();
    render();
  }
  $("media-close").onclick = $("media-back").onclick = () => dialog.close();
  dialog.addEventListener("close", () => {
    generation++;
    clearTimeout(photoTimer);
    $("media-content").replaceChildren();
  });
  dialog.addEventListener("keydown", (event) => {
    event.stopPropagation();
  });
  $("media-place").onchange = () => {
    selected = places.get($("media-place").value) || selected;
    photoIndex = 0;
    render();
  };
  document
    .querySelectorAll("[data-photo-place]")
    .forEach(
      (b) =>
        (b.onclick = () =>
          open(catalog.find((p) => p.id === b.dataset.photoPlace))),
    );
  document.querySelectorAll("[data-media-tab]").forEach((b) => {
    b.onclick = () => {
      mode = b.dataset.mediaTab;
      render();
    };
    b.onkeydown = (event) => {
      if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
      event.preventDefault();
      const tabs = [...document.querySelectorAll("[data-media-tab]")],
        i = tabs.indexOf(b),
        next = tabs[(i + (event.key === "ArrowRight" ? 1 : 2)) % 3];
      next.click();
      next.focus();
    };
  });
  return { open };
}
