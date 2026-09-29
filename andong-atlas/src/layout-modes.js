import {relayHubHTML} from './relay-entry.js';
import './atlas-design.css';
import './layout-modes.css';
import './atlas-home.css';
import { initAtlasShell, initAtlasDiscovery } from './atlas-design.js';

export function initLayoutModes({catalog, mediaData, media, locate, setTab, refreshIcons, frameJourney}) {
  const $ = id => document.getElementById(id);
  initAtlasShell();
  const panel = $('explore');
  const tabs = document.querySelector('.tabs');
  panel.insertBefore(tabs, panel.querySelector('.panel-body'));
  const switcher = document.createElement('nav');
  switcher.className = 'layout-switch';
  switcher.setAttribute('aria-label','탐색 방식');
  switcher.innerHTML = '<button data-layout-mode="atlas" aria-pressed="true"><i data-lucide="map-pin"></i>지도 탐색</button><button data-layout-mode="journey" aria-pressed="false"><i data-lucide="route"></i>코스 여행</button><button data-layout-mode="photo" aria-pressed="false"><i data-lucide="image"></i>사진 탐색</button>';
  document.querySelector('.atlas-masthead .shell-actions').before(switcher);

  const primary = document.createElement('div');
  primary.className = 'journey-primary';
  primary.append($('journey-summary'), $('journey-start-tour'));
  panel.append(primary);
  const route = document.createElement('section');
  route.id = 'atlas-route'; route.className = 'journey-preview';
  route.setAttribute('aria-label','코스 미리보기');
  route.innerHTML = '<div class="journey-preview-heading"><div><h2>오늘의 안동 여행</h2><p id="atlas-route-summary"></p></div><div class="route-actions"><button id="atlas-route-edit">코스 수정</button><button id="atlas-route-start">이 코스 여행하기</button></div></div><div class="journey-preview-stops"></div>';
  document.body.append(route);
  const render = () => {
    const original = [...$('journey-stages').querySelectorAll('button[data-stage]')];
    route.querySelector('.journey-preview-stops').replaceChildren(...original.map((source,index) => {
      const b = source.cloneNode(true);
      b.removeAttribute('data-stage');
      b.disabled=$('journey-start-tour').disabled;
      b.setAttribute('aria-label',`${index + 1}구간 · ${source.textContent.trim()}`);
      b.onclick = () => source.click();
      return b;
    }));
    $('atlas-route-summary').textContent = $('journey-start-tour').disabled?$('journey-summary').textContent:`${original.length}개 구간 · 구간을 누르면 그곳부터 여행합니다.`;
    $('atlas-route-start').disabled=$('journey-start-tour').disabled;
    if(document.body.dataset.layout==='journey'&&!document.body.classList.contains('journey-playing'))requestAnimationFrame(frameJourney);
  };
  new MutationObserver(render).observe($('journey-stages'),{childList:true});
  new MutationObserver(render).observe($('journey-start-tour'),{attributes:true,attributeFilter:['disabled']});
  $('atlas-route-start').onclick = () => $('journey-start-tour').click();
  $('atlas-route-edit').onclick = () => {setTab('journey');if($('shell-panel').getAttribute('aria-expanded')!=='true')$('shell-panel').click();$('journey-origin-trigger').focus();};
  render();
  $('panel-city').insertAdjacentHTML('afterbegin',relayHubHTML());
  initAtlasDiscovery(catalog,mediaData,media,locate);

  function apply(mode, syncUrl = true) {
    if (!['atlas','journey','photo'].includes(mode)) mode='atlas';
    if(document.body.classList.contains('journey-playing'))$('journey-exit').click();
    if(document.body.dataset.layout!==mode)panel.querySelector('.panel-body').scrollTop=0;
    document.body.dataset.layout=mode;
    const scope=document.querySelector('.map-scope'),masthead=document.querySelector('.atlas-masthead');
    if(mode==='atlas'&&innerWidth>700){
      panel.insertBefore(switcher,tabs);panel.insertBefore(scope,panel.querySelector('.panel-body'));
    }else{masthead.insertBefore(switcher,masthead.querySelector('.shell-actions'));document.body.append(scope);}
    const environment=document.getElementById('atlas-environment');
    environment.hidden=!(mode==='atlas'&&innerWidth>700);
    document.getElementById('shell-scenery').setAttribute('aria-expanded',String(!environment.hidden));
    document.querySelector('.discovery-all').open=mode!=='photo';
    switcher.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.layoutMode===mode)));
    if (!document.body.classList.contains('journey-playing')) {
      if(mode==='journey') setTab('journey');
      if(mode!=='journey') setTab('city');
      const expanded=mode!=='journey';
      const current=$('shell-panel').getAttribute('aria-expanded')==='true';
      if(expanded!==current) $('shell-panel').click();
    }
    if(syncUrl) {
      const url=new URL(location.href);url.searchParams.set('layout',mode);
      history.replaceState(null,'',url);
    }
    // The standalone A/B/C comparison page now previews the same real modes.
    if(parent!==window)parent.postMessage({type:'atlas-layout-changed',mode},location.origin);
    window.dispatchEvent(new Event('atlas-layout-change'));
    if(mode==='journey'&&!document.body.classList.contains('journey-playing'))requestAnimationFrame(frameJourney);
  }
  switcher.addEventListener('click',e=>{const b=e.target.closest('[data-layout-mode]');if(b)apply(b.dataset.layoutMode);});
  window.addEventListener('resize',()=>{
    const atlas=document.body.dataset.layout==='atlas'&&innerWidth>700;
    const scope=document.querySelector('.map-scope'),masthead=document.querySelector('.atlas-masthead');
    if(atlas){panel.insertBefore(switcher,tabs);panel.insertBefore(scope,panel.querySelector('.panel-body'));}
    else{masthead.insertBefore(switcher,masthead.querySelector('.shell-actions'));document.body.append(scope);}
    $('atlas-environment').hidden=!atlas;
    $('shell-scenery').setAttribute('aria-expanded',String(atlas));
  });
  window.addEventListener('popstate',()=>apply(new URLSearchParams(location.search).get('layout'),false));
  window.addEventListener('message',e=>{
    if(e.origin===location.origin && e.source===parent && e.data?.type==='atlas-study-mode')apply(e.data.mode);
  });
  const params=new URLSearchParams(location.search);
  apply(params.get('layout') || (params.has('journey')&&!params.has('showcase')?'journey':'atlas'),false);
  if(!params.has('layout')&&params.has('showcase'))setTab('relay');
  refreshIcons();
  window.dispatchEvent(new Event('atlas-layout-change'));
  if(parent!==window) parent.postMessage({type:'atlas-study-ready'},location.origin);
}
