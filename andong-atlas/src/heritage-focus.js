export function updateHeritageFocus(atlas) {
  let host=document.getElementById('heritage-focus');
  if(!host){host=document.createElement('div');host.id='heritage-focus';host.className='heritage-focus';document.querySelector('.location').append(host);}
  const data=atlas.district.data,detail=data.heritageDetail;
  host.hidden=!atlas.district.group.visible||!detail;
  if(host.hidden)return;
  const views=[{name:data.id==='hahoe'?'마을 골목 가까이':'경내 가까이',coordinates:data.activityCenter||data.center,distance:data.id==='hahoe'?.55:.7}];
  if(data.id==='hahoe'){
    const tree=detail.sites.find(s=>s.name==='삼신당');
    if(tree)views.push({name:'삼신당 주변',coordinates:tree.coordinates,distance:.48});
    const grove=detail.groves.find(f=>f.id==='osm-77121468');
    if(grove){const ring=grove.geometry.coordinates[0];views.push({name:'만송정 숲',coordinates:[0,1].map(k=>ring.reduce((sum,c)=>sum+c[k],0)/ring.length),distance:.95});}
  }
  host.replaceChildren(...views.map(view=>{
    const button=document.createElement('button');button.textContent=view.name;
    button.onclick=()=>{
      atlas.fly(view.coordinates,view.distance);
      document.getElementById('location-name').textContent=`${data.name.split('·')[0]} · ${view.name}`;
      document.getElementById('location-description').textContent='공개 지도에 수록된 골목·담장·건물과 방문객 풍경';
      document.getElementById('coordinates').textContent='외관·사람은 미니어처';
    };
    return button;
  }));
  const explore=document.createElement('button');explore.textContent='명소·골목 탐색';
  explore.onclick=()=>atlas.heritageExplorer?.open();host.append(explore);
}
