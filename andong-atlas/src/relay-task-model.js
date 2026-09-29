// Input rules shared by the 3D workshop and keyboard controls.
export const WORKSHOP_SEQUENCES=[['rice','nuruk','water'],['ferment','still','collect'],['bottle','label','package']];
export const WORKSHOP_LABELS={rice:'쌀',nuruk:'누룩',water:'물',ferment:'발효 항아리',still:'소주고리',collect:'받는 그릇',bottle:'완성 술병',label:'표찰',package:'포장 상자'};
export function createWorkshopTask(program,step){return {program,step,selected:[],amount:0,holding:false,done:false,error:''};}
export function workshopInput(task,id){
 if(task.done)return task;
 const sequence=task.program==='tea'?['flower-0','flower-1','flower-2']:WORKSHOP_SEQUENCES[task.step];
 if(!sequence?.includes(id)||task.selected.includes(id))return task;
 if(task.program==='soju'&&sequence[task.selected.length]!==id)return {...task,error:`먼저 ${WORKSHOP_LABELS[sequence[task.selected.length]]}을 선택하세요.`};
 const selected=[...task.selected,id];return {...task,selected,done:selected.length===sequence.length,error:''};
}
export function pourInput(task,action,delta=0){
 if(task.done)return task;
 if(action==='reset')return {...task,amount:0,holding:false,error:''};
 if(action==='start')return {...task,holding:true,error:''};
 if(action==='tick')return task.holding?{...task,amount:Math.min(100,task.amount+Math.max(0,delta)*26)}:task;
 if(action==='tap')return {...task,amount:Math.min(100,task.amount+10),error:''};
 if(action==='release')return {...task,holding:false,done:task.amount>=58&&task.amount<=82,error:task.amount<58?'아직 양이 적어요. 조금 더 부어주세요.':task.amount>82?'너무 많이 부었어요. 비우고 다시 해보세요.':''};
 return task;
}
