---
version: alpha
name: 안동 이어드림 — 데이터랩 파랑 (영상 프레임)
description: >
  팀 그림 기준(docs/디자인.md 0장)을 영상 화면 크기로 옮긴 것. 흰 바탕 한 장, 강조는 데이터랩 파랑 한 가지,
  비교 대상은 차콜, 나머지는 연회색. Pretendard 한 가족. 서식4·분석보고서 그림과 같은 시각 언어라서
  심사위원이 문서와 영상을 같은 사업으로 알아보게 한다.
unit: 1920x1080
principle: 숫자는 정본 JSON에서 · 강조색은 한 화면에 하나 · 안동 값 옆엔 늘 전국 중앙값

colors:
  bg: "#FBFCFE"          # 파랑 쪽으로 아주 살짝 기운 흰색 (순백 금지)
  ink: "#34383C"         # 차콜: 제목 첫 톤, 비교 대상
  text: "#222222"
  text-muted: "#555555"
  text-light: "#8A9096"
  primary: "#2D6BD9"     # 데이터랩 파랑: 안동·이어드림·강조
  primary-deep: "#1A4FA8"
  primary-light: "#A8C4F0"
  primary-wash: "#EAF1FC"
  gray: "#D5D9DC"        # 나머지
  track: "#ECEEF0"

typography:
  eyebrow:  { fontFamily: "Pretendard", px: 24, weight: 700, tracking: "0.14em", upper: true, color: "primary" }
  h1:       { fontFamily: "Pretendard", px: 76, weight: 800, lineHeight: 1.18, tracking: "-0.02em", color: "ink", second-tone: "primary" }
  h2:       { fontFamily: "Pretendard", px: 52, weight: 800, lineHeight: 1.2, color: "ink" }
  body:     { fontFamily: "Pretendard", px: 32, weight: 500, lineHeight: 1.5, color: "text-muted" }
  stat:     { fontFamily: "Pretendard", px: 150, weight: 800, lineHeight: 1.0, tracking: "-0.03em", color: "primary" }
  label:    { fontFamily: "Pretendard", px: 24, weight: 600, color: "text-muted" }
  source:   { fontFamily: "Pretendard", px: 20, weight: 500, color: "text-light" }

spacing:
  pad-x: "120px"
  pad-top: "96px"
  accent-line: "72px × 5px primary"

components:
  head: "eyebrow(흐름 + 번호, 예: 시행 전 계산 02) → 두 톤 h1(차콜 + 파랑) → 파랑 짧은 선"
  source-line: "왼쪽 아래: 파랑 12px 사각형 + '출처: …' source 글자"
  progress-strip: "맨 아래 4구간 띠(문제 · 해법 · 시행 전 계산 · 시행 후 확인), 현재 구간만 파랑"
  tag: "둥근 칩, 파랑 테두리 2px: '외지인'·'예측'·'설문 72명'"
---

## Overview

심사위원이 서식4와 분석보고서에서 본 그림과 같은 색·글꼴이다. 새 브랜드를 만들지 않는다.

## Do

- 한 화면에 강조(파랑)는 하나. 나머지는 차콜과 회색.
- 숫자 옆에는 늘 크기를 보여 주는 장치(막대, 점, 사람 아이콘, 링)를 둔다.
- 안동 값에는 전국 중앙값(−2.0%)을 같은 화면에 둔다.
- 예측 화면에는 '예측' 태그와 "시행 전 예측, 1만 번 계산의 가운데 값"을 둔다.

## Don't

- 그라디언트 글자, 네온, 어두운 바탕, 카드 격자 반복, 원그래프.
- 증명·검증 완료·신뢰구간·1인당·사후 검증 같은 말.
- 엠대시(—).
