import {popupSite,popupDetailsHTML,popupBooth} from './popup-map-layer.js';
import {relayEntryHTML} from './relay-entry.js';
import './relay-entry.css';
import './tourism-map.css';
import {MAP_LAYER_KEY,layerState,visibleMapPlaces,fitMapBounds,projectMapPoint,clusterMapPlaces,mapPlaceLayer,layerCoordinates} from './tourism-map-model.js';
export const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let dataPromise;
export function loadTourismMap() {
  if(!dataPromise)dataPromise=fetch('/data/tourism-map.json').then(r=>{if(!r.ok)throw Error('지도 자료를 불러오지 못했습니다.');return r.json();}).catch(e=>{dataPromise=null;throw e;});
  return dataPromise;
}
export function readLayers(defaults) {try{return layerState(localStorage.getItem(MAP_LAYER_KEY),defaults);}catch{return layerState(null,defaults);}}
export function saveLayers(state) {try{localStorage.setItem(MAP_LAYER_KEY,JSON.stringify(state));}catch{}}
export function boothToggleHTML(state){return `<label class="tourism-booth-toggle"><input type="checkbox" role="switch" data-layer="booths" ${state.booths?'checked':''}><i aria-hidden="true"></i><span>야간 팝업 부스</span><small>9</small></label>`;}
export function controlsHTML(state) {
  return `<div class="tourism-switches" role="group" aria-label="지도에 표시할 정보"><label><input type="checkbox" role="switch" data-layer="benefits" ${state.benefits?'checked':''}><i aria-hidden="true"></i><span>관광주민증 혜택업체</span></label><label><input type="checkbox" role="switch" data-layer="route" ${state.route?'checked':''}><i aria-hidden="true"></i><span>릴레이 1·2·3단계 연결선</span></label>${boothToggleHTML(state)}</div>`;
}
export function stageButtonsHTML(model) {return `<div class="tourism-stages" aria-label="릴레이 단계">${model.stages.map(p=>`<button type="button" data-tourism-place="${p.id}"><b>${p.relayStage}</b><span>${esc(p.name)}</span></button>`).join('')}</div>`;}
export function placeDetailsHTML(p) {
  if(p.popupSite)return popupDetailsHTML();
  if(p.relayStage)return `<span class="tourism-eyebrow">릴레이 ${p.relayStage}단계 · ${esc(p.area)}</span><h3>${esc(p.name)}</h3><p>${esc(p.description)}</p><p class="tourism-note">${esc(p.note)}</p>${relayEntryHTML(p)}`;
  return `<span class="tourism-eyebrow">디지털 관광주민증 · ${p.coordinates?'지도 위치 연결':'좌표 확인 전'}</span><h3>${esc(p.name)}</h3><p class="tourism-benefit">${esc(p.benefit)}</p><dl>${p.address?`<dt>주소</dt><dd>${esc(p.address)}</dd>`:''}${p.hours?`<dt>영업시간</dt><dd>${esc(p.hours)}</dd>`:''}</dl><p class="tourism-note">${esc(p.benefitSource)}<br>수집 당시의 혜택입니다. 방문 전 할인 조건과 운영 여부를 확인하세요.</p>${!p.coordinates?'<p class="tourism-note">확인되지 않은 위치에는 지도 표식을 만들지 않았습니다.</p>':''}${relayEntryHTML(p)}`;
}
export function benefitListHTML(model) {
  return `<p class="tourism-note">지도 위치 ${model.benefits.length}곳 · 좌표 확인 전 ${model.unlocated.length}곳</p><div class="tourism-benefit-list">${[...model.benefits,...model.unlocated].map(p=>`<button type="button" data-tourism-place="${p.id}"><span>${esc(p.name)}</span><small>${p.coordinates?'지도에서 보기':'혜택 보기 · 좌표 확인 전'}</small></button>`).join('')}</div>`;
}

