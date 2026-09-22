(() => {
  const colors = {food:'#286481',cafe:'#bd8544',pub:'#925e75'};
  const map = L.map('andong-map', {preferCanvas:true, scrollWheelZoom:false}).setView([36.570,128.732],13);
  const tile = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom:19, attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);
  tile.on('load',()=>{document.getElementById('map-load-status').textContent='배경지도 OpenStreetMap';});
  tile.on('tileerror',()=>{document.getElementById('map-load-status').textContent='일부 지도 타일을 불러오지 못했습니다. 인터넷 연결을 확인하세요.';});
  const layers = {food:L.layerGroup().addTo(map),cafe:L.layerGroup().addTo(map),pub:L.layerGroup().addTo(map)};
  function select(name,detail) {
    document.getElementById('selected-place').textContent=name;
    document.getElementById('selected-detail').textContent=detail;
  }
  andongPlaces.points.forEach(p=>{
    const marker=L.circleMarker([p.lat,p.lng],{radius:3.2,color:colors[p.kind],weight:0.6,fillColor:colors[p.kind],fillOpacity:0.7}).addTo(layers[p.kind]);
    const label=document.createElement('div');
    const name=document.createElement('strong');name.textContent=p.name;
    const detail=document.createElement('p');detail.textContent=p.district+' · '+p.type;
    label.append(name,detail);marker.bindPopup(label);
    marker.on('click',()=>select(p.name,p.district+' · '+p.type+' / 상가정보 2026.06.30 기준. 영업시간·릴레이 참여 여부는 미확인입니다.'));
  });
  const landmarks = L.layerGroup().addTo(map);
  const references=[
    {name:'안동역',lat:36.5748,lng:128.6746,tag:'교통',detail:'도착·귀가편과 원도심 이동을 검토할 참고 지점. 표시용 대표좌표입니다.'},
    {name:'원도심 · 찜닭골목',lat:36.5654,lng:128.7295,tag:'식음',detail:'식사 인증을 시작할 상권 후보. 표시용 대표좌표이며 참여 업체가 확정된 것은 아닙니다.'},
    {name:'월영교',lat:36.5767,lng:128.7608,tag:'야간',detail:'야간 코스의 참고 지점. 표시용 대표좌표이며 실제 프로그램 운영일·이동수단 확인이 필요합니다.'},
    {name:'하회마을',lat:36.5389,lng:128.5181,tag:'문화',detail:'광역 관광자원 참고 지점. 원도심과 별도 이동 검토가 필요한 권역입니다.'}
  ];
  references.forEach(p=>{
    const icon=L.divIcon({className:'map-node',html:'<span>'+p.tag+'</span>',iconSize:[40,28],iconAnchor:[20,14]});
    const marker=L.marker([p.lat,p.lng],{icon,title:p.name}).addTo(landmarks);
    marker.bindTooltip(p.name,{permanent:true,direction:'bottom',offset:[0,12],className:'place-label'});
    marker.on('click',()=>select(p.name,p.detail));
  });
  const scenario=L.layerGroup().addTo(map);
  L.circle([36.5654,128.7295],{radius:650,color:'#bd8544',weight:1,dashArray:'5 5',fillColor:'#bd8544',fillOpacity:0.09}).addTo(scenario);
  L.circle([36.5767,128.7608],{radius:650,color:'#bd8544',weight:1,dashArray:'5 5',fillColor:'#bd8544',fillOpacity:0.09}).addTo(scenario);
  L.polyline([[36.5654,128.7295],[36.5767,128.7608],[36.586,128.765]],{color:'#b76731',weight:3,dashArray:'8 8'}).addTo(scenario);
  const stay=L.marker([36.586,128.765],{icon:L.divIcon({className:'map-node stay-node',html:'<span>숙박</span>',iconSize:[40,28]}),title:'가상 숙박 후보'}).addTo(scenario);
  stay.bindTooltip('숙박 후보 · 가상 배치',{permanent:true,direction:'right',className:'place-label'});
  stay.on('click',()=>select('숙박 후보 · 예시','실제 숙소를 특정하지 않은 화면 예시입니다. 운영 시 참여 고택의 정확한 좌표·객실·입실 마감을 연결합니다.'));
  function countVisible(){
    const bounds=map.getBounds();
    const count=andongPlaces.points.filter(p=>map.hasLayer(layers[p.kind])&&bounds.contains([p.lat,p.lng])).length;
    document.getElementById('visible-places').textContent=count.toLocaleString('ko-KR')+'곳';
  }
  for(const kind of Object.keys(layers)) document.getElementById('layer-'+kind).addEventListener('change',event=>{
    if(event.target.checked)map.addLayer(layers[kind]);else map.removeLayer(layers[kind]);countVisible();
  });
  [['nodes',landmarks],['scenario',scenario]].forEach(([id,layer])=>document.getElementById('layer-'+id).addEventListener('change',event=>{
    if(event.target.checked)map.addLayer(layer);else map.removeLayer(layer);
  }));
  const views={city:{center:[36.565,128.662],zoom:11},downtown:{center:[36.570,128.732],zoom:13},bridge:{center:[36.574,128.749],zoom:14}};
  document.querySelectorAll('[data-view]').forEach(button=>button.addEventListener('click',()=>{
    const view=views[button.dataset.view];
    if(button.dataset.view==='city') map.fitBounds(andongPlaces.points.map(p=>[p.lat,p.lng]),{padding:[20,20],animate:false});
    else map.setView(view.center,view.zoom,{animate:false});
    document.querySelectorAll('[data-view]').forEach(item=>item.setAttribute('aria-pressed',String(item===button)));
  }));
  const bars=document.getElementById('district-bars');
  andongPlaces.districts.slice(0,5).forEach(([name,count])=>{
    const row=document.createElement('div');
    const label=document.createElement('span');label.textContent=name;
    const track=document.createElement('span');const bar=document.createElement('i');bar.style.width=(count/555*100)+'%';track.append(bar);
    const value=document.createElement('b');value.textContent=count;
    row.append(label,track,value);bars.append(row);
  });
  map.on('moveend',countVisible);countVisible();
  new ResizeObserver(()=>map.invalidateSize()).observe(document.getElementById('andong-map'));
})();
