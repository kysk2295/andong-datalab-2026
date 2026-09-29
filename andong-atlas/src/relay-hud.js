const locations = {
 market: ['안동구시장', '찜닭골목'],
 meal: ['안동 원도심', '식당'],
 receipt: ['안동 원도심', '식당 · 계산대'],
 workshop: ['안동 원도심', '전통 공방'],
 transit: ['안동', '월영교 가는 길'],
 bridge: ['안동호', '월영교'],
 popup: ['월영교 강변', '야간 팝업존'],
};

export function hudLocation(id, station) {
 const [area, place] = locations[id] || ['안동', '산책길'];
 return {area, place: station ? `${place} · ${station}` : place};
}

export function hudActionLabel(action) {
 const labels = {ORDER:'메뉴 고르기', EAT:'식사하기', PAY:'계산하기', SCAN:'영수증 확인', REDEEM:'체험 접수', ARRIVE:'출발하기', WALK:'월영정 산책', FINISH:action.disabled?'장터 둘러보기':'여행 마치기'};
 return labels[action.type] || action.label.replace(/[→↗]/g, '').trim();
}