// A geographic map inside the first-person menu; it does not create a second WebGL renderer.
export function mountTourismMap(host,model) {
  let state=readLayers({benefits:false,route:true}),bounds,selected=null,selectedBooth=null,disposed=false;
  const site=popupSite(model);
  const lookup=new Map([...model.benefits,...model.unlocated,...model.stages,...(site?[site]:[])].map(p=>[p.id,p]));
  host.className='tourism-map-ui';
  host.innerHTML=`${controlsHTML(state)}<div class="tourism-map-tools"><button type="button" data-map-fit="route">릴레이 전체</button><button type="button" data-map-fit="benefits">혜택업체 전체</button><button type="button" data-map-fit="booths">팝업 부스</button><button type="button" data-map-zoom="in" aria-label="여행 지도 확대">＋</button><button type="button" data-map-zoom="out" aria-label="여행 지도 축소">−</button></div><div class="tourism-map-surface" role="group" aria-label="혜택업체와 릴레이 실제 위치 지도"><svg aria-hidden="true"></svg><div class="tourism-map-pins"></div><span class="tourism-north" aria-hidden="true">N ↑</span></div><div class="tourism-map-caption"><span data-map-count role="status"></span><a href="${esc(model.sourceUrl)}" target="_blank" rel="noopener">© OpenStreetMap</a></div><div data-map-popup hidden><button type="button" data-tourism-place="popup-site" class="tourism-popup-open">월영 밤마당 · 부스 9개 배치 보기 ↗</button><small>기획 배치 시안</small></div><div data-map-stages>${stageButtonsHTML(model)}</div><p class="tourism-note">약 ${(model.route.distanceMeters/1000).toFixed(1)}km · 공개 도로망을 따른 제안 연결선입니다. 실제 버스 노선이 아닙니다. 지도를 끌어서 이동할 수 있습니다.</p><section class="tourism-map-selection" hidden aria-label="선택한 위치 정보"></section><details class="tourism-all-benefits"><summary>관광주민증 혜택업체 ${model.benefits.length+model.unlocated.length}곳</summary>${benefitListHTML(model)}</details><a class="tourism-atlas-link" href="?layout=atlas&layers=relay">3D 전체 지도에서 보기 ↗</a>`;
  const surface=host.querySelector('.tourism-map-surface'),svg=surface.querySelector('svg'),pins=surface.querySelector('.tourism-map-pins');
  const panel=host.querySelector('.tourism-map-selection');
  let w=800,h=420,drag=null,lastSize='',clusters=[];
  const frame=coords=>{bounds=fitMapBounds(coords,w,h);};
  function render() {
    if(disposed)return;
    w=surface.clientWidth||800;h=surface.clientHeight||420;
    if(!bounds)frame(state.route?model.route.coordinates:state.benefits?model.benefits.map(p=>p.coordinates):state.booths?layerCoordinates(model,'booths'):model.route.coordinates);
    svg.setAttribute('viewBox',`0 0 ${w} ${h}`);
    const pt=c=>projectMapPoint(c,bounds,w,h).map(n=>Number(n.toFixed(1))).join(',');
    const line=c=>`M${c.map(pt).join('L')}`;
    const paths=model.background.filter(f=>!f.bbox || !(f.bbox[2]<bounds[0]||f.bbox[0]>bounds[2]||f.bbox[3]<bounds[1]||f.bbox[1]>bounds[3])).map(f=>{
      const g=f.geometry,groups=g.type==='Polygon'?[g.coordinates]:g.type==='MultiPolygon'?g.coordinates:null;
      if(groups)return `<path class="map-water" d="${groups.map(p=>p.map(r=>line(r)+'Z').join('')).join('')}" fill-rule="evenodd"/>`;
      const lines=g.type==='LineString'?[g.coordinates]:g.coordinates;
      return `<path class="map-road" d="${lines.map(line).join('')}"/>`;
    }).join('');
    svg.innerHTML=paths+(state.route?`<path class="tourism-route-halo" d="${line(model.route.coordinates)}"/><path class="tourism-route-line" d="${line(model.route.coordinates)}"/>`:'');
    clusters=clusterMapPlaces(visibleMapPlaces(model,state),bounds,w,h);
    pins.replaceChildren(...clusters.map((cluster,index)=>{
      const {x,y}=cluster,p=cluster.points[0].place,b=document.createElement('button');
      if(cluster.points.length>1){b.type='button';b.className='tourism-map-pin is-cluster';b.dataset.mapCluster=String(index);b.style.left=`${x}px`;b.style.top=`${y}px`;b.textContent=`${cluster.points.length}곳`;b.setAttribute('aria-label',`겹친 위치 ${cluster.points.length}곳 확대`);return b;}
      b.type='button';b.dataset.tourismPlace=p.id;b.className=`tourism-map-pin ${p.popupSite?'is-popup':p.relayStage?'is-stage':'is-benefit'}`;
      b.hidden=x<16||y<16||x>w-16||y>h-16;
      b.style.left=`${x}px`;b.style.top=`${y}px`;b.setAttribute('aria-label',p.popupSite?'월영 밤마당 야간 팝업 9개 부스 지도 표식':p.relayStage?`${p.relayStage}단계 ${p.name} 지도 표식`:`${p.name} 혜택 지도 표식`);
      b.setAttribute('aria-pressed',String(selected?.id===p.id));b.textContent=p.popupSite?'부스 9':p.relayStage||'혜택';return b;
    }));
    host.querySelector('[data-map-stages]').hidden=!state.route;
    host.querySelector('[data-map-popup]').hidden=!state.booths;
    host.querySelector('[data-map-count]').textContent=`${state.benefits?`혜택업체 ${model.benefits.length}곳`:'혜택업체 숨김'} · ${state.route?'릴레이 연결선 표시':'연결선 숨김'} · ${state.booths?'팝업 부스 표시':'부스 숨김'}`;
    host.querySelector('.tourism-atlas-link').href=`?layout=atlas&layers=${[state.benefits?'benefits':'',state.route?'relay':'',state.booths?'booths':''].filter(Boolean).join(',')}`;
  }
  function select(p) {
    if(!p)return;selected=p;selectedBooth=null;
    if(p.coordinates) {
      const layer=mapPlaceLayer(p);state[layer]=true;host.querySelector(`[data-layer="${layer}"]`).checked=true;saveLayers(state);
      frame(p.relayStage===2?model.route.coordinates:[p.coordinates]);
    }
    panel.hidden=false;panel.innerHTML=`<button type="button" data-map-close aria-label="위치 정보 닫기">×</button>${placeDetailsHTML(p)}`;
    render();panel.scrollIntoView({block:'nearest',behavior:'smooth'});
  }
  host.addEventListener('change',e=>{
    const layer=e.target.dataset.layer;if(!layer)return;state[layer]=e.target.checked;saveLayers(state);
    if(state[layer])frame(layerCoordinates(model,layer));
    if(!state[layer]&&((selected&&mapPlaceLayer(selected)===layer)||(layer==='booths'&&panel.querySelector('[data-tourism-place="popup-site"]')))){selected=null;selectedBooth=null;panel.hidden=true;}
    render();
  });
  host.addEventListener('click',e=>{
    const button=e.target.closest('button');if(!button)return;
    if(button.dataset.popupBooth&&popupBooth(button.dataset.popupBooth)){selectedBooth=button.dataset.popupBooth;panel.innerHTML=`<button type="button" data-map-close aria-label="위치 정보 닫기">×</button>${popupDetailsHTML(selectedBooth)}`;panel.querySelector('.popup-booth-detail a').focus({preventScroll:true});panel.scrollIntoView({block:'nearest',behavior:'smooth'});}
    if(button.dataset.tourismPlace)select(lookup.get(button.dataset.tourismPlace));
    if(button.dataset.mapCluster!==undefined){const entries=clusters[Number(button.dataset.mapCluster)].points.map(p=>p.place);frame(entries.map(p=>p.coordinates));render();panel.hidden=false;panel.innerHTML=`<button type="button" data-map-close aria-label="위치 정보 닫기">×</button><h3>이 주변의 위치</h3><div class="tourism-benefit-list">${entries.map(p=>`<button type="button" data-tourism-place="${p.id}">${esc(p.relayStage?`${p.relayStage}단계 ${p.name}`:p.name)}</button>`).join('')}</div>`;}
    if(button.hasAttribute('data-map-close')){selected=null;panel.hidden=true;render();}
    if(button.dataset.mapFit){const layer=button.dataset.mapFit;state[layer]=true;host.querySelector(`[data-layer="${layer}"]`).checked=true;saveLayers(state);frame(layerCoordinates(model,layer));render();}
    if(button.dataset.mapZoom){const factor=button.dataset.mapZoom==='in'?.65:1.5;const cx=(bounds[0]+bounds[2])/2,cy=(bounds[1]+bounds[3])/2;const dx=Math.max(.0003,Math.min(1,(bounds[2]-bounds[0])*factor))/2,dy=dx*(bounds[3]-bounds[1])/(bounds[2]-bounds[0]);bounds=[cx-dx,cy-dy,cx+dx,cy+dy];render();}
  });
  surface.addEventListener('pointerdown',e=>{if(e.target.closest('button'))return;drag={x:e.clientX,y:e.clientY,b:[...bounds]};surface.setPointerCapture(e.pointerId);});
  surface.addEventListener('pointermove',e=>{if(!drag)return;const dx=(e.clientX-drag.x)/w*(drag.b[2]-drag.b[0]),dy=(e.clientY-drag.y)/h*(drag.b[3]-drag.b[1]);bounds=[drag.b[0]-dx,drag.b[1]+dy,drag.b[2]-dx,drag.b[3]+dy];render();});
  for(const event of ['pointerup','pointercancel'])surface.addEventListener(event,()=>{drag=null;});
  const observer=new ResizeObserver(()=>{const size=`${surface.clientWidth},${surface.clientHeight}`;if(size===lastSize)return;lastSize=size;if(bounds){const cx=(bounds[0]+bounds[2])/2,cy=(bounds[1]+bounds[3])/2;const dy=(bounds[3]-bounds[1])/2,dx=dy*surface.clientWidth/Math.max(1,surface.clientHeight)/Math.cos(cy*Math.PI/180);bounds=[cx-dx,cy-dy,cx+dx,cy+dy];}render();});
  observer.observe(surface);render();
  return ()=>{disposed=true;observer.disconnect();};
}
