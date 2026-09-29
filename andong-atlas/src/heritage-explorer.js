import {relayEntryHTML} from './relay-entry.js';
import * as THREE from 'three';
import {polygons,inRing} from './geo.js';
import { MapPoints } from './map-points.js';
import { JourneyScene } from './journey-scene.js';
import { heritagePlaces,heritageNetwork,makeHeritageTour } from './heritage-tour.js';
import { escapeHtml as esc,placeLinks } from './place-media-model.js';
import {heritageViewpoints,makeHeritageInspection} from './heritage-viewpoint.js';
import {heritageVisit} from './heritage-visit.js';
import './heritage-explorer.css';

export class HeritageExplorer {
  constructor(atlas,media){
    this.a=atlas;this.media=media;
    this.outline=new THREE.Group();atlas.world.add(this.outline);
    this.points=new MapPoints(atlas,p=>this.select(p));
    this.points.element.setAttribute('aria-label','관광지 안의 건물과 명소');
    this.points.element.classList.add('heritage-points');
    document.body.insertAdjacentHTML('beforeend',`<aside id="heritage-sheet" class="glass heritage-sheet" hidden aria-label="관광지 내부 탐색"><div class="heritage-heading"><span id="heritage-region"></span><button id="heritage-close" aria-label="관광지 탐색 닫기">닫기 ×</button></div><h2>골목과 마당 사이</h2><p class="heritage-intro">작은 지점을 눌러 장소를 고르고, 연결된 길을 걸어보세요.</p><div id="heritage-site-list"></div><div id="heritage-place-detail" hidden></div><button id="heritage-inspect" class="heritage-inspect">건물 가까이 둘러보기</button><div class="heritage-tour-entry"><span id="heritage-tour-summary"></span><button id="heritage-walk" class="primary">산책 시작</button></div><p id="heritage-route-note" class="note"></p></aside><section id="heritage-player" class="glass heritage-player" hidden aria-label="관광지 산책 재생"><div class="heritage-heading"><span id="heritage-progress-text"></span><button id="heritage-exit">산책 종료</button></div><strong id="heritage-stage-title"></strong><progress id="heritage-progress" max="1" value="0"></progress><div class="heritage-player-actions"><button id="heritage-prev" aria-label="이전 산책 구간">이전</button><button id="heritage-play">계속 걷기</button><button id="heritage-next" aria-label="다음 산책 구간">다음</button><button id="heritage-look" aria-pressed="false">따라가기</button></div><p id="heritage-walk-note" class="note"></p></section>`);
    this.$=id=>document.getElementById(id);
    this.$('heritage-close').onclick=()=>this.close();
    this.$('heritage-walk').onclick=()=>this.start();
    this.$('heritage-inspect').onclick=()=>this.inspect();
    this.$('heritage-exit').onclick=()=>this.stop();
    this.$('heritage-prev').onclick=()=>this.player.seek(this.player.index-1);
    this.$('heritage-next').onclick=()=>this.player.seek(this.player.index+1);
    this.$('heritage-play').onclick=()=>{this.player.playing=!this.player.playing;this.tick();};
    this.$('heritage-look').onclick=()=>{this.player.setView(this.player.view==='follow'?'first':'follow');this.tick();};
    const canvas=atlas.renderer.domElement;let down;
    canvas.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY];});
    canvas.addEventListener('pointerup',e=>{
      if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5||this.a.journey?.active||this.points.element.hidden)return;
      const rect=canvas.getBoundingClientRect(),ray=new THREE.Raycaster();
      ray.setFromCamera(new THREE.Vector2((e.clientX-rect.left)/rect.width*2-1,1-(e.clientY-rect.top)/rect.height*2),atlas.camera);
      const hit=ray.intersectObjects(atlas.district.group.children,true)[0];if(!hit)return;
      const local=atlas.world.worldToLocal(hit.point.clone()),geo=atlas.project.toGeo(local.x,local.z);
      const feature=this.data.buildings.find(f=>polygons(f.geometry).some(poly=>inRing(geo,poly[0])&&!poly.slice(1).some(r=>inRing(geo,r))));
      const place=feature&&this.places.find(p=>p.id===`${this.data.id}:${feature.id}`);
      if(place)this.select(place);
    });
  }
  sync(){
    const data=this.a.district.data,available=this.a.district.group.visible&&data.heritageDetail;
    if(!available){this.points.update(false);if(!this.player?.active)this.$('heritage-sheet').hidden=true;return;}
    if(this.data===data)return;
    this.close();this.selected=null;this.$('heritage-place-detail').hidden=true;this.$('heritage-place-detail').replaceChildren();this.data=data;this.places=heritagePlaces(data);this.network=heritageNetwork(data);this.tour=makeHeritageTour(data,this.network);this.viewpoints=heritageViewpoints(data,this.a.project,this.places);
    this.points.setPlaces(this.places,[],null);
  }
  open(){
    this.sync();if(!this.data?.heritageDetail)return;
    if(innerWidth<1200&&document.getElementById('shell-panel')?.getAttribute('aria-expanded')==='true')document.getElementById('shell-panel').click();
    this.$('heritage-sheet').hidden=false;
    this.$('heritage-sheet').classList.toggle('heritage-compact',!!this.player?.active&&innerWidth<=700);
    this.$('heritage-region').textContent=this.data.name.split('·')[0].trim();
    this.$('heritage-site-list').replaceChildren(...this.places.map(p=>{
      const button=document.createElement('button');button.textContent=p.name;button.dataset.heritageSite=p.id;button.onclick=()=>this.select(p);return button;
    }));
    this.$('heritage-tour-summary').textContent=`${(this.tour.distance/1000).toFixed(2)}km · 약 ${this.tour.end-this.tour.start}분 (시연 가정)`;
    this.$('heritage-walk').disabled=!this.tour.stages.some(s=>s.path);
    this.$('heritage-inspect').disabled=!this.viewpoints.size;
    this.$('heritage-route-note').textContent=['dosan','bongjeong'].includes(this.data.id)?'건물은 지도에서 선택할 수 있습니다. 경내 보행로 자료가 부족해 산책은 기록된 접근 길로 연결합니다.':'공개 지도에 연결된 길을 따르는 탐색 코스입니다. 건물 내부·사유지 개방 여부는 현장 안내를 확인하세요.';
    if(innerWidth<=700)document.getElementById('explore').classList.remove('open');
  }
  select(place,fly=true){
    this.selected=place;this.open();
    const visit=heritageVisit(place),urls=placeLinks(place),detail=this.$('heritage-place-detail');detail.hidden=false;
    detail.innerHTML=`<h3>${esc(place.name)}</h3>${relayEntryHTML({...place,kind:"heritage"})}<button id="heritage-expand" class="heritage-expand" aria-expanded="false">설명 펼치기</button><p>${esc(place.description||'공개 지도에 기록된 산책 장소입니다.')}</p><div class="heritage-links"><button id="heritage-photo">사진·거리 보기</button>${this.viewpoints.has(place.id)?'<button id="heritage-close-view">가까이 보기</button>':''}<a href="${esc(urls.map)}" target="_blank" rel="noopener noreferrer">실제 위치 ↗</a></div><small>${place.coordinates[1].toFixed(5)}° N · ${place.coordinates[0].toFixed(5)}° E · OpenStreetMap</small>`;
    this.$('heritage-expand').onclick=()=>{const compact=detail.parentElement.classList.toggle('heritage-compact');this.$('heritage-expand').setAttribute('aria-expanded',String(!compact));this.$('heritage-expand').textContent=compact?'설명 펼치기':'설명 접기';};
    this.$('heritage-photo').onclick=()=>this.media.open(place);
    if(this.$('heritage-close-view'))this.$('heritage-close-view').onclick=()=>this.inspect(place.id);
    if(visit){const info=document.createElement('div');info.className='heritage-visit';info.innerHTML=`<p>${esc(visit.hours)}<br>${esc(visit.price)}</p><a href="${esc(visit.source)}" target="_blank" rel="noopener noreferrer">공식 관람 안내 ↗</a><small>확인 ${esc(visit.checkedAt)}</small>`;detail.append(info);}
    if(visit?.vr){const vr=document.createElement('button');vr.className='heritage-vr';vr.textContent='공식 실사 VR로 둘러보기';vr.onclick=()=>this.media.open(place,'street');detail.append(vr);}
    if(place.descriptionSource){const source=document.createElement('a');source.href=place.descriptionSource;source.target='_blank';source.rel='noopener noreferrer';source.textContent='공식 해설 출처 ↗';source.className='heritage-source';detail.append(source);}
    this.points.setPlaces(this.places,[],place.id);
    this.clearOutline();
    const building=this.data.buildings.find(f=>`${this.data.id}:${f.id}`===place.id);
    if(building)for(const poly of polygons(building.geometry))for(const ring of poly){const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(ring.map(c=>this.a.point(c,.004))),new THREE.LineBasicMaterial({color:'#a46732',depthTest:false,depthWrite:false}));line.renderOrder=9;this.outline.add(line);}
    this.$('heritage-site-list').querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.heritageSite===place.id)));
    if(fly&&!this.player?.active)this.a.fly(place.coordinates,.45);
  }
  inspect(selectedId){
    const tour=makeHeritageInspection(this.data,this.places,this.viewpoints,selectedId);
    if(tour.stages.length)this.start(tour,tour.initial);
  }
  start(tour=this.tour,index=1){
    if(!tour?.stages.length)return;
    if(this.player?.active)this.stop();
    this.activeTour=tour;
    this.primary=this.a.journey;
    if(!this.player){this.player=new JourneyScene(this.a,this.network,p=>this.select(p,false),t=>this.tick(t));this.player.onExit=()=>this.stop();}
    this.player.network=this.network;
    this.player.setJourney(tour);this.player.setVisible(true);
    this.player.showPlaces([],[],null);
    this.a.journey=this.player;
    this.player.preferredView='first';this.player.start(index);this.player.playing=tour.kind!=='heritage-inspection'&&!this.a.reduced;
    this.$('heritage-sheet').hidden=!!tour.stages[index]?.path;this.tick();
  }
  tick(t){
    const p=this.player;if(!p?.active){this.$('heritage-player').hidden=true;return;}
    const tour=this.activeTour,inspection=tour.kind==='heritage-inspection',stage=tour.stages[p.index];
    t??=Math.min(1,p.elapsed/p.duration(stage));
    this.$('heritage-player').hidden=false;
    this.$('heritage-play').hidden=inspection;this.$('heritage-look').hidden=inspection;
    this.$('heritage-exit').textContent=inspection?'둘러보기 종료':'산책 종료';
    this.$('heritage-player').setAttribute('aria-label',inspection?'명소 가까이 둘러보기':'관광지 산책 재생');
    this.$('heritage-prev').setAttribute('aria-label',inspection?'이전 명소':'이전 산책 구간');
    this.$('heritage-next').setAttribute('aria-label',inspection?'다음 명소':'다음 산책 구간');
    this.$('heritage-progress-text').textContent=`${this.data.name.split('·')[0].trim()} · ${p.index+1}/${tour.stages.length}`;
    this.$('heritage-stage-title').textContent=stage.title||stage.place.name;
    this.$('heritage-progress').value=(p.index+t)/tour.stages.length;
    this.$('heritage-play').textContent=p.playing?'일시정지':'계속 걷기';
    this.$('heritage-prev').disabled=p.index===0;this.$('heritage-next').disabled=p.index===tour.stages.length-1;
    this.$('heritage-look').setAttribute('aria-pressed',String(p.view==='follow'));
    this.$('heritage-walk-note').textContent=inspection?'드래그로 둘러보기 · 다음 명소로 화면 전환. 가상 관찰 시점이며 실제 보행 경로는 아닙니다.':stage.cameraClear===false?'건물과 길의 자료가 겹쳐 이 구간은 위에서 살펴봅니다.':'드래그로 둘러보기 · 이동 시간은 압축 재생됩니다.';
    if(stage.path)this.$('heritage-sheet').hidden=true;
  }
  stop(){
    if(this.player){this.player.setVisible(false);if(this.a.journey===this.player)this.a.journey=this.primary;}
    this.$('heritage-player').hidden=true;
  }
  clearOutline(){for(const o of [...this.outline.children]){o.geometry.dispose();o.material.dispose();this.outline.remove(o);}}
  close(){this.stop();this.$('heritage-sheet').hidden=true;this.clearOutline();}
  update(){
    const shown=this.a.district.group.visible&&this.a.district.data.heritageDetail&&document.getElementById('tab-city')?.getAttribute('aria-selected')==='true'&&!this.a.journey?.active;
    if(shown)this.sync();
    this.points.update(!!shown&&this.a.labelsVisible!==false);
    this.outline.visible=!!shown;
  }
}
