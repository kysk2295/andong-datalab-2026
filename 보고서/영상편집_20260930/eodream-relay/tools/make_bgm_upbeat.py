"""박자감 있는 배경음악(assets/audio/bgm.wav) 합성. 9/30 사용자 요청: "너무 잔잔해 다른 걸로".

약 102BPM, D장조 I–V–vi–IV. 드럼·베이스·플럭 아르페지오·후렴 선율을 직접 합성한다(외부 음원 없음).
월영교 첫 전경(timeline.json events.night)이 17마디째 첫 박에 오도록 마디 길이를 맞춘다.
  0~4마디   지도: 패드·플럭, 하이햇이 들어오며 준비
  4~15      골목~공방: 킥·클랩·하이햇·베이스 그루브, 8마디부터 선율
  15~17     이동: 스네어 롤·상승음으로 올림
  17~24     월영교·밤마당: 후렴(가장 크게), 크래시로 시작
  24~28     수면 반사: 킥 빼고 반박 클랩, 선율만
  28~끝     엔딩: 마지막 화음 한 번 치고 여운

실행: .venv_pdf/bin/python tools/make_bgm_upbeat.py  (make_audio.py의 악기·리버브 함수를 그대로 쓴다)
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_audio as A  # noqa: E402

SR, N, DUR, EV = A.SR, A.N, A.DUR, A.EV
rng = np.random.default_rng(930)

B_NIGHT = 17
BAR = EV["night"] / B_NIGHT
BEAT = BAR / 4
S16 = BEAT / 4
B_GROOVE, B_MEL, B_BUILD, B_BREAK = 4, 8, 15, 24
B_FINAL = int((DUR - 5.5) // BAR)  # 엔딩 제목 직전 마디에서 마지막 화음

CH = {  # 루트, 보이싱
    "D": (38, [62, 66, 69, 74]),
    "A": (45, [61, 64, 69, 73]),
    "Bm": (47, [62, 66, 71, 74]),
    "G": (43, [62, 67, 71, 74]),
}
PROG = ["D", "A", "Bm", "G"]


def env_exp(n, tau):
    return np.exp(-np.arange(n) / SR / tau)


def kick(v=1.0):
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 45 + 85 * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * env_exp(n, 0.16)
    x[: int(0.004 * SR)] += rng.standard_normal(int(0.004 * SR)) * 0.3
    return x * v


def clap(v=1.0):
    n = int(0.35 * SR)
    x = np.zeros(n)
    for k, d in enumerate([0, 0.011, 0.022]):
        i = int(d * SR)
        m = n - i
        x[i:] += A.bp(rng.standard_normal(m), 900, 5200) * env_exp(m, 0.012 if k < 2 else 0.11)
    t = np.arange(n) / SR
    x += 0.25 * np.sin(2 * np.pi * 190 * t) * env_exp(n, 0.05)
    return x * v * 0.9


def hat(v=1.0, open_=False):
    n = int((0.25 if open_ else 0.06) * SR)
    x = A.bp(rng.standard_normal(n), 6500, 15000) * env_exp(n, 0.09 if open_ else 0.018)
    return x * v * 0.5


def shaker(v=1.0):
    n = int(0.08 * SR)
    t = np.arange(n) / SR
    x = A.bp(rng.standard_normal(n), 4500, 11000) * np.sin(np.pi * np.clip(t / 0.08, 0, 1)) ** 2
    return x * v * 0.25


def crash(v=1.0):
    n = int(2.2 * SR)
    return A.bp(rng.standard_normal(n), 3000, 14000) * env_exp(n, 0.7) * v * 0.45


def bass(m, dur, v=0.8):
    f = A.mtof(m)
    n = int((dur + 0.05) * SR)
    t = np.arange(n) / SR
    x = sum((1 / k) * np.sin(2 * np.pi * k * f * t) for k in range(1, 7))
    x = A.lp(x, 900)
    e = np.clip(t / 0.005, 0, 1) * np.exp(-t / 0.25) * np.clip((dur + 0.05 - t) / 0.05, 0, 1)
    return x * e * v * 0.5


def pluck(m, v=0.5):
    f = A.mtof(m)
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.28)
         + 0.45 * np.sin(2 * np.pi * 2.0 * f * t) * np.exp(-t / 0.12)
         + 0.2 * np.sin(2 * np.pi * 3.98 * f * t) * np.exp(-t / 0.05))
    return x * np.clip(t / 0.002, 0, 1) * v * 0.45


def riser(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    out = np.zeros(n)
    seg = int(0.05 * SR)
    for i in range(0, n, seg):  # 구간마다 대역을 올려 가며 쉬익 소리
        c = 800 + 7000 * (i / n) ** 2
        out[i:i + seg] = A.bp(x[i:i + seg], c * 0.7, min(c * 1.4, 20000))
    return out * (t / dur) ** 2 * 0.5


# 후렴 선율(2마디 × 2): (마디 오프셋, 박, 음, 길이 박)
HOOK = [
    (0, 0, 78, 1), (0, 1, 81, 0.5), (0, 1.5, 78, 0.5), (0, 2, 76, 1), (0, 3, 74, 1),
    (1, 0, 76, 1.5), (1, 1.5, 73, 0.5), (1, 2, 76, 1), (1, 3, 69, 1),
    (2, 0, 74, 1), (2, 1, 78, 0.5), (2, 1.5, 74, 0.5), (2, 2, 71, 1), (2, 3, 74, 1),
    (3, 0, 76, 2), (3, 2, 74, 1), (3, 3, 71, 0.5), (3, 3.5, 69, 0.5),
]


def build():
    mel = np.zeros((2, N + SR * 6))
    drm = np.zeros((2, N + SR * 6))
    P = A.place
    nb = B_FINAL + 1
    for b in range(nb):
        st = b * BAR
        name = "D" if b >= B_FINAL else PROG[b % 4]
        root, voic = CH[name]
        chorus = B_NIGHT <= b < B_BREAK
        # 패드(얇게) — 코드 바닥
        lvl = 0.05 if b < B_GROOVE else (0.07 if not chorus else 0.1)
        dur = BAR if b < B_FINAL else DUR - st + 1.5
        P(mel, A.pad([m - 12 for m in voic], dur, lvl, bright=5), st, pan=-0.2)

        if b >= B_FINAL:  # 마지막 화음 한 번 크게, 여운
            P(drm, kick(0.9), st)
            P(drm, crash(0.8), st, pan=0.3)
            P(mel, A.pad(voic, dur, 0.12, bright=6), st, pan=0.2)
            P(mel, bass(root, 3.0, 0.9), st)
            for k, m in enumerate(voic + [voic[0] + 12]):
                P(mel, pluck(m, 0.55), st + k * S16 * 1.5, pan=-0.3 + 0.15 * k)
            continue

        # 플럭 아르페지오(16분) — 처음부터 끝까지 밝게 움직이는 층
        arp = [voic[0], voic[1], voic[2], voic[3], voic[2], voic[1], voic[2], voic[3]]
        for k in range(16):
            if b < 2 and k % 2:  # 도입 두 마디는 8분만
                continue
            v = (0.42 if k % 4 == 0 else 0.3) * (1.15 if chorus else 1.0) * (0.8 if b >= B_BREAK else 1.0)
            P(mel, pluck(arp[k % 8] + (12 if chorus and k % 4 == 2 else 0), v), st + k * S16,
              pan=0.35 if k % 2 else -0.1)

        # 드럼
        if b >= 2:  # 하이햇 8분(도입 3~4마디), 이후 16분
            step = 2 if b < B_GROOVE else 1
            for k in range(0, 16, step):
                v = 0.55 if k % 4 == 2 else 0.32
                if b >= B_BREAK:
                    v *= 0.7
                P(drm, hat(v, open_=(k % 8 == 6 and b >= B_GROOVE)), st + k * S16, pan=0.25)
        if B_GROOVE <= b < B_BREAK and b not in (B_BUILD + 1,):
            for k in [0, 6, 8, 11] if not chorus else [0, 4, 8, 11, 12]:
                P(drm, kick(0.95 if k in (0, 8) else 0.7), st + k * S16)
            for k in (4, 12):
                P(drm, clap(0.85 if chorus else 0.7), st + k * S16, pan=-0.05)
            for k in range(1, 16, 2):
                P(drm, shaker(0.6), st + k * S16, pan=-0.4)
        if b == B_BUILD + 1:  # 이동 마지막 마디: 스네어 롤 + 상승음, 킥 없음
            for k in range(16):
                P(drm, clap(0.25 + 0.5 * k / 15), st + k * S16)
            P(mel, riser(BAR), st, pan=0.0)
        if B_BREAK <= b < B_FINAL:  # 수면 반사: 반박 클랩만
            P(drm, clap(0.45), st + 8 * S16)
            P(drm, kick(0.5), st)
        if b in (B_GROOVE, B_NIGHT):
            P(drm, crash(0.9 if b == B_NIGHT else 0.6), st, pan=0.3)
        if b == B_GROOVE - 1:
            P(mel, riser(BAR), st)

        # 베이스: 8분 뿌리음(옥타브 오가기)
        if B_GROOVE <= b < B_BREAK and b != B_BUILD + 1:
            for k in range(8):
                m = root + (12 if k % 4 == 3 else 0)
                P(mel, bass(m, BEAT / 2 * 0.85, 0.9 if chorus else 0.8), st + k * BEAT / 2)
        elif b >= B_BREAK:
            P(mel, bass(root, BAR * 0.9, 0.7), st)

    # 선율: 8마디부터 후렴 전까지(부드럽게), 후렴에서 옥타브 겹쳐 크게, 수면 반사에서 한 번 더 조용히
    def hook_at(b0, v, octave_double, bars=4):
        for r, bt, m, d in HOOK:
            if r >= bars:
                continue
            st = (b0 + r) * BAR + bt * BEAT
            P(mel, A.piano(m, d * BEAT * 0.9, v), st, pan=0.05)
            if octave_double:
                P(mel, pluck(m + 12, v * 0.7), st, pan=0.2)
                P(mel, A.piano(m - 12, d * BEAT * 0.9, v * 0.6), st, pan=-0.1)

    for b0 in range(B_MEL, B_BUILD, 4):
        hook_at(b0, 0.36, False, bars=min(4, B_BUILD - b0))
    for b0 in range(B_NIGHT, B_BREAK, 4):
        hook_at(b0, 0.5, True, bars=min(4, B_BREAK - b0))
    for b0 in range(B_BREAK, B_FINAL, 4):
        hook_at(b0, 0.34, False, bars=min(4, B_FINAL - b0))

    mel = A.reverb(mel[:, :N], secs=2.4, mix=0.22)
    drm = drm[:, :N]
    drm = A.reverb(drm, secs=1.2, mix=0.08)
    mix = mel + drm * 0.9
    t = np.arange(N) / SR
    mix *= np.clip(t / 0.8, 0, 1) * np.clip((DUR - t) / 2.0, 0, 1)
    # 부드러운 압축(피크만 눌러 전체를 앞으로)
    mix = np.tanh(mix / (np.abs(mix).max() * 0.55)) * 0.55
    return mix


if __name__ == "__main__":
    print(f"BAR {BAR:.3f}s ({240 / BAR:.1f} BPM), 마지막 화음 {B_FINAL * BAR:.1f}s")
    A.write("bgm.wav", build(), -17)
