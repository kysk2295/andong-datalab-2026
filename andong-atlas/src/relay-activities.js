// Small, keyboard/touch accessible activities. Success is driven by player input.
export function runActivity({type,program,step=0,color='#c77a48',onInput=async()=>{}}){
 return new Promise(resolve=>{
  const dialog=document.createElement('dialog');dialog.className='relay-activity';
  const mode=type==='SCAN'?'scan':type==='EAT'?'eat':program;
  const titles={scan:'영수증을 카메라에 맞춰주세요',eat:'한 입씩, 안동의 맛',mask:['탈의 바탕을 칠해요','두 볼에 색을 입혀요','마지막 표정을 완성해요'][step],tea:['다관에 국화꽃을 담아요','따뜻한 물을 부어요','잔에 차를 따라요'][step],soju:['쌀과 누룩을 차례로 준비해요','발효에서 증류까지 이어보세요','완성품에 표찰을 달아요'][step]};
  dialog.innerHTML=`<button class="activity-close" aria-label="체험 동작 닫기">×</button><p class="relay-overline">직접 해보는 안동</p><h2>${titles[mode]}</h2><p class="activity-instruction"></p><div class="activity-play"></div><p class="activity-status" role="status" aria-live="polite"></p><button class="activity-assist">이 동작은 간단히 진행하기</button>`;
  document.body.append(dialog);dialog.showModal();const area=dialog.querySelector('.activity-play'),instruction=dialog.querySelector('.activity-instruction'),status=dialog.querySelector('.activity-status');
  const abort=new AbortController();const signal=abort.signal;let done=false,frame=0;
  function finish(ok){if(done)return;done=true;cancelAnimationFrame(frame);abort.abort();dialog.close();dialog.remove();resolve(ok);}
  dialog.querySelector('.activity-close').onclick=()=>finish(false);dialog.querySelector('.activity-assist').onclick=()=>finish(true);dialog.addEventListener('cancel',e=>{e.preventDefault();finish(false);},{signal});
  function completeButton(){status.textContent='동작을 마쳤어요.';const button=document.createElement('button');button.className='relay-primary';button.textContent='3D 공간에서 이어가기 →';button.onclick=()=>finish(true);area.append(button);button.focus();}
  if(mode==='scan'){
   instruction.textContent='영수증을 직접 끌어 테두리 안에 맞춘 뒤 인증하세요. 슬라이더와 방향키로도 조절할 수 있어요.';
   area.innerHTML='<div class="scan-game"><div class="scan-guide"></div><div class="scan-receipt"><small>이어드림 · 식사 영수증</small><div class="scan-qr-symbol">▦</div><small>ED-DEMO-001</small></div></div><label class="game-range-label">영수증 위치<input type="range" min="0" max="100" value="15" aria-label="영수증 정렬"></label><button class="relay-primary">정렬한 영수증 인증</button>';
   const input=area.querySelector('input'),receipt=area.querySelector('.scan-receipt'),button=area.querySelector('button');
   const update=()=>{receipt.style.left=`${15+Number(input.value)*.7}%`;};input.oninput=update;update();let dragX=null,initial=0;receipt.style.touchAction='none';receipt.addEventListener('pointerdown',e=>{dragX=e.clientX;initial=Number(input.value);receipt.setPointerCapture(e.pointerId);},{signal});receipt.addEventListener('pointermove',e=>{if(dragX===null||input.disabled)return;input.value=String(Math.max(0,Math.min(100,initial+(e.clientX-dragX)/area.querySelector('.scan-game').clientWidth*100/.7)));update();},{signal});receipt.addEventListener('pointerup',()=>{dragX=null;},{signal});receipt.addEventListener('pointercancel',()=>{dragX=null;},{signal});
   button.onclick=()=>{if(Math.abs(Number(input.value)-50)<=9){button.remove();input.disabled=true;status.textContent='QR 위치 확인 · 인증할 준비가 되었어요.';completeButton();}else status.textContent='테두리를 벗어났어요. 가운데로 더 맞춰주세요.';};
  }else if(mode==='mask'){
   instruction.textContent='탈 위에 표시된 곳을 눌러 붓으로 칠하세요. 키보드 Tab과 Enter로도 칠할 수 있어요.';
   const points=step===0?[[50,20],[25,42],[75,42],[36,70],[65,70]]:step===1?[[24,57],[76,57]]:[[28,34],[72,34],[50,76]];
   area.innerHTML=`<div class="paint-game" style="--mask-paint:${color}"><div class="paint-face"><i class="paint-eye left"></i><i class="paint-eye right"></i><i class="paint-nose"></i><i class="paint-mouth"></i></div>${points.map(([x,y],i)=>`<button class="paint-spot" style="left:${x}%;top:${y}%" aria-label="탈의 ${i+1}번째 부분 칠하기">${i+1}</button>`).join('')}</div>`;
   let count=0;area.querySelectorAll('.paint-spot').forEach(button=>{button.onclick=()=>{button.disabled=true;button.classList.add('painted');button.textContent='✓';count++;status.textContent=`${count} / ${points.length} 부분을 칠했어요.`;if(count===points.length)completeButton();};});
  }else if(mode==='tea'&&step===0){
   instruction.textContent='국화꽃 세 송이를 다관으로 끌어 담아보세요. 꽃을 눌러서 담을 수도 있어요.';
   area.innerHTML='<div class="flower-pot" aria-label="국화꽃을 담을 다관"><span>다관</span><div></div></div><div class="flower-tray">'+[1,2,3].map(i=>`<button aria-label="국화꽃 ${i} 담기">🌼</button>`).join('')+'</div>';
   let count=0;const pot=area.querySelector('.flower-pot');
   area.querySelectorAll('.flower-tray button').forEach(button=>{let start=null,dragged=false;const pick=()=>{if(button.disabled)return;button.disabled=true;button.style.opacity='.25';pot.querySelector('div').textContent+='🌼';count++;status.textContent=`국화꽃 ${count} / 3 송이를 담았어요.`;if(count===3)completeButton();};button.onclick=()=>{if(!dragged)pick();};button.addEventListener('pointerdown',e=>{start=[e.clientX,e.clientY];dragged=false;button.setPointerCapture(e.pointerId);},{signal});button.addEventListener('pointermove',e=>{if(!start)return;const dx=e.clientX-start[0],dy=e.clientY-start[1];dragged=Math.hypot(dx,dy)>5;button.style.transform=`translate(${dx}px,${dy}px)`;},{signal});button.addEventListener('pointerup',e=>{if(dragged){const r=pot.getBoundingClientRect();if(e.clientX>=r.left&&e.clientX<=r.right&&e.clientY>=r.top&&e.clientY<=r.bottom)pick();else status.textContent='다관 안에 꽃을 놓아주세요.';}start=null;button.style.transform='';},{signal});button.addEventListener('pointercancel',()=>{start=null;button.style.transform='';},{signal});});
  }else if(mode==='tea'){
   instruction.textContent='붓기 버튼을 누르고 있다가 표시된 구간에서 놓으세요. 키보드는 Space를 누르고 떼면 됩니다.';
   area.innerHTML='<div class="pour-game"><div class="pour-target"></div><div class="pour-fill"></div><span>알맞은 양</span></div><button class="pour-hold">누르고 있다가 놓기</button><div class="pour-buttons"><button class="pour-tap">조금씩 붓기</button><button class="pour-reset">다시 담기</button></div>';
   let level=0,holding=false,last=0,complete=false;const fill=area.querySelector('.pour-fill'),hold=area.querySelector('.pour-hold');
   function start(){if(complete||holding)return;holding=true;last=performance.now();hold.classList.add('holding');}
   function release(){if(!holding)return;holding=false;hold.classList.remove('holding');if(level>=58&&level<=82){complete=true;hold.disabled=true;completeButton();}else status.textContent=level>82?'조금 넘쳤어요. 다시 담기로 한 번 더 해보세요.':'조금 더 담아주세요.';}
   hold.addEventListener('pointerdown',e=>{e.preventDefault();hold.setPointerCapture(e.pointerId);start();},{signal});hold.addEventListener('pointerup',release,{signal});hold.addEventListener('pointercancel',release,{signal});window.addEventListener('blur',release,{signal});hold.addEventListener('blur',release,{signal});hold.addEventListener('keydown',e=>{if(e.code==='Space'){e.preventDefault();start();}},{signal});hold.addEventListener('keyup',e=>{if(e.code==='Space'){e.preventDefault();release();}},{signal});
   area.querySelector('.pour-tap').onclick=()=>{if(complete)return;level=Math.min(100,level+10);holding=true;release();};
   area.querySelector('.pour-reset').onclick=()=>{if(complete)return;level=0;status.textContent='다시 알맞은 양을 담아보세요.';};
   function tick(t){if(holding)level=Math.min(100,level+Math.min(50,t-last)*.028);last=t;fill.style.height=level+'%';if(level===100)release();if(!done)frame=requestAnimationFrame(tick);}frame=requestAnimationFrame(tick);
  }else if(mode==='soju'){
   const sequences=[['쌀','누룩','물'],['발효','증류','숙성'],['술병','표찰','완성']];const seq=sequences[step];
   instruction.textContent=`${seq.join(' → ')} 순서로 선택하세요. 실제 제조 과정은 교육용으로 압축했습니다.`;
   area.innerHTML=`<div class="soju-sequence">${seq.map((text,i)=>`<span data-sequence="${i}">${i+1}<small>${text}</small></span>`).join('')}</div><div class="material-choices">${[2,0,1].map(i=>`<button data-material="${i}">${seq[i]}</button>`).join('')}</div>`;
   let count=0;area.querySelectorAll('[data-material]').forEach(button=>{button.onclick=()=>{if(Number(button.dataset.material)!==count){status.textContent=`먼저 ${seq[count]} 단계를 선택하세요.`;return;}button.disabled=true;area.querySelector(`[data-sequence="${count}"]`).classList.add('done');count++;status.textContent=`${count} / 3 과정 완료`;if(count===3)completeButton();};});
  }else{
   instruction.textContent='세 번의 젓가락질로 한 상을 맛보세요. 한 입마다 직접 들어 올려요.';
   area.innerHTML='<div class="meal-game"><span>🥢</span><div class="meal-bites"><i></i><i></i><i></i></div></div><button class="relay-primary">한 입 맛보기</button>';
   let count=0;const button=area.querySelector('button');button.onclick=async()=>{button.disabled=true;await onInput();if(done)return;button.disabled=false;area.querySelectorAll('.meal-bites i')[count].classList.add('done');count++;status.textContent=`${count} / 3 한 입을 맛봤어요.`;if(count===3){button.remove();completeButton();}};
  }
 });
}
