# 출처와 에셋 이용 조건

아래는 앱의 수집 메타데이터와 제작 기록을 정리한 목록입니다. 코드, 지도 파생 자료, 사진, 글꼴과 영상의 이용 조건은 서로 다릅니다.

## 지도와 분석 자료

| 자료 | 기록된 출처·조건 |
|---|---|
| 도로·시설·건물 윤곽 | [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), ODbL 1.0 |
| 벡터 타일과 스키마 | [OpenFreeMap](https://openfreemap.org/), [OpenMapTiles](https://openmaptiles.org/) |
| 표고 | [AWS Terrain Tiles](https://registry.opendata.aws/terrain-tiles/), [원천별 출처 기록](https://github.com/tilezen/joerd/blob/master/docs/attribution.md) |
| 행정경계 | 통계청 SGIS 기반 [vuski/admdongkor](https://github.com/vuski/admdongkor), 수집 기록의 공공누리 제1유형 표시 유지 |
| 추가 건물 | [GlobalBuildingAtlas](https://huggingface.co/datasets/zhu-xlab/GBA.LoD1), Zhu et al. (2025), [논문](https://doi.org/10.5194/essd-17-6647-2025), CC BY-NC 4.0. 비상업 조건 및 저자 표시 유지 |
| 기대효과와 조사 집계 | 상위 저장소의 분석 보고서. 앱에 사용한 원본 경로와 해시는 [report-effects.json](../public/data/report-effects.json)에 기록 |

건물 높이·지면·선로 접지 및 시각적 외관은 화면 표시를 위해 보정한 부분이 있습니다. 표시 보정은 원천 자료의 측량 정확도를 높였다는 의미가 아닙니다.

## 재질·모델·사진

- Poly Haven의 CC0 재질·HDRI: [relay-materials.json](../public/data/relay-materials.json). 파일별 출처, 다운로드 주소, 크기와 SHA256 포함.
- 스캔 모델: [relay-model-assets.json](../public/data/relay-model-assets.json). 개별 파일과 출처·이용 조건 포함.
- 관광정보·장소 사진: [relay-media.json](../public/data/relay-media.json), [place-media.json](../public/data/place-media.json), [heritage-media.json](../public/data/heritage-media.json). 사진별 원출처·제공자·이용 조건을 유지합니다.
- 사용자 제공 기획 문서의 참고 사진: [relay-document-photos.json](../public/data/relay-document-photos.json). **원출처 권리는 유지되며 자유 이용 허락을 뜻하지 않습니다.** 해당 메타데이터에는 개별 이용허락 확인이 필요한 항목이 표시되어 있습니다.
- Pretendard 글꼴: SIL Open Font License 1.1. 글꼴 및 관련 원저작권 표시를 유지합니다.

전체 에셋을 일괄적으로 MIT·CC0 자료로 해석하지 않습니다. 재사용할 파일의 메타데이터와 원출처 조건을 확인하세요.

## 라이브러리와 영상

- Three.js: MIT. Lucide: ISC. 버전은 [package-lock.json](../package-lock.json)에 고정됩니다.
- 영상의 배경음은 기존 제작 기록상 자체 합성 음악이며, 효과음은 Pixabay 출처로 기록되어 있습니다. 자세한 내용은 [영상 정보](VIDEOS.md)를 참고하세요.
- 지도·1인칭 체험 영상은 이 앱 화면의 녹화·편집본이며 실제 현장 촬영 영상이 아닙니다.
