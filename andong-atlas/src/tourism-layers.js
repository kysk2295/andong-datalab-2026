import * as THREE from 'three';
import {Line2} from 'three/addons/lines/Line2.js';
import {LineGeometry} from 'three/addons/lines/LineGeometry.js';
import {LineMaterial} from 'three/addons/lines/LineMaterial.js';
import {MapPoints} from './map-points.js';
import {popupSite,popupDetailsHTML,popupBooth} from './popup-map-layer.js';
import {createPopupMapOverlay} from './popup-map-overlay.js';
import {visibleMapPlaces,mapPlaceLayer,layerCoordinates} from './tourism-map-model.js';
import {loadTourismMap,readLayers,saveLayers,controlsHTML,stageButtonsHTML,placeDetailsHTML,benefitListHTML} from './tourism-map-ui.js';

export async function initTourismLayers(atlas) {
  const model=await loadTourismMap();
  let state=readLayers(),selected=null,selectedBooth=null;
  const site=popupSite(model),popupOverlay=site?createPopupMapOverlay(atlas,site,id=>{select(site);selectBooth(id);}):null;
  const defaultMinDistance=atlas.controls.minDistance;
  const params=new URLSearchParams(location.search);
  if(params.has('layers')){const enabled=params.get('layers').split(',');state={benefits:enabled.includes('benefits'),route:enabled.includes('relay'),booths:enabled.includes('booths')};}
  const lookup=new Map([...model.benefits,...model.unlocated,...model.stages,...(site?[site]:[])].map(p=>[p.id,p]));
  const controls=document.createElement('section');controls.className='tourism-layer-panel';controls.setAttribute('aria-label','혜택업체와 릴레이 지도 설정');
  controls.innerHTML=`${controlsHTML(state)}<div class="tourism-layer-actions"><button type="button" data-tourism-list>혜택업체 목록</button><button type="button" data-tourism-fit>표시한 위치 전체 보기</button></div><div data-tourism-popup hidden><button type="button" data-tourism-place="popup-site" class="tourism-popup-open">부스 9개 배치 보기 <span aria-hidden="true">↗</span></button><small>월영교 주변 · 기획 배치 시안</small></div><div data-tourism-stages>${stageButtonsHTML(model)}</div>`;
  const explore=document.getElementById('explore');explore.insertBefore(controls,explore.querySelector('.panel-body'));
  const info=document.createElement('aside');info.className='tourism-info';info.hidden=true;info.setAttribute('aria-label','선택한 혜택업체 또는 릴레이 단계');document.body.append(info);
  const points=new MapPoints(atlas,select);points.element.classList.add('tourism-atlas-points');points.element.setAttribute('aria-label','관광주민증 혜택업체와 릴레이 단계 지도 표식');
  const group=new THREE.Group();group.name='tourism-relay-route';atlas.world.add(group);
  // Keep the line in screen pixels, draped on the same terrain as the existing map.
  const halo=new Line2(new LineGeometry(),new LineMaterial({color:'#fff8e5',linewidth:6,depthTest:false,depthWrite:false,transparent:true,opacity:.92}));halo.renderOrder=11;group.add(halo);
  const line=new Line2(new LineGeometry(),new LineMaterial({color:'#a86c2b',linewidth:3,depthTest:false,depthWrite:false,transparent:true}));line.renderOrder=12;group.add(line);
  const refreshTerrain=()=>{const coords=model.route.coordinates.flatMap((b,i,all)=>{if(!i)return [b];const a=all[i-1],n=Math.max(1,Math.ceil(Math.hypot((a[0]-b[0])*89300,(a[1]-b[1])*111320)/15));return Array.from({length:n},(_,j)=>a.map((x,k)=>x+(b[k]-x)*(j+1)/n));});const positions=coords.flatMap(c=>atlas.point(c,.012).toArray());for(const object of [line,halo]){object.geometry.dispose();object.geometry=new LineGeometry();object.geometry.setPositions(positions);}};
  refreshTerrain();let terrainKey='';
  function persist(){saveLayers(state);const url=new URL(location.href);if(url.searchParams.has('layers')){url.searchParams.set('layers',[state.benefits?'benefits':'',state.route?'relay':'',state.booths?'booths':''].filter(Boolean).join(','));history.replaceState(null,'',url);}}
  function frame(coords,popup=false){atlas.journey?.stop();if(popup&&site){atlas.controls.minDistance=.16;atlas.fly(site.coordinates,innerWidth<=700?.34:.26,false,new THREE.Vector3(.9,1.3,.6),atlas.elevation(site.coordinates)+.025);}else atlas.frameCoordinates(coords,{minDistance:1.7});}
  function render() {
    points.setPlaces(visibleMapPlaces(model,state),[],selected?.id);
    points.records.forEach(({place,button})=>{if(place.popupSite){button.classList.add('tourism-popup-marker');button.querySelector('.gis-symbol').textContent='9';button.setAttribute('aria-label','월영 밤마당 야간 팝업 9개 부스 지도 표식');}if(place.relayStage){button.classList.add('tourism-stage-marker');button.querySelector('.gis-symbol').textContent=String(place.relayStage);button.setAttribute('aria-label',`${place.relayStage}단계 ${place.name} 지도 표식`);}});
    controls.querySelector('[data-tourism-stages]').hidden=!state.route;
    controls.querySelector('[data-tourism-popup]').hidden=!state.booths;
    if(popupOverlay){popupOverlay.setVisible(state.booths);popupOverlay.select(selectedBooth);}
    atlas.controls.minDistance=state.booths?.16:defaultMinDistance;
    group.visible=state.route;
    atlas.container.dataset.tourismBenefits=String(state.benefits);
    atlas.container.dataset.tourismRoute=String(state.route);
    atlas.container.dataset.tourismBooths=String(state.booths);
    controls.querySelectorAll('[data-layer]').forEach(el=>{el.checked=state[el.dataset.layer];});
    sync();
  }
  function select(p) {
    if(!p)return;if(p.popupSite&&innerWidth<=700)explore.classList.remove('open');selected=p;selectedBooth=null;info.classList.toggle('is-popup',!!p.popupSite);
    if(p.coordinates){state[mapPlaceLayer(p)]=true;persist();frame(p.relayStage===2?model.route.coordinates:[p.coordinates],p.popupSite);}
    info.hidden=false;info.innerHTML=`<button type="button" data-tourism-close aria-label="업체·단계 정보 닫기">×</button>${placeDetailsHTML(p)}${p.relayStage||p.popupSite?'':'<button type="button" data-tourism-list>전체 혜택업체 목록</button>'}`;
    render();if(p.popupSite)popupOverlay?.flash();
  }
  function selectBooth(id){
    if(!popupBooth(id))return;selectedBooth=id;
    info.innerHTML=`<button type="button" data-tourism-close aria-label="업체·단계 정보 닫기">×</button>${popupDetailsHTML(id)}`;
    render();popupOverlay?.flash(id);info.scrollTop=0;info.querySelector('.popup-booth-detail a').focus({preventScroll:true});
  }
  function handleClick(e) {
    const b=e.target.closest('button');if(!b)return;
    if(b.dataset.popupBooth)selectBooth(b.dataset.popupBooth);
    if(b.dataset.tourismPlace)select(lookup.get(b.dataset.tourismPlace));
    if(b.hasAttribute('data-tourism-close')){info.hidden=true;selected=null;selectedBooth=null;render();}
    if(b.hasAttribute('data-tourism-list')){info.classList.remove('is-popup');info.hidden=false;info.innerHTML=`<button type="button" data-tourism-close aria-label="업체·단계 정보 닫기">×</button><h3>관광주민증 혜택업체</h3>${benefitListHTML(model)}`;}
    if(b.hasAttribute('data-tourism-fit'))frame(visibleMapPlaces(model,state).map(p=>p.coordinates));
  }
  controls.addEventListener('click',handleClick);info.addEventListener('click',handleClick);
  controls.addEventListener('change',e=>{const layer=e.target.dataset.layer;if(!layer)return;state[layer]=e.target.checked;persist();if(selected&&mapPlaceLayer(selected)===layer&&!state[layer]){info.hidden=true;selected=null;selectedBooth=null;}render();if(state[layer])frame(layerCoordinates(model,layer),layer==='booths');});
  function sync() {
    const playing=Boolean(atlas.journey?.active);
    controls.inert=playing;info.style.visibility=playing?'hidden':'';
    points.update(!playing&&(state.benefits||state.route||state.booths));group.visible=!playing&&state.route;
    if(popupOverlay){popupOverlay.setVisible(!playing&&state.booths);popupOverlay.update();}
    for(const object of [line,halo])object.material.resolution.set(atlas.renderer.domElement.clientWidth,atlas.renderer.domElement.clientHeight);
    const key=`${atlas.district.group.visible}:${atlas.terrainExaggeration}:${atlas.district.data.bbox.join(',')}`;
    if((state.route||state.booths)&&key!==terrainKey){terrainKey=key;refreshTerrain();popupOverlay?.refresh();}
  }
  render();if(params.has('layers'))frame(visibleMapPlaces(model,state).map(p=>p.coordinates),state.booths&&!state.route&&!state.benefits);
  return {sync};
}
