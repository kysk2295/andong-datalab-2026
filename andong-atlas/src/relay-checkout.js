const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money=n=>n.toLocaleString('ko-KR')+'원';
export function runCheckout({title,items,selected,discount=0,order=false,coupon=false,inWorld=false}){
 return new Promise(resolve=>{
  const dialog=document.createElement('dialog');dialog.className='relay-checkout relay-activity'+(order?' dining-menu-card':'');
  let choice=selected||Object.keys(items)[0],method='card',closed=false;const opener=document.activeElement;
  dialog.innerHTML=`<button class="activity-close" aria-label="계산 창 닫기">×</button><h2>${esc(title)}</h2>${order?'<figure class="dining-menu-photo" hidden><img src="/assets/relay/document/stage-1-image8.webp" alt="간장 양념과 당면을 곁들인 실제 찜닭 참고 사진"><figcaption>첨부 자료의 찜닭 사진 · 상차림 참고</figcaption></figure>':''}<div class="checkout-items"></div><div class="checkout-bill"></div>${order||coupon?'':'<fieldset class="checkout-method"><legend>결제 방법 시연</legend><label><input type="radio" name="demo-payment" value="card" checked> 카드</label><label><input type="radio" name="demo-payment" value="cash"> 현금</label></fieldset>'}<p class="small-note">체험용 예시 금액 · 실제 결제는 발생하지 않습니다.</p><button class="relay-primary checkout-confirm">${order?'주문하기':coupon?'할인권 사용 · 접수':inWorld?'계산하기':'구매하기'}</button>`;
  const render=()=>{const p=items[choice];const photo=dialog.querySelector('.dining-menu-photo');if(photo)photo.hidden=choice!=='jjimdak';dialog.querySelector('.checkout-bill').innerHTML=`${discount?`<div><span>영수증 혜택 ${discount}%</span><b>−${money(p.examplePrice*discount/100)}</b></div>`:''}<div class="checkout-total"><span>합계 · 체험용</span><strong>${money(p.examplePrice*(1-discount/100))}</strong></div>${coupon?'<small>선택한 체험에 1회 사용 · 다른 체험·팝업에 중복 적용되지 않습니다.</small>':''}`;dialog.querySelectorAll('[data-checkout-item]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.checkoutItem===choice)));};
  dialog.querySelector('.checkout-items').innerHTML=Object.entries(items).map(([id,p])=>`<button data-checkout-item="${id}"><b>${esc(p.name)}</b><small>${esc(p.detail||p.description||'')}</small></button>`).join('');
  dialog.querySelectorAll('[data-checkout-item]').forEach(b=>b.onclick=()=>{choice=b.dataset.checkoutItem;render();});
  dialog.querySelectorAll('input[name=demo-payment]').forEach(i=>i.onchange=()=>{method=i.value;});
  const finish=value=>{if(closed)return;closed=true;dialog.close();dialog.remove();opener?.focus?.({preventScroll:true});resolve(value);};
  dialog.querySelector('.activity-close').onclick=()=>finish(null);dialog.addEventListener('cancel',e=>{e.preventDefault();finish(null);});dialog.querySelector('.checkout-confirm').onclick=()=>finish({id:choice,method});render();document.body.append(dialog);dialog.showModal();
 });
}
