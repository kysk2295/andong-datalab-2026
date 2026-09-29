import * as THREE from 'three';
import transport from '../public/data/transport.json';
import {originDepartures,routeForOrigin,routeProjection} from './transport-model.js';
import {escapeHtml as esc} from './place-media-model.js';
import './visitor-info.css';

export function initTransportUI(atlas,player,restore) {
  const $=id=>document.getElementById(id);
  let route=transport.routes[0],selectedStop=0;
  const group=new THREE.Group();player.group.add(group);
  const onPlace=player.onPlace;
  document.body.insertAdjacentHTML('beforeend',`<dialog id="transit-dialog" class="journey-dialog transit-dialog" aria-labelledby="transit-title"><div class="dialog-heading"><span>안동시 공식 BIS · ${transport.checkedAt} 수집</span><button id="transit-close">닫기</button></div><h2 id="transit-title">버스로 이어지는 안동</h2><p id="transit-connection"></p><div class="transit-fields"><label class="field">노선·운행 방향<select id="transit-route">${transport.routes.map(r=>`<option value="${r.id}">${esc(r.name)}</option>`).join('')}</select></label><label class="field">시간표 구분<select id="transit-day"><option value="1">평일</option><option value="2">공휴일·일요일</option></select></label></div><div id="transit-detail"></div><div class="journey-actions"><button id="transit-on-map" class="primary">3D 지도에 이 노선 표시</button><a id="transit-official" target="_blank" rel="noopener">공식 BIS에서 확인 ↗</a></div><p class="note">실제 노선 선형·정류장과 저장한 기점 시간표입니다. 실시간 차량 위치·중간 정류장 도착 시각은 제공하지 않습니다. 토요일 적용 시간표·임시 변경은 BIS에서 확인하세요.</p></dialog><aside id="transit-map-bar" class="glass" hidden aria-label="표시 중인 공식 버스 노선"><span id="transit-map-name"></span><button id="transit-reopen">정류장·시간표</button><button id="transit-map-clear">노선 닫기</button></aside>`);
  const dialog=$('transit-dialog');
  function clear(redraw=true){
    player.clear(group);$('transit-map-bar').hidden=true;
    document.body.classList.remove('transit-map-open');player.onPlace=onPlace;
    player.routeGroup.visible=true;
    if(redraw)restore?.();
  }
  function selectStop(index){
    selectedStop=index;
    const stop=route.stops[index];
    $('transit-stop-detail').textContent=`${index+1}. ${stop.name} · 정류장 ${stop.id} · ${index===0?'기점 출발표 참고':'이 정류장의 승차 시각은 별도 확인'}`;
    dialog.querySelectorAll('[data-transit-stop]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.transitStop)===index)));
    dialog.querySelectorAll('[data-route-dot]').forEach(dot=>dot.setAttribute('r',Number(dot.dataset.routeDot)===index?'6':'2.5'));
  }
  function render(){
    const times=originDepartures(route,$('transit-day').value),projection=routeProjection(route);
    $('transit-detail').innerHTML=`<div class="transit-caption"><span class="transit-number">${route.number}</span><div><strong>${esc(route.origin)} → ${esc(route.destination)}</strong><small>${route.stops.length}개 정류장 · 실제 BIS 노선 선형</small></div></div><svg class="transit-diagram" viewBox="0 0 600 300" role="img" aria-label="${esc(route.name)} 실제 노선 선형, 아래 목록에서 정류장 선택"><path d="${projection.path}" fill="none" stroke="currentColor" stroke-width="2.5"/>${projection.points.map((p,i)=>`<circle data-route-dot="${i}" cx="${p[0]}" cy="${p[1]}" r="2.5" fill="var(--panel)" stroke="currentColor" stroke-width="1.5"/>`).join('')}</svg><section class="transit-departures"><h3>${esc(route.origin)} 기점 출발</h3><div class="departure-times">${times.length?times.map(t=>`<time>${t}</time>`).join(''):'<p>이 방향·요일의 게시 시간표가 없습니다. 운휴를 뜻하지 않습니다.</p>'}</div><p class="note">위 시각은 기점에서 출발하는 시각입니다. 월영교 등 중간 정류장 승차 시각으로 사용할 수 없습니다.</p></section><details><summary>정류장 ${route.stops.length}곳 · 운행 순서</summary><ol class="transit-stops">${route.stops.map((s,i)=>`<li><button data-transit-stop="${i}" aria-pressed="false"><span>${String(i+1).padStart(2,'0')}</span>${esc(s.name)}</button></li>`).join('')}</ol></details><p id="transit-stop-detail" class="note" role="status"></p>`;
    $('transit-official').href=route.source;
    dialog.querySelectorAll('[data-transit-stop]').forEach(b=>b.onclick=()=>selectStop(Number(b.dataset.transitStop)));
    selectStop(Math.min(selectedStop,route.stops.length-1));
  }
  $('transit-route').onchange=()=>{route=transport.routes.find(r=>r.id===$('transit-route').value);selectedStop=0;render();};
  $('transit-day').onchange=render;
  $('transit-close').onclick=()=>dialog.close();
  $('transit-on-map').onclick=()=>{
    clear(false);player.stop();atlas.setDetailed(false);
    const points=route.coordinates.map(c=>player.point(c).add(new THREE.Vector3(0,.008,0)));
    const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(points),new THREE.LineBasicMaterial({color:'#267e89',depthTest:false,depthWrite:false}));line.renderOrder=10;group.add(line);
    player.routeGroup.visible=false;
    player.showPlaces(route.stops.map((s,i)=>({id:`bis-${route.id}-${i}`,name:s.name,kind:'stop',coordinates:s.coordinates,description:`${route.number}번 공식 정류장 · 운행 순서 ${i+1}`,source:transport.provider,url:route.source})),[],`bis-${route.id}-${selectedStop}`);
    player.onPlace=(place,...args)=>{
      if(place.id.startsWith(`bis-${route.id}-`)){
        selectedStop=Number(place.id.split('-').at(-1));render();dialog.showModal();
      }else onPlace(place,...args);
    };
    atlas.frameCoordinates(route.coordinates,{minDistance:3});
    $('transit-map-name').textContent=`공식 ${route.number}번 · ${route.origin} → ${route.destination}`;
    $('transit-map-bar').hidden=false;$('scenario-map-summary').hidden=true;dialog.close();
    document.body.classList.add('transit-map-open');
    if(innerWidth<=700)$('explore').classList.remove('open');
  };
  $('transit-map-clear').onclick=()=>clear();
  $('transit-reopen').onclick=()=>{render();dialog.showModal();};
  return {clear,open(origin){
    route=routeForOrigin(transport,origin);selectedStop=0;$('transit-route').value=route.id;
    $('transit-connection').textContent=origin==='bridge'?'월영교 → 안동역: 112번의 시내 방향을 먼저 확인하세요. 기점 리첼호텔 출발 시각과 월영교 승차 시각은 다릅니다. 이후 역 연결편·환승 시간은 별도 확인이 필요합니다.':origin==='hahoe'?'하회마을 → 월영교: 안동시 관광 안내는 210번 → 안동중 하차 → 112번 환승을 안내합니다. 각 방향의 정류장·출발표를 따로 확인하세요.':origin==='downtown'?'원도심 → 월영교: 112번의 운행 방향을 선택하세요. 구 안동역과 현재 KTX 안동역은 다른 위치입니다.':'KTX 안동역·터미널 → 월영교: 112번 경유 노선을 확인하세요. 시간표의 안동역(안동터미널)은 승차 정류장 이름입니다.';
    render();dialog.showModal();
  }};
}
