"""편집 정본: 컷(원본 구간)·전환·표시 자막·효과음 시점. 1.3배속 편집(9/30 사용자 요청).

타임라인 시간은 여기서 계산해 tools/timeline.json으로 내보내고,
prep_clips.py(클립 전처리) · build_index.py(index.html) · make_audio.py(음악·효과음)가 같은 값을 읽는다.
실행: python3 tools/edit_plan.py
"""
import json
from pathlib import Path

SPEED = 1.3
ROOT = Path(__file__).resolve().parent.parent

# 전처리 방식
#  frame : 프레임별 실제 렌더(30fps, 매끄러움) → 1.3배로 프레임만 솎음
#  rt25  : 실시간 녹화 25fps를 30fps로 바꾼 것(6장마다 중복) → 중복 제거 후 1.3배
#  lowfps: 실시간 녹화 중 고유 프레임이 적은 것(흔들림) → 중복 제거 후 움직임 보간, 1.3배
#  static: 대부분 멈춘 화면 → 1.3배로 솎음
#  hand  : 손 동작이 드문드문 갱신된 녹화 → 짧은 중복만 버리고 움직임 보간
#  paint : 색칠이 가끔 갱신 → 사이를 섞어 서서히 칠해지게
#  hold  : 실제 화면 정지 캡처 → 속도 변경 없이 표시 시간만 지정
# (id, [(파일, 원본 시작, 원본 끝), ...], 방식, 들어올 때 겹침 초, 메모, hold 표시 초)
SHOTS = [
    ("map", [("s01", 1.0, 7.0), ("s02", 0.0, 6.3)], "frame", 0.0,
     "S01+S02 한 줄 카메라 경로(S01 끝 = S02 시작, 건너뛰기 없음)", None),
    ("alley", [("s03", 4.4, 12.4)], "rt25", 0.6, "S03 골목 걷기 → 식당 문(문틀 가림에서 다음 컷)", None),
    ("meal", [("s04", 1.3, 7.3)], "hand", 0.0, "S04 찜닭 식사", None),
    ("pay", [("s05", 0.8, 5.8)], "hand", 0.0, "S05 결제·영수증", None),
    ("qr", [("s06", 1.15, 7.0)], "hand", 0.0, "S06 QR 인증(첫 프레임 번쩍임 제외)", None),
    ("coupon", [("s06b", 0.0, 3.0)], "hold", 0.0, "S06b 할인권 발급 실제 화면", 2.2),
    ("apply", [("s07c_hold", 0.0, 3.0)], "hold", 0.4, "S07c 할인 적용 실제 화면", 1.9),
    ("paint", [("s07b", 1.0, 5.0)], "paint", 0.0, "S07b 붓질", None),
    ("mask", [("s07b", 24.2, 26.5)], "static", 0.4, "S07b 완성", None),
    ("ride", [("s08", 1.7, 8.0)], "rt25", 0.5, "S08 월영교로 이동", None),
    ("bridge", [("s09", 0.5, 8.4)], "frame", 0.9, "S09 월영교 첫 전경", None),
    ("walk", [("s10", 0.6, 8.3)], "frame", 0.7, "S10 다리 산책", None),
    # S11a는 고유 프레임이 초당 약 10장이고 한 번에 크게 튀어 보간으로도 끊김이 남는다.
    # 부스 전체가 보이는 실제 캡처 프레임(원본 4.7초)을 천천히 밀어 넣는다(build_index.py PUSHES).
    ("market", [("s11a", 4.7, 7.4)], "hold", 0.5, "S11a 밤마당 전경(실제 캡처 프레임, 흔들림 때문에 정지+밀어넣기)", 2.7),
    ("tea", [("s11c", 0.3, 5.9)], "hand", 0.3, "S11c 국화차 맛보기", None),
    ("river", [("s12", 0.6, 9.4)], "frame", 0.7, "S12 수면 반사 → 월영교", None),
    ("ending", [("s13", 0.0, 12.8)], "frame", 0.7, "S13·S14 엔딩 전경(한 소스 연속)", None),
]

# 자막 = 지금 어느 체험·장소인지만. (첫 컷, 마지막 컷, 위치, 문구, 작은 표시, 시작 지연, 끝 당김)
LABELS = [
    ("map", "map", "bottom", "안동 원도심", "", 0.8, 1.2),
    ("alley", "alley", "bottom", "찜닭골목 · 이어드림 식당", "", 0.7, 0.5),
    ("meal", "meal", "bottom", "찜닭 식사", "", 0.3, 0.3),
    ("pay", "pay", "bottom", "계산 · 영수증", "", 0.3, 0.2),
    ("qr", "coupon", "top", "영수증 QR 인증 · 체험 할인권", "인증·혜택 시연", 0.3, 0.2),
    ("paint", "mask", "bottom", "하회탈 꾸미기 체험", "", 0.2, 0.3),
    ("ride", "ride", "bottom", "월영교 가는 연결차량", "연결차량 운영 제안", 0.4, 0.4),
    ("bridge", "bridge", "bottom", "월영교", "", 0.8, 3.0),
    ("market", "tea", "bottom", "월영교 밤마당 · 국화차", "야간 팝업 제안", 0.3, 0.4),
]

ENDING_HOLD = 4.0  # 마지막 제목 표시 초


def build():
    shots, t = [], 0.0
    for sid, parts, mode, x, memo, hold in SHOTS:
        src = sum(b - a for _, a, b in parts)
        dur = hold if mode == "hold" else round(src / SPEED, 3)
        start = round(t - x, 3) if shots else 0.0
        shots.append(dict(id=sid, parts=parts, mode=mode, x=x, memo=memo, start=start, dur=dur,
                          end=round(start + dur, 3)))
        t = start + dur
    by = {s["id"]: s for s in shots}
    total = round(shots[-1]["end"], 2)

    def at(sid, src_time, part=0):
        """원본 시각 → 타임라인 시각."""
        s = by[sid]
        f, a, b = s["parts"][part]
        return round(s["start"] + (src_time - a) / SPEED, 3)

    labels = []
    for first, last, pos, text, tag, d0, d1 in LABELS:
        st = by[first]["start"] + by[first]["x"] + d0
        en = by[last]["end"] - d1
        labels.append(dict(id=f"lab-{first}", start=round(st, 2), dur=round(en - st, 2), pos=pos, text=text, tag=tag))

    events = {
        "map_to_alley": by["alley"]["start"],
        "pay_tap": at("pay", 2.8),          # 카드가 단말기에 닿는 순간
        "qr_align": at("qr", 4.0),           # "잘 맞았어요" 표시
        "qr_success": at("qr", 5.3),         # "QR을 확인했어요" 표시
        "night": by["bridge"]["start"] + by["bridge"]["x"] / 2,
        "meal": by["meal"]["start"],
        "ride": by["ride"]["start"],
        "market": by["market"]["start"],
        "river": by["river"]["start"],
        "ending_title": round(total - ENDING_HOLD, 2),
    }
    return dict(speed=SPEED, total=total, shots=shots, labels=labels, events=events)


if __name__ == "__main__":
    plan = build()
    (ROOT / "tools" / "timeline.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    for s in plan["shots"]:
        print(f'{s["id"]:8s} {s["start"]:6.2f} ~ {s["end"]:6.2f}  ({s["dur"]:.2f}s, 겹침 {s["x"]})  {s["memo"]}')
    print("총 길이", plan["total"], "초 / 사건", plan["events"])
