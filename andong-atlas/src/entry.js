const params=new URLSearchParams(location.search);
try {
// Keep the original map as the home page. Enter the playable relay explicitly.
if(params.get('experience')!=='relay'){
 document.title='안동 3D Atlas · 지도와 코스 여행';
 document.documentElement.classList.remove('relay-loading');
 await import('./main.js');
}else{
 const {initRelay}=await import('./relay-ui.js');await initRelay();
}
}catch(error){console.error(error);document.dispatchEvent(new Event('app-load-error'));}
