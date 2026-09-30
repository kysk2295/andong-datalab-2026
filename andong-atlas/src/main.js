import {relayEntryHTML,relayEntryFor} from './relay-entry.js';
import {loadJSON,yieldToPage} from './loading.js';
import './relay-entry.css';
import { report } from "./report-effects.js";
import { enrichRestaurant } from "./restaurant-info.js";
import "./map-points.css";
import "./style.css";
import { initLayoutModes } from './layout-modes.js';
import { initSelectUI } from "./select-ui.js";
import { initPlaceMedia } from "./place-media-ui.js";
import mediaData from "../public/data/place-media.json";
import heritageMedia from '../public/data/heritage-media.json';
Object.assign(mediaData.photos,heritageMedia.photos);
Object.assign(mediaData.records,heritageMedia.records);
import { initJourneyUI } from "./journey-ui.js";
import { initTourismLayers } from './tourism-layers.js';
import { HeritageExplorer } from './heritage-explorer.js';
import { initSolutionUI } from "./solution-ui.js";
import {
  createIcons,
  Sun,
  Sunset,
  Moon,
  CloudRain,
  Snowflake,
  Info,
  X,
  ArrowUpRight,
  Navigation,
  Plus,
  Minus,
  House,
  PanelLeft,
  Play,
  Pause,
  Layers,
  MapPin,
  Maximize,
  Route,
  Image,
} from "lucide";
import { buildPlaces } from "./places.js";
import {
  timeLabel,
  closingState,
} from "./geo.js";

const $ = (id) => document.getElementById(id),
  icons = {
    Sun,
    Sunset,
    Moon,
    CloudRain,
    Snowflake,
    Info,
    X,
    ArrowUpRight,
    Navigation,
    Plus,
    Minus,
    House,
    PanelLeft,
    Play,
    Pause,
    Layers,
    MapPin,
    Maximize,
    Route,
    Image,
  };
const refreshIcons = () => createIcons({ icons });
const escape = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const weather = [
  ["day", "sun", "낮", "Day"],
  ["sunset", "sunset", "노을", "Sunset"],
  ["night", "moon", "야경", "Night"],
  ["rain", "cloud-rain", "비", "Rain"],
  ["snow", "snowflake", "눈", "Snow"],
];
$("weather").innerHTML = weather
  .map(
    ([key, icon, ko, en]) =>
      `<button data-weather="${key}" aria-label="${ko} (${en})" aria-pressed="${key === "day"}"><i data-lucide="${icon}"></i>${ko}<small>(${en})</small></button>`,
  )
  .join("");
refreshIcons();
let solutionUI, journeyUI, mediaUI, mediaPlace;
let scene,
  data,
  places,
  tab = "city",
  proposal = false,
  step = 0,
  tourTimer = null,
  tourIndex = 0,
  storyIndex = -1;
