import {waitForArt,withDeadline,yieldToPage} from './loading.js';
import {popupBooth,popupEntryStation} from './popup-map-layer.js';
import {popupMapHTML} from './relay-popup-map.js';
import {drawPostcard} from './relay-popup-postcard.js';
import {RESTAURANT_ARRIVALS,restaurantStage} from './relay-passages.js';
import {TOUR_SAVE} from './relay-popup-visit.js';
import {createRelayVisit,restoreRelayVisit,relayVisitSaveKey,applyRelayEntry} from './relay-visit.js';
import {validRelayVisit} from './relay-entry.js';
import {DINING_SEATS} from './relay-dining-layout.js';
import './relay.css';
import './relay-hud.css';
import './relay-landing.css';
import {hudLocation,hudActionLabel} from './relay-hud.js';
import {loadTourismMap,mountTourismMap,readLayers,saveLayers} from './tourism-map-ui.js';
import {loadRelayProps} from './relay-scanned-props.js';
import {bindThumbstick} from './relay-input.js';
import {runCheckout} from './relay-checkout.js';
import {runActivity} from './relay-activities.js';
import {RELAY_STEPS,relayStepIndex,relayProgress} from './relay-story.js';
import {loadRelayMaterials} from './relay-materials.js';
import {JOURNEYS,journeyFor} from './relay-journey.js';
import {RelayScene} from './relay-scene.js';
import {CHAPTERS,MEALS,PROGRAMS,TRANSPORTS,POPUP_ITEMS,createRelayState,relayReducer,restoreRelayState,canEnter,nextAction,minutesAt,clockLabel} from './relay-model.js';
import research from '../public/data/relay-research.json';
import photos from '../public/data/relay-media.json';
import documentPhotos from '../public/data/relay-document-photos.json';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money=n=>n.toLocaleString('ko-KR')+'원';
const icon=(name,size=20)=>{
 const paths={menu:'<path d="M5 7h14M5 12h14M5 17h14"/>',book:'<path d="M4 4h7a3 3 0 0 1 3 2 3 3 0 0 1 3-2h3v16h-3a3 3 0 0 0-3 1 3 3 0 0 0-3-1H4V4Zm10 2v15"/>',arrow:'<path d="M5 12h14m-6-6 6 6-6 6"/>',map:'<path d="m3 5 6-2 6 2 6-2v16l-6 2-6-2-6 2V5ZM9 3v16m6-14v16"/>',photo:'<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8" cy="8" r="1.5"/><path d="m3 17 6-6 4 4 3-3 5 5"/>',ticket:'<path d="M3 6h18v4a2 2 0 0 0 0 4v4H3v-4a2 2 0 0 0 0-4V6Zm12 0v12"/>',close:'<path d="m6 6 12 12M6 18 18 6"/>',check:'<path d="m5 12 4 4L19 6"/>',reset:'<path d="M3 10a9 9 0 1 1 2 9M3 4v6h6"/>',sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l2 2m10 10 2 2M5 19l2-2M17 7l2-2"/>',pin:'<path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z"/><circle cx="12" cy="10" r="2"/>',clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',hand:'<path d="M8 12V5a2 2 0 0 1 4 0v7-8a2 2 0 0 1 4 0v8-5a2 2 0 0 1 4 0v9c0 4-3 6-7 6-2 0-4-1-5-3l-5-7a2 2 0 0 1 3-2l2 2Z"/>'};
 return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name]||paths.arrow}</svg>`;
};
const photoById=id=>photos.find(p=>p.id===id);

export async function initRelay(){
 const loadStarted=performance.now();
 document.title='안동 이어드림 · 한 끼에서 안동의 밤까지';
 document.body.className='relay-body';
 let state=createRelayState();try{const saved=localStorage.getItem('andong-relay-v1');if(saved)state=restoreRelayState(saved);}catch{}
 const entryParams=new URL(location.href).searchParams;
 let placeVisit=validRelayVisit(entryParams.get('visit')),resumeState=placeVisit?state:null;
 if(placeVisit){try{state=restoreRelayVisit(placeVisit,localStorage.getItem(relayVisitSaveKey(placeVisit)));}catch{state=createRelayVisit(placeVisit);}
  state=applyRelayEntry(state,placeVisit,{at:entryParams.get('at'),program:entryParams.get('program')});
 }else if(entryParams.get('play')==='1')state=relayReducer(state,{type:'START'});
 const entryBooth=placeVisit==='popup'?popupBooth(entryParams.get('booth')):null;
 let journey=null;
 let preview=null,busy=false,sceneReady=false,scene=null,sceneKey='',aim=50,lowQuality=false,drawerOpener=null;
 const app=document.createElement('div');app.className='relay-app immersive-hud';document.body.replaceChildren(app);
 app.innerHTML=`<main id="relay-world" aria-label="이어드림 1인칭 여행"></main><section id="relay-loading-status" class="relay-loading-status" role="status"><strong>공간을 준비하고 있어요</strong><p id="relay-loading-note">사진 재질을 불러오고 있습니다.</p><progress id="relay-loading-progress" aria-label="공간 자료 로딩" max="1" value="0"></progress><button id="relay-loading-continue">먼저 입장하기</button><a href="?layout=atlas">전체 지도</a></section><div class="relay-shade" aria-hidden="true"></div>
 <header class="relay-header"><a class="relay-brand" href="/" aria-label="기존 지도 첫 화면으로 돌아가기"><span class="brand-symbol" aria-hidden="true">이</span><span>안동 이어드림</span></a><a class="relay-landing-map" href="?layout=atlas">${icon('map',18)}<span>3D 지도</span></a></header>
 <header class="relay-play-header" hidden><div class="relay-current-place"><span id="relay-area"></span><h1 id="relay-title" tabindex="-1"></h1></div><nav aria-label="여행 메뉴"><button id="relay-map" aria-label="지도 열기" title="지도">${icon('map',18)}</button><button id="relay-journal" aria-label="여행 기록 열기">${icon('book',18)}<span>기록</span></button><button id="relay-menu" aria-label="공간 메뉴 열기" aria-haspopup="dialog">${icon('menu',19)}<span>메뉴</span></button></nav></header>
 <section class="relay-welcome" aria-labelledby="relay-welcome-title"><h1 id="relay-welcome-title">한 끼에서 밤까지</h1><div class="relay-landing-actions"><button class="relay-primary" id="relay-start"><span id="relay-start-label">플레이</span>${icon('arrow',18)}</button><button id="relay-popup-welcome" class="relay-landing-secondary">밤마당 둘러보기 ${icon('arrow',16)}</button></div></section>
 <button id="relay-popup-return" class="relay-popup-return" hidden>본 여정으로 돌아가기</button>
 <div class="relay-reticle" aria-hidden="true"></div><button id="relay-interact" class="relay-world-interact" hidden><kbd>E</kbd><span></span></button><div id="relay-paint-task" class="relay-paint-task" hidden><strong>탈 위에서 누른 채 붓을 움직여보세요</strong><p>색을 칠할수록 진행됩니다. 터치로도 칠할 수 있어요.</p><progress max="1" value="0" aria-label="탈 색칠 진행률"></progress><div><button id="relay-paint-assist">키보드로 한 구역 색칠</button><button id="relay-paint-cancel">돌아가기</button></div></div><div id="relay-dialogue" class="relay-dialogue" hidden></div>
 <section id="relay-walking" class="relay-walking" hidden aria-label="자리까지 이동"><span id="relay-walking-label"></span><progress max="1" value="0" aria-label="자리까지 이동 진행"></progress><button id="relay-walking-cancel">이동 멈추기</button></section>
 <section class="relay-control" hidden aria-label="지금 할 수 있는 행동"><div id="relay-preview-note" hidden>장면 둘러보기</div><button class="relay-primary" id="relay-action"></button><p id="relay-action-note"></p><button id="relay-ride-again" class="relay-inline" hidden>버스 다시 타기</button></section>
 <dialog id="relay-game-menu" class="relay-menu-panel" aria-labelledby="relay-menu-title"><div class="drawer-heading"><h2 id="relay-menu-title">공간 메뉴</h2><button id="relay-menu-close" aria-label="공간 메뉴 닫기">${icon('close')}</button></div><div class="relay-menu-body"><button id="relay-popup-entry" class="relay-night-entry">야간 팝업존 체험</button><div id="relay-context"></div><div id="relay-link-transport" class="transport-options" hidden></div><section class="relay-places" id="relay-places" hidden aria-label="공간 안에서 이동"><h3>자리로 이동</h3><div id="relay-place-buttons"></div><p id="relay-place-status"></p></section><button id="relay-link-back" class="relay-link-back" hidden>이전 장소로 돌아가기</button><div class="relay-header-actions"><button id="relay-game-look" aria-pressed="false">${icon('hand',18)}<span>마우스 고정</span></button><button id="relay-sources">${icon('photo',18)}<span>사진·현장 정보</span></button><button id="relay-sound" aria-pressed="true">공간 소리 켜짐</button><button id="relay-settings">${icon('sun',18)}<span>화면·조작 설정</span></button><a href="?layout=atlas" id="relay-atlas">${icon('map',18)}<span>전체 지도</span></a></div><button id="relay-reset" class="relay-menu-reset">여행 처음부터</button><p class="relay-menu-note">기획에 맞춰 재구성한 공간입니다.<br>인증·구매·할인은 체험용이며 실제 거래는 발생하지 않습니다.</p></div></dialog>
 <div id="relay-mouth" class="relay-mouth" hidden aria-label="음식을 가져오는 입 위치"><svg viewBox="0 0 64 34" aria-hidden="true"><path d="M7 15Q19 4 32 10Q45 4 57 15Q46 30 32 30Q18 30 7 15ZM7 15Q32 22 57 15"/></svg><span>입 쪽으로 가져오기</span></div>
 <section id="relay-work-task" class="relay-work-task" hidden aria-label="3D 작업대 체험"><strong id="relay-work-title"></strong><p id="relay-work-message" role="status"></p><progress id="relay-work-progress" max="1" value="0" aria-label="작업 진행률"></progress><details id="relay-work-controls"><summary>버튼으로 조작</summary><div id="relay-work-options"></div><div id="relay-work-pour" hidden><button id="relay-work-hold">누르고 있는 동안 붓기</button><div><button id="relay-work-tap">10%씩 붓기</button><button id="relay-work-check">양 확인하기</button><button id="relay-work-reset">비우고 다시</button></div></div><button id="relay-work-assist">조작 도움받기</button></details><button id="relay-work-done" class="relay-primary" disabled>완료</button><div class="work-task-footer"><button id="relay-work-cancel">체험 취소</button></div></section>
 <section id="relay-trip-progress" class="relay-trip-progress" hidden aria-label="저녁 이동 진행"><div><strong id="relay-trip-label">원도심 → 월영교</strong><button id="relay-trip-view">이동 경로를 3D로 보기</button></div><progress id="relay-trip-meter" max="1" value="0" aria-label="월영교까지 이동 진행률"></progress><p id="relay-trip-time"></p><div id="relay-bus-tools" hidden><span>드래그로 창밖·차내 둘러보기</span><button id="relay-bus-bell" aria-pressed="false">하차 벨</button></div><button id="relay-trip-skip" class="relay-trip-skip">이동 연출 건너뛰기</button></section>
 <div class="relay-mobile-look" hidden><div id="relay-thumbstick" role="group" tabindex="0" aria-label="이동 조이스틱. 끌어서 걷기. 키보드는 방향키 또는 WASD."><i aria-hidden="true"></i></div><button id="relay-jump" aria-label="점프" title="점프 · Space">점프</button></div>
 <p class="relay-toast" id="relay-status" role="status" aria-live="polite"></p>
 <dialog id="relay-drawer" class="relay-drawer"><div class="drawer-heading"><h2 id="relay-drawer-title"></h2><button id="relay-drawer-close" aria-label="정보 닫기">${icon('close')}</button></div><div id="relay-drawer-content"></div></dialog>
 <dialog id="relay-route-dialog" class="tourism-route-dialog" aria-labelledby="relay-route-title"><div class="drawer-heading"><h2 id="relay-route-title">혜택업체 · 릴레이 지도</h2><button id="relay-popup-map" class="relay-night-entry">야간 팝업 체험</button><button id="relay-route-close" aria-label="여행 지도 닫기">${icon('close')}</button></div><div id="relay-route-host" class="tourism-map-host"></div></dialog>
 <dialog id="relay-summary" class="relay-summary"><button class="summary-close" id="relay-summary-close" aria-label="완주 기록 닫기">${icon('close')}</button><div id="relay-summary-content"></div></dialog>`;
 document.documentElement.classList.remove('relay-loading');
 const $=id=>document.getElementById(id);
 const flowHTML=(steps,{live=false,previewing=false}={})=>steps.map((step,n)=>`<button data-chapter="${step.stage}" class="flow-step ${live&&step.completed?'flow-completed':''}" ${live&&step.current?'aria-current="step"':''}><b>${live&&step.completed?'✓':String(n+1).padStart(2,'0')}</b><span>${step.label}${live?`<small>${previewing&&step.current?'장면 미리보기':step.current?'지금 체험 중':step.completed?'연결 완료':step.detail}</small>`:''}</span></button>`).join('');
 let toastTimer;
 function announce(text){$('relay-status').textContent=text;$('relay-status').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('relay-status').classList.remove('show'),2800);}
 function persist(){try{localStorage.setItem(relayVisitSaveKey(placeVisit),JSON.stringify(state));}catch{}}
 if(placeVisit||entryParams.get('play')==='1')persist();
 if(entryParams.has('at')||entryParams.has('program')||entryParams.has('booth')){const url=new URL(location.href);url.searchParams.delete('at');url.searchParams.delete('program');url.searchParams.delete('booth');history.replaceState(null,'',url);}
 function dispatch(action){state=relayReducer(state,action);persist();render();}
 function popupURL(active){const url=new URL(location.href);if(active)url.searchParams.set('visit','popup');else{url.searchParams.delete('visit');url.searchParams.delete('program');}history.replaceState(null,'',url);}
 function openPopupVisit(){
  if(busy||journey)return;closeMenu(false);closeDrawer();$('relay-route-dialog').close();preview=null;
  if(state.stage===6&&state.started){render();return;}
  if(!placeVisit)resumeState=state;placeVisit='popup';try{state=restoreRelayVisit('popup',localStorage.getItem(relayVisitSaveKey('popup')));}catch{state=createRelayVisit('popup');}
  popupURL(true);sceneKey='';persist();render();$('relay-title').focus({preventScroll:true});
 }
 function leavePopupVisit(){
  if(busy||!placeVisit)return;closeMenu(false);closeDrawer();preview=null;placeVisit=null;state=resumeState||createRelayState();try{const saved=localStorage.getItem(TOUR_SAVE);if(saved)state=restoreRelayState(saved);}catch{}resumeState=null;
  popupURL(false);sceneKey='';render();(state.started?$('relay-title'):$('relay-start')).focus({preventScroll:true});
 }
 $('relay-popup-welcome').onclick=$('relay-popup-entry').onclick=$('relay-popup-map').onclick=openPopupVisit;
 $('relay-popup-return').onclick=leavePopupVisit;
 function displayed(){return preview===null?state:{...state,stage:preview,started:true};}
 function openDrawer(title,html){closeMenu(false);drawerOpener=document.activeElement;$('relay-drawer-title').textContent=title;$('relay-drawer-content').innerHTML=html;if(!$('relay-drawer').open)$('relay-drawer').showModal();scene?.setPaused(true);$('relay-drawer-content').scrollTop=0;}
 function closeDrawer(){$('relay-drawer').close();scene?.setPaused(false);drawerOpener?.focus?.({preventScroll:true});}
 $('relay-drawer-close').onclick=closeDrawer;$('relay-drawer').addEventListener('cancel',()=>scene?.setPaused(false));
 $('relay-drawer').addEventListener('click',e=>{if(e.target===$('relay-drawer')){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)closeDrawer();}});
 function photoHTML(p){if(!p)return '';return `<figure class="reference-photo">${p.local?`<img loading="lazy" src="${esc(p.local)}" alt="${esc(p.caption)}">`:'<div class="photo-unavailable">사진 제공 서버에 연결되지 않아 원문 링크로 안내합니다.</div>'}<figcaption><strong>${esc(p.caption)}</strong><span>${esc(p.credit)} · <a target="_blank" rel="noopener" href="${esc(p.licenseUrl)}">${esc(p.license)}</a></span><span>촬영 ${esc(p.capturedAt||'미확인')} · ${p.local?'원본 전체 표시':'이미지 미수집'}</span><a target="_blank" rel="noopener" href="${esc(p.sourceUrl)}">사진 출처 보기 ↗</a></figcaption></figure>`;}
 function documentGallery(stageNumber){
  const group=documentPhotos.filter(p=>p.stage===stageNumber);
  return `<section class="document-reference"><h3>기획 문서 속 사진과 구성 예시</h3><p>수집한 참고 이미지 ${documentPhotos.length}개 · 장면 재구성의 기준<br><small>합성·화면 구성 예시는 현장 사진과 구분했습니다. 촬영 시점과 운영 정보는 원문에서 확인하세요.</small></p><div class="document-tabs" role="group" aria-label="문서 단계 선택">${[1,2,3,4].map(n=>`<button data-doc-stage="${n}" aria-pressed="${n===stageNumber}">${n}단계 · ${['','식사','인증','체험','월영교·팝업'][n]}</button>`).join('')}</div><div class="document-photo-grid">${group.map(p=>`<button class="document-photo" data-doc-photo="${p.id}" aria-label="${esc(p.caption)} 확대"><img src="${p.thumbnail}" alt="${esc(p.caption)}" loading="lazy" width="400" height="300"><span>${esc(p.caption)}</span><small>${p.kind}</small></button>`).join('')}</div><p class="small-note">사용자 제공 문서 · 원출처 권리 유지 · 공개 재배포 전 이용허락 확인 필요</p></section>`;
 }
 function bindDocumentGallery(){
  $('relay-drawer-content').querySelectorAll('[data-doc-stage]').forEach(b=>b.onclick=()=>{const host=$('relay-doc-gallery');host.innerHTML=documentGallery(Number(b.dataset.docStage));bindDocumentGallery();host.scrollIntoView({block:'start'});});
  $('relay-drawer-content').querySelectorAll('[data-doc-photo]').forEach(b=>b.onclick=()=>{const p=documentPhotos.find(p=>p.id===b.dataset.docPhoto),host=$('relay-doc-gallery');host.innerHTML=`<div class="document-photo-detail"><button data-doc-stage="${p.stage}">← ${p.stage}단계 사진 목록</button><h3>${esc(p.caption)}</h3><img src="${p.file}" alt="${esc(p.caption)}" width="${p.width}" height="${p.height}"><p>${esc(p.kind)} · ${esc(p.credit)}</p><a href="${p.sourceUrl}" target="_blank" rel="noopener">기획 문서에서 보기 ↗</a></div>`;bindDocumentGallery();host.scrollIntoView({block:'start'});});
 }
 function showSources(){
  const d=displayed(),stage=CHAPTERS[!state.started&&preview===null?5:d.stage];const ids=research.chapters[stage.id]||[];
  const mediaIds=stage.id==='workshop'?d.program==='tea'?['tea','hahoe']:d.program==='soju'?['soju','hahoe']:['mask','hahoe']:['market','meal','receipt'].includes(stage.id)?['jjimdak','tour-2866691','tour-2679452','tour-134770']:stage.id==='popup'?['maskdance','moon','mask']:stage.id==='transit'?['moon']:['moon'];
  openDrawer('사진과 현장 정보',`${stage.id==='popup'?'<section class="popup-design-sources"><h3>추가로 참고한 공간 디자인</h3><p>부스와 식탁, 조명, 공연장 배치에 참고했습니다.</p><a href="https://kmong.com/portfolio/view/180635" target="_blank" rel="noopener">부산항 1부두 행사 조감도 · 글래드스튜디오 ↗</a><a href="https://www.behance.net/gallery/109171323/Concept-design-Night-Market-in-Beijing" target="_blank" rel="noopener">Night Market in Beijing · Coro Urdaneta ↗</a><a href="https://design.museaward.com/winners-info.php?id=33138" target="_blank" rel="noopener">MIXC YARD 2.0 · 목조 파빌리온 배치 ↗</a></section>':''}<div id="relay-doc-gallery">${documentGallery(['market','meal'].includes(stage.id)?1:stage.id==='receipt'?2:stage.id==='workshop'?3:4)}</div><p class="drawer-intro">${esc(stage.location)}<br><small>확인일 ${research.checkedAt} · 실내·부스는 기획을 설명하기 위해 재구성했습니다.</small></p><div class="reference-gallery">${mediaIds.map(id=>photoHTML(photoById(id))).join('')}</div><h3>이 장면의 확인 자료</h3>${research.sources.filter(s=>ids.includes(s.id)).map(sourceHTML).join('')}<details><summary>전체 조사 자료 ${research.sources.length}곳</summary>${research.sources.filter(s=>!ids.includes(s.id)).map(sourceHTML).join('')}</details><details><summary>현재 확인하지 못한 항목</summary><ul>${research.unknowns.map(x=>`<li>${esc(x)}</li>`).join('')}</ul></details>`);bindDocumentGallery();
 }
 function sourceHTML(s){return `<article class="source-record"><span>${esc(s.status)}</span><h4>${esc(s.title)}</h4><ul>${s.facts.map(f=>`<li>${esc(f)}</li>`).join('')}</ul><a href="${esc(s.url)}" target="_blank" rel="noopener">원문 확인 ↗</a><small>확인 ${esc(s.checkedAt)}</small></article>`;}
 let disposeRouteMap=null,routeRequest=0,routeOpener=null;
 $('relay-route-close').onclick=()=>$('relay-route-dialog').close();
 $('relay-route-dialog').addEventListener('close',()=>{routeRequest++;disposeRouteMap?.();disposeRouteMap=null;scene?.setPaused(false);routeOpener?.focus?.({preventScroll:true});});
 async function showRoute(){
  routeOpener=document.activeElement;closeMenu(false);const request=++routeRequest;
  const host=$('relay-route-host');host.innerHTML='<p class="tourism-note" role="status">지도와 혜택업체를 불러오는 중입니다.</p>';
  if(!$('relay-route-dialog').open)$('relay-route-dialog').showModal();scene?.setPaused(true);
  try {
   const model=await loadTourismMap();if(request!==routeRequest||!$('relay-route-dialog').open)return;
   host.innerHTML='<div></div>';disposeRouteMap?.();disposeRouteMap=mountTourismMap(host.firstElementChild,model);
   host.insertAdjacentHTML('beforeend',`<details class="tourism-all-benefits"><summary>교통·주차 조사 안내</summary>${Object.values(TRANSPORTS).map(t=>`<article class="source-record"><h4>${esc(t.name)}</h4><p>${esc(t.note)}</p></article>`).join('')}${sourceHTML(research.sources.find(x=>x.id==='transport'))}${sourceHTML(research.sources.find(x=>x.id==='parking'))}</details>`);
  } catch(error) {
   if(request!==routeRequest||!$('relay-route-dialog').open)return;
   host.innerHTML='<p role="status">지도를 불러오지 못했습니다.</p><button id="relay-route-retry">다시 불러오기</button>';$('relay-route-retry').onclick=showRoute;
  }
 }

 function showPopupMap(){
  if(busy)return;openDrawer('밤마당 현장 안내도',popupMapHTML(scene?.camera.position.toArray(),readLayers({booths:true})));
  $('relay-drawer-content').querySelectorAll('[data-popup-go]').forEach(b=>b.onclick=()=>{closeDrawer();moveToStation(b.dataset.popupGo);});
  $('relay-drawer-content').querySelector('[data-popup-booth-toggle]').onchange=e=>{const layers=readLayers();layers.booths=e.target.checked;saveLayers(layers);$('relay-drawer-content').querySelector('[data-popup-layout]').classList.toggle('is-booths-hidden',!layers.booths);};
  $('popup-tourism-map').onclick=()=>{closeDrawer();showRoute();};
 }
 function popupRecordHTML(){return `<ul class="journal-list"><li><span>맛본 음식·차</span><b>${state.popupTasted.map(id=>POPUP_ITEMS[id].name).join(' · ')||'아직 이용 전'}</b></li><li><span>달빛 엽서</span><b>${state.popupStamps.length}/3 도장</b></li><li><span>야경 사진</span><b>${state.popupPhotos}장</b></li></ul>${state.popupStamps.length===3?'<button id="popup-save-postcard" class="drawer-link">내가 찍은 엽서 저장하기</button>':''}`;}
 function bindPostcardDownload(){if($('popup-save-postcard'))$('popup-save-postcard').onclick=()=>{const c=document.createElement('canvas');c.width=900;c.height=600;drawPostcard(c,state.popupStamps);const a=document.createElement('a');a.href=c.toDataURL('image/png');a.download='안동-달빛-엽서.png';a.click();};}
 async function popupPhoto(){
  if(busy||state.stage!==6||!scene)return;closeMenu(false);
  try{const photo=scene.capturePhoto();dispatch({type:'PHOTO'});openDrawer('지금 바라본 안동의 밤',`<img class="popup-snapshot" src="${photo}" alt="1인칭 시점에서 직접 촬영한 밤마당 3D 장면"><a class="drawer-link" href="${photo}" download="안동-밤마당-사진.png">이 사진 저장하기</a><p>구도를 바꾸고 다시 촬영할 수 있어요.</p>`);}catch{announce('사진을 저장하지 못했어요. 다시 촬영해 주세요.');}
 }
 async function popupPostcard(){
  if(busy||state.stage!==6||!scene)return;closeMenu(false);busy=true;render();
  const panel=$('relay-work-task');
  try{
   if(!await scene.approach('print'))return;
   panel.hidden=false;app.classList.add('working-at-table','making-postcard');$('relay-work-controls').open=true;$('relay-work-title').textContent='달빛 엽서 만들기';$('relay-work-pour').hidden=true;$('relay-work-done').textContent='엽서 받기';
   $('relay-work-options').innerHTML='<div class="program-tabs"><button data-stamp="moon">달 도장</button><button data-stamp="bridge">다리 도장</button><button data-stamp="mask">탈 도장</button></div>';
   app.querySelectorAll('[data-stamp]').forEach(b=>b.onclick=()=>scene.workshop?.select(b.dataset.stamp));
   $('relay-work-assist').textContent='선택한 도장 찍기';$('relay-work-assist').onclick=()=>scene.workshop?.assist();$('relay-work-done').onclick=()=>scene.workshop?.finish(true);$('relay-work-cancel').onclick=()=>scene.workshop?.finish(false);
   const result=await scene.postcardTask({stamps:state.popupStamps,onUpdate:u=>{$('relay-work-message').textContent=u.message;$('relay-work-progress').value=u.progress;$('relay-work-done').disabled=!u.done;app.querySelectorAll('[data-stamp]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.stamp===u.selected)));}});
   if(result){for(const id of result)state=relayReducer(state,{type:'STAMP',id});persist();announce('완성한 엽서를 기록에 담았어요. 기록에서 저장할 수 있습니다.');}
  }finally{busy=false;panel.hidden=true;app.classList.remove('working-at-table','making-postcard');$('relay-work-assist').textContent='조작 도움받기';$('relay-work-done').textContent='완료';render();}
 }
 async function popupTaste(id){if(busy||state.stage!==6||!state.cart.includes(id)||!POPUP_ITEMS[id]?.edible)return;closeMenu(false);busy=true;render();try{if(await scene?.act('taste',{id})){state=relayReducer(state,{type:'TASTE',id});persist();announce(POPUP_ITEMS[id].name+' 맛보기 완료. 강변 자리에서도 쉬어가세요.');}}finally{busy=false;render();}}
 function showPopupGallery(){openDrawer('하회탈 야외 전시','<p>공예 골목 뒤편에서 탈의 표정과 형태를 가까이 둘러보세요.</p><button class="relay-primary" id="popup-gallery-go">전시 앞으로 걷기</button>');$('popup-gallery-go').onclick=()=>{closeDrawer();moveToStation('gallery');};}
 function walletHTML(){const program=PROGRAMS[state.redeemedProgram||state.program];return `${state.paid?`<article class="visitor-receipt"><small>이어드림 시연 영수증 · ED-DEMO-001</small><h3>${MEALS[state.meal].name}</h3><p>${money(MEALS[state.meal].examplePrice)} · ${state.payment==='cash'?'현금':'카드'} 결제 시연</p><small>실제 매출·결제 기록이 아닙니다.</small></article>`:''}<div class="wallet-ticket"><span>이어드림 · 체험 할인권</span><strong>10<em>%</em></strong><p>${state.coupon==='used'?'사용 완료':state.coupon==='issued'?'발급 완료 · 체험장에서 사용':'식사 후 영수증을 인증하세요'}</p><small>제안 혜택 · 이 여정의 전통 체험 1회에만 적용<br>실제 가맹점 사용·팝업 중복 할인 불가</small></div><ul class="journal-list"><li><span>식사</span><b>${state.eaten?MEALS[state.meal].name+' · 완료':'아직 이용 전'}</b></li><li><span>인증</span><b>${state.receipt==='verified'?'시연 영수증 인증 완료':'대기'}</b></li><li><span>체험</span><b>${state.completedPrograms.length?state.completedPrograms.map(p=>PROGRAMS[p].short).join(' · '):'아직 체험 전'}</b></li><li><span>이동</span><b>${state.arrived?TRANSPORTS[state.transport].name:'아직 이동 전'}</b></li><li><span>야경</span><b>${state.bridgeWalked?'월영정 산책 완료':'아직 산책 전'}</b></li><li><span>팝업</span><b>${state.cart.length?state.cart.map(p=>POPUP_ITEMS[p].name).join(' · '):'구매 시연 전'}</b></li><li><span>탈춤 장단</span><b>${state.performanceScore===null?'아직 체험 전':state.performanceScore+' / 4 박자 성공'}</b></li><li><span>투호</span><b>${state.gameScore} / ${state.gameAttempts} 성공</b></li></ul>${state.coupon==='used'?`<div class="journal-cost"><span>${program.name} · 할인 계산 예시</span><p><del>${money(program.examplePrice)}</del> → <strong>${money(program.examplePrice*.9)}</strong></p><small>예시 기준 ${money(program.examplePrice*.1)} 할인. 이 거점의 실제 판매가격은 미확정입니다.</small></div>`:''}${state.cart.length?`<h3>팝업 구매 시연 영수증</h3><ul class="journal-list">${state.cart.map(id=>`<li><span>${POPUP_ITEMS[id].name}</span><b>${money(POPUP_ITEMS[id].examplePrice)} · ${state.popupPayments[id]==='cash'?'현금':'카드'} 시연</b></li>`).join('')}</ul>`:''}${state.maskArt?`<a class="drawer-link" href="${esc(state.maskArt)}" download="내가-칠한-안동탈.png">내가 칠한 탈의 색칠 기록 저장하기 ↗</a>`:''}<p class="small-note">개인정보·실제 영수증을 수집하지 않습니다. 이 브라우저에 시연 진행 기록만 저장합니다. QR 인증은 디지털 관광주민증 실적과 별개입니다.</p>`;}
 function bindChapters(){app.querySelectorAll('[data-chapter]').forEach(b=>{const i=Number(b.dataset.chapter);b.disabled=busy||!!journey;b.onclick=()=>{closeDrawer();if(canEnter(state,i)&&state.started){preview=null;dispatch({type:'GO',index:i});}else{preview=i;render();}scene?.resetView();};});}
 function showJournal(){if(placeVisit&&placeVisit!=='popup'){openDrawer('명소에서 시작한 체험 기록',`<p>이 장소부터 별도로 체험한 기록입니다. 본 여정의 진행과 할인권은 그대로 유지됩니다.</p>${walletHTML()}${popupRecordHTML()}<button id="relay-visit-resume" class="drawer-link">전체 릴레이로 돌아가기</button>`);$('relay-visit-resume').onclick=leavePopupVisit;bindPostcardDownload();return;}if(placeVisit==='popup'){openDrawer('야간 팝업 체험 기록',`<p>팝업만 먼저 체험한 기록입니다. 본 여정의 식사·인증·전통 체험 기록은 유지됩니다.</p><ul class="journal-list"><li><span>이용한 부스</span><b>${state.cart.map(id=>POPUP_ITEMS[id].name).join(' · ')||'아직 이용 전'}</b></li><li><span>투호</span><b>${state.gameScore} / ${state.gameAttempts} 성공</b></li><li><span>탈춤 장단</span><b>${state.performanceScore===null?'아직 체험 전':state.performanceScore+' / 4'}</b></li></ul>${popupRecordHTML()}<button id="relay-popup-resume" class="drawer-link">본 여정으로 돌아가기</button>`);$('relay-popup-resume').onclick=leavePopupVisit;bindPostcardDownload();return;}openDrawer('여행 기록',`<nav class="relay-journal-stops" aria-label="방문 기록">${flowHTML(relayProgress(state,displayed().stage),{live:true,previewing:preview!==null})}</nav>${state.finished?'<button id="relay-finish-record" class="drawer-link">오늘의 여행 돌아보기</button>':''}${walletHTML()}${popupRecordHTML()}`);bindChapters();bindPostcardDownload();if($('relay-finish-record'))$('relay-finish-record').onclick=()=>{closeDrawer();showSummary();};}
 $('relay-journal').onclick=showJournal;$('relay-map').onclick=()=>state.stage===6&&!journey?showPopupMap():showRoute();$('relay-sources').onclick=showSources;
 function closeMenu(focus=true){if(!$('relay-game-menu').open)return;$('relay-game-menu').close();app.classList.remove('menu-open');scene?.setPaused(false);if(focus)$('relay-menu').focus({preventScroll:true});}
 $('relay-menu').onclick=()=>{if(busy)return;renderPlaces(state.started||preview!==null);$('relay-game-menu').showModal();app.classList.add('menu-open');scene?.setPaused(true);};
 $('relay-sound').onclick=()=>{if(!scene)return;scene.audio.setEnabled(!scene.audio.enabled);if(scene.audio.enabled)scene.audio.unlock();try{localStorage.setItem('andong-relay-sound',scene.audio.enabled?'on':'off');}catch{}$('relay-sound').setAttribute('aria-pressed',String(scene.audio.enabled));$('relay-sound').textContent='공간 소리 '+(scene.audio.enabled?'켜짐':'꺼짐');};
 $('relay-menu-close').onclick=()=>closeMenu();$('relay-game-menu').addEventListener('cancel',e=>{e.preventDefault();closeMenu();});
 $('relay-reset').onclick=()=>{openDrawer('여정을 처음부터',`<p class="drawer-intro">${placeVisit?'이 장소부터 별도로 체험한 기록을 초기화합니다. 본 여정은 유지됩니다.':'식사·쿠폰·체험·팝업 시연 기록을 초기화합니다.'}</p><button class="relay-primary" id="relay-confirm-reset">처음부터 다시 체험 ${icon('reset')}</button><p class="small-note">실제 지도와 보고서 데이터에는 영향을 주지 않습니다.</p>`);$('relay-confirm-reset').onclick=()=>{closeDrawer();preview=null;sceneKey='';if(placeVisit){state=createRelayVisit(placeVisit);persist();render();}else dispatch({type:'RESET'});$('relay-start-label').textContent='플레이';announce('시연 기록을 초기화했습니다.');};};
 $('relay-settings').onclick=()=>{openDrawer('화면과 조작',`<p class="drawer-intro">드래그 또는 방향키로 시선을 움직여보세요.<br>3D 공간을 누른 뒤 ↑↓ 또는 W A S D로 이동할 수 있습니다.<br>자동 이동 중에도 이동키를 누르면 직접 걷기로 전환됩니다.</p><div class="settings-options"><label><span>움직임 최소화<small>이동과 손동작을 짧게 표시합니다.</small></span><input type="checkbox" id="relay-reduce" ${scene?.reduced?'checked':''}></label><label><span>가볍게 보기<small>화면 해상도와 그림자를 줄입니다.</small></span><input type="checkbox" id="relay-low" ${lowQuality?'checked':''}></label></div><button id="relay-view-reset" class="drawer-link">시점을 원래대로 ${icon('reset')}</button><p class="small-note">Space: 점프 · Shift: 달리기 · E: 현재 행동 · R: 시점 복원 · 긴 이동은 건너뛰기 가능</p>`);$('relay-reduce').onchange=e=>{if(scene)scene.reduced=e.target.checked;};$('relay-low').onchange=e=>{lowQuality=e.target.checked;scene?.setQuality(lowQuality);};$('relay-view-reset').onclick=()=>{scene?.resetView();closeDrawer();};};
 $('relay-interact').onclick=()=>scene?.interact();
 function talk(role){const messages={guide:['골목 안내인','안동구시장에 오셨어요. 앞쪽 이어드림 식당으로 걸어가 간판을 바라보고 E를 눌러보세요. 식사 영수증이 다음 체험을 이어줍니다.'],host:['식당 직원',state.eaten?'식사는 어떠셨어요? 영수증을 챙겨서 QR을 직접 맞춰보세요. 발급받은 할인권은 체험장에서 사용할 수 있어요.':'어서 오세요. 찜닭, 간고등어, 헛제사밥 중 골라보세요. 메뉴를 고른 뒤 상 위의 음식을 눌러 직접 맛볼 수 있어요.'],teacher:['체험 선생님','할인권을 사용하고 원하는 체험을 골라보세요. 탈은 붓으로 직접 칠하고, 차는 알맞은 양을 따르는 게 중요해요. 다른 체험으로 옮겨도 작업은 남아있어요.'],vendor:['장터 운영자','안동의 맛과 작은 공예품이 있는 장터예요. 부스 앞으로 걸어와 물건을 눌러보세요. 옆에서는 투호도 할 수 있어요.']};const [name,message]=messages[role]||messages.vendor;$('relay-dialogue').innerHTML=`<strong>${name}</strong><p>${message}</p><button id="relay-talk-close">닫기</button>`;$('relay-dialogue').hidden=false;$('relay-talk-close').onclick=()=>{$('relay-dialogue').hidden=true;scene?.renderer.domElement.focus();};}
 async function paintInWorld(){if(!scene)return runActivity({type:'CRAFT',program:'mask',step:state.craftSteps,color:state.paintColor});$('relay-paint-task').hidden=false;app.classList.add('painting-mask');$('relay-paint-task').querySelector('progress').value=0;$('relay-paint-assist').onclick=()=>scene.paintAssist();$('relay-paint-cancel').onclick=()=>scene.cancelPaint(false);const result=await scene.paintTask({color:state.paintColor,step:state.craftSteps,onProgress:p=>{$('relay-paint-task').querySelector('progress').value=p;}});$('relay-paint-task').hidden=true;app.classList.remove('painting-mask');if(result){const artwork=scene.maskArtwork();if(artwork)state=relayReducer(state,{type:'ART',image:artwork});}return result;}
 function showProgramGuide(){const p=PROGRAMS[displayed().program],guides={mask:['나무 탈, 붓, 물감, 물통','직접 칠한 탈 · 색칠 기록 PNG 저장'],tea:['국화꽃, 다관, 주전자, 찻잔','꽃을 담고 물을 조절해 완성한 국화차'],soju:['쌀, 누룩, 물, 발효 항아리, 소주고리, 술병·표찰','전통 제조 과정과 완성품 포장 시연']},g=guides[displayed().program];openDrawer(p.name+' · 체험 안내',`<p class="drawer-intro">${esc(p.description)}</p><dl class="visit-facts"><dt>체험 시간 가정</dt><dd>${p.minutes}분</dd><dt>준비물</dt><dd>${g[0]}</dd><dt>완성품</dt><dd>${g[1]}</dd><dt>이용 금액 예시</dt><dd>${money(p.examplePrice)} → 할인 적용 시 ${money(p.examplePrice*.9)}</dd><dt>접수·정원</dt><dd>원도심 거점은 제안 단계입니다. 실제 회차·정원·예약 시스템은 미확정입니다.</dd></dl><p>${esc(p.reality)}</p><h3>공식 운영 참고</h3>${sourceHTML(research.sources.find(x=>x.id=== (displayed().program==='soju'?'soju':displayed().program==='tea'?'tea':'craft')))}`);}
 async function workshopInWorld(){
  const panel=$('relay-work-task');$('relay-work-controls').open=false;panel.hidden=false;app.classList.add('working-at-table');$('relay-work-title').textContent=PROGRAMS[state.program].steps[state.craftSteps];$('relay-work-options').innerHTML='';$('relay-work-done').disabled=true;
  let signature='';const update=t=>{$('relay-work-message').textContent=t.message;$('relay-work-progress').value=t.progress;$('relay-work-done').disabled=!t.done;$('relay-work-pour').hidden=!t.pouring;const next=JSON.stringify(t.options);if(signature!==next){signature=next;$('relay-work-options').innerHTML=t.options.map(o=>`<button data-work-choice="${o.id}" ${o.disabled?'disabled':''}>${o.disabled?'✓ ':''}${esc(o.label)}</button>`).join('');panel.querySelectorAll('[data-work-choice]').forEach(b=>b.onclick=()=>scene.workshop?.choose(b.dataset.workChoice));}for(const id of ['relay-work-hold','relay-work-tap','relay-work-check','relay-work-reset'])$(id).disabled=t.done;};
  $('relay-work-done').onclick=()=>{if(scene.workshop?.task.done)scene.workshop.finish(true);};$('relay-work-assist').onclick=()=>{$('relay-work-controls').open=true;const next=panel.querySelector('[data-work-choice]:not(:disabled)');if(next){next.focus();$('relay-work-message').textContent='키보드로도 하나씩 체험할 수 있어요. 재료 버튼을 순서대로 선택하세요.';}else{$('relay-work-tap').focus();$('relay-work-message').textContent='10%씩 붓고, 58–82% 사이에서 양 확인하기를 누르세요.'}};$('relay-work-cancel').onclick=()=>scene.workshop?.finish(false);$('relay-work-tap').onclick=()=>scene.workshop?.tap();$('relay-work-check').onclick=()=>scene.workshop?.hold(false);$('relay-work-reset').onclick=()=>scene.workshop?.reset();
  const hold=$('relay-work-hold');hold.onpointerdown=e=>{hold.setPointerCapture(e.pointerId);scene.workshop?.hold(true);};hold.onpointerup=()=>scene.workshop?.hold(false);hold.onpointercancel=()=>scene.workshop?.cancelPointer();hold.onkeydown=e=>{if(['Space','Enter'].includes(e.code)&&!e.repeat){e.preventDefault();scene.workshop?.hold(true);}};hold.onkeyup=e=>{if(['Space','Enter'].includes(e.code)){e.preventDefault();scene.workshop?.hold(false);}};hold.onblur=()=>scene.workshop?.cancelPointer();
  const result=await scene.workshopTask({program:state.program,step:state.craftSteps,onUpdate:update});panel.hidden=true;app.classList.remove('working-at-table');return result;
 }
 async function eatInWorld(){
  const panel=$('relay-work-task'),mouth=$('relay-mouth');$('relay-work-controls').open=false;panel.hidden=false;mouth.hidden=false;app.classList.add('working-at-table','eating-meal');
  $('relay-work-title').textContent=MEALS[state.meal].name+' · 직접 맛보기';$('relay-work-pour').hidden=true;$('relay-work-done').disabled=true;$('relay-work-done').textContent='식사 마치기';
  $('relay-work-options').innerHTML='<button id="relay-bite">키보드로 한 입 집어 먹기</button>';$('relay-work-assist').textContent='조작 방법 보기';
  $('relay-bite').onclick=()=>scene.meal?.keyboardBite();$('relay-work-assist').onclick=()=>{$('relay-work-controls').open=true;$('relay-work-message').textContent='음식을 누른 채 입 모양으로 끌어오세요. 키보드는 한 입 버튼을 세 번 이용하세요.';};
  $('relay-work-cancel').onclick=()=>scene.meal?.finish(false);$('relay-work-done').onclick=()=>scene.meal?.finish(true);
  const result=await scene.mealTask({dropBounds:()=>mouth.getBoundingClientRect(),onUpdate:t=>{
   $('relay-work-message').textContent=t.message;$('relay-work-progress').value=t.count/3;$('relay-work-done').disabled=!t.done;$('relay-bite').disabled=t.done||t.holding;
   mouth.classList.toggle('ready',t.holding);mouth.classList.toggle('inside',t.inside);mouth.querySelector('span').textContent=t.done?'맛보기 완료':t.inside?'여기서 놓으세요':`입 쪽으로 가져오기 · ${t.count} / 3`;
  }});
  panel.hidden=true;mouth.hidden=true;app.classList.remove('working-at-table','eating-meal');$('relay-work-done').textContent='완료';$('relay-work-assist').textContent='조작 도움받기';return result;
 }
 async function payInWorld(method){
  const panel=$('relay-work-task');$('relay-work-controls').open=false;panel.hidden=false;app.classList.add('working-at-table','paying-meal');$('relay-work-title').textContent='계산하기';$('relay-work-pour').hidden=true;$('relay-work-done').textContent='영수증 챙기기';$('relay-work-done').disabled=true;
  $('relay-work-options').innerHTML='<button id="relay-pay-step">키보드로 결제 수단 건네기</button>';$('relay-work-assist').textContent='조작 방법 보기';
  $('relay-pay-step').onclick=()=>scene.payment?.assist();$('relay-work-cancel').onclick=()=>scene.payment?.finish(false);$('relay-work-done').onclick=()=>scene.payment?.finish(true);
  $('relay-work-assist').onclick=()=>{$('relay-work-controls').open=true;$('relay-work-message').textContent='카드·현금을 단말기의 금색 원으로 끌어다 놓고, 출력된 영수증을 누르세요. 키보드는 단계별 버튼으로 진행할 수 있어요.';};
  const result=await scene.paymentTask({meal:MEALS[state.meal],method,onUpdate:t=>{
   $('relay-work-message').textContent=t.message;$('relay-work-progress').value=t.progress;$('relay-work-done').disabled=!t.done;
   $('relay-pay-step').disabled=!['ready','receipt'].includes(t.phase);$('relay-pay-step').textContent=t.phase==='receipt'?'키보드로 출력된 영수증 받기':'키보드로 결제 수단 건네기';
  }});
  panel.hidden=true;app.classList.remove('working-at-table','paying-meal');$('relay-work-done').textContent='완료';$('relay-work-assist').textContent='조작 도움받기';return result;
 }
 async function scanInWorld(){
  const panel=$('relay-work-task');$('relay-work-controls').open=false;panel.hidden=false;app.classList.add('working-at-table');$('relay-work-title').textContent='손에 든 영수증 QR 인증';$('relay-work-progress').value=0;$('relay-work-pour').hidden=true;$('relay-work-done').disabled=true;$('relay-work-done').textContent='할인권 받기';
  $('relay-work-options').innerHTML='<div class="scan-directions"><button data-scan-shift="-.025,0" aria-label="영수증 왼쪽으로">←</button><button data-scan-shift="0,.025" aria-label="영수증 위로">↑</button><button data-scan-shift="0,-.025" aria-label="영수증 아래로">↓</button><button data-scan-shift=".025,0" aria-label="영수증 오른쪽으로">→</button><small>화면 위를 드래그해 영수증 이동 · 샘플 QR</small></div>';
  app.querySelectorAll('[data-scan-shift]').forEach(b=>b.onclick=()=>scene.scanner?.shift(...b.dataset.scanShift.split(',').map(Number)));
  $('relay-work-assist').onclick=()=>scene.scanner?.align();$('relay-work-cancel').onclick=()=>scene.scanner?.finish(false);$('relay-work-done').onclick=()=>{if(scene.scanner?.done)scene.scanner.finish(true);};
  const completed=await scene.scanTask(u=>{$('relay-work-message').textContent=u.message;$('relay-work-progress').value=u.progress;$('relay-work-done').disabled=!u.done;});panel.hidden=true;app.classList.remove('working-at-table');$('relay-work-done').textContent='완료';return completed;
 }
 async function tuhoInWorld(){
  const panel=$('relay-work-task');$('relay-work-controls').open=false;panel.hidden=false;app.classList.add('working-at-table','playing-tuho');$('relay-work-title').textContent=`투호 · ${state.gameAttempts+1}번째 화살`;$('relay-work-pour').hidden=true;$('relay-work-progress').value=state.gameAttempts/3;
  $('relay-work-options').innerHTML='<div class="scan-directions"><button data-tuho-shift="-.06,0" aria-label="조준 왼쪽으로">←</button><button data-tuho-shift="0,-.06" aria-label="조준 멀리">↑</button><button data-tuho-shift="0,.06" aria-label="조준 가까이">↓</button><button data-tuho-shift=".06,0" aria-label="조준 오른쪽으로">→</button><small>키보드: 방향키로 조준 · Space로 던지기</small></div>';
  panel.querySelectorAll('[data-tuho-shift]').forEach(b=>b.onclick=()=>scene.tuho?.shift(...b.dataset.tuhoShift.split(',').map(Number)));
  $('relay-work-done').textContent='조준한 곳으로 화살 던지기';$('relay-work-done').disabled=false;$('relay-work-done').onclick=()=>scene.tuho?.throw();$('relay-work-cancel').onclick=()=>scene.tuho?.finish(null);$('relay-work-assist').onclick=()=>{$('relay-work-controls').open=true;$('relay-work-message').textContent='금색 원을 항아리 입구에 맞추세요. 빗나가도 놀이 기록은 남고, 취소하면 기회를 쓰지 않아요.';};
  const result=await scene.tuhoTask({onUpdate:t=>{$('relay-work-message').textContent=t.message;$('relay-work-done').disabled=t.flying;panel.querySelectorAll('[data-tuho-shift]').forEach(b=>b.disabled=t.flying);}});
  panel.hidden=true;app.classList.remove('working-at-table','playing-tuho');$('relay-work-done').textContent='완료';return result;
 }
 function performanceInWorld(){return new Promise(resolve=>{
  const panel=$('relay-work-task');$('relay-work-controls').open=false;panel.hidden=false;app.classList.add('working-at-table','watching-performance');scene?.watchPerformance();$('relay-work-controls').open=true;$('relay-work-title').textContent='탈춤 장단 따라하기';$('relay-work-message').textContent='빛이 가운데 금색 구간을 지날 때 장단을 눌러보세요.';$('relay-work-progress').value=0;$('relay-work-pour').hidden=true;$('relay-work-done').disabled=true;$('relay-work-options').innerHTML='<div class="rhythm-game"><div class="rhythm-track"><i id="relay-beat"></i></div><button id="relay-clap">장단 맞추기</button><label><input id="relay-beat-assist" type="checkbox">천천히 연습하기</label></div>';let tries=0,score=0,phase=0,frame=0,closed=false,last=performance.now(),slow=false;
  const finish=value=>{if(closed)return;closed=true;cancelAnimationFrame(frame);panel.hidden=true;app.classList.remove('working-at-table','watching-performance');scene?.syncHands();resolve(value);};const tick=now=>{phase=(phase+Math.min(.05,(now-last)/1000)/(slow?4.5:1.8))%1;last=now;$('relay-beat').style.left=(phase*100)+'%';frame=requestAnimationFrame(tick);};frame=requestAnimationFrame(tick);
  $('relay-beat-assist').onchange=e=>slow=e.target.checked;$('relay-clap').onclick=()=>{if(tries>=4)return;const hit=Math.abs(phase-.5)<=.17;tries++;if(hit)score++;phase=0;$('relay-work-progress').value=tries/4;$('relay-work-message').textContent=(hit?'장단이 맞았어요! ':'조금 더 가운데에서 눌러보세요. ')+tries+' / 4회 · '+score+'성공';if(tries===4){$('relay-clap').disabled=true;$('relay-work-done').disabled=false;cancelAnimationFrame(frame);}};$('relay-work-done').onclick=()=>{if(tries===4)finish(score);};$('relay-work-assist').onclick=()=>{$('relay-work-controls').open=true;slow=true;$('relay-beat-assist').checked=true;$('relay-work-message').textContent='장단이 천천히 움직여요. 가운데에서 눌러보세요.';};$('relay-work-cancel').onclick=()=>finish(null);
 });}
 function contextHTML(d){
  const disabled=busy||preview!==null;
  if(d.stage===0)return `<p class="control-kicker">첫 번째 방문</p><h2>안동구시장 찜닭골목</h2><p>골목을 둘러본 뒤 식당 안으로 들어가요. 메뉴와 실용 정보는 사진·현장 정보에서 확인할 수 있어요.</p><div class="context-facts"><span>식당 내부 재구성</span><span>식사 45분 가정</span></div>${d.ordered?'<p class="context-small">주문한 식사와 영수증 기록은 식당에 그대로 남아 있어요.</p>':''}${d.coupon!=='none'?'<button id="relay-market-workshop" class="relay-inline">할인권 들고 공방으로 가기</button>':''}`;
  if(d.stage===1)return `<div class="program-tabs" aria-label="식사 자리">${Object.entries(DINING_SEATS).map(([id,s])=>`<button data-seat="${id}" aria-pressed="${d.seat===id}" ${disabled||d.ordered?'disabled':''}>${s.name}</button>`).join('')}</div><p class="control-kicker">오늘의 메뉴</p><div class="meal-options">${Object.entries(MEALS).map(([id,m])=>`<button data-meal="${id}" aria-pressed="${d.meal===id}" ${disabled||d.ordered?'disabled':''}><b>${m.name}</b><small>${m.detail}</small>${d.meal===id?icon('check',16):''}</button>`).join('')}</div><p class="context-small">${d.eaten?'맛있게 먹었습니다. 계산대에서 영수증을 받아보세요.':'메뉴 가격은 현장 확인이 필요합니다. 이 식당은 기획 시연용 공간입니다.'}</p>`;
  if(d.stage===2&&!d.paid)return `<div class="receipt-preview"><p class="control-kicker">계산대에서</p><h2>한 끼를 다음 경험으로</h2><p>${MEALS[d.meal].name}을 맛봤어요. 계산을 마치고 영수증을 받아보세요.</p><strong>${money(MEALS[d.meal].examplePrice)} · 예시</strong><p class="context-small">실제 카드·현금은 사용하지 않습니다.</p></div>`;
  if(d.stage===2)return `<div class="phone-ui ${busy?'scanning':''}"><div class="phone-top">이어드림 <span>영수증 인증</span></div>${d.coupon==='none'?`<div class="scan-frame"><div class="demo-qr" aria-hidden="true">${Array.from({length:81},(_,i)=>`<i style="opacity:${(i*3+Math.floor(i/9)*7)%5<3?1:0}"></i>`).join('')}</div><span class="scan-line"></span></div><strong>${d.scanError?'인식하지 못했어요':'QR을 화면 가운데 놓아주세요'}</strong><p>${d.scanError?'영수증을 밝은 곳에 놓고 다시 스캔하세요.':'개인정보 없는 샘플 영수증으로 체험합니다.'}</p>`:`<div class="coupon-success">${icon('check',24)}<strong>체험 10% 할인권</strong><p>${d.coupon==='used'?'이미 사용한 할인권입니다.':'발급 완료 · 다음 체험에서 사용하세요.'}</p></div>`}<small>ED-DEMO-001 · 시연 전용</small></div>${d.paid&&d.coupon==='none'?`<button class="relay-inline" id="relay-scan-fail" ${disabled?'disabled':''}>흐린 영수증으로 인식 실패 체험</button>`:''}`;
  if(d.stage===3){const p=PROGRAMS[d.program];return `<p class="control-kicker">내가 고르는 전통 체험</p><div class="program-tabs">${Object.entries(PROGRAMS).map(([id,p])=>`<button data-program="${id}" aria-pressed="${d.program===id}" ${disabled?'disabled':''}>${p.short}${d.completedPrograms.includes(id)?' ✓':''}</button>`).join('')}</div><h2>${p.name}</h2><p>${p.description}</p>${d.coupon==='issued'?`<div class="price-example"><span>시연 가격 예시 · 10% 적용</span><b><del>${money(p.examplePrice)}</del> ${money(p.examplePrice*.9)}</b></div>`:`<ol class="craft-steps">${p.steps.map((x,i)=>`<li class="${d.craftSteps>i?'done':d.craftSteps===i?'current':''}"><span>${d.craftSteps>i?'✓':i+1}</span>${x}</li>`).join('')}</ol>`}${d.program==='mask'?`<div class="paint-colors" aria-label="탈 바탕색">${['#c77a48','#d9b661','#4a8274','#bd5b4b'].map((c,i)=>`<button data-color="${c}" aria-label="${['나무빛','국화빛','청록','다홍'][i]}" aria-pressed="${d.paintColor===c}" style="--paint:${c}" ${disabled?'disabled':''}></button>`).join('')}<span>탈 바탕색</span></div>`:''}<button id="relay-program-guide" class="relay-inline">준비물·완성품·예약 안내 보기 ↗</button><details class="program-reality"><summary>실제 운영과 시연의 차이</summary><p>${p.reality}</p><p>회차 정원·현재 예약 가능일·휴무는 확인 필요. 체험 10% 할인은 제안입니다.</p></details>`;}
  if(d.stage===4)return `<p class="control-kicker">원도심에서 월영교까지</p><h2>저녁 이동을 선택하세요</h2><div class="transport-options">${Object.entries(TRANSPORTS).map(([id,t])=>`<button data-transport="${id}" aria-pressed="${d.transport===id}" ${disabled||d.arrived?'disabled':''}><b>${t.name}</b><span>${t.minutes}분 가정</span></button>`).join('')}</div><p class="context-small">${TRANSPORTS[d.transport].note}</p><button class="relay-inline" id="relay-transit-source">실제 버스 시간표·택시·주차 정보 ↗</button>`;
  if(d.stage===5)return `<p class="control-kicker">월영교의 밤</p><h2>강 위에 남은 달빛</h2><p>난간 너머 문보트와 황포돛배를 둘러보고 월영정으로 걸어보세요.</p><div class="bridge-options"><button id="relay-fountain" ${disabled?'disabled':''}>분수 연출 켜기 / 끄기</button><button id="relay-bridge-info">방문·운항 정보</button></div><p class="context-small">분수·조명·배는 풍경 연출입니다. 실제 가동·운항 시간과 요금은 현장 확인이 필요합니다.</p>`;
  return `<p class="control-kicker">월영교 야간 팝업 · 제안</p><h2>월영 밤마당</h2><button id="popup-site-guide" class="relay-inline">밤마당 현장 안내도</button><div class="popup-products">${Object.entries(POPUP_ITEMS).map(([id,p])=>`<button data-buy="${id}" ${disabled||(d.cart.includes(id)&&!p.edible)?'disabled':''}><span><b>${p.name}</b><small>${d.cart.includes(id)?p.edible?(d.popupTasted.includes(id)?'맛보기 완료 · 다시 맛보기':'손에 들고 맛보기'):'기념품 수령 완료':money(p.examplePrice)+' · 예시'}</small></span>${icon(d.cart.includes(id)?'check':'arrow',16)}</button>`).join('')}</div><div class="popup-extra"><button id="popup-postcard">달빛 엽서 만들기</button><button id="popup-photo">지금 풍경 사진 찍기</button><button id="popup-gallery">하회탈 야외 전시</button></div><button id="relay-performance" class="relay-inline" ${disabled?'disabled':''}>${d.performanceScore!==null?'탈춤 장단 다시 해보기 · '+d.performanceScore+'/4 성공':'탈춤 장단 따라하기'}</button><div class="tuho-game"><label for="relay-aim">투호 놀이 <span>${d.gameScore}성공 / ${d.gameAttempts}회</span></label>${scene?'':`<input id="relay-aim" type="range" min="0" max="100" value="${aim}" aria-label="투호 조준" ${disabled||d.gameAttempts>=3?'disabled':''}>`}<small>${scene?'항아리 입구를 직접 조준하고 놓아 던지세요':'가운데 표적에 조준하세요'} · 남은 기회 ${3-d.gameAttempts}회</small><button id="relay-throw" ${disabled||d.gameAttempts>=3?'disabled':''}>${d.gameAttempts>=3?'놀이 완료':scene?'직접 조준하고 투호하기':'화살 던지기'}</button></div>`;
 }
 function render(){
  if(journey){renderJourney();return;}
  app.classList.remove('relay-linking');$('relay-link-back').hidden=true;$('relay-link-transport').hidden=true;
  const d=displayed(),live=state.started||preview!==null,c=CHAPTERS[d.stage];app.dataset.stage=c.id;app.classList.toggle('tour-live',live);app.classList.toggle('tour-busy',busy);$('relay-dialogue').hidden=true;
  $('relay-popup-return').textContent='전체 릴레이로 돌아가기';$('relay-popup-return').hidden=!placeVisit;$('relay-popup-return').disabled=busy;
  $('relay-popup-entry').hidden=d.stage===6;$('relay-popup-entry').disabled=busy;
  $('relay-reset').disabled=busy;document.querySelector('.relay-welcome').hidden=live;document.querySelector('.relay-play-header').hidden=!live;document.querySelector('.relay-control').hidden=!live;document.querySelector('.relay-mobile-look').hidden=!live;
  $('relay-start').disabled=!sceneReady;$('relay-popup-welcome').disabled=!sceneReady;$('relay-start-label').textContent=!sceneReady?'불러오는 중':state.started?'계속하기':'플레이';
  const location=hudLocation(c.id);$('relay-area').textContent=location.area;$('relay-title').textContent=location.place;
  $('relay-preview-note').hidden=preview===null;$('relay-context').innerHTML=contextHTML(d);const action=nextAction(d);
  $('relay-action').textContent=busy?'잠시만요':preview!==null?'내 여행으로 돌아가기':hudActionLabel(action);
  $('relay-action').disabled=!sceneReady||busy||(preview===null&&!!action.disabled);
  if(d.stage===6&&preview===null&&!busy){$('relay-action').textContent=placeVisit&&d.finished?'본 여정으로 돌아가기':action.disabled?'부스 둘러보기':placeVisit?'이 체험 마치기':'여행 마치기';$('relay-action').disabled=!sceneReady;}
  $('relay-ride-again').hidden=busy||preview!==null||d.stage!==4||!d.arrived||d.transport!=='shuttle';
  $('relay-action-note').innerHTML=busy?'<button id="relay-skip">동작 건너뛰기</button>':'';
  $('relay-menu').disabled=busy;$('relay-map').disabled=busy;$('relay-journal').disabled=busy;
  bindChapters();
  app.querySelectorAll('[data-seat]').forEach(b=>b.onclick=()=>chooseSeat(b.dataset.seat));
  app.querySelectorAll('[data-meal]').forEach(b=>b.onclick=()=>dispatch({type:'MEAL',id:b.dataset.meal}));app.querySelectorAll('[data-program]').forEach(b=>b.onclick=()=>dispatch({type:'PROGRAM',id:b.dataset.program}));app.querySelectorAll('[data-color]').forEach(b=>b.onclick=()=>dispatch({type:'COLOR',color:b.dataset.color}));app.querySelectorAll('[data-transport]').forEach(b=>b.onclick=()=>dispatch({type:'TRANSPORT',id:b.dataset.transport}));app.querySelectorAll('[data-buy]').forEach(b=>b.onclick=()=>state.cart.includes(b.dataset.buy)?popupTaste(b.dataset.buy):perform({type:'BUY',id:b.dataset.buy,animation:'buy'}));
  if($('popup-site-guide'))$('popup-site-guide').onclick=showPopupMap;if($('popup-postcard'))$('popup-postcard').onclick=popupPostcard;if($('popup-photo'))$('popup-photo').onclick=popupPhoto;if($('popup-gallery'))$('popup-gallery').onclick=showPopupGallery;
  if($('relay-scan-fail'))$('relay-scan-fail').onclick=()=>perform({type:'SCAN',valid:false,animation:'scan'});
  if($('relay-program-guide'))$('relay-program-guide').onclick=showProgramGuide;
  if($('relay-transit-source'))$('relay-transit-source').onclick=showRoute;if($('relay-bridge-info'))$('relay-bridge-info').onclick=showSources;if($('relay-fountain'))$('relay-fountain').onclick=()=>{scene?.fountain();announce('분수 시연을 전환했습니다. 실제 운영 시간과는 무관합니다.');};
  if($('relay-market-workshop'))$('relay-market-workshop').onclick=()=>perform({type:'GO',index:3});
  if($('relay-performance'))$('relay-performance').onclick=()=>perform({type:'PERFORMANCE'});
  if($('relay-aim'))$('relay-aim').oninput=e=>{aim=Number(e.target.value);};if($('relay-throw'))$('relay-throw').onclick=()=>perform({type:'THROW',hit:Math.abs(aim-50)<=10,animation:'game'});
  if($('relay-skip'))$('relay-skip').onclick=()=>{if(scene?.action)scene.action.elapsed=scene.action.duration;};
  const options={cart:d.cart,payment:d.payment,gameScore:d.gameScore,gameAttempts:d.gameAttempts,ordered:d.ordered,eaten:d.eaten,paid:d.paid,meal:d.meal,seat:d.seat,program:d.program,craftSteps:d.craftSteps,color:d.paintColor,maskArt:d.maskArt,transport:d.transport,cover:!live,walked:d.bridgeWalked};const id=live?c.id:'bridge';const key=JSON.stringify([id,options]);if(scene&&key!==sceneKey){scene.setScene(id,options);sceneKey=key;}
  $('relay-jump').hidden=!live||id==='transit';renderPlaces(live);
 }
 function renderPlaces(live){
  if(journey){$('relay-places').hidden=true;return;}
  const stations=scene?.current?.stations||{};$('relay-places').hidden=!live||!Object.keys(stations).length||preview!==null;
  $('relay-place-buttons').innerHTML=Object.entries(stations).map(([id,p])=>`<button data-place="${id}" aria-pressed="${scene.station===id}" ${busy?'disabled':''}>${esc(p.name)}${scene.station===id?' · 현재':''}</button>`).join('');
  $('relay-place-status').textContent=scene?.station?`${stations[scene.station]?.name||'체험 자리'}`:'직접 걸어가거나 원하는 자리를 선택하세요.';
  app.querySelectorAll('[data-place]').forEach(b=>b.onclick=()=>{closeMenu(false);moveToStation(b.dataset.place);});
 }
 function renderJourney(){
  const def=JOURNEYS[journey.id],leg=def.legs[journey.leg];app.classList.add('relay-linking');app.classList.toggle('tour-busy',busy);
  $('relay-title').textContent=def.location.replaceAll(' → ',' · ');$('relay-area').textContent='안동 · 이동 중';
  $('relay-action').textContent=busy?'걸어가는 중':leg.label.replaceAll(' →','');$('relay-action').disabled=busy;$('relay-action-note').textContent='';
  $('relay-menu').disabled=busy;$('relay-map').disabled=busy;$('relay-journal').disabled=busy;
  $('relay-link-transport').hidden=journey.id!=='pickup';if(journey.id==='pickup'){$('relay-link-transport').innerHTML=Object.entries(TRANSPORTS).map(([id,t])=>`<button data-link-transport="${id}" aria-pressed="${state.transport===id}" ${busy||state.arrived?'disabled':''}><b>${esc(t.name)}</b><span>${t.minutes}분 가정</span></button>`).join('');app.querySelectorAll('[data-link-transport]').forEach(b=>b.onclick=()=>{state=relayReducer(state,{type:'TRANSPORT',id:b.dataset.linkTransport});persist();render();});if(state.transport==='walk'&&journey.leg===1)$('relay-action').textContent='보행로로 출발';}
  $('relay-popup-entry').disabled=true;
  $('relay-link-back').hidden=false;$('relay-link-back').disabled=busy;$('relay-places').hidden=true;$('relay-reset').disabled=true;$('relay-dialogue').hidden=true;
  document.querySelectorAll('[data-chapter]').forEach(b=>b.disabled=true);
  const options={journey:journey.id,transport:state.transport,cover:false};const key=JSON.stringify(['link',options]);if(scene&&sceneKey!==key){scene.setScene('link',options);sceneKey=key;}

 }
 async function advanceJourney(){
  if(!journey||busy)return;const active=journey,def=JOURNEYS[active.id];busy=true;render();
  try{if(!await scene.approach(def.legs[active.leg].key))return;if(journey!==active)return;
   active.leg++;if(active.leg===def.legs.length){journey=null;sceneKey='';state=relayReducer(state,active.action);persist();announce('도착했습니다.');}
  }catch(error){console.error('Relay walking failed',error);announce('길 안내를 다시 시도할 수 있어요.');}finally{busy=false;render();}
 }
 $('relay-link-back').onclick=()=>{closeMenu(false);scene?.cancelNavigation();journey=null;sceneKey='';busy=false;render();};
 async function chooseSeat(id,menu=false){
  if(busy||preview!==null||state.stage!==1||!Object.hasOwn(DINING_SEATS,id))return;
  if(state.ordered&&id!==state.seat){announce('주문한 음식이 있는 자리로 돌아가세요.');return;}
  closeMenu(false);dispatch({type:'SEAT',id});
  if(menu)await perform(nextAction(state));else await moveToStation('table');
 }
 async function useRestaurantDoor(direction,{walk=true}={}){
  if(!sceneReady||!scene||busy||preview!==null||journey||!state.started)return;
  const entering=direction==='enter';if(entering?state.stage!==0:![1,2].includes(state.stage))return;
  const walkingView=walk?{}:{yaw:scene.yaw,pitch:scene.pitch};
  closeMenu(false);busy=true;render();
  try{
   if(walk&&!await scene.approach(entering?'entrance':'exit'))return;
   if(entering&&!await scene.act('enter'))return;
   state=relayReducer(state,{type:'GO',index:entering?restaurantStage(state):0});persist();
   busy=false;render();scene.placeAt({...RESTAURANT_ARRIVALS[entering?'dining':'market'],...walkingView});scene.renderer.domElement.focus({preventScroll:true});
  }catch(error){console.error('Restaurant doorway failed',error);announce('출입구로 다시 이동할 수 있어요. 여행 기록은 유지됩니다.');}
  finally{busy=false;render();}
 }
 async function moveToStation(id){if(id==='exit'&&[1,2].includes(state.stage))return useRestaurantDoor('exit');if(busy||!scene||preview!==null)return;busy=true;render();try{const arrived=await scene.approach(id);if(arrived)announce(`${scene.current.stations[id].name} 도착`);}finally{busy=false;render();}}
 function actionStation(action){
  if(action.type==='ORDER'||action.type==='EAT'||action.type==='CRAFT')return 'table';
  if(['PAY','SCAN','REDEEM'].includes(action.type))return 'counter';
  if(action.type==='WALK')return 'pavilion';if(action.type==='FINISH'&&action.disabled)return 'tea';if(action.type==='BUY')return action.id;if(action.type==='THROW')return 'game';if(action.type==='PERFORMANCE')return 'performance';
  if(action.type==='GO'&&state.stage===0)return 'entrance';if(action.type==='GO'&&state.stage===1&&action.index===2)return 'counter';return null;
 }
 async function perform(action){if(!sceneReady||busy||preview!==null)return;if(state.stage===0&&action.type==='GO'&&action.index===1)return useRestaurantDoor('enter');closeMenu(false);busy=true;render();try{let completed=true;
  const link=action.type==='GO'&&canEnter(state,action.index)?journeyFor(state.stage,action.index):null;
  if(link&&scene){const def=JOURNEYS[link];if(def.exit&&!await scene.approach(def.exit)){busy=false;render();return;}journey={id:link,action,leg:0};busy=false;render();return;}
  const station=actionStation(action);if(station&&scene&&!await scene.approach(station)){busy=false;render();return;}
  if(['ORDER','PAY','REDEEM','BUY'].includes(action.type)){
   scene?.setPaused(true);
   const items=action.type==='ORDER'?MEALS:action.type==='PAY'?{[state.meal]:MEALS[state.meal]}:action.type==='REDEEM'?{[state.program]:PROGRAMS[state.program]}:{[action.id]:POPUP_ITEMS[action.id]};
   const result=await runCheckout({title:action.type==='ORDER'?'메뉴':action.type==='PAY'?'식사 계산과 영수증':action.type==='REDEEM'?'체험 접수':'상품 보기',items,inWorld:action.type==='PAY'&&!!scene,selected:action.type==='ORDER'?state.meal:null,order:action.type==='ORDER',coupon:action.type==='REDEEM',discount:action.type==='REDEEM'?10:0});
   scene?.setPaused(false);completed=!!result;if(result){if(action.type==='ORDER')state=relayReducer(state,{type:'MEAL',id:result.id});if(action.type==='PAY'||action.type==='BUY')action={...action,method:result.method};if(action.type==='PAY'&&scene)completed=await payInWorld(result.method);}
  }else if(action.type==='SCAN'&&action.valid!==false&&scene){completed=await scanInWorld();}
  else if(action.type==='PERFORMANCE'){const score=await performanceInWorld();completed=score!==null;action={...action,score};}
  else if(action.type==='THROW'&&scene){const result=await tuhoInWorld();completed=!!result;action={...action,hit:result?.hit,animation:null};}
  else if(action.type==='EAT'&&scene)completed=await eatInWorld();
  else if(action.type==='CRAFT'&&state.program==='mask')completed=await paintInWorld();
  else if(action.type==='CRAFT'&&scene)completed=await workshopInWorld();
  else if(action.type==='EAT'||action.type==='CRAFT'||(action.type==='SCAN'&&action.valid!==false)){scene?.keys.clear();completed=await runActivity({type:action.type,program:state.program,step:state.craftSteps,color:state.paintColor,onInput:()=>scene?.act('eat')});}
  if(completed&&action.type==='ARRIVE'){$('relay-bus-tools').hidden=!scene?.current?.refs.busCabin;$('relay-bus-bell').textContent='하차 벨';$('relay-bus-bell').setAttribute('aria-pressed','false');$('relay-trip-progress').hidden=false;$('relay-trip-meter').value=0;$('relay-trip-view').textContent='이동 경로를 3D로 보기';app.classList.add('travelling');}
  if(completed&&action.animation&&scene&&(action.type!=='GO'||state.stage===0)&&action.type!=='EAT'&&action.type!=='WALK'&&!(action.type==='CRAFT'&&state.program!=='mask'))completed=await scene.act(action.animation,action);busy=false;$('relay-trip-progress').hidden=true;app.classList.remove('travelling');if(!completed){render();return;}const before=state;state=relayReducer(state,action);persist();if(action.type==='ORDER'&&scene){busy=true;render();await scene.act('serve');busy=false;}render();
  if(action.type==='GO')$('relay-title').focus({preventScroll:true});
  if(state!==before){const messages={ORDER:'상차림이 준비됐습니다.',PAY:'영수증을 받았습니다.',EAT:'잘 먹었습니다.',SCAN:state.scanError?'인증 실패: 흐린 QR입니다. 다시 스캔할 수 있어요.':'체험 할인권을 여행 기록에 담았습니다.',REDEEM:'체험 접수를 마쳤습니다.',CRAFT:state.craftSteps===3?`${PROGRAMS[state.program].name} 완성! 다른 체험도 선택할 수 있어요.`:`${state.craftSteps} / 3 단계 완료`,PERFORMANCE:'탈춤 장단 체험을 여행 기록에 담았어요.',ARRIVE:'월영교에 도착했습니다.',WALK:'월영정에 도착했습니다.',BUY:'구매 시연을 여행 기록에 담았습니다.',THROW:action.hit?'성공! 화살이 들어갔어요.':'아쉽게 빗나갔어요. 가운데로 다시 조준해보세요.'};if(messages[action.type])announce(messages[action.type]);}
  if(action.type==='FINISH'&&state.finished){if(placeVisit)showJournal();else announce('오늘의 여행을 기록했습니다.');}
  }catch(error){console.error('Relay action failed',error);busy=false;scene?.setPaused(false);app.classList.remove('travelling','working-at-table','painting-mask','paying-meal','eating-meal');$('relay-work-task').hidden=true;$('relay-paint-task').hidden=true;$('relay-trip-progress').hidden=true;render();announce('동작을 마치지 못했습니다. 진행 기록은 유지되어 다시 시도할 수 있어요.');}
 }
 function showSummary(){const p=PROGRAMS[state.redeemedProgram||state.program];$('relay-summary-content').innerHTML=`<p class="relay-overline">YOUR ANDONG STORY</p><div class="finish-seal">이어<br>드림</div><h2>한 끼가,<br>하루의 추억이 되었어요.</h2><p>원도심의 식사와 체험에서 월영교의 밤까지.<br>이어드림의 세 단계를 모두 경험했습니다.</p><div class="finish-relay" aria-label="완주한 릴레이">${RELAY_STEPS.map(step=>`<span>✓ ${step.label}</span>`).join('<i>→</i>')}</div><div class="finish-route"><span>${MEALS[state.meal].name}</span> → <span>${state.completedPrograms.map(x=>PROGRAMS[x].short).join(' · ')}</span> → <span>월영교·팝업</span></div><div class="finish-stats"><div><b>${state.completedPrograms.length}</b><span>완성한 전통 체험</span></div><div><b>${money(p.examplePrice*.1)}</b><span>체험 할인 예시</span></div><div><b>${state.cart.length}</b><span>팝업 구매 시연</span></div></div><button class="relay-primary" id="relay-another">다른 전통 체험도 해보기 ${icon('arrow')}</button><a class="summary-atlas" href="?layout=journey">전체 지도에서 코스·귀가편 살펴보기 ↗</a><small>모든 이용 기록과 할인은 시연입니다. 실제 방문·매출·주민증 실적에 합산하지 않습니다.</small>`;$('relay-summary').showModal();scene?.setPaused(true);$('relay-another').onclick=()=>{$('relay-summary').close();scene?.setPaused(false);dispatch({type:'GO',index:3});};}
 $('relay-summary-close').onclick=()=>{$('relay-summary').close();scene?.setPaused(false);};$('relay-summary').addEventListener('cancel',()=>scene?.setPaused(false));
 $('relay-game-look').onclick=()=>{if(state.started&&!busy&&preview===null){closeMenu(false);scene?.toggleGameLook();}else announce('체험을 시작한 뒤 게임 조작을 켜세요.');};
 $('relay-walking-cancel').onclick=()=>scene?.cancelNavigation();
 $('relay-trip-skip').onclick=()=>{if(scene?.action?.type==='travel')scene.action.elapsed=scene.action.duration;};
 $('relay-ride-again').onclick=()=>perform({type:'ARRIVE',animation:'travel'});
 $('relay-bus-bell').onclick=()=>{if(scene?.requestBusStop()){$('relay-bus-bell').textContent='하차 요청됨';$('relay-bus-bell').setAttribute('aria-pressed','true');}};
 $('relay-trip-view').onclick=()=>{$('relay-trip-view').textContent=scene?.toggleRouteView()?'탑승 시점으로 돌아가기':'이동 경로를 3D로 보기';};
 $('relay-start').onclick=()=>{preview=null;dispatch({type:'START'});$('relay-title').focus({preventScroll:true});};
 $('relay-action').onclick=()=>{if(journey){advanceJourney();return;}if(preview!==null){preview=null;render();return;}if(state.stage===6){if(placeVisit&&state.finished){leavePopupVisit();return;}if(nextAction(state).disabled){showPopupMap();return;}}perform(nextAction(state));};
 $('relay-jump').onclick=()=>scene?.jump();
 const releaseThumbstick=bindThumbstick($('relay-thumbstick'),()=>scene);
 render();
 try{
  const continueEarly=new Promise(resolve=>{$('relay-loading-continue').onclick=resolve;});
  const art=Promise.allSettled([withDeadline(()=>document.fonts.load('500 16px Pretendard'),{timeoutMs:2500}),loadRelayMaterials((done,total)=>{$('relay-loading-progress').value=done/total;$('relay-loading-note').textContent=`사진 재질 ${done} / ${total}`;}),loadRelayProps()]);
  await waitForArt(art,{continueEarly});
  $('relay-loading-note').textContent='3D 공간을 배치하고 있습니다.';$('relay-loading-continue').disabled=true;
  await yieldToPage();
  scene=new RelayScene($('relay-world'),{onLocation:name=>{if(state.stage===6&&!journey){$('relay-area').textContent='월영 밤마당';if($('relay-title').textContent!==name)$('relay-title').textContent=name;}},onPassage:action=>{if(busy||preview!==null||journey||!state.started)return false;useRestaurantDoor(action.split(':')[1],{walk:false});return true;},onGameLook:locked=>{$('relay-game-look').setAttribute('aria-pressed',String(locked));$('relay-game-look').querySelector('span').textContent=locked?'Esc로 해제':'게임 조작';if(locked)announce('마우스로 시선 · ↑↓ / WASD 이동 · ←→ 회전 · Shift 빠르게 · Space 점프 · E 또는 클릭으로 상호작용 · Esc 해제');},onInteract:action=>{if(!state.started||preview!==null||busy)return;if(journey){if(action.startsWith('journey:')){const leg=JOURNEYS[journey.id].legs[journey.leg];if(action==='journey:'+leg.key)advanceJourney();else announce('가까운 이정표부터 따라가세요.');}return;}if(action==='transit:stop'){scene?.requestBusStop();return;}if(action.startsWith('restaurant:')){useRestaurantDoor(action.split(':')[1]);return;}if(action==='night-market'){if(state.stage===5&&state.bridgeWalked)perform({type:'GO',index:6});else openPopupVisit();return;}if(action.startsWith('seat:')){chooseSeat(action.slice(5));return;}if(action.startsWith('dining-menu:')){chooseSeat(action.slice(12),true);return;}if(action.startsWith('station:')){const place=action.slice(8),next=nextAction(state);if(actionStation(next)===place)perform(next);else moveToStation(place);return;}if(action.startsWith('talk:')){talk(action.split(':')[1]);return;}if(action==='primary')perform(nextAction(state));if(action==='popup-map')showPopupMap();if(action==='stamp')popupPostcard();if(action==='photo')popupPhoto();if(action==='gallery')showPopupGallery();if(action.startsWith('buy-')){const id=action.slice(4);if(Object.hasOwn(POPUP_ITEMS,id)){if(state.cart.includes(id))popupTaste(id);else perform({type:'BUY',id,animation:'buy'});}}if(action==='performance')perform({type:'PERFORMANCE'});if(action==='game'&&state.gameAttempts<3)perform({type:'THROW',hit:Math.abs(aim-50)<=10,animation:'game'});},onFocus:focus=>{const active=state.started&&preview===null&&!busy&&focus;$('relay-interact').hidden=!active;if(active)$('relay-interact').querySelector('span').textContent=focus.action==='primary'?hudActionLabel(nextAction(state)):focus.name.replace(/[→↗]/g,'').trim();app.classList.toggle('has-interaction',!!active);},onError:announce,onNavigation:n=>{$('relay-walking').hidden=!n;app.classList.toggle('walking-to-place',!!n);if(!n&&scene)renderPlaces(state.started||preview!==null);if(n){$('relay-walking-label').textContent=n.name+' · 이동 중';$('relay-walking').querySelector('progress').value=n.progress;}},onTravel:p=>{$('relay-trip-meter').value=p;$('relay-trip-time').textContent=`${Math.round(p*100)}% · ${TRANSPORTS[state.transport].name} · 약 ${Math.ceil((1-p)*TRANSPORTS[state.transport].minutes)}분 남음 (시연 시간)`;}});$('relay-sound').setAttribute('aria-pressed',String(scene.audio.enabled));$('relay-sound').textContent='공간 소리 '+(scene.audio.enabled?'켜짐':'꺼짐');sceneReady=true;sceneKey='';render();const station=popupEntryStation(placeVisit,entryBooth?.id);if(station&&state.stage===6){scene.placeAt(station);$('relay-title').textContent=station.name;}}catch(error){console.error('Relay 3D unavailable',error);scene?.dispose();$('relay-world').classList.add('world-unavailable');scene=null;sceneReady=true;render();announce('3D 화면을 열 수 없습니다. 아래 조작으로 여정은 계속 체험할 수 있습니다.');}
 $('relay-loading-status').hidden=true;app.dataset.ready='true';app.dataset.loadMs=String(Math.round(performance.now()-loadStarted));
 document.dispatchEvent(new Event('app-ready'));
 window.addEventListener('pagehide',event=>{if(!event.persisted){releaseThumbstick();scene?.dispose();}});
}
