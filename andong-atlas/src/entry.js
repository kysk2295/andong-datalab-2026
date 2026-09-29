const params=new URLSearchParams(location.search);
// Keep the original map as the home page. Enter the playable relay explicitly.
if(params.get('experience')!=='relay'){
 document.title='안동 3D Atlas · 지도와 코스 여행';
 document.documentElement.classList.remove('relay-loading');
 await import('./main.js');
}else{
 try{const {initRelay}=await import('./relay-ui.js');await initRelay();}
 catch(error){console.error(error);document.documentElement.classList.remove('relay-loading');document.body.replaceChildren();const p=document.createElement('p');p.textContent='이어드림 화면을 불러오지 못했습니다. 새로고침하거나 전체 지도를 열어주세요.';const a=document.createElement('a');a.href='?layout=atlas';a.textContent='전체 지도 열기';document.body.append(p,a);}
}