const interactiveSections = [
  ...document.querySelectorAll(".environment,.explore,.toolbar,.map-tools"),
];
interactiveSections.forEach((el) => (el.inert = true));
const steps = [
  {
    title: "01 식음에서 체험으로",
    current: "원도심 식음·체험과 주민증 혜택의 위치를 살펴봅니다.",
    proposal:
      "식음 이용 후 체험 10% 할인 연결을 제안합니다. 영수증 QR·주민증 조건형 병행 구상입니다.",
    place: "market",
  },
  {
    title: "02 저녁의 이동을 잇다",
    current: "112번은 기점·방향별 출발표입니다. 월영교 승차 시각은 별도 확인이 필요합니다.",
    proposal:
      "18:30~21:00 야간 이동을 연결하는 구상입니다. 운영 주체·대수·배차는 미확정입니다.",
    place: "woryeong",
  },
  {
    title: "03 월영교의 밤에 머물다",
    current: "주변 시설의 업종과 조사된 종료 시각을 확인합니다.",
    proposal:
      "월영교 권역의 야간 팝업을 검토합니다. 표시 위치는 권역이며 확정 부지가 아닙니다.",
    place: "woryeong",
  },
];
function stopTour() {
  clearInterval(tourTimer);
  tourTimer = null;
  $("tour").setAttribute("aria-pressed", "false");
  $("tour").querySelector("svg")?.setAttribute("data-lucide", "play");
}
function selected(place, fly = true, keepPanel = false) {
  mediaPlace = place;
  $("location-relay").innerHTML=relayEntryHTML(place);
  if (!scene.inDetail(place.coordinates)) scene.setDetailed(false);
  stopTour();
  $("location-name").textContent = place.name;
  $("location-description").textContent = place.description || '지도에서 이 장소의 주변을 탐색해 보세요.';
  $("coordinates").textContent = "";
  document
    .querySelectorAll(".place-row")
    .forEach((b) => b.classList.toggle("active", b.dataset.place === place.id));
  if (fly) scene.select(place);
  if (innerWidth <= 700 && !keepPanel) $("explore").classList.remove("open");
}
function overview() {
  $("location-relay").replaceChildren();
  stopTour();
  scene.home();
  $("district").value = "";
  scene.setDistrict(null);
  $("location-name").textContent = "안동, 한눈에";
  $("location-description").textContent =
    "낙동강과 호수, 그 사이에 펼쳐진 24개 읍면동";
  $("coordinates").textContent = "실제 지형과 공개 지도 기반";
  document
    .querySelectorAll(".place-row")
    .forEach((b) => b.classList.remove("active"));
}
function renderSteps() {
  $("steps").innerHTML = steps
    .map(
      (s, i) =>
        `<button class="step ${step === i ? "active" : ""}" data-step="${i}" aria-pressed="${step === i}"><b>${s.title}</b><p>${proposal ? s.proposal : s.current}</p></button>`,
    )
    .join("");
  $("steps")
    .querySelectorAll("button")
    .forEach((b) =>
      b.addEventListener("click", () => {
        step = Number(b.dataset.step);
        renderSteps();
        const p = places.find((p) => p.id === steps[step].place);
        selected(p);
        $("location-name").textContent = steps[step].title;
        $("location-description").textContent = proposal
          ? steps[step].proposal
          : steps[step].current;
      }),
    );
}
function setTab(next) {
  scene.heritageExplorer?.close();
  if(tab!==next)document.querySelector('.panel-body').scrollTop=0;
  tab = next;
  stopTour();
  document.querySelectorAll("[data-tab]").forEach((b) => {
    const active = b.dataset.tab === tab;
    b.setAttribute("aria-selected", String(active));
    b.tabIndex = active ? 0 : -1;
  });
  for (const k of ["city", "relay", "journey"])
    $(`panel-${k}`).hidden = k !== tab;
  scene.setRelay(tab === "relay", proposal);
  solutionUI?.sync(tab === "relay" && proposal, Number($("time").value));
  if (scene.facilityGroup)
    scene.facilityGroup.visible = tab === "relay" && !proposal;
  if (tab === "relay") {
    scene.fly([128.7445, 36.571], 13);
    $("location-name").textContent = "원도심에서 월영교까지";
    $("location-description").textContent = proposal
      ? "식음 · 체험 · 야간 이동 · 팝업을 잇는 제안 흐름"
      : "점선은 두 권역의 위치 관계이며 실제 이동 경로가 아닙니다.";
    $("coordinates").textContent = "안동 이어드림 · 3단계 릴레이";
  }
  journeyUI?.setVisible(tab === "journey");
  if (tab === "journey") scene.routeGroup.visible = false;
}
function renderTime() {
  solutionUI?.sync(tab === "relay" && proposal, Number($("time").value));
  const minutes = Number($("time").value);
  $("time-value").textContent = timeLabel(minutes);
  const inWindow = minutes >= 1110 && minutes <= 1260;
  $("operation").innerHTML = `<div class="status-line"><strong>${proposal ? (inWindow ? "제안 운영 시간 안" : "제안 운영 시간 밖") : "112번 · 기점 출발표 확인"}</strong>${proposal ? "18:30~21:00 · 차량·배차 미확정" : "기점별 시각과 중간 정류장 도착 시각은 다릅니다."}<br><span class="note">${proposal ? "점선은 사업의 개념 연결입니다." : "코스 여행 → 공식 버스 노선·시간표에서 확인"}</span></div>`;
  $("facilities").innerHTML =
    data.analysis.survey
      .map((item) => {
        const f = data.facilities.features.find(
          (f) => f.properties["상호명"] === item["상호명"],
        );
        return `<button class="facility" data-facility="${escape(item["상호명"])}" ${f ? "" : "disabled"}><span>${escape(item["상호명"])}</span><span>${escape(item["영업종료"] || "—")}<br>${closingState(item, minutes)}</span></button>`;
      })
      .join("") +
    `<p class="note">17곳 좌표 연결 · 눌러 위치 보기<br>초록: 종료 전(개점 미확인), 회색: 종료·폐업</p>`;
  $("facilities")
    .querySelectorAll("button")
    .forEach((b) =>
      b.addEventListener("click", () => {
        const f = data.facilities.features.find(
          (f) => f.properties["상호명"] === b.dataset.facility,
        );
        if (f) {
          scene.fly(f.geometry.coordinates, 2.8);
          $("location-name").textContent = f.properties["상호명"];
          $("coordinates").textContent = "";
          $("location-description").textContent =
            `${closingState(f.properties, minutes)} · 조사 종료 ${f.properties["영업종료"]} · 2026.09.19 확인`;
          if (innerWidth <= 700) $("explore").classList.remove("open");
        }
      }),
    );
  scene.setFacilities(
    data.facilities.features,
    minutes,
    tab === "relay" && !proposal,
  );
}
function renderMetrics() {
  const s = data.analysis.scenarios[$("scenario").value],
    baseline = data.analysis.consumption["안동_2026"];
  const rows = [
    [
      "방문당 체험·문화 소비",
      (baseline * (1 + s["지표1_증가율"].P50)).toFixed(1),
      "원",
    ],
    ["연간 추가 소비", (s["추가소비합"].P50 / 1e8).toFixed(2), "억 원"],
    [
      "주말 하루 새 저녁 이동",
      Math.round(s["새이동_하루"].P50).toLocaleString(),
      "명",
    ],
  ];
  $("metrics").innerHTML =
    rows
      .map(
        ([label, value, unit]) =>
          `<div class="metric"><span>${label}</span><strong>${value}</strong><small>${unit}</small></div>`,
      )
      .join("") +
    `<p class="note">현재 방문당 ${baseline.toFixed(1)}원 · 모의실험 중앙값<br>추가 소비 모의실험 P5~P95: ${(s["추가소비합"].P5 / 1e8).toFixed(2)}~${(s["추가소비합"].P95 / 1e8).toFixed(2)}억 원<br>모형 가정에 따른 범위이며 통계적 신뢰구간이 아닙니다.</p>`;
}
function renderEvidence() {
  const c = data.analysis.consumption,
    rail = data.analysis.rail.find((p) => p["관광지명"] === "월영교");
  $("evidence").innerHTML =
    `<p class="note"><strong>체험·문화 소비 변화</strong><br>안동시 방문당 ${c["안동_2024"].toFixed(1)} → ${c["안동_2026"].toFixed(1)}원 (${c["안동_변화율"].toFixed(1)}%). 2024→2026년 각 1~8월, 외지인 카드. 개별 시설의 매출을 뜻하지 않습니다.</p><p class="note"><strong>월영교 방문·소비건수</strong><br>방문 점유율 ${rail["방문점유율_pct"]}%, 소비건수 점유율 ${rail["방문객소비건수점유율_pct"]}%. 철도공사 2022.4~6 자료. 서로 다른 집계 체계로 구매 전환율이 아닙니다.</p><p class="note"><strong>시설·시간표</strong><br>주변 시설: 2026.09.19 현장 확인 기록. 개점 시각과 요일별 차이는 미확인입니다. 교통: 팀이 수집한 안동 BIS 시간표. 운행 변경은 해당 기관에서 확인하세요.</p>`;
}
function story() {
  setTab("relay");
  $("story-controls").hidden = false;
  const names = [
    "안동 전역",
    "원도심 식음·체험",
    "저녁 이동",
    "월영교 야간 팝업",
    "연결과 예상 효과",
  ];
  $("story-index").textContent = `${storyIndex + 1} / 5`;
  if (storyIndex === 0) {
    scene.home();
    $("location-name").textContent = names[0];
    $("coordinates").textContent = "실제 지형과 공개 지도 기반";
    $("location-description").textContent =
      "도심과 외곽 관광지를 함께 둘러봅니다.";
  } else if (storyIndex < 4) {
    step = storyIndex - 1;
    renderSteps();
    selected(
      places.find((p) => p.id === steps[step].place),
      true,
      true,
    );
    $("location-name").textContent = names[storyIndex];
    $("location-description").textContent = proposal
      ? steps[step].proposal
      : steps[step].current;
  } else {
    proposal = true;
    $("mode-current").setAttribute("aria-pressed", "false");
    $("mode-proposal").setAttribute("aria-pressed", "true");
    scene.setRelay(true, true);
    scene.fly([128.7445, 36.571], 13);
    renderSteps();
    renderTime();
    $("effects").open = true;
    $("effects").scrollIntoView({ block: "nearest" });
    $("location-name").textContent = names[4];
    $("coordinates").textContent = "안동 이어드림 · 3단계 릴레이";
    $("location-description").textContent =
      "조건부 예상 효과 · 참여율에 따라 달라집니다.";
  }
}
async function init() {
  const started=performance.now(),requests=new AbortController();
  try {
    let done = 0;
    $("progress").max = 10;
    const [
      terrain,
      map,
      boundaries,
      analysis,
      manifest,
      facilities,
      solution,
      district,
      buildings,
      journey,
    ] = await Promise.all(
      [
        "terrain",
        "map",
        "boundaries",
        "analysis",
        "manifest",
        "facilities",
        "solution",
        "district",
        "buildings",
        "journey",
      ].map(async (key) => {
        const value=await loadJSON(`/data/${key}.json`,{
          compressed:["map","district","buildings","journey"].includes(key),
          signal:requests.signal,
        });
        $("progress").value = ++done;
        return value;
      }),
    );
    data = {
      terrain,
      map,
      boundaries,
      analysis,
      manifest,
      facilities,
      solution,
      district,
      buildings,
      journey,
    };
    data.analysis.scenarios=report.scenarios;
    data.analysis.consumption["안동_2026"]=report.baseline.consumption2026;
    data.journey.places=data.journey.places.map(enrichRestaurant);
    places = buildPlaces(map.poi);
    $("loading-text").textContent = "지형에 숲과 마을을 놓는 중";
    const { AtlasScene } = await import("./scene.js");
    await yieldToPage();
    scene = new AtlasScene($("viewport"), data, places, selected, stopTour);
    document.querySelectorAll("[data-district-view]").forEach((b) =>
      b.addEventListener("click", () => {
        stopTour();
        const key = b.dataset.districtView;
        if (key === "overview") {
          overview();
          return;
        }
        scene.setDetailed(true, key);
        document
          .querySelectorAll("[data-district-view]")
          .forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
        const center =
          key === "market"
            ? [128.731, 36.5659]
            : key === "city"
              ? [128.739, 36.569]
              : places.find((place) => place.id === "woryeong").coordinates;
        if (key === "popup")
          scene.select(places.find((place) => place.id === "woryeong"));
        else scene.fly(center, key === "city" ? 9 : 1.45);
        $("location-name").textContent =
          key === "market"
            ? "원도심 거리 상세"
            : key === "city"
              ? "안동 도심과 낙동강"
              : "월영교 권역 상세";
        $("location-description").textContent =
          "실제 건물·도로 좌표 기반 · 차선·보도·가로시설은 추정 표현";
        $("coordinates").textContent = "";
        if (innerWidth <= 700) $("explore").classList.remove("open");
      }),
    );
    $("district-note").textContent =
      `상세 구역 건물 ${district.buildings.length.toLocaleString()}개 · 도로/보행 ${district.roads.length}구간 · 표시 차량 ${scene.district.carCount}대·보행자 ${scene.district.peopleCount}명. 표시 수는 교통량 통계가 아닙니다.`;
    $("district-note").title = $("district-note").textContent;
    $("district-note").textContent =
      "지도·위성 건물 자료 기반 · 이동은 시뮬레이션";
    solutionUI = initSolutionUI(scene, data, () => {
      proposal = true;
      scene.setDetailed(true);
      setTab("relay");
      $("mode-current").setAttribute("aria-pressed", "false");
      $("mode-proposal").setAttribute("aria-pressed", "true");
      renderSteps();
      renderTime();
    });
    mediaUI = initPlaceMedia(scene, data.journey.places, mediaData);
    journeyUI = initJourneyUI(
      scene,
      data,
      () => {
        stopTour();
        if (tab !== "journey") setTab("journey");
      },
      mediaUI,
    );
    scene.heritageExplorer=new HeritageExplorer(scene,mediaUI);
    $("open-place-photos").onclick = () => {
      const aliases = { woryeong: "bridge", market: "downtown" };
      const p =
        mediaPlace &&
        (data.journey.places.find(
          (p) => p.id === (aliases[mediaPlace.id] || mediaPlace.id),
        ) ||
          mediaPlace);
      mediaUI.open(p || data.journey.places.find((p) => p.id === "bridge"));
    };
    initSelectUI();
    $("open-journey").addEventListener("click", () => {
      setTab("journey");
      $("explore").classList.add("open");
    });
    $("places").innerHTML = places
      .map(
        (p, i) =>
          `<div class="place-row-shell"><button class="place-row" data-place="${p.id}"><span class="number">${String(i + 1).padStart(2, "0")}</span><span class="place-name">${p.name}<small>(${p.en})</small></span><i data-lucide="arrow-up-right"></i></button><a class="landmark-relay" href="${relayEntryFor(p).href}" aria-label="${p.name} 릴레이 체험" title="${relayEntryFor(p).detail}">체험 ↗</a></div>`,
      )
      .join("");
    $("place-count").textContent = `${places.length}곳 (places)`;
    $("places")
      .querySelectorAll("button")
      .forEach((b) =>
        b.addEventListener("click", () =>
          selected(places.find((p) => p.id === b.dataset.place)),
        ),
      );
    boundaries.features.forEach((f) => {
      const o = document.createElement("option");
      o.value = f.properties.adm_cd2;
      o.textContent = f.properties.adm_nm.replace("경상북도 안동시 ", "");
      $("district").append(o);
    });
    $("district").addEventListener("change", () => {
      scene.setDetailed(false);
      stopTour();
      const f = boundaries.features.find(
        (f) => f.properties.adm_cd2 === $("district").value,
      );
      scene.setDistrict(f);
      if (f) {
        $("location-name").textContent = f.properties.adm_nm.replace(
          "경상북도 ",
          "",
        );
        $("location-description").textContent =
          "선택한 행정구역의 경계를 표시합니다.";
        $("coordinates").textContent = "SGIS · vuski/admdongkor · 2026.07.01";
      } else overview();
    });
    $("boundaries").addEventListener(
      "change",
      () => (scene.boundaryGroup.visible = $("boundaries").checked),
    );
    document.querySelectorAll("[data-tab]").forEach((b, i, buttons) => {
      b.addEventListener("click", () => setTab(b.dataset.tab));
      b.addEventListener("keydown", (e) => {
        if (["ArrowLeft", "ArrowRight"].includes(e.key)) {
          e.preventDefault();
          const next = buttons[(i + (e.key === "ArrowRight" ? 1 : buttons.length - 1)) % buttons.length];
          setTab(next.dataset.tab);
          next.focus();
        }
      });
    });
    document.querySelectorAll("[data-weather]").forEach((b) =>
      b.addEventListener("click", () => {
        scene.setMode(b.dataset.weather);
        document
          .querySelectorAll("[data-weather]")
          .forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      }),
    );
    $("season").addEventListener("change", () =>
      scene.setSeason($("season").value),
    );
    for (const [id, value] of [
      ["mode-current", false],
      ["mode-proposal", true],
    ])
      $(id).addEventListener("click", () => {
        proposal = value;
        $("mode-current").setAttribute("aria-pressed", String(!proposal));
        $("mode-proposal").setAttribute("aria-pressed", String(proposal));
        scene.setRelay(true, proposal);
        renderSteps();
        renderTime();
        $("location-description").textContent = proposal
          ? "点선은 제안 연결입니다. 운영 주체·부지·배차는 미확정입니다.".replace(
              "点",
              "점",
            )
          : "점선은 두 권역의 위치 관계이며 실제 이동 경로가 아닙니다.";
      });
    $("time").addEventListener("input", renderTime);
    $("scenario").addEventListener("change", renderMetrics);
    renderSteps();
    renderTime();
    renderMetrics();
    renderEvidence();
    $("street-focus").addEventListener("click", () => {
      stopTour();
      scene.setDetailed(true, "market");
      scene.fly([128.7321024, 36.5660271], 0.85);
      $("location-name").textContent = "서동문로의 사람과 차량";
      $("coordinates").textContent = "";
      $("location-description").textContent =
        "공개 도로·보도 위 미니어처 생활 풍경 · 실제 교통량 아님";
      if (innerWidth <= 700) $("explore").classList.remove("open");
    });
    $("park-focus").addEventListener("click", () => {
      stopTour();
      scene.setDetailed(true, "market");
      const park = places.find((p) => p.id === "ungbu");
      scene.fly(park?.coordinates || [128.733, 36.566], 0.85);
      $("location-name").textContent = "웅부공원 산책";
      $("coordinates").textContent = "";
      $("location-description").textContent =
        "실제 공원 경계 위 산책 공간 · 내부 길·조경은 미니어처 연출";
      if (innerWidth <= 700) $("explore").classList.remove("open");
    });
    $("boats-focus").disabled = !scene.cityDetail.boats.length;
    $("boats-focus").addEventListener("click", () => {
      scene.setDetailed(true, "popup");
      scene.cityDetail.focusBoats();
      $("location-name").textContent = "월영교 수상 풍경";
      $("coordinates").textContent = "월영교 주변 · 수상 풍경 시연";
      $("location-description").textContent =
        "배와 탑승객의 미니어처 연출 · 실제 운항 정보가 아닙니다.";
    });
    $("city-motion").addEventListener("click", () => {
      const active = (scene.cityDetail.running = !scene.cityDetail.running);
      scene.district.running = active;
      $("city-motion").setAttribute("aria-pressed", String(active));
      $("city-motion").textContent = active
        ? "풍경 움직임 켜짐"
        : "풍경 움직임 멈춤";
    });
    $("home").addEventListener("click", overview);
    $("zoom-in").addEventListener("click", () => {
      stopTour();
      scene.zoom(0.75);
    });
    $("zoom-out").addEventListener("click", () => {
      stopTour();
      scene.zoom(1.33);
    });
    $("north").addEventListener("click", () => {
      stopTour();
      scene.north();
    });
    $("view-mode").addEventListener("click", () => {
      stopTour();
      scene.setFlat(!scene.flat);
      $("view-mode").setAttribute("aria-pressed", String(scene.flat));
    });
    $("toggle-labels").addEventListener("click", () => {
      scene.labelsVisible = !scene.labelsVisible;
      $("toggle-labels").setAttribute(
        "aria-pressed",
        String(scene.labelsVisible),
      );
    });
    $("tour").addEventListener("click", () => {
      if (tourTimer) {
        stopTour();
        return;
      }
      if (scene.reduced) {
        selected(places[tourIndex++ % places.length]);
        return;
      }
      const advance = () => {
        const p = places[tourIndex++ % places.length];
        selected(p);
        $("tour").setAttribute("aria-pressed", "true");
        tourTimer = setInterval(advance, 6500);
      };
      advance();
    });
    $("fullscreen").addEventListener("click", async () => {
      try {
        if (document.fullscreenElement) await document.exitFullscreen();
        else await document.documentElement.requestFullscreen();
      } catch {
        $("fullscreen").title =
          "현재 브라우저에서 전체 화면을 사용할 수 없습니다.";
      }
    });
    $("story").addEventListener("click", () => {
      storyIndex = 0;
      story();
    });
    $("story-next").addEventListener("click", () => {
      storyIndex = Math.min(4, storyIndex + 1);
      story();
    });
    $("story-prev").addEventListener("click", () => {
      storyIndex = Math.max(0, storyIndex - 1);
      story();
    });
    $("story-stop").addEventListener("click", () => {
      storyIndex = -1;
      $("story-controls").hidden = true;
    });
    $("data-summary").innerHTML =
      `<div class="data-counts">24개 읍면동 · ${places.length}개 장소<br>표고 ${manifest.terrain.samples.toLocaleString()}점<br>타일 건물 윤곽 ${map.building.reduce((n, f) => n + (f.geometry.type === "MultiPolygon" ? f.geometry.coordinates.length : 1), 0).toLocaleString()}개 · 묶음 ${manifest.counts.building.toLocaleString()}개<br>도로·보행 구간 ${manifest.counts.transportation.toLocaleString()}개<br>위성 연구 건물 보충 ${buildings.features.length.toLocaleString()}개<br>도심 상세 건물 ${district.buildings.length.toLocaleString()}개 · 표고 ${district.terrain.heights.length.toLocaleString()}점<br>외곽 상세 ${scene.regions.regions.length}개 구역 · 약18m 간격 표고<br>안동역·터미널, 하회마을·부용대, 병산서원, 도산서원, 봉정사와 읍면 지역</div><p class="note">상세 자료는 확대하거나 장소를 선택할 때 구역별로 불러옵니다. 타일·구역 경계 중복과 미등록 건물이 있어 실제 고유 건물 수와 다릅니다. 미수록 건물을 임의로 생성하지 않았습니다. 지형의 주변 여유 범위에는 인접 지역 일부가 포함됩니다.</p>`;
    $("sources").innerHTML =
      manifest.sources
        .filter((s) => s.url.startsWith("https"))
        .map(
          (s) =>
            `<div class="source-row"><a href="${escape(s.url.includes("{z}") ? "https://openfreemap.org/" : s.url)}" target="_blank" rel="noreferrer">${escape(s.name)}</a><br>${escape(s.license)}${s.date ? ` · ${escape(s.date)}` : ""}</div>`,
        )
        .join("") +
      `<div class="source-row">안동 이어드림 팀 분석 · 2026.09.28<br>기존 수치.json·시뮬레이션결과.json 연결</div>`;
    refreshIcons();
    $("loading").hidden = true;
    scene.setDetailed(true, "city");
    scene.fly([128.739, 36.569], 9, true);
    $("location-name").textContent = "안동 도심과 낙동강";
    $("location-description").textContent =
      "원도심에서 월영교까지, 건물과 강변을 가까이 탐색하세요.";
    document.body.dataset.ready = "true";
    document.dispatchEvent(new Event('app-ready'));
    document.body.dataset.loadMs=String(Math.round(performance.now()-started));
    interactiveSections.forEach((el) => (el.inert = false));
    if (new URLSearchParams(location.search).has("journey")) {
      setTab("journey");
      $("explore").classList.add("open");
    }
    if (new URLSearchParams(location.search).has("showcase")) {
      $("explore").classList.add("open");
      setTab("relay");
      $("effects").open = true;
    }
    initLayoutModes({catalog:data.journey.places,mediaData,media:mediaUI,setTab,refreshIcons,frameJourney:()=>journeyUI.frame(),
      locate:p=>selected(places.find(x=>x.id===({bridge:'woryeong',downtown:'market'}[p.id]||p.id))||p)});
    const loadLayers=async()=>{
      const previous=document.getElementById('tourism-load-error');previous?.remove();
      try {scene.tourismLayers=await initTourismLayers(scene);}
      catch(error) {
        console.warn('Tourism layers unavailable',error);
        const notice=document.createElement('div');notice.id='tourism-load-error';notice.setAttribute('role','status');
        notice.textContent='혜택·팝업 지도 자료를 불러오지 못했습니다. ';
        const retry=document.createElement('button');retry.textContent='다시 불러오기';retry.onclick=loadLayers;notice.append(retry);
        $('explore').append(notice);
      }
    };
    void loadLayers();
  } catch (error) {
    requests.abort();
    document.dispatchEvent(new Event('app-load-handled'));
    console.error(error);
    $("loading").hidden = false;
    $("loading-text").textContent =
      `지도를 준비하지 못했습니다. ${error.message}`;
    $("retry").hidden = false;
    $("progress").hidden = true;
  }
}
$("retry").addEventListener("click", () => location.reload());
$("open-explore").addEventListener("click", () =>
  $("explore").classList.toggle("open"),
);
$("close-explore").addEventListener("click", () =>
  $("explore").classList.remove("open"),
);
for (const id of ["info", "credits"])
  $(id).addEventListener("click", () => {
    stopTour();
    $("about").showModal();
  });
$("close-about").addEventListener("click", () => $("about").close());
$("about").addEventListener("click", (e) => {
  if (e.target === $("about")) {
    const r = $("about").getBoundingClientRect();
    if (
      e.clientX < r.left ||
      e.clientX > r.right ||
      e.clientY < r.top ||
      e.clientY > r.bottom
    )
      $("about").close();
  }
});
init();
