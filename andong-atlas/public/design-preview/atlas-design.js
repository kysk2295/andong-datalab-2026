import { escapeHtml as esc, photosFor } from './place-media-model.js';

// A native DOM shell around the existing atlas, not a new routing framework.
export function initAtlasShell() {
  document.body.classList.add('atlas-shell');
  document.body.dataset.tab = 'city';
  const header = document.querySelector('body > header');
  header.classList.add('atlas-masthead');
  header.append(document.querySelector('.tabs'));
  header.insertAdjacentHTML('beforeend', `<div class="shell-actions"><button id="shell-panel" aria-label="탐색 패널 접기" aria-expanded="true"><i data-lucide="panel-left"></i></button><button id="shell-scenery" aria-controls="atlas-environment" aria-expanded="false"><i data-lucide="sun"></i><span>풍경</span></button><button id="shell-theme" aria-label="어두운 화면으로 전환"><i data-lucide="moon"></i></button></div>`);
  const environment = document.querySelector('.environment');
  environment.id = 'atlas-environment';
  environment.hidden = true;
  environment.insertAdjacentHTML('afterbegin','<h2>풍경을 바꿔보세요</h2>');
  const scope = document.querySelector('.view-switch');
  scope.classList.add('map-scope');
  document.body.append(scope);
  document.getElementById('shell-scenery').onclick = () => {
    environment.hidden = !environment.hidden;
    document.getElementById('shell-scenery').setAttribute('aria-expanded', String(!environment.hidden));
  };
  const panel = document.getElementById('explore');
  const panelButton = document.getElementById('shell-panel');
  panelButton.onclick = () => {
    if (innerWidth <= 700) panel.classList.toggle('open');
    else document.body.classList.toggle('sidebar-collapsed');
    syncPanel();
  };
  function syncPanel() {
    const shown = innerWidth <= 700 ? panel.classList.contains('open') : !document.body.classList.contains('sidebar-collapsed');
    panelButton.setAttribute('aria-expanded', String(shown));
    panelButton.setAttribute('aria-label', shown ? '탐색 패널 접기' : '탐색 패널 펼치기');
    panel.inert = document.body.dataset.ready !== 'true' || !shown;
    document.body.classList.toggle('panel-visible', shown);
  }
  new MutationObserver(syncPanel).observe(panel,{attributes:true,attributeFilter:['class']});
  new MutationObserver(syncPanel).observe(document.body,{attributes:true,attributeFilter:['data-ready']});
  window.addEventListener('resize', syncPanel);
  document.querySelector('.tabs').addEventListener('click', (e) => {
    if (!e.target.closest('[data-tab]')) return;
    document.body.classList.remove('sidebar-collapsed');
    if (innerWidth <= 700) panel.classList.add('open');
    syncPanel();
  });
  const theme = document.getElementById('shell-theme');
  const preference = matchMedia('(prefers-color-scheme: dark)');
  let manual = false;
  function applyTheme(dark) {
    document.body.dataset.uiTheme = dark ? 'dark' : 'light';
    theme.setAttribute('aria-label', dark ? '밝은 화면으로 전환' : '어두운 화면으로 전환');
    theme.setAttribute('aria-pressed', String(dark));
  }
  theme.onclick = () => { manual = true; applyTheme(document.body.dataset.uiTheme !== 'dark'); };
  preference.addEventListener('change', e => { if (!manual) applyTheme(e.matches); });
  applyTheme(preference.matches);
  syncPanel();
}

export function initAtlasDiscovery(catalog, mediaData, media, locate) {
  const city = document.getElementById('panel-city');
  const featured = ['bridge','hahoe','station'].map(id => catalog.find(p => p.id === id));
  let current = featured[0];
  city.insertAdjacentHTML('afterbegin', `<section class="atlas-discovery" aria-label="사진으로 고르는 안동 명소"><h2>어디부터 가볼까요?</h2><p>장소를 고르고, 지도 속으로 들어가 보세요.</p><div class="discovery-places" role="group" aria-label="둘러볼 명소">${featured.map(p => `<button data-discover="${p.id}" aria-pressed="${p.id === current.id}">${esc(p.id === 'bridge' ? '월영교' : p.id === 'station' ? '안동역' : '하회마을')}</button>`).join('')}</div><button id="discovery-photo" aria-label="선택한 명소 실제 사진 보기"><img id="discovery-img" alt="" width="640" height="400"></button><div id="discovery-credit"></div><button id="discovery-locate">이 장소로 이동<i data-lucide="arrow-up-right"></i></button></section>`);
  const render = () => {
    const photo = photosFor(current, mediaData)[0];
    const img = document.getElementById('discovery-img');
    img.src = photo.src; img.alt = photo.caption;
    document.getElementById('discovery-credit').innerHTML = `© ${esc(photo.credit)} <a href="${esc(photo.sourceUrl)}" target="_blank" rel="noopener">사진 출처</a> <a href="${esc(photo.licenseUrl)}" target="_blank" rel="noopener">${esc(photo.license)}</a>`;
    document.querySelectorAll('[data-discover]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.discover === current.id)));
  };
  document.querySelectorAll('[data-discover]').forEach(b => b.onclick = () => { current = featured.find(p => p.id === b.dataset.discover); render(); });
  document.getElementById('discovery-photo').onclick = () => media.open(current);
  document.getElementById('discovery-locate').onclick = () => locate(current);
  const all = document.createElement('details');
  all.className = 'discovery-all';
  all.innerHTML = '<summary>안동 명소 전체 보기</summary>';
  document.getElementById('places').before(all);
  all.append(document.getElementById('places'));
  render();
}
