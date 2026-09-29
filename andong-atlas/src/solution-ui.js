import {relayEntryHTML} from './relay-entry.js';
import {report, reportComparisonHTML} from "./report-effects.js";
const metrics = [
  ["하루_택시운행", "4인 택시 환산 필요 운행", "회 / 주말 하루", 1],
  ["연결_문보트", "연결 문보트 추가 소비", "억 원 / 연", 1e-8],
  ["연결_팝업", "연결 팝업 추가 소비", "억 원 / 연", 1e-8],
  ["체험총지출", "체험 총지출 (추가 소비와 별도)", "억 원 / 연", 1e-8],
  ["팝업총지출", "팝업 총지출 (추가 소비와 별도)", "억 원 / 연", 1e-8],
  ["인증_월", "릴레이 인증", "건 / 월", 1],
  ["체험결제합", "체험 결제 합계", "건 / 연", 1],
  ["낮체험", "낮 체험 결제", "건 / 연", 1],
  ["문보트", "문보트 결제", "건 / 연", 1],
  ["하루_이동", "저녁 이동", "명 / 주말 하루", 1],
  ["새이동_하루", "추가 저녁 이동", "명 / 주말 하루", 1],
  ["팝업_하루", "팝업 이용", "명 / 주말 하루", 1],
  ["체험추가소비", "체험 추가 소비", "억 원 / 연", 1e-8],
  ["팝업추가소비", "팝업 추가 소비", "억 원 / 연", 1e-8],
  ["추가소비합", "총 추가 소비", "억 원 / 연", 1e-8],
  ["연결효과", "단계를 이어서 생기는 소비", "억 원 / 연", 1e-8],
  ["연결비중", "추가 소비 중 연결 몫", "%", 100],
  ["지표1_증가율", "방문당 체험·문화 소비 증가", "%", 100],
  ["격차기여율", "회복 목표 격차를 메우는 비율", "%", 100],
  ["지표2_강남동", "강남동 관광소비 증가", "%", 100],
];
const number = (n, f = 1) =>
  (n * f).toLocaleString("ko-KR", { maximumFractionDigits: f === 1 ? 0 : 2 });
