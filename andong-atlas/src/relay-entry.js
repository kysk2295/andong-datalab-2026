// Shared, explicit destinations: a related prototype is not an on-site recreation.
export const RELAY_VISITS = {market:0,meal:1,workshop:3,transit:4,bridge:5,popup:6};
export function validRelayVisit(value){return Object.hasOwn(RELAY_VISITS,value)?value:null;}
export function relayHref(visit,program){
 const q=new URLSearchParams({experience:'relay'});
 if(validRelayVisit(visit)){q.set('visit',visit);q.set('at',visit);}
 else q.set('play','1');
 if(visit==='workshop'&&['mask','tea','soju'].includes(program))q.set('program',program);
 return '?'+q;
}
export function relayEntryFor(place={}){
 const id=String(place.id||''),name=String(place.name||''),kind=place.kind;
 let visit=null,program=null,label='릴레이 체험하기',detail='식사부터 월영교의 밤까지 · 진행 중인 여정 이어가기';
 if(kind==='popup'||id==='popup'||id==='relay-3'){visit='popup';label='야간 팝업 체험';detail='월영 밤마당 · 먹거리와 놀이';}
 else if(place.relayStage===2||id==='transport'){visit='transit';label='저녁 이동 체험';detail='원도심에서 월영교로 · 연결차량 시연';}
 else if(place.relayStage===3||['bridge','woryeong','folk'].includes(id)||kind==='bridge'||/월영교|월영정/.test(name)){visit='bridge';label='월영교 릴레이 체험';detail='1인칭으로 다리를 걷고 야간 팝업으로';}
 else if(kind==='restaurant'){visit='meal';label='식사 릴레이 체험';detail='원도심 시연 식당 · 주문부터 영수증 인증까지';}
 else if(place.relayStage===1||['market','downtown','station','ungbu'].includes(id)){visit='market';label='찜닭골목 릴레이 체험';detail='원도심 골목에서 식당으로 들어가기';}
 else if(kind==='experience'||kind==='heritage'||/^(hahoe|dosan|bongjeong)(:|$)/.test(id)||/탈|공방|소주|국화차/.test(name)){
  visit='workshop';program=/소주/.test(name+id)?'soju':/국화차|찻|다례/.test(name+id)?'tea':'mask';label='전통 체험 릴레이';detail='원도심 제안 공방 · 탈 꾸미기·국화차·전통주';
 }
 return {visit,program,label,detail,href:relayHref(visit,program)};
}
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function relayEntryHTML(place,extraClass=''){
 const e=relayEntryFor(place);
 return `<a class="place-relay-entry ${esc(extraClass)}" href="${esc(e.href)}" aria-label="${esc(place?.name||'이 장소')}에서 ${esc(e.label)}"><strong>${esc(e.label)} <span aria-hidden="true">↗</span></strong><small>${esc(e.detail)}</small></a>`;
}
export function relayHubHTML(){return `<section class="atlas-relay-hub" aria-label="릴레이 체험 바로가기"><a class="relay-hub-primary" href="${relayHref()}"><span>직접 걸으며 즐기는 안동</span><strong>1인칭 릴레이 체험 <b aria-hidden="true">↗</b></strong><small>처음 시작하거나 내 여행 이어가기</small></a><div class="relay-hub-shortcuts">${[['market','찜닭골목'],['workshop','전통 체험'],['bridge','월영교'],['popup','야간 팝업']].map(([id,name])=>`<a href="${relayHref(id)}">${name}<span aria-hidden="true">↗</span></a>`).join('')}</div></section>`;}
