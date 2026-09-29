import report from '../public/data/report-effects.json' with {type:'json'};
import { escapeHtml as esc } from './place-media-model.js';
export { report };
export function reportSummary(name='기준') {
  const s=report.scenarios[name];
  if(!s) throw new Error('Unknown report scenario');
  return {name, participation:s.참여율, additionalConsumption:s.추가소비합,
    annualExperiences:s.체험결제합.P50, newEvening:s.새이동_하루.P50,
    popupVisitors:s.팝업_하루.P50, recovery:s.격차기여율.P50,
    consumption:report.baseline.consumption2026*(1+s.지표1_증가율.P50),
    residentMonthly:report.resident.afterMonthly};
}
const number=(n,d=0)=>n.toLocaleString('ko-KR',{maximumFractionDigits:d,minimumFractionDigits:d});
export function reportComparisonHTML() {
  const names=Object.keys(report.scenarios),values=names.map(reportSummary);
  const rows=[
    ['참여율 가정',...values.map(s=>number(s.participation*100)+'%')],
    ['연간 추가 소비',...values.map(s=>number(s.additionalConsumption.P50/1e8,2)+'억 원')],
    ['소비 모의실험 범위 · P5–P95',...values.map(s=>number(s.additionalConsumption.P5/1e8,2)+'–'+number(s.additionalConsumption.P95/1e8,2)+'억 원')],
    ['체험 결제 · 연',...values.map(s=>number(s.annualExperiences)+'건')],
    ['새 저녁 이동 · 주말 하루',...values.map(s=>number(s.newEvening)+'명')],
    ['방문당 체험·문화 소비',...values.map(s=>number(s.consumption,1)+'원')],
    ['회복 목표 격차 기여',...values.map(s=>number(s.recovery*100,1)+'%')],
  ];
  return `<section class="report-comparison"><h3>보고서 기대효과 · 83곳 운영 가정</h3><p class="note">시설 배치 안과 별도로, 참여율을 바꾼 비교입니다.</p><div class="comparison-scroll" tabindex="0" role="region" aria-label="보고서 참여율별 기대효과 표"><table><thead><tr><th>중앙 추정 · P50</th>${names.map(n=>`<th>${n}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map((v,i)=>`<${i?'td':'th'}>${esc(v)}</${i?'td':'th'}>`).join('')}</tr>`).join('')}</tbody></table></div><p class="note">${report.period}. ${report.method}. 범위는 신뢰구간이 아닙니다. 개인 코스·혜택 배치를 바꿔도 이 추정은 변하지 않습니다.</p><p class="note">주민증 조건형 혜택 병행 시 월 ${number(report.resident.currentMonthly)} → ${number(report.resident.afterMonthly)}건. 별도 회귀 추정으로 참여율 2·4·10%에 따라 배수로 늘리지 않습니다. QR 인증과 합산하지 않습니다.</p><details><summary>수치 출처와 계산 기준</summary><p class="note">팝업 부스·차량 대수와 배차는 미확정입니다. 지도 시설은 위치를 설명하는 모형입니다.</p>${report.sources.map(s=>`<p class="note">${esc(s.path)}</p>`).join('')}<a href="/data/report-effects.json" target="_blank" rel="noopener">출처·원수치 JSON ↗</a></details></section>`;
}