export function initSolutionUI(scene, data, activate) {
  const $ = (id) => document.getElementById(id);
  let plan = "기본안",
    focus = "popup";
  const model = scene.solution;
  const current = () => report.scenarios[$("scenario").value];
  function render() {
    const s = current();
    $("solution-experience").innerHTML=relayEntryHTML({id:focus,name:"이 거점"});
    $("solution-title").textContent = `${$("scenario").value} · 참여율 ${s["참여율"] * 100}%`;
    document.querySelectorAll("[data-plan]").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.plan===plan)));
    $("plan-assumptions").textContent = `보고서 기준: 식당 83곳 · 12개월 환산. 지도 배치는 ${plan}입니다. 팝업·차량 수량과 배차는 미확정이며 지도 모형은 설치 수량·축척 재현이 아닙니다.`;
    $("solution-report-scenario").value=$("scenario").value;
    $("solution-highlights").innerHTML = [
      ["연간 추가 소비", `${number(s["추가소비합"].P50, 1e-8)}억`],
      ["팝업 이용 / 주말 하루", `${number(s["팝업_하루"].P50)}명`],
      ["체험 결제 / 연", `${number(s["체험결제합"].P50)}건`],
    ]
      .map(
        ([label, value]) =>
          `<div><span>${label}</span><strong>${value}</strong></div>`,
      )
      .join("");
    $("solution-metrics").innerHTML = metrics
      .filter(([key]) => s[key])
      .map(
        ([key, label, unit, f]) =>
          `<tr><th scope="row">${label}<small>${unit}</small></th><td>${number(s[key].P50, f)}<small>${number(s[key].P5, f)} ~ ${number(s[key].P95, f)}</small></td></tr>`,
      )
      .join("");
    const baseline = data.analysis.consumption["안동_2026"],
      after = baseline * (1 + s["지표1_증가율"].P50);
    $("solution-recovery").innerHTML =
      `<span>방문당 체험·문화 소비</span><strong>${baseline.toFixed(1)} → ${after.toFixed(1)}원</strong><progress max="100" value="${Math.min(100, s["격차기여율"].P50 * 100)}"></progress><small>회복 목표 격차의 ${number(s["격차기여율"].P50, 100)}% · 목표 도달 모의실험 비율 ${number(s["목표도달확률"], 100)}%</small>`;
    const r = report.resident, added = r.addedMonthly;
    $("resident-detail").innerHTML =
      `<p>영수증 QR 인증은 누구나 참여할 수 있는 경로입니다. <strong>QR 인증 건수를 주민증 이용 실적으로 세지 않습니다.</strong></p><ol><li>원도심 식음 이용 후 영수증 QR 인증</li><li>연결 체험에서 10% 할인</li><li>18:30~21:00 저녁 이동 연결 제안</li><li>월영교 문보트·팝업 이용</li></ol><p>디지털 관광주민증 조건형 혜택을 병행할 경우:</p><div class="resident-number">월 ${number(r.currentMonthly)} → ${number(r.afterMonthly)}건<small>추정 추가 ${number(added)}건 · +${number(added / r.currentMonthly, 100)}%</small></div><p class="note">2026년 1~8월 월평균과 83곳 운영 시 회귀 추정. 주민증 혜택 협의 전의 조건부 예측이며 QR 참여율·지도 배치와 별개입니다.</p>`;
    $("plan-comparison").innerHTML = reportComparisonHTML();
    $("solution-detail").textContent =
      focus === "popup"
        ? "월영교 권역에 로컬 푸드·공예·체험·관광 안내 부스를 제안 배치했습니다. 표시한 부스는 위치 설명용 예시이며 실제 설치 수량은 미확정입니다."
        : focus === "market"
          ? "식당 이용을 QR 인증과 체험 할인으로 연결하는 거점 모형입니다. 실제 가맹 업소와 설치 위치는 미확정입니다."
          : "차량은 내려받은 도로망을 따라 움직입니다. 실제 112번 경로나 확정 셔틀 노선이 아니며 차종·대수·속도는 연출입니다.";
    $("solution-coordinate").textContent =
      focus === "transport"
        ? data.solution.routeNote
        : `${data.solution.sites.find((x) => x.id === focus).coordinates.join(", ")} · ${data.solution.sites.find((x) => x.id === focus).note}`;
  }
  function sync(visible, minutes) {
    $("solution-panel").hidden = !visible;
    document.body.classList.toggle("solution-open", visible);
    model.configure({ visible, expanded: plan === "확대안", minutes });
    scene.routeGroup.visible = !visible;
    if (scene.facilityGroup)
      scene.facilityGroup.visible =
        !visible &&
        document.getElementById("tab-relay").getAttribute("aria-selected") ===
          "true";
    $("animation-status").textContent =
      minutes >= 1110 && minutes <= 1260
        ? (model.running && !scene.reduced ? "운영 시간 안 · 이동·이용 장면 재생" : "운영 시간 안 · 장면 일시정지")
        : "운영 시간 밖 · 이동·이용 장면 멈춤";
  }
  function chooseSite(id) {
    if (!model.group.visible) activate();
    focus = id;
    model.focus(id);
    render();
    if (innerWidth <= 700) {
      document.getElementById("explore").classList.remove("open");
      $("solution-panel").classList.add("folded");
      $("solution-fold").textContent = "효과 펼치기";
      $("solution-fold").setAttribute("aria-expanded", "false");
    }
  }
  document.querySelectorAll("[data-plan]").forEach((b) =>
    b.addEventListener("click", () => {
      plan = b.dataset.plan;
      $("effects").open = false;
      activate();
      render();
      document.querySelector(".solution-body").scrollTop = 0;
      chooseSite("popup");
    }),
  );
  document
    .querySelectorAll("[data-site]")
    .forEach((b) =>
      b.addEventListener("click", () => chooseSite(b.dataset.site)),
    );
  $("follow-bus").addEventListener("click", () => {
    chooseSite("transport");
    model.follow = true;
  });
  $("solution-pause").addEventListener("click", () => {
    model.running = !model.running;
    $("solution-pause").textContent = model.running
      ? "장면 일시정지"
      : "장면 재생";
    $("solution-pause").setAttribute("aria-pressed", String(!model.running));
    sync(model.group.visible, Number($("time").value));
  });
  $("solution-fold").addEventListener("click", () => {
    const folded = $("solution-panel").classList.toggle("folded");
    $("solution-fold").textContent = folded ? "효과 펼치기" : "효과 접기";
    $("solution-fold").setAttribute("aria-expanded", String(!folded));
  });
  $("scenario").addEventListener("change", () => {
    if(!model.group.visible)activate();
    render();
  });
  $("solution-report-scenario").onchange=()=>{
    $("scenario").value=$("solution-report-scenario").value;
    $("scenario").dispatchEvent(new Event('change',{bubbles:true}));
  };
  model.onPick = chooseSite;
  render();
  return { sync, render, chooseSite };
}
