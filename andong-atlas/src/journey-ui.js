import {relayEntryHTML} from './relay-entry.js';
import { reportComparisonHTML } from "./report-effects.js";
import { initTransportUI } from "./transport-ui.js";
import { restaurantFactsHTML } from "./restaurant-info.js";
import "./journey.css";
import {
  JourneyNetwork,
  PLANS,
  parseTime,
  clockTime,
  benefitAt,
  placementComparison,
  returnDeadline,
  makeJourney,
  appendReturn,
} from "./journey-model.js";
import { JourneyScene } from "./journey-scene.js";
import { scenarioSummary, benefitPaths } from "./scenario-model.js";
const esc = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const $ = (id) => document.getElementById(id);
const fmt = (n) => Math.round(n).toLocaleString("ko-KR");
export function initJourneyUI(atlas, data, activate, media) {
  const catalog = data.journey.places,
    network = new JourneyNetwork(data.journey.network, (c) => {
      if (!atlas.inDetail(c)) return false;
      const [x, z] = atlas.project.toWorld(c);
      return atlas.district.buildingBlocked(x, z, 0.001);
    }),
    foods = catalog.filter((p) => p.kind === "restaurant"),
    experiences = catalog.filter((p) => p.kind === "experience"),
    mapped = catalog;
  let plan = "기본안",
    additions = [],
    extra = [],
    selected = foods[0],
    visible = false,
    journey,
    deadline,
    benefitUsed = new Set(),
    receipt = false,
    mapComparison = "scenario",
    showAddedBenefits = true;
  $("panel-journey").innerHTML =
    `<p class="intro">나의 안동 여행<br><strong>걷고, 타고, 혜택을 만나세요.</strong></p>
    <div class="media-entry"><button id="journey-transit">공식 버스 노선·시간표</button><button id="journey-photo-explore">실제 사진으로 장소 둘러보기</button></div>
    <div class="journey-plans" aria-label="여행 적용안">${PLANS.map((p) => `<button data-journey-plan="${p}" aria-pressed="${p === plan}">${p}</button>`).join("")}</div>
    <div class="journey-fields"><label>출발 거점<select id="journey-origin">${catalog
      .filter((p) => p.kind === "origin")
      .map(
        (p) =>
          `<option value="${p.id}" ${p.id === "downtown" ? "selected" : ""}>${esc(p.name)}</option>`,
      )
      .join(
        "",
      )}</select></label><label>출발 시각<input type="time" id="journey-start" value="17:00" required></label></div>
    <label class="field">들를 식당<select id="journey-food">${foods.map((p) => `<option value="${p.id}">${esc(p.name)}</option>`).join("")}</select></label>
    <label class="field">체험 선택<select id="journey-experience"><option value="">체험 생략</option>${experiences
      .filter((p) => network.snap(p.coordinates, "walk"))
      .map(
        (p) =>
          `<option value="${p.id}" ${p.id === "workshop" ? "selected" : ""}>${esc(p.name)}${p.proposed ? " (제안)" : ""}</option>`,
      )
      .join("")}</select></label>
    <div class="journey-actions"><button id="journey-food-info">식당 정보 보기</button><button id="journey-experience-info">체험 정보 보기</button></div>
    <div class="journey-summary" id="journey-summary"></div><button id="journey-start-tour" class="wide-button primary">이 코스 여행하기</button>
    <p class="note">도보·차량 속도와 체류 시간은 시연 가정입니다. 장소 앞에서 멈추며, 정보를 확인하고 계속할 수 있습니다.</p>
    <div id="journey-scenario-overview"></div><div class="journey-actions"><button id="journey-show-comparison">현재·기본·확대 비교</button><button id="journey-show-benefits">혜택 배치 비교</button></div>
    <div class="gis-legend" aria-label="지도 기호"><span><i class="gis-symbol" aria-hidden="true"></i>식음</span><span><i class="gis-symbol symbol-experience" aria-hidden="true"></i>체험</span><span><i class="gis-symbol symbol-benefit" aria-hidden="true"></i>주민증 혜택</span><span><i class="gis-symbol symbol-added" aria-hidden="true"></i>추가 혜택</span><span><i class="gis-route-key gis-walk-key" aria-hidden="true"></i>도보</span><span><i class="gis-route-key" aria-hidden="true"></i>차량</span></div><p class="note">작은 지도 기호를 누르면 장소 정보가 열립니다. 겹치는 지점은 확대해서 보거나 장소 목록에서 선택하세요.</p>
    <details open><summary>귀가편 맞추기</summary><p class="note">예약한 열차 시각을 직접 입력하세요. 열차 시간표 조회·예약 기능은 아닙니다.</p>
      <div class="journey-fields"><label>귀가 열차 출발<input id="return-train" type="time" value="21:30" required></label><label>역 도착 여유 (분)<input id="return-buffer" type="number" min="5" max="120" value="20"></label></div>
      <label class="field">월영교 → 안동역<select id="return-mode"><option value="car">택시·차량 (시간 가정)</option><option value="bus">시내버스 귀가편 확인</option><option value="proposal">제안 저녁 이동 (시간 가정)</option></select></label>
      <div class="journey-fields"><label>승차·이동 (분)<input id="return-drive" type="number" min="5" max="180" value="35"></label><label>대기·환승 (분)<input id="return-transfer" type="number" min="0" max="120" value="10"></label></div>
      <p class="note">정류장·승차 지점까지 도보 8분 가정. 버스 자료는 기점 출발표입니다. 월영교 승차 시각과 역 연결편은 공식 BIS에서 확인하세요.</p><div id="return-result" role="status"></div>
    </details>
    <details><summary>여행 순서 · 구간 바로 보기</summary><ol id="journey-stages"></ol></details>
    <details><summary>식당·체험·혜택 장소</summary><label class="field">장소 검색<input type="search" id="journey-search" placeholder="상호·장소 이름"></label><div id="journey-place-list"></div><p class="note">주소 점과 건물 일치는 별도 확인이 필요합니다. 지도 표식을 누르거나 목록에서 선택하세요.</p></details>
    <details><summary>자료와 여행 가정</summary><p class="note">${esc(data.journey.source)}. ${esc(data.journey.routeNote)} 하회마을 연결은 저장한 OSRM 공개 도로 경로입니다. 도보 분당 75m, 차량 평균 시속 25.2km, 식사 45분, 제안 공예체험 30분. 개별 지출·가격은 미확인 시 계산하지 않습니다.</p><p class="note">기존 혜택 ${catalog.filter((p) => p.benefit).length}곳 좌표 연결. ${data.journey.unlocatedBenefits.length}곳은 좌표 미확인으로 지도에서 제외했습니다.</p><div class="note">${data.journey.unlocatedBenefits.map((p) => esc(p.name)).join(" · ")}</div></details>`;
  document.body.insertAdjacentHTML(
    "beforeend",
    `
    <aside class="glass journey-place" id="journey-place" hidden aria-label="선택한 여행 장소"><div class="journey-card-head"><span id="journey-place-kind"></span><button id="journey-place-close" aria-label="장소 정보 닫기">×</button></div><h2 id="journey-place-name"></h2><div class="media-entry"><button id="journey-place-photo">실제 사진·거리·후기 보기</button></div><button id="journey-place-expand" hidden aria-expanded="false">장소 정보 펼치기</button><div id="journey-place-info"></div><div class="journey-actions"><button id="journey-place-visit">여정에 추가</button><button id="journey-place-benefit">혜택 추가</button></div><button id="journey-receipt" class="wide-button" hidden>영수증 인증 체험</button><p class="note" id="journey-place-status" role="status"></p></aside>
    <aside id="scenario-map-summary" class="glass scenario-map-summary" hidden aria-label="지도에서 사업과 혜택 비교"></aside>
    <section class="glass journey-player" id="journey-player" hidden aria-label="코스 여행 재생"><div class="journey-card-head"><span id="journey-live-time"></span><button id="journey-details-toggle" aria-expanded="false">여행 정보</button><button id="journey-exit">여행 종료</button></div><strong id="journey-live-title"></strong><p id="journey-live-info"></p><p id="journey-next-place"></p><button id="journey-photo-now" class="journey-photo-now">이 구간의 장소 실제 모습 ↗</button><progress id="journey-progress" max="1" value="0"></progress><div class="journey-player-controls"><button id="journey-prev" aria-label="이전 여행 구간">이전</button><button id="journey-play">계속 여행</button><button id="journey-next" aria-label="다음 여행 구간">다음</button><label>재생 속도<select id="journey-speed"><option value="1">1×</option><option value="2">2×</option><option value="4">4×</option></select></label></div><div id="journey-bus-tools" class="journey-bus-tools" hidden><button id="journey-bus-seat">통로 쪽으로 앉기</button><button id="journey-bus-bell" aria-pressed="false">하차 벨</button><span>드래그해서 창밖·차내 둘러보기</span></div><div class="journey-views"><button data-journey-view="first" aria-pressed="true">1인칭</button><button data-journey-view="follow" aria-pressed="false">여행자 따라가기</button><button data-journey-view="map" aria-pressed="false">전체 지도</button></div><p class="note">드래그·← → 둘러보기 · 지형 높이 1× · 이동·대기 압축 재생</p></section>
    <div id="journey-window" hidden aria-hidden="true"><span>BUS · 승객 시점</span></div>
    <dialog id="journey-compare-dialog" class="journey-dialog"><div class="dialog-heading">같은 조건으로 비교<button data-close-dialog="journey-compare-dialog" aria-label="여행 비교 닫기">닫기</button></div><h2>현재 · 기본안 · 확대안</h2><div id="journey-comparison"></div></dialog>
    <dialog id="journey-benefit-dialog" class="journey-dialog"><div class="dialog-heading">혜택을 놓고, 연결을 살펴보기<button data-close-dialog="journey-benefit-dialog" aria-label="혜택 배치 닫기">닫기</button></div><h2>혜택 배치 비교</h2><p class="note">초록은 기존 혜택, 황토색은 추가 제안입니다. 예시 배치는 실제 참여 확정을 뜻하지 않습니다.</p><div class="journey-actions"><button id="benefit-downtown">원도심 2곳 배치</button><button id="benefit-river">월영교 2곳 배치</button><button id="benefit-reset">추가 혜택 초기화</button></div><label class="field">혜택을 추가할 장소<select id="benefit-place">${mapped
      .filter((p) => !["origin", "sight", "stop"].includes(p.kind))
      .map((p) => `<option value="${p.id}">${esc(p.name)}</option>`)
      .join(
        "",
      )}</select></label><div class="journey-fields"><label>제안 할인율 (%)<input type="number" id="benefit-discount" min="1" max="100" value="10"></label><label>비교 시각<input type="time" id="benefit-time" value="18:30"></label><label>혜택 시작<input type="time" id="benefit-start" value="17:00"></label><label>혜택 종료<input type="time" id="benefit-end" value="21:00"></label></div><label class="toggle-row">추가 장소를 코스에도 넣기<input id="benefit-include" type="checkbox"></label><button id="benefit-add" class="wide-button primary">이 장소에 혜택 추가</button><p id="benefit-message" class="note" role="status"></p><div id="benefit-added"></div><label class="field">접근성 비교 출발점<select id="benefit-origin"><option value="downtown">원도심</option><option value="bridge">월영교</option><option value="station">안동역</option></select></label><button id="benefit-map" class="wide-button primary">지도로 배치 전후 비교</button><div id="benefit-results"></div><p class="note">공개 도로망의 도보 10분(분당 75m) 범위. 영업 시간이 미확인인 곳은 조건 확인 필요로 표시합니다. 혜택 추가만으로 사업 전체 소비 추정값을 올리지 않습니다.</p></dialog>`,
  );
  const player = new JourneyScene(atlas, network, selectPlace, tick);
  atlas.journey = player;
  $("journey-bus-seat").onclick=()=>player.setBusSeat();
  $("journey-bus-bell").onclick=()=>player.requestBusStop();
  const transportUI=initTransportUI(atlas,player,refresh);
  $("journey-transit").onclick=()=>transportUI.open($("journey-origin").value);
  player.onExit=()=>{tick();$('journey-place').hidden=true;if(visible)renderMapComparison();};
  $("journey-photo-explore").onclick = () =>
    media.open(catalog.find((p) => p.id === "bridge"));
  $("journey-place-photo").onclick = () => media.open(selected);
  $("journey-photo-now").onclick = () =>
    media.open(journey.stages[player.index].place);
  function parameters() {
    return {
      catalog,
      network,
      analysis: data.analysis,
      stops: data.journey.stops,
      origin: $("journey-origin").value,
      restaurant: $("journey-food").value,
      experience: $("journey-experience").value,
      plan,
      start: parseTime($("journey-start").value),
      additions,
      extra,
    };
  }
  function computeReturn() {
    if (
      ["return-train", "return-buffer", "return-drive", "return-transfer"].some(
        (id) => !$(id).value || !$(id).checkValidity(),
      )
    )
      return {
        valid: false,
        error: "귀가 시각과 이동 시간을 올바르게 입력하세요.",
      };
    return returnDeadline({
      train: parseTime($("return-train").value),
      buffer: Number($("return-buffer").value),
      drive: Number($("return-drive").value),
      transfer: Number($("return-transfer").value),
      mode: $("return-mode").value,
      timetableBasis: "origin-departure",
      departures: [],
    });
  }
  function refresh() {
    transportUI.clear(false);
    if (parseTime($("journey-start").value) === null) {
      $("journey-summary").textContent = "출발 시각을 입력하세요.";
      $("journey-start-tour").disabled = true;
      return;
    }
    deadline = computeReturn();
    journey = makeJourney(parameters());
    const visitEnd = journey.end;
    journey = appendReturn(journey, {
      catalog,
      network,
      deadline,
      mode: $("return-mode").value,
    });
    player.setJourney(journey);
    $("journey-player").hidden = true;
    $("journey-window").hidden = true;
    $("journey-summary").innerHTML =
      `<strong>${clockTime(journey.start)} → ${clockTime(journey.end)}</strong><span>${plan} · ${journey.stages.filter((s) => ["food", "experience", "visit", "sight", "popup"].includes(s.kind)).length}곳 방문 · 이동 ${(journey.distance / 1000).toFixed(1)}km · ${journey.stages.some((s) => s.path && s.place.id === "station") ? "귀가 포함" : "귀가 연결 불가"}</span>`;
    if (journey.issues.length)
      $("journey-summary").insertAdjacentHTML(
        "beforeend",
        `<p class="note">${journey.issues.slice(0, 2).map(esc).join("<br>")}</p>`,
      );
    $("return-result").innerHTML = deadline.valid
      ? `<strong>월영교에서 ${clockTime(deadline.leave)}까지 출발</strong><p>역 도착 ${clockTime(deadline.arrival)} · 열차 ${$("return-train").value}</p><small>${visitEnd <= deadline.leave ? `방문 종료 후 ${Math.floor(deadline.leave - visitEnd)}분 여유` : `${Math.ceil(visitEnd - deadline.leave)}분 초과 · 코스 조정 필요`}</small><p class="note">${esc(deadline.source)}</p>`
      : `<strong>${esc(deadline.error)}</strong>${deadline.reason==='origin-times-only'?'<button id="return-bus-info" class="wide-button">귀가 방향 노선·시간표 확인</button>':''}`;
    if($('return-bus-info'))$('return-bus-info').onclick=()=>transportUI.open('bridge');
    $("return-result").className =
      deadline.valid && visitEnd <= deadline.leave
        ? "return-ok"
        : "return-late";
    $("journey-stages").innerHTML =
      journey.stages
        .map(
          (s, i) =>
            `<li><button data-stage="${i}"><time>${clockTime(s.start)}</time> ${esc(s.title || s.place.name)}${s.closed ? " · 시간 확인" : ""}</button></li>`,
        )
        .join("") +
      journey.issues.map((t) => `<li class="note">${esc(t)}</li>`).join("");
    $("journey-start-tour").disabled = !journey.stages.length;
    $("journey-stages")
      .querySelectorAll("[data-stage]")
      .forEach((b) => (b.onclick = () => start(Number(b.dataset.stage))));
    atlas.solution.configure({
      visible: visible && plan !== "현재",
      expanded: plan === "확대안",
      minutes: 1110,
    });
    atlas.solution.follow = false;
    if (visible)
      player.showPlaces(
        [
          ...mapped.filter((p) => plan !== "현재" || !p.proposed),
          ...journey.stages
            .filter((s) => s.place.kind === "stop")
            .map((s) => s.place),
        ].filter((p, i, all) => all.findIndex((x) => x.id === p.id) === i),
        additions,
        selected?.id,
      );
    renderComparison();
    renderBenefits();
    renderMapComparison();
  }
  function tick(t = Math.min(1,player.elapsed / player.duration(journey.stages[player.index]))) {
    if (!player.active) {
      $("journey-player").hidden = true;
      $("journey-window").hidden = true;
      return;
    }
    const s = journey.stages[player.index];
    if (!s) return;
    if (s.path) $("journey-place").hidden = true;
    $("journey-player").hidden = false;
    $("journey-live-time").textContent =
      `${clockTime(s.start + (s.end - s.start) * t)} · ${player.index + 1}/${journey.stages.length}`;
    $("journey-live-title").textContent = s.title || s.place.name;
    $("journey-live-info").textContent = s.path
      ? `${s.kind === "walk" ? "도보" : "차량"} ${(s.path.distance / 1000).toFixed(2)}km · 여행 시간 ${s.end - s.start}분 · 경로 시뮬레이션`
      : s.closed
        ? "운영 시간 밖 · 장소 정보 확인"
        : `${s.end - s.start}분 체류 가정 · ${s.benefit ? s.benefit.type + " 혜택" : "장소에서 멈춤"}`;
    const phases={boarding:"승차 중 · 차량에 오르기",riding:"이동 중",alighting:"하차 중 · 내려서 걷기"};
    if(s.path&&phases[player.phase])$("journey-live-info").textContent=phases[player.phase]+" · "+$("journey-live-info").textContent;
    if (s.cameraClear === false)
      $("journey-live-info").textContent +=
        " · 건물과 도로 자료가 겹쳐 이 구간은 전체 지도로 표시";
    const nextPlace = journey.stages
      .slice(player.index + 1)
      .find((next) => !next.path && !["wait", "alight"].includes(next.kind));
    $("journey-next-place").textContent =
      `${nextPlace ? "다음 · " + nextPlace.place.name : "여행 마지막 구간"} · 예상 지출: 가격 확인 필요`;
    $("journey-progress").value = (player.index + t) / journey.stages.length;
    $("journey-play").textContent = player.playing ? "일시정지" : "계속 여행";
    $("journey-prev").disabled = player.index === 0;
    $("journey-next").disabled = player.index === journey.stages.length - 1;
    const inBus=player.view==='first'&&["bus","return"].includes(s.kind)&&s.vehicleType!=='car';
    $("journey-bus-tools").hidden=!inBus;
    $("journey-player").classList.toggle('bus-riding',inBus);
    $("journey-bus-seat").textContent=player.busSeat==='aisle'?'창가 쪽으로 앉기':'통로 쪽으로 앉기';
    $("journey-bus-bell").setAttribute('aria-pressed',String(!!player.cabin?.stopRequested));
    $("journey-bus-bell").textContent=player.cabin?.stopRequested?'하차 요청됨':'하차 벨';
    $("journey-window").hidden=!(player.view==='first'&&["bus","return"].includes(s.kind)&&s.vehicleType==='car');
    $('journey-window').querySelector('span').textContent=s.vehicleType==='car'?'CAR · 차량 동승 시점':'BUS · 승객 시점';
    document
      .querySelectorAll("[data-journey-view]")
      .forEach((b) =>
        b.setAttribute(
          "aria-pressed",
          String(b.dataset.journeyView === player.view),
        ),
      );
  }
  function selectPlace(p, fly = true) {
    selected = p;
    $("journey-place").hidden = false;
    $("journey-place").classList.toggle("arrival-compact",player.active);
    $("journey-place-expand").hidden=!player.active;
    $("journey-place-expand").setAttribute("aria-expanded","false");
    $("journey-place-expand").textContent="장소 정보 펼치기";
    $("journey-place-kind").textContent = p.proposed
      ? "이어드림 제안 장소"
      : p.benefit
        ? "기존 주민증 혜택 장소"
        : {
            restaurant: "식당 · 카페",
            experience: "체험 · 관람",
            origin: "여행 거점",
            stop: "버스 정류장",
            sight: "산책 장소",
            stay: "숙박",
            attraction: "관람 장소",
          }[p.kind] || "여행 장소";
    $("journey-place-name").textContent = p.name;
    const visitMinute = player.active
      ? journey.stages[player.index].start
      : (parseTime($("benefit-time").value) ?? 1110);
    const benefit = benefitAt(p, additions, visitMinute);
    $("journey-place-info").innerHTML =
      `<p>${esc(p.description || "안동 여행에 연결할 장소입니다.")}</p>${relayEntryHTML(p)}<dl><dt>주소·위치</dt><dd>${esc(p.address || p.coordinates.map((v) => v.toFixed(5)).join(", "))}</dd><dt>운영 시간</dt><dd>${esc(p.hours || "확인 필요")}</dd><dt>요금</dt><dd>${esc(p.priceText || "확인 필요")}</dd>${p.reservation ? `<dt>예약</dt><dd>${esc(p.reservation)}</dd>` : ""}<dt>혜택</dt><dd>${esc(benefit?.text || p.benefit || (p.id === "workshop" ? "영수증 인증 후 체험 10% 할인 제안" : "등록된 혜택 없음"))}</dd></dl>${p.benefit || additions.some((a) => a.id === p.id) ? `<p class="note">${clockTime(visitMinute)} 기준 · ${benefit ? "시간 조건 충족 (이용 자격·운영 여부 별도 확인)" : "이 시각에는 이용 시간 조건을 충족하지 않습니다."}</p>` : ""}${restaurantFactsHTML(p)}<p class="note">${esc(p.source)}${p.benefit ? " · " + esc(p.benefitSource) : ""}</p>${p.url?.startsWith("https://") ? `<a href="${esc(p.url)}" target="_blank" rel="noreferrer">수집 자료의 공식 안내 ↗</a>` : ""}`;
    $("journey-place-status").textContent = "";
    $("journey-place-visit").disabled = ["origin", "sight", "stop"].includes(
      p.kind,
    );
    $("journey-place-benefit").disabled = ["origin", "sight", "stop"].includes(
      p.kind,
    );
    $("journey-receipt").hidden = ![
      "restaurant",
      "experience",
      "popup",
    ].includes(p.kind);
    $("journey-receipt").textContent =
      p.kind === "restaurant" ? "영수증 인증 체험" : "혜택 사용 체험";
    if (fly) {
      player.stop();
      $("journey-player").hidden = true;
      atlas.select({...p,kind:p.kind||'place',viewDistance:1.2});
    }
    player.showPlaces(
      [
        ...mapped.filter((p) => plan !== "현재" || !p.proposed),
        ...journey.stages
          .filter((s) => s.place.kind === "stop")
          .map((s) => s.place),
      ].filter((p, i, all) => all.findIndex((x) => x.id === p.id) === i),
      additions,
      p.id,
    );
    if (innerWidth <= 700) $("explore").classList.remove("open");
    if(mapComparison==='benefits')renderMapComparison();
  }
  function renderPlaces() {
    const query = $("journey-search").value.trim();
    $("journey-place-list").innerHTML = mapped
      .filter((p) => p.name.includes(query))
      .map(
        (p) =>
          `<button class="journey-place-row" data-catalog="${p.id}"><span>${esc(p.name)}</span><small>${p.proposed ? "제안" : p.benefit ? "주민증 혜택" : p.kind === "restaurant" ? "식음" : "장소"}</small></button>`,
      )
      .join("");
    $("journey-place-list")
      .querySelectorAll("button")
      .forEach(
        (b) =>
          (b.onclick = () =>
            selectPlace(catalog.find((p) => p.id === b.dataset.catalog))),
      );
  }
  function renderComparison() {
    const cases = PLANS.map((p) => makeJourney({ ...parameters(), plan: p }));
    const rows = [
      ["참여 식당 규모", "—", "20곳 (가정)", "83곳 (가정)"],
      ["선택 코스 방문 종료", ...cases.map((c) => clockTime(c.end))],
      [
        "귀가 권장 출발 충족",
        ...cases.map((c) =>
          deadline.valid
            ? c.end <= deadline.leave
              ? "가능 (입력 조건)"
              : "코스 조정 필요"
            : "귀가 조건 확인",
        ),
      ],
      ["체험 10% 할인 연결", "추가 사업 없음", "제안", "제안"],
      ["월영교 팝업", "추가 사업 없음", "제안", "제안"],
    ];
    $("journey-comparison").innerHTML =
      `<p>출발 ${esc(catalog.find((p) => p.id === $("journey-origin").value).name)} · ${$("journey-start").value} · 귀가 열차 ${$("return-train").value}</p><p class="comparison-hint">표를 좌우로 밀어 세 안을 비교하세요.</p><div class="comparison-scroll" tabindex="0" role="region" aria-label="현재 기본안 확대안 비교 표"><table><thead><tr><th>비교 항목</th>${PLANS.map((p) => `<th>${p}</th>`).join("")}</tr></thead><tbody>${rows.map((r) => `<tr>${r.map((v, i) => `<${i ? "td" : "th"}>${esc(v)}</${i ? "td" : "th"}>`).join("")}</tr>`).join("")}</tbody></table></div><p class="note">이 표는 시설 배치와 개인 코스 비교입니다. 사업 기대효과는 아래 최신 보고서의 83곳·참여율별 비교를 보세요. 같은 장소를 선택하면 개인 이동 시간은 같을 수 있습니다. 추가한 혜택 위치의 소비 효과는 검증할 행동 계수가 없어 이 표에 합산하지 않습니다. QR 인증과 주민증 이용은 별도로 집계합니다.</p><div class="journey-actions">${PLANS.map((p) => `<button data-compare-apply="${p}">${p} 지도에 적용</button>`).join("")}</div>${reportComparisonHTML()}`;
    $("journey-comparison")
      .querySelectorAll("[data-compare-apply]")
      .forEach(
        (b) =>
          (b.onclick = () => {
            choosePlan(b.dataset.compareApply);
            $("journey-compare-dialog").close();
          }),
      );
  }
  function renderBenefits() {
    const minute = parseTime($("benefit-time").value);
    if (minute === null) {
      $("benefit-results").textContent = "비교 시각을 입력하세요.";
      return;
    }
    const base = catalog.find((p) => p.id === $("benefit-origin").value),
      result = placementComparison(
        catalog,
        additions,
        base.coordinates,
        minute,
        network,
      );
    $("benefit-added").innerHTML = additions.length
      ? `<h3>추가한 혜택 ${additions.length}곳</h3>` +
        additions
          .map(
            (a) =>
              `<div class="benefit-added-row"><span>${esc(catalog.find((p) => p.id === a.id).name)} · ${a.discount}%</span><button data-remove-benefit="${a.id}" aria-label="${esc(catalog.find((p) => p.id === a.id).name)} 혜택 삭제">삭제</button></div>`,
          )
          .join("")
      : '<p class="note">추가 혜택 없음 · 기존 혜택 유지</p>';
    const areaRows = ["downtown", "bridge"]
      .map((id) => {
        const area = catalog.find((p) => p.id === id);
        const r = placementComparison(
          catalog,
          additions,
          area.coordinates,
          minute,
          network,
        );
        return `<tr><th>${esc(area.name)}</th><td>${r.before}곳</td><td>${r.after}곳</td></tr>`;
      })
      .join("");
    $("benefit-results").innerHTML =
      `<h3>${esc(base.name)}에서 도보 10분</h3><div class="benefit-counts"><div><span>추가 전</span><strong>${result.before}곳</strong></div><span>→</span><div><span>추가 후</span><strong>${result.after}곳</strong></div></div><table><thead><tr><th>동일 조건 · 도보 10분</th><th>전</th><th>후</th></tr></thead><tbody>${areaRows}</tbody></table>${result.rows.map((r) => `<p class="benefit-reachable">${esc(r.place.name)} <b>${r.walk}분</b><small>${r.after?.type || "기존"}${r.uncertain ? " · 운영 조건 확인 필요" : ""}</small></p>`).join("") || '<p class="note">선택한 시각과 도보 범위에서 연결된 혜택이 없습니다.</p>'}`;
    $("benefit-added")
      .querySelectorAll("button")
      .forEach(
        (b) =>
          (b.onclick = () => {
            additions = additions.filter(
              (a) => a.id !== b.dataset.removeBenefit,
            );
            extra = extra.filter((id) => id !== b.dataset.removeBenefit);
            refresh();
          }),
      );
  }
  function renderMapComparison(frame=false) {
    document.body.dataset.mapComparison=mapComparison;
    const report=scenarioSummary(data.solution,plan);
    $("scenario-map-summary").hidden=!visible;
    $("journey-scenario-overview").innerHTML=`<div class="scenario-inline"><span>${esc(plan)}의 사업 규모</span><strong>${report.restaurants?`식당 ${report.restaurants}곳 규모 가정`:"기존 장소·이동만 표시"}</strong><small>${report.proposed?"지도 거점은 배치 제안입니다. 효과는 83곳 운영의 참여율별 비교를 보세요.":"추가 제안 시설과 제안 이용 장면을 숨겼습니다."}</small></div>`;
    const host=$("scenario-map-summary");
    if(mapComparison==='benefits'){
      const base=catalog.find(p=>p.id===$("benefit-origin").value),minute=parseTime($("benefit-time").value);
      if(minute===null){host.textContent='비교 시각을 입력하세요.';player.showBenefitPaths([]);return;}
      const result=placementComparison(catalog,additions,base.coordinates,minute,network);
      const paths=benefitPaths(result,network,base.coordinates,showAddedBenefits);
      host.innerHTML=`<div class="scenario-map-head"><span>혜택 배치 · ${esc(base.name)}</span><button id="map-return-scenario">사업안 보기</button></div><h3>도보 10분 안에서</h3><div class="journey-plans"><button id="map-benefit-before" aria-pressed="${!showAddedBenefits}">추가 전 ${result.before}곳</button><button id="map-benefit-after" aria-pressed="${showAddedBenefits}">추가 후 ${result.after}곳</button></div><p>${$("benefit-time").value} 기준 · 실선은 연결된 보행로</p><div class="scenario-map-places">${paths.map(r=>`<button data-benefit-map-place="${esc(r.place.id)}">${esc(r.place.name)} <span>${r.walk}분</span></button>`).join('')||'<p>현재 조건에 맞는 혜택 없음</p>'}</div><button id="map-edit-benefits" class="scenario-text-button">장소·시각·할인율 편집 ↗</button><small>운영 미확인 장소 포함 · 추가 소비 추정은 그대로 유지</small>`;
      $('map-benefit-before').onclick=()=>{showAddedBenefits=false;renderMapComparison();};
      $('map-benefit-after').onclick=()=>{showAddedBenefits=true;renderMapComparison();};
      $('map-edit-benefits').onclick=()=>$('journey-benefit-dialog').showModal();
      $('map-return-scenario').onclick=()=>{mapComparison='scenario';refresh();};
      host.querySelectorAll('[data-benefit-map-place]').forEach(b=>b.onclick=()=>selectPlace(catalog.find(p=>p.id===b.dataset.benefitMapPlace)));
      player.showBenefitPaths(paths);
      player.routeGroup.visible=false;
      player.showPlaces([base,...result.rows.filter(r=>showAddedBenefits?r.after:r.before).map(r=>r.place)],showAddedBenefits?additions:[],selected?.id||base.id);
      if(frame){
        if($('shell-panel')?.getAttribute('aria-expanded')==='true')$('shell-panel').click();
        atlas.frameCoordinates([base.coordinates,...result.rows.map(r=>r.place.coordinates),...paths.flatMap(r=>r.path.coordinates)],{minDistance:.9});
      }
    }else{
      player.showBenefitPaths([]);player.routeGroup.visible=true;
      host.innerHTML=`<div class="scenario-map-head"><span>이어드림 · 지도 비교</span><button id="map-full-comparison">전체 비교 ↗</button></div><div class="journey-plans">${PLANS.map(p=>`<button data-map-plan="${p}" aria-pressed="${p===plan}">${p}</button>`).join('')}</div><div class="scenario-inline"><span>시설 배치 비교</span><strong>${report.proposed?`참여 식당 ${report.restaurants}곳 가정`:'현재 운영 장소'}</strong><small>최신 보고서 효과는 전체 비교에서 확인</small></div><div class="scenario-map-sites"><button data-map-site="market">식음 → 체험</button><button data-map-site="transport">저녁 이동</button><button data-map-site="popup">월영교 팝업</button></div><p>${report.proposed?`식당 ${report.restaurants}곳 규모 가정 · 팝업 수량 미확정`:'제안 시설 없음 · 기존 장소와 선택 코스 표시'}</p><small>${report.proposed?'시설·군중·차량은 연출입니다. 주민증과 QR 인증은 별도로 집계합니다.':'기존 관광객·소비가 0이라는 뜻은 아닙니다.'}</small>`;
      host.querySelectorAll('[data-map-plan]').forEach(b=>b.onclick=()=>choosePlan(b.dataset.mapPlan));
      host.querySelectorAll('[data-map-site]').forEach(b=>b.onclick=()=>{if(report.proposed)atlas.solution.focus(b.dataset.mapSite);else atlas.fly(b.dataset.mapSite==='market'?[128.729,36.565]:[128.760,36.576],b.dataset.mapSite==='transport'?9:1.5);});
      $('map-full-comparison').onclick=()=>$('journey-compare-dialog').showModal();
      const travel=document.createElement('button');travel.className='scenario-start-tour primary';travel.textContent='이 코스 여행하기';travel.onclick=()=>start();host.append(travel);
    }
  }
  function choosePlan(value) {
    transportUI.clear(false);
    mapComparison="scenario";
    plan = value;
    document
      .querySelectorAll("[data-journey-plan]")
      .forEach((b) =>
        b.setAttribute("aria-pressed", String(b.dataset.journeyPlan === plan)),
      );
    refresh();
  }
  function start(index = 0) {
    transportUI.clear(false);
    activate();
    $("journey-place").hidden = true;
    $("explore").classList.remove("open");
    benefitUsed = new Set();
    receipt = false;
    player.start(index);
    tick();
  }
  $("journey-start-tour").onclick = () => start();
  $("journey-place-expand").onclick=()=>{const compact=$("journey-place").classList.toggle("arrival-compact");$("journey-place-expand").setAttribute("aria-expanded",String(!compact));$("journey-place-expand").textContent=compact?"장소 정보 펼치기":"장소 정보 접기";};
  $("benefit-map").onclick=()=>{mapComparison="benefits";showAddedBenefits=true;$("journey-benefit-dialog").close();renderMapComparison(true);};
  document
    .querySelectorAll("[data-journey-plan]")
    .forEach((b) => (b.onclick = () => choosePlan(b.dataset.journeyPlan)));
  for (const id of [
    "journey-origin",
    "journey-start",
    "journey-food",
    "journey-experience",
    "return-train",
    "return-buffer",
    "return-mode",
    "return-drive",
    "return-transfer",
  ])
    $(id).addEventListener("change", refresh);
  $("journey-search").oninput = renderPlaces;
  $("journey-food-info").onclick = () =>
    selectPlace(catalog.find((p) => p.id === $("journey-food").value));
  $("journey-experience-info").onclick = () => {
    const p = catalog.find((p) => p.id === $("journey-experience").value);
    if (p) selectPlace(p);
  };
  $("journey-show-comparison").onclick = () => {
    $("journey-compare-dialog").showModal();
  };
  $("journey-show-benefits").onclick = () => {
    $("journey-benefit-dialog").showModal();
  };
  document
    .querySelectorAll("[data-close-dialog]")
    .forEach((b) => (b.onclick = () => $(b.dataset.closeDialog).close()));
  $("journey-place-close").onclick = () => {
    $("journey-place").hidden = true;
  };
  $("journey-place-visit").onclick = () => {
    if (selected.kind === "restaurant") $("journey-food").value = selected.id;
    else if (selected.kind === "experience")
      $("journey-experience").value = selected.id;
    else if (!extra.includes(selected.id)) extra.push(selected.id);
    refresh();
    $("journey-place-status").textContent =
      "이 장소를 넣어 코스를 다시 계산했습니다.";
  };
  $("journey-place-benefit").onclick = () => {
    $("benefit-place").value = selected.id;
    $("journey-benefit-dialog").showModal();
  };
  $("journey-receipt").onclick = () => {
    if (selected.kind === "restaurant") {
      receipt = true;
      $("journey-place-status").textContent =
        "영수증 인증 시연 완료 · 실제 인증·주민증 실적에 반영되지 않습니다.";
    } else if (!receipt && selected.id === "workshop") {
      $("journey-place-status").textContent =
        "식당에서 영수증 인증 체험을 먼저 진행하세요.";
    } else {
      benefitUsed.add(selected.id);
      $("journey-place-status").textContent =
        `혜택 사용 시연 ${benefitUsed.size}곳 · 실제 결제·예약 없음. 가격 미확인으로 할인 금액은 계산하지 않습니다.`;
    }
  };
  $("journey-details-toggle").onclick = () => {
    const expanded=$("journey-details-toggle").getAttribute("aria-expanded")!=="true";
    $("journey-details-toggle").setAttribute("aria-expanded",String(expanded));
    $("journey-player").classList.toggle("details-open",expanded);
  };
  $("journey-exit").onclick = () => {
    player.stop();
    player.onExit();
  };
  $("journey-play").onclick = () => {
    if (
      player.elapsed >= player.duration(journey.stages[player.index]) &&
      player.index === journey.stages.length - 1
    ) {
      player.seek(0);
    }
    player.playing = !player.playing;
    tick();
  };
  $("journey-next").onclick = () => {
    player.seek(player.index + 1);
  };
  $("journey-prev").onclick = () => {
    player.seek(player.index - 1);
  };
  $("journey-speed").onchange = () => {
    player.speed = Number($("journey-speed").value);
  };
  document.querySelectorAll("[data-journey-view]").forEach(
    (b) =>
      (b.onclick = () => {
        player.setView(b.dataset.journeyView);
        tick();
      }),
  );
  $("benefit-add").onclick = () => {
    const discount = Number($("benefit-discount").value),
      start = parseTime($("benefit-start").value),
      end = parseTime($("benefit-end").value),
      id = $("benefit-place").value;
    if (
      !(discount > 0 && discount <= 100) ||
      start === null ||
      end === null ||
      end <= start
    ) {
      $("benefit-message").textContent =
        "할인율 1–100%와 같은 날의 시작·종료 시각을 확인하세요.";
      return;
    }
    additions = additions.filter((a) => a.id !== id);
    additions.push({ id, discount, start, end });
    if ($("benefit-include").checked && !extra.includes(id)) extra.push(id);
    $("benefit-message").textContent =
      "제안 혜택을 추가했습니다. 지도와 접근성 비교에 반영됩니다.";
    refresh();
  };
  function preset(area) {
    const list = foods
      .filter((p) =>
        area === "downtown"
          ? p.coordinates[0] < 128.74
          : p.coordinates[0] > 128.75,
      )
      .slice(0, 2);
    additions = list.map((p) => ({
      id: p.id,
      discount: 10,
      start: 1020,
      end: 1260,
    }));
    $("benefit-origin").value = area === "downtown" ? "downtown" : "bridge";
    refresh();
  }
  $("benefit-downtown").onclick = () => preset("downtown");
  $("benefit-river").onclick = () => preset("river");
  $("benefit-reset").onclick = () => {
    extra = extra.filter((id) => !additions.some((a) => a.id === id));
    additions = [];
    refresh();
  };
  for (const id of ["benefit-origin", "benefit-time"])
    $(id).onchange = ()=>{renderBenefits();renderMapComparison();};
  renderPlaces();
  refresh();
  return {
    frame() {
      atlas.frameCoordinates(journey.stages.filter(s=>!s.title?.startsWith('안동역 복귀')&&s.title!=='안동역 도착 · 귀가편 준비').flatMap(s=>s.path?.coordinates||[s.place.coordinates]));
    },
    setVisible(value) {
      if(!value)transportUI.clear(false);
      visible = value;
      player.setVisible(value);
      $("scenario-map-summary").hidden=!value;
      document.body.classList.toggle("journey-open", value);
      if (value) {
        atlas.setDetailed(true, "city");
        atlas.fly([128.741, 36.569], 8);
        refresh();
      } else {
        $("scenario-map-summary").hidden=true;
        $("journey-place").hidden = true;
        $("journey-player").hidden = true;
        $("journey-window").hidden = true;
      }
    },
  };
}
