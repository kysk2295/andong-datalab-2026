import info from '../public/data/restaurant-info.json' with {type:'json'};
import {escapeHtml as esc} from './place-media-model.js';
export function restaurantInfo(place){return place.kind==='restaurant'?info.records[place.id]:null;}
export function enrichRestaurant(place){
  const r=restaurantInfo(place);if(!r)return place;
  const copy={...place};
  if(r.areaHours){delete copy.open;delete copy.close;copy.hours='점포별 영업시간 확인 필요';}
  if(r.hours){
    copy.hours=r.hours+(r.restDays?' · 휴무: '+r.restDays:'');
    delete copy.open;delete copy.close;
    if(Number.isFinite(r.open)&&Number.isFinite(r.close)){copy.open=r.open;copy.close=r.close;}
  }
  return copy;
}
export function restaurantFactsHTML(place){
  const r=restaurantInfo(place);if(!r)return '';
  return `<section class="restaurant-practical"><h3>방문 전 확인</h3><p>${r.hours?'개별 영업시간 수록 · 휴무·임시 변경은 방문 전 확인':'개별 영업시간 미확인'}${r.areaHours?`<br>${esc(r.area||'골목')} 안내 ${esc(r.areaHours)} · 개별 점포 시간과 다릅니다.`:''}</p><div>${r.phone?`<a href="tel:${esc(r.phone.replace(/[^0-9+]/g,''))}">전화 문의 ${esc(r.phone)}</a>`:''}<a href="https://map.kakao.com/link/search/${encodeURIComponent('안동 '+place.name+' 주차')}" target="_blank" rel="noopener">주변 주차장 찾기 ↗</a></div>${r.source?`<a href="${esc(r.source)}" target="_blank" rel="noopener">개별 영업정보 출처 ↗</a>`:r.phoneSource?`<a href="${esc(r.phoneSource)}" target="_blank" rel="noopener">업소 연락처 출처 ↗</a>`:''}<small class="food-source-status">${r.hours?`${esc(r.provider)} · 수집 ${r.collectedAt}${r.checkedAt?' · 공식 웹 재확인 '+r.checkedAt:''}`:r.phone?'안동시 업소 목록 · 수집 '+r.phoneCollectedAt:'개별 안내 자료 확인 필요'}</small></section>`;
}
