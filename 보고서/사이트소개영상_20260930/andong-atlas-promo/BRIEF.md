---
workflow: general-video
flow: automation
storyboard: no
message: "3D 안동 지도에서 명소를 둘러보고, 버튼 하나로 밤이 되고, 1인칭으로 안동의 밤까지 걸어 들어간다"
destination: 사이트 소개·홍보 영상(발표·공유)
aspect: 1920x1080
language: ko
length: 76s
angle: 안동 홍보영상 형식(항공 → 하회마을 → 원도심 → 사이트 조작 → 월영교 밤 → 1인칭 체험 → 엔딩 주소)
---

## Intent
사용자(9/30): "이 웹 사이트 소개를 안동 홍보영상처럼 자연스럽게 찍어서 영상으로. 묻지 말고 렌더까지." 질문 없이 자동 진행.

## Assets
- ../clips/M*.mp4 — 이번 촬영(capture/ 서버, 프레임별 실제 WebGL). 카메라 경로는 ../capture/*.json
- ../../영상촬영_20260930/clips/S03·S04·S07b·S10·S11a·S13 — 1인칭 릴레이 촬영본 재사용
- Pretendard(OFL), 효과음 Pixabay 번들 2개(click-soft, whoosh-short), 음악 tools/make_audio.py 자체 합성

## Notes
- 공방·팝업·혜택은 "제안", 식당은 "시연" 표기. 엔딩에 사이트 주소와 지도 출처.
- 엠대시·카드·배지 없이 흰 글자 + 어둠 번짐.
