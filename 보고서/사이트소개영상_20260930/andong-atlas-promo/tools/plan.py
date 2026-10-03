"""사이트 소개 영상 편집 계획(정본). 컷·자막·효과음 시점을 여기서만 고친다.

실행 순서: python3 tools/plan.py && python3 tools/prep.py && python3 tools/build_index.py && .venv_pdf/bin/python tools/make_audio.py
단위 초. 컷 start는 타임라인 시작, src는 원본에서 쓰는 시작점, x는 앞 컷과 겹치는 전환 길이.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEW = "../clips"  # 이번에 새로 찍은 지도 장면(보고서/사이트소개영상_20260930/clips)
OLD = "../../영상촬영_20260930/clips"  # 9/30 1인칭 릴레이 촬영본

SHOTS = [
    # id, 원본, src 시작, 타임라인 시작, 길이, 전환, 메모
    ("aerial", f"{NEW}/M01_안동_항공.mp4", 0.0, 0.0, 9.0, 0, "안동 전역 항공, 도심 쪽으로 천천히 전진"),
    ("hahoe", f"{NEW}/M02_하회마을.mp4", 0.2, 8.2, 8.0, 0.8, "하회마을 물돌이 둘레 선회"),
    ("city", f"{NEW}/M03_원도심_낙동강.mp4", 0.2, 15.4, 7.6, 0.8, "원도심 강변을 따라 옆으로 이동"),
    ("ui", f"{NEW}/M05a_화면_노을야경.mp4", 0.0, 22.4, 8.0, 0.6, "사이트 화면: 노을 → 야경 버튼"),
    ("bridge", f"{NEW}/M04_월영교_night.mp4", 0.3, 29.8, 6.8, 0.6, "밤의 월영교(지도)"),
    ("cta", f"{NEW}/M05b_화면_릴레이진입.mp4", 0.0, 36.0, 4.9, 0.6, "사이트 화면: 1인칭 릴레이 체험 누르기"),
    ("alley", f"{OLD}/S03_골목에서_식당으로.mp4", 0.2, 40.5, 4.3, 0.4, "찜닭골목 걷기"),
    ("meal", f"{OLD}/S04_찜닭_직접식사.mp4", 2.4, 44.4, 4.0, 0.4, "젓가락으로 찜닭 집기"),
    ("mask", f"{OLD}/S07b_하회탈_붓질과완성.mp4", 18.0, 48.0, 5.6, 0.4, "하회탈 색칠 → 완성"),
    ("walk", f"{OLD}/S10_월영교_산책.mp4", 2.4, 53.0, 6.0, 0.6, "밤의 월영교 걷기"),
    ("popup", f"{OLD}/S11a_월영밤마당_산책.mp4", 0.3, 58.4, 5.2, 0.6, "월영 밤마당(야간 팝업 제안)"),
    ("ending", f"{OLD}/S13_S14_월영교_엔딩전경.mp4", 0.0, 62.8, 13.2, 0.8, "월영교 엔딩 전경"),
]
TOTAL = 76.0

# pos: bottom(왼쪽 아래) / ui(사이트 화면 위 가운데, 도구 막대·패널을 피함)
LABELS = [
    ("c-hahoe", 9.3, 5.9, "bottom", "물이 마을을 감싸 도는 곳", "하회마을"),
    ("c-city", 16.4, 5.6, "bottom", "원도심의 건물과 강변을 가까이", "안동 원도심 · 낙동강"),
    ("c-ui", 23.2, 6.4, "ui", "낮에서 밤까지, 버튼 하나로", "날씨 · 시간 바꾸기"),
    ("c-bridge", 30.6, 5.0, "bottom", "밤이 되면 월영교에 불이 켜지고", "월영교"),
    ("c-cta", 36.6, 3.4, "ui", "지도에서 바로 1인칭 체험으로", "1인칭 릴레이 체험"),
    ("c-alley", 41.1, 3.2, "bottom", "골목을 걸어 식당으로", "찜닭골목"),
    ("c-meal", 44.8, 3.0, "bottom", "찜닭 한 끼를 직접", "원도심 식당 · 시연"),
    ("c-mask", 48.5, 4.2, "bottom", "하회탈에 색을 입히고", "전통 체험 · 제안 공방"),
    ("c-walk", 53.7, 4.5, "bottom", "강 위의 밤길을 걷는다", "월영교"),
    ("c-popup", 59.0, 3.6, "bottom", "강변 야간 팝업까지", "월영 밤마당 · 제안"),
]

EVENTS = {
    "open_title": 1.0,
    "sunset_click": 22.4 + 74 / 30,
    "night_click": 22.4 + 164 / 30,
    "cta_click": 36.0 + 100 / 30,
    "to_relay": 40.5,
    "night": 53.0,
    "ending_title": 66.2,
}


def main():
    shots = []
    for sid, src, ss, start, dur, x, memo in SHOTS:
        shots.append({"id": sid, "src": src, "ss": ss, "start": start, "dur": dur, "end": round(start + dur, 3), "x": x, "memo": memo})
    for a, b in zip(shots, shots[1:]):
        gap = round(a["end"] - b["start"], 3)
        assert gap >= b["x"] - 1e-6, f"{a['id']}→{b['id']} 겹침 {gap} < 전환 {b['x']}"
    assert abs(shots[-1]["end"] - TOTAL) < 1e-6, shots[-1]["end"]
    labels = [{"id": i, "start": s, "dur": d, "pos": p, "text": t, "tag": g} for i, s, d, p, t, g in LABELS]
    out = {"total": TOTAL, "shots": shots, "labels": labels, "events": EVENTS}
    (ROOT / "tools" / "timeline.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("timeline.json:", len(shots), "shots, total", TOTAL)


if __name__ == "__main__":
    main()
