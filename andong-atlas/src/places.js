export function buildPlaces(pois) {
  const definitions = [
    {
      id: "station",
      name: "안동역",
      en: "Andong Station",
      coordinates: [128.6748, 36.5747],
      source: "팀 교통 조사 기준점",
      description: "안동 여행의 시작과 귀가를 잇는 철도 거점입니다.",
      kind: "station",
    },
    {
      id: "market",
      name: "안동구시장 · 찜닭골목",
      en: "Old Market · Jjimdak Alley",
      coordinates: [128.728, 36.5655],
      source: "팀 원도심 분석 기준점",
      description:
        "식음 이용에서 체험으로 이어지는 이어드림의 첫 번째 권역입니다.",
      kind: "market",
    },
    {
      id: "ungbu",
      name: "웅부공원",
      en: "Ungbu Park",
      match: "웅부공원",
      description: "안동 원도심의 역사와 일상이 만나는 공원입니다.",
      kind: "heritage",
    },
    {
      id: "woryeong",
      name: "월영교",
      en: "Woryeonggyo Bridge",
      match: "월영교",
      description:
        "낙동강을 가로지르는 목교. 야간 이동과 팝업 연결을 검토하는 권역입니다.",
      kind: "bridge",
    },
    {
      id: "folk",
      name: "안동민속마을",
      en: "Andong Folk Village",
      match: "안동민속마을",
      description: "월영교 동쪽, 안동의 전통 가옥을 만나는 공간입니다.",
      kind: "heritage",
    },
    {
      id: "museum",
      name: "안동민속박물관",
      en: "Andong Folk Museum",
      match: "안동민속박물관",
      description: "안동의 민속과 생활문화를 살펴보는 문화 거점입니다.",
      kind: "museum",
    },
    {
      id: "hahoe",
      name: "하회마을 입구",
      en: "Hahoe Village Entrance",
      match: "하회마을",
      // Camera composition only: mapped historic houses span west of the entrance.
      viewCoordinates: [128.5185, 36.5393],
      viewDistance: 3.2,
      description:
        "공개 지도에 등록된 하회마을 정류장 위치입니다. 강이 감싸는 마을을 둘러보세요.",
      kind: "heritage",
    },
    {
      id: "buyong",
      name: "부용대",
      en: "Buyongdae Cliff",
      match: "부용대 (Buyongdae Cliff)",
      description: "낙동강 건너 하회마을의 지형을 조망하는 전망 지점입니다.",
      kind: "viewpoint",
    },
    {
      id: "byeongsan",
      name: "병산서원 입구",
      en: "Byeongsan Seowon Entrance",
      match: "병산서원",
      // OSM archaeological-site way 313681777; route/entrance coordinate is unchanged.
      viewCoordinates: [128.5526877, 36.5406538],
      viewDistance: 2.7,
      description:
        "공개 지도에 등록된 병산서원 정류장 위치입니다. 강변의 서원 권역을 탐색합니다.",
      kind: "heritage",
    },
    {
      id: "dosan",
      name: "도산서원",
      en: "Dosan Seowon",
      match: "도산서원",
      // OSM archaeological-site way 313680336.
      viewCoordinates: [128.8435618, 36.7272993],
      description: "안동호 북쪽의 유교문화 관광 거점입니다.",
      kind: "heritage",
    },
    {
      id: "bongjeong",
      name: "봉정사",
      en: "Bongjeongsa Temple",
      match: "봉정사",
      description: "안동 북서쪽 산지에 자리한 전통 사찰입니다.",
      kind: "heritage",
    },
  ];
  return definitions.flatMap((p) => {
    const f = pois.find((f) => f.properties.name === p.match);
    if (!p.coordinates && !f) return [];
    return [
      {
        ...p,
        coordinates: p.coordinates || f.geometry.coordinates,
        source: p.source || "OpenStreetMap · OpenFreeMap 2026-09-13",
      },
    ];
  });
}
