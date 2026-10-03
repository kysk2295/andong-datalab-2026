# 이어드림 1인칭 체험 Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development. User approved autonomous research and implementation on 2026-09-29. Preserve concurrent changes and existing Atlas features. No public deployment requested.

**Goal:** Make the supplied food → receipt → traditional experience → transport → Woryeong bridge / popup proposal the main product experience, with persistent interactions and researched source material.

**Architecture:** Default entry renders a dedicated first-person Three.js experience; explicit Atlas layout URLs retain the existing map. Small scene modules, a pure state reducer, and a DOM controller separate visual animation from progress/coupon logic. Real-place references, proposed operations, and invented demonstration geometry are identified individually.

**Tech Stack:** Existing Vite, Three.js, vanilla ES modules, Node tests.

## Tasks and ownership

- [ ] Research: collect public primary-source restaurant/menu/interior references, Andong soju/mask/tea programs, bridge/boats/festival and transport/parking facts. Save source URL, access date, field-level uncertainty and media licensing in `public/data/relay-research.json` and `artifacts/relay/research.md`. Reuse existing verified local source data. No inferred participation, fake hours or copied reviews.
- [ ] 3D scenes: `src/relay-scene.js` and optional `src/relay-sets.js`. Dedicated renderer with market, restaurant, receipt, workshop (mask/tea/soju), transit, bridge, popup. Detailed meter-scale geometry, first-person hands/tools, camera drag, reduced motion, action animation and disposal. Export `RelayScene(container, {onInteract})` with `setScene(id, options)`, `act(action, payload)`, `setQuality`, `dispose`.
- [ ] State: `src/relay-model.js` and `tests/relay.test.mjs`. Pure `createRelayState`, `relayReducer`, stage definitions. Meal required for receipt; scan failure/retry; coupon issued once, redeemed once, retained across navigation; each craft completes through distinct steps; selected transport and popup purchase recorded; reset clears only this simulation. Guard arbitrary stage jumping and malformed actions.
- [ ] UI: `src/relay-ui.js`, `src/relay.css`, `src/entry.js`, `index.html`. Default prominent project introduction and first-person start. Compact chapter rail, primary contextual action, integrated phone/coupon, program choice, source drawer with reference photographs, mini route, mobility data, subtitles, all chapter navigation, reset and finish summary. Mobile touch layout and keyboard-accessible controls. Clearly label demonstration transactions and proposed spaces.
- [ ] Integrate data into sources, practical-information and travel panels. Show confirmed facts separately from route simulation times. Three business stages remain food→experience / evening transport / Woryeong popup; four user-provided scenes remain presentation chapters, with travel explicitly connected.
- [ ] Verification: state tests for blocked coupon use, invalid/duplicate receipts, reset and all three craft paths; run existing tests and build. Browser desktop/mobile start→eat→scan→craft→transport→bridge→popup→finish, image loading/fallback, map return, drawer focus, reload and WebGL failure. Capture actual screenshots and report limits.
- [ ] Independent specification review followed by code review; fix findings. Update README, QA and work log with exact verified results and available source gaps.

## Acceptance

The default screen gives the relay proposal visual priority; each user-requested stage has an explorable detailed scene and meaningful interaction. Photos inform or accompany constructed models rather than being misrepresented as reconstructed interiors. No actual payment/receipt validation, no unsupported benefits or fixed bus schedules. Existing report effects and data remain unchanged. Public deployment remains separate.
