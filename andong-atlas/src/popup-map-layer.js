import {POPUP_BOOTHS,popupMapPoint,popupLayout} from './relay-popup-layout.js';

export const popupBooth = id => POPUP_BOOTHS.find(b=>b.id===id)||null;
export function popupBoothHref(id){return `?experience=relay&visit=popup&at=popup${popupBooth(id)?'&booth='+encodeURIComponent(id):''}`;}
export function popupSite(model){
 const coordinates=model.stages.find(p=>p.relayStage===3)?.coordinates;
 return coordinates?{id:'popup-site',kind:'popup',popupSite:true,proposed:true,coordinates:[...coordinates],name:'월영 밤마당',description:'먹거리 · 공예 · 차 · 놀이, 9개 부스가 이어지는 강변 팝업',note:'기획 배치 시안 · 실제 설치 위치와 운영은 미확정입니다.'}:null;
}
// The geographic anchor denotes a proposed area; the metre layout is shared with the playable scene.
export function popupBoothCoordinate(site,x,z){return [site.coordinates[0]+x/(111320*Math.cos(site.coordinates[1]*Math.PI/180)),site.coordinates[1]-z/111320];}
export function popupEntryStation(visit,id){return visit==='popup'&&popupBooth(id)?popupLayout().stations[id]:null;}
export function popupPlanHTML(selected=null,{walking=false,position=null}={}){
 const you=position?popupMapPoint(position[0],position[2]):null;
 const valid=popupBooth(selected),attrs=b=>walking?`data-popup-go="${b.id}"`:`data-popup-booth="${b.id}"`;
 return `<div class="popup-layer-plan" role="group" aria-label="야간 팝업 9개 부스 배치도"><svg viewBox="0 0 100 71" preserveAspectRatio="none" aria-hidden="true"><rect width="100" height="71" rx="3" fill="#203e3b"/><path d="M0 0H100V7H0Z" fill="#477780"/><path d="M47 71V15M4 42H96M5 16H95" stroke="#61766b" stroke-width="5" fill="none"/><rect x="42" y="12" width="16" height="7" rx="1" fill="#b5a18a"/>${POPUP_BOOTHS.map(b=>{const p=popupMapPoint(b.x,b.z);return `<rect data-booth-shape x="${p.x-4}" y="${p.y*.71-2}" width="8" height="4" rx=".6" fill="${b.color}"/>`;}).join('')}</svg>${you?`<span class="popup-you" style="left:${you.x}%;top:${you.y}%" aria-label="현재 위치" title="현재 위치"></span>`:''}<span class="popup-plan-river">월영교 · 수변</span><span class="popup-plan-stage">달빛 무대</span>${POPUP_BOOTHS.map((b,i)=>{const p=popupMapPoint(b.x,b.z);return `<button type="button" ${attrs(b)} style="left:${p.x}%;top:${p.y}%" aria-label="${b.name} ${walking?'부스로 걷기':'부스 선택'}" aria-pressed="${b.id===valid?.id}">${i+1}</button>`;}).join('')}</div><div class="popup-layer-legend">${POPUP_BOOTHS.map((b,i)=>`<button type="button" ${attrs(b)} aria-pressed="${b.id===valid?.id}"><b>${i+1}</b>${b.name}</button>`).join('')}</div>`;
}
export function popupDetailsHTML(selected=null){
 const b=popupBooth(selected);
 const descriptions={food:'찜닭을 주문하고 직접 맛보세요.',grill:'그릴에서 구운 간고등어를 맛보세요.',apple:'사과 먹거리를 고르고 맛보세요.',craft:'탈과 공예품을 둘러보세요.',print:'엽서에 도장을 찍어 나만의 기록을 만드세요.',tea:'강변에서 따뜻한 차를 맛보세요.',sikhye:'안동 식혜를 주문하고 맛보세요.',game:'항아리를 조준해 투호를 던져보세요.',guide:'밤마당을 둘러보고 가고 싶은 부스를 고르세요.'};
 const detail=`<div class="popup-booth-detail" aria-live="polite"><strong>${b?b.name:'부스를 골라 둘러보세요'}</strong><p>${b?descriptions[b.id]:'먹거리·공예·차·놀이를 1인칭으로 체험해요.'}</p><a class="place-relay-entry" href="${popupBoothHref(b?.id)}"><strong>${b?'이 부스에서 체험하기':'야간 팝업 들어가기'} <span aria-hidden="true">↗</span></strong></a></div>`;
 return `<span class="tourism-eyebrow">야간 팝업 · 9개 부스</span><h3>월영 밤마당</h3><p class="tourism-note">기획 배치 시안 · 실제 설치 위치와 운영은 미확정입니다.</p>${b?detail:''}${popupPlanHTML(selected)}${b?'':detail}`;
}
