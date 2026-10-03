"""index.html 생성기. 컷·자막·효과음 시점은 tools/edit_plan.py(→ timeline.json)가 정본이다.

실행: python3 tools/edit_plan.py && python3 tools/prep_clips.py && python3 tools/build_index.py
영상 소스는 prep_clips.py가 만든 assets/cut/<컷id>.mp4(1.3배속·흔들림 보정 완료)를 그대로 재생한다.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN = json.loads((ROOT / "tools" / "timeline.json").read_text(encoding="utf-8"))
SHOTS = PLAN["shots"]
BY = {s["id"]: s for s in SHOTS}
EV = PLAN["events"]
TOTAL = PLAN["total"]

# 작은 안내창을 읽히게 천천히 밀어 넣는 구간: (컷, 기준점, 시작, 길이, 배율 from→to)
PUSHES = [
    ("qr", "1640px 1000px", EV["qr_align"], BY["qr"]["end"] - EV["qr_align"], 1.0, 1.2),
    ("coupon", "1644px 800px", BY["coupon"]["start"], BY["coupon"]["dur"], 1.0, 1.08),
    ("apply", "1738px 255px", BY["apply"]["start"], BY["apply"]["dur"], 1.15, 1.28),
    ("mask", "960px 460px", BY["mask"]["start"], BY["mask"]["dur"], 1.0, 1.05),
    ("market", "1150px 430px", BY["market"]["start"], BY["market"]["dur"], 1.0, 1.08),
]

MAP_CREDIT = "지도 © OpenStreetMap contributors / OpenFreeMap · 행정경계 통계청 SGIS"


def fmt(x):
    return f"{round(x, 3):g}"


def video_html():
    out = []
    for i, s in enumerate(SHOTS):
        out.append(
            f'      <!-- {s["memo"]} -->\n'
            f'      <div id="{s["id"]}-w" class="shot" style="z-index: {i + 1}">\n'
            f'        <video id="{s["id"]}" class="clip" src="assets/cut/{s["id"]}.mp4" data-start="{fmt(s["start"])}" '
            f'data-duration="{fmt(s["dur"])}" data-media-start="0" data-track-index="{i % 2}" muted playsinline></video>\n'
            f'      </div>'
        )
    return "\n".join(out)


def caption_html():
    out = []
    for c in PLAN["labels"]:
        tag_html = f'\n          <p class="tag">{c["tag"]}</p>' if c["tag"] else ""
        out.append(
            f'      <div id="{c["id"]}" class="clip cap cap-{c["pos"]}" data-start="{fmt(c["start"])}" '
            f'data-duration="{fmt(c["dur"])}" data-track-index="3">\n'
            f'        <div class="scrim"></div>\n'
            f'        <div class="cap-body">\n'
            f'          <p class="line">{c["text"]}</p>{tag_html}\n'
            f'        </div>\n'
            f'      </div>'
        )
    return "\n".join(out)


def timeline_js():
    js = []
    a = BY["alley"]["start"]
    # 시작 상태 고정(여러 번 움직이는 컷은 구간 전 탐색에서도 같은 화면)
    js.append('gsap.set("#map-w", { scale: 1, filter: "blur(0px)" });')
    for sid, origin, t, d, s0, s1 in PUSHES:
        js.append(f'gsap.set("#{sid}-w", {{ transformOrigin: "{origin}", scale: {s0}, opacity: {0 if BY[sid]["x"] else 1} }});')
    # 겹침 전환: 들어오는 컷만 투명→불투명(나가는 컷은 아래에 그대로 두어 밝기가 꺼지지 않게)
    for s in SHOTS:
        if s["x"] > 0 and s["id"] != "alley":
            js.append(f'tl.fromTo("#{s["id"]}-w", {{ opacity: 0 }}, {{ opacity: 1, duration: {fmt(s["x"])}, '
                      f'ease: "sine.inOut", immediateRender: false }}, {fmt(s["start"])});')
    # 지도 → 1인칭: 지도 카메라가 향하던 화면 가운데(원도심)로 계속 파고들며 흐려지고,
    # 같은 전진 방향의 골목 걷기가 흐림에서 초점을 찾는다
    js.append(f'tl.fromTo("#map-w", {{ scale: 1, filter: "blur(0px)" }}, {{ scale: 1.3, filter: "blur(10px)", '
              f'duration: 0.9, ease: "power2.in", immediateRender: false }}, {fmt(a - 0.3)});')
    js.append(f'tl.fromTo("#alley-w", {{ opacity: 0, scale: 1.14, filter: "blur(10px)" }}, {{ opacity: 1, scale: 1, '
              f'filter: "blur(0px)", duration: 0.8, ease: "power2.out" }}, {fmt(a)});')
    for sid, origin, t, d, s0, s1 in PUSHES:
        js.append(f'tl.fromTo("#{sid}-w", {{ scale: {s0} }}, {{ scale: {s1}, duration: {fmt(d)}, '
                  f'ease: "sine.inOut", immediateRender: false }}, {fmt(t)});')
    # 표시 자막: 들어올 때 0.5초, 나갈 때 0.4초
    for c in PLAN["labels"]:
        cid, t, d = c["id"], c["start"], c["dur"]
        dy = 14 if c["pos"] == "bottom" else -10
        js.append(f'tl.fromTo("#{cid} .scrim", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5, ease: "sine.out" }}, {fmt(t)});')
        js.append(f'tl.fromTo("#{cid} .line", {{ opacity: 0, y: {dy} }}, {{ opacity: 1, y: 0, duration: 0.5, '
                  f'ease: "power2.out" }}, {fmt(t + 0.05)});')
        if c["tag"]:
            js.append(f'tl.fromTo("#{cid} .tag", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, ease: "sine.out" }}, {fmt(t + 0.3)});')
        js.append(f'tl.to("#{cid} .cap-body, #{cid} .scrim", {{ opacity: 0, duration: 0.4, ease: "sine.in" }}, {fmt(t + d - 0.4)});')
    # 시작 표시
    js.append('tl.fromTo("#open-note .scrim", { opacity: 0 }, { opacity: 1, duration: 0.5, ease: "sine.out" }, 0.6);')
    js.append('tl.fromTo("#open-note .notes", { opacity: 0 }, { opacity: 1, duration: 0.5, ease: "sine.out" }, 0.8);')
    js.append(f'tl.to("#open-note .notes, #open-note .scrim", {{ opacity: 0, duration: 0.4, ease: "sine.in" }}, {fmt(a - 0.6)});')
    # 엔딩
    e = EV["ending_title"]
    js.append(f'tl.fromTo("#ending .scrim", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.9, ease: "sine.out" }}, {fmt(e)});')
    js.append(f'tl.fromTo("#ending .title", {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.9, ease: "power2.out" }}, {fmt(e + 0.1)});')
    js.append(f'tl.fromTo("#ending .rule", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.7, ease: "power3.out" }}, {fmt(e + 0.5)});')
    js.append(f'tl.fromTo("#ending .subtitle", {{ opacity: 0, y: 10 }}, {{ opacity: 1, y: 0, duration: 0.8, ease: "power2.out" }}, {fmt(e + 0.6)});')
    js.append(f'tl.fromTo("#ending .credits", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.7, ease: "sine.out" }}, {fmt(e + 0.9)});')
    return "\n      ".join(js)


def audio_html():
    ev = EV
    rows = [
        ("bgm", "assets/audio/bgm.wav", 0, TOTAL, 10, 1),
        ("amb", "assets/audio/ambience.wav", 0, TOTAL, 11, 0.8),
        ("foley", "assets/audio/foley.wav", 0, TOTAL, 12, 0.9),
        ("sfx-whoosh", "assets/audio/sfx/whoosh-short.mp3", ev["map_to_alley"] - 0.25, 0.57, 13, 0.3),
        ("sfx-pay", "assets/audio/sfx/click-soft.mp3", ev["pay_tap"] - 0.03, 0.37, 14, 0.55),
        ("sfx-qr", "assets/audio/sfx/chime.mp3", ev["qr_success"], 2.5, 15, 0.4),
    ]
    return "\n".join(
        f'      <audio id="{i}" src="{src}" data-start="{fmt(t)}" data-duration="{fmt(d)}" '
        f'data-track-index="{k}" data-volume="{v}"></audio>'
        for i, src, t, d, k, v in rows)


HTML = """<!doctype html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>안동 이어드림 · 한 끼에서, 안동의 밤까지</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      @font-face { font-family: "Pretendard"; src: url("assets/fonts/Pretendard-Light.otf") format("opentype"); font-weight: 300; }
      @font-face { font-family: "Pretendard"; src: url("assets/fonts/Pretendard-Regular.otf") format("opentype"); font-weight: 400; }
      @font-face { font-family: "Pretendard"; src: url("assets/fonts/Pretendard-Medium.otf") format("opentype"); font-weight: 500; }
      @font-face { font-family: "Pretendard"; src: url("assets/fonts/Pretendard-SemiBold.otf") format("opentype"); font-weight: 600; }
      @font-face { font-family: "Pretendard"; src: url("assets/fonts/Pretendard-Bold.otf") format("opentype"); font-weight: 700; }
      :root {
        --ink: #f5f2ea;
        --ink-soft: #e6e2d8;
        --lamp: #e8bf78;
        --night: 6, 12, 10;
      }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #070b0a; }
      #root {
        position: relative; width: 100%; height: 100%; overflow: hidden;
        font-family: "Pretendard", sans-serif; color: var(--ink);
        word-break: keep-all;
      }
      .shot { position: absolute; inset: 0; will-change: transform, opacity; }
      .shot video { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
      p { margin: 0; }

      /* 표시 자막: 지금 어느 체험·장소인지만. 흰 글자 + 약한 그림자, 뒤에 경계 없는 어둠 번짐만 */
      .cap { position: absolute; inset: 0; z-index: 100; pointer-events: none; }
      .cap .scrim { position: absolute; left: 0; right: 0; }
      .cap-bottom .scrim { bottom: 0; height: 320px; background: linear-gradient(to top, rgba(var(--night), 0.6), rgba(var(--night), 0.26) 55%, rgba(var(--night), 0)); }
      .cap-top .scrim { top: 0; height: 300px; background: linear-gradient(to bottom, rgba(var(--night), 0.64), rgba(var(--night), 0.28) 55%, rgba(var(--night), 0)); }
      .cap-body { position: absolute; left: 132px; right: 132px; display: flex; flex-direction: column; gap: 12px; }
      .cap-bottom .cap-body { bottom: 92px; }
      .cap-top .cap-body { top: 84px; }
      .line {
        font-size: 50px; font-weight: 600; letter-spacing: -0.01em; line-height: 1.3;
        text-shadow: 0 2px 14px rgba(0, 0, 0, 0.55), 0 1px 2px rgba(0, 0, 0, 0.5);
      }
      .tag {
        display: flex; align-items: center; gap: 12px;
        font-size: 26px; font-weight: 500; color: var(--ink-soft); letter-spacing: 0.02em;
        text-shadow: 0 1px 8px rgba(0, 0, 0, 0.6);
      }
      .tag::before { content: ""; display: block; width: 9px; height: 9px; border-radius: 50%; background: var(--lamp); }

      /* 시작 표시·지도 출처 */
      #open-note { position: absolute; inset: 0; z-index: 110; pointer-events: none; }
      #open-note .scrim { position: absolute; left: 0; right: 0; bottom: 0; height: 320px; background: linear-gradient(to top, rgba(var(--night), 0.6), rgba(var(--night), 0.26) 55%, rgba(var(--night), 0)); }
      #open-note .notes { position: absolute; right: 132px; bottom: 96px; display: flex; flex-direction: column; align-items: flex-end; gap: 10px; text-align: right; }
      #open-note .demo { font-size: 26px; font-weight: 600; letter-spacing: 0.02em; text-shadow: 0 1px 8px rgba(0, 0, 0, 0.6); }
      #open-note .credit { font-size: 20px; font-weight: 400; color: var(--ink-soft); text-shadow: 0 1px 6px rgba(0, 0, 0, 0.7); }

      /* 엔딩: 하늘 쪽 왼쪽 위에 제목, 오른쪽 위에 출처. 월영정·수면 반사를 가리지 않는다 */
      #ending { position: absolute; inset: 0; z-index: 120; pointer-events: none; }
      #ending .scrim { position: absolute; left: 0; top: 0; width: 1100px; height: 420px; background: radial-gradient(ellipse at 0% 0%, rgba(var(--night), 0.55), rgba(var(--night), 0) 70%); }
      #ending .title-block { position: absolute; left: 132px; top: 104px; display: flex; flex-direction: column; gap: 22px; }
      #ending .title { font-size: 112px; font-weight: 700; letter-spacing: -0.02em; line-height: 1.05; text-shadow: 0 2px 18px rgba(0, 0, 0, 0.5); }
      #ending .rule { display: block; width: 84px; height: 3px; background: var(--lamp); transform-origin: left center; }
      #ending .subtitle { font-size: 48px; font-weight: 300; letter-spacing: -0.005em; text-shadow: 0 2px 12px rgba(0, 0, 0, 0.55); }
      #ending .credits { position: absolute; right: 96px; top: 64px; display: flex; flex-direction: column; align-items: flex-end; gap: 8px; text-align: right; }
      #ending .credits p { font-size: 20px; font-weight: 400; color: var(--ink-soft); text-shadow: 0 1px 6px rgba(0, 0, 0, 0.7); }
      #ending .credits .demo { font-size: 24px; font-weight: 600; color: var(--ink); }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="__TOTAL__" data-width="1920" data-height="1080">
__VIDEOS__

      <div id="open-note" class="clip" data-start="0.6" data-duration="__OPEN_DUR__" data-track-index="4">
        <div class="scrim"></div>
        <div class="notes">
          <p class="demo">안동 이어드림 제안 · 3D 체험 시연</p>
          <p class="credit">__MAP_CREDIT__</p>
        </div>
      </div>

__CAPTIONS__

      <div id="ending" class="clip" data-start="__END_START__" data-duration="__END_DUR__" data-track-index="6">
        <div class="scrim"></div>
        <div class="title-block">
          <p class="title">안동 이어드림</p>
          <span class="rule"></span>
          <p class="subtitle">한 끼에서, 안동의 밤까지.</p>
        </div>
        <div class="credits">
          <p class="demo">3D 체험 시연 · 일부 공간·혜택·운영은 제안</p>
          <p>__MAP_CREDIT__</p>
          <p>음악 자체 제작 · 효과음 Pixabay</p>
        </div>
      </div>

__AUDIO__
    </div>
    <script>
      const tl = gsap.timeline({ paused: true });
      __TIMELINE__
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""

html = (HTML.replace("__VIDEOS__", video_html())
        .replace("__CAPTIONS__", caption_html())
        .replace("__TIMELINE__", timeline_js())
        .replace("__AUDIO__", audio_html())
        .replace("__TOTAL__", fmt(TOTAL))
        .replace("__OPEN_DUR__", fmt(BY["alley"]["start"] - 0.6))
        .replace("__END_START__", fmt(EV["ending_title"]))
        .replace("__END_DUR__", fmt(TOTAL - EV["ending_title"]))
        .replace("__MAP_CREDIT__", MAP_CREDIT))
(ROOT / "index.html").write_text(html, encoding="utf-8")
print("index.html written:", len(SHOTS), "shots,", len(PLAN["labels"]), "labels, total", TOTAL)
