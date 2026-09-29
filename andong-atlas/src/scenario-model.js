export function scenarioSummary(solution,plan){
  const current=plan==='현재',p=solution.plans[current?'기본안':plan];
  if(!p)throw new Error('Unknown scenario');
  const resident=solution.resident;
  return {plan,proposed:!current,restaurants:current?0:p.입력.n1,popups:current?0:p.입력.n3,
    additionalConsumption:current?null:p.추가소비합.P50,annualExperiences:current?null:p.체험결제합.P50,
    eveningVisitors:current?null:p.하루_이동.P50,popupVisitors:current?null:p.팝업_하루.P50,
    residentMonthly:resident.currentMonthly+(current?0:resident.addedMonthlyExpanded*p.입력.n1/83),
    currentResidentMonthly:resident.currentMonthly};
}
export function benefitPaths(result,network,origin,after=true){
  return result.rows.filter(r=>after?r.after:r.before).flatMap(row=>{
    const path=network.route(origin,row.place.coordinates,'walk');
    return path?.coordinates.length>1?[{...row,path,added:after&&row.after?.type==='추가 제안'}]:[];
  });
}
