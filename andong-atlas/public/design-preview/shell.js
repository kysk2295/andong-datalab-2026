import { initAtlasShell, initAtlasDiscovery } from './atlas-design.js';
const $ = id => document.getElementById(id);
function ready() {
  initAtlasShell();
  const primary = document.createElement('div');
  primary.className = 'study-primary';
  primary.append($('journey-summary'), $('journey-start-tour'));
  $('explore').append(primary);
  const preview = document.createElement('section');
  preview.id = 'study-route'; preview.className = 'journey-preview';
  preview.setAttribute('aria-label','코스 미리보기');
  preview.innerHTML = '<div class="journey-preview-heading"><div><h2>오늘의 안동 여행</h2><p>구간을 누르면 그곳부터 여행합니다.</p></div><button id="study-start">이 코스 여행하기</button></div><div class="journey-preview-stops"></div>';
  document.body.append(preview);
  const renderRoute = () => {
    preview.querySelector('.journey-preview-stops').replaceChildren();
    // Mirror real calculated stages; actions invoke the original journey controls.
    const stops = [...$('journey-stages').querySelectorAll('button[data-stage]')];
    stops.forEach((original, index) => {
      if (stops.length > 9 && index !== 0 && index !== stops.length - 1 && !/체류|식사|체험|산책|팝업|구시장|찜닭/.test(original.textContent)) return;
      const button = original.cloneNode(true);
      button.removeAttribute('data-stage');
      button.onclick = () => original.click();
      preview.querySelector('.journey-preview-stops').append(button);
    });
  };
  new MutationObserver(renderRoute).observe($('journey-stages'),{childList:true});
  $('study-start').onclick = () => $('journey-start-tour').click();
  renderRoute();
  document.querySelectorAll('[data-lucide]').forEach(node => {
    // Reuse this app's already rendered icon family without another package.
    const existing = document.querySelector(`svg.lucide-${node.dataset.lucide}`);
    if (existing) node.replaceWith(existing.cloneNode(true));
  });
  const aliases={bridge:'woryeong',hahoe:'hahoe',station:'station'};
  Promise.all([fetch('/data/journey.json').then(r=>r.json()),fetch('/data/place-media.json').then(r=>r.json())]).then(([journey,media]) => {
    initAtlasDiscovery(journey.places, media, {open(place){
      $('open-place-photos').click();
      $('media-place').value=place.id;
      $('media-place').dispatchEvent(new Event('change',{bubbles:true}));
    }}, p=>document.querySelector(`[data-place="${aliases[p.id] || p.id}"]`)?.click());
  });
  function mode(value) {
    const allowed=['atlas','journey','photo'];
    if(!allowed.includes(value))return;
    if(document.body.classList.contains('journey-playing'))$('journey-exit').click();
    for(const dialog of document.querySelectorAll('dialog[open]'))dialog.close();
    document.body.dataset.study=value;
    document.body.classList.remove('sidebar-collapsed');
    $(value==='photo'?'tab-city':'tab-journey').click();
    if(value==='journey')$('shell-panel').click();
    if(innerWidth<=700 && value==='journey')$('explore').classList.remove('open');
  }
  window.addEventListener('message',e=>{
    if(e.origin!==location.origin || e.source!==parent)return;
    if(e.data?.type==='atlas-study-mode')mode(e.data.mode);
  });
  parent.postMessage({type:'atlas-study-ready'},location.origin);
}
if(document.body.dataset.ready==='true')ready();
else{
  const observer=new MutationObserver(()=>{if(document.body.dataset.ready==='true'){observer.disconnect();ready();}});
  observer.observe(document.body,{attributes:true,attributeFilter:['data-ready']});
}
