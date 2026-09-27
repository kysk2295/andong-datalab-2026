# Andong Atlas design contract

## 1. Source and purpose
Reference: https://seoul-3d-atlas.synabreu.chatgpt.site/ v1.9, inspected 2026-09-28 in desktop and 390×844 mobile views. Implementation follows docs/안동_3D_Atlas_설계안.md. A physical miniature of Andong, pale terrain, blue rivers, fine trees and buildings. Floating UI occupies the perimeter. The map is the focal object. No dashboard grid.

## 2. Tokens extracted from runtime
Ink #254b43; label ink #426657; panel rgba(253,255,251,.9); edge rgba(65,97,80,.11); shadow 0 8px 32px rgba(51,79,64,.075); label shadow 0 3px 10px rgba(43,82,61,.08). Panel radius 16px; location radius 13px; toolbar item 9px; label 6px. Font Arial, Apple SD Gothic Neo, Noto Sans KR, sans-serif. Title 45px, body 14px, labels 12px. Main panel 310px wide, 32px inset; location 265px wide. Toolbar item about 78×80px. Panel transition background .6s. Label padding 7px 11px; place card padding 18px; panel padding 17px 14px.

## 3. Project extensions
Ink-muted #61756a, selected #376c62, background #e2e6de, tab-track #e0e5de. Warm accent #ad7450 for proposal lines. Night: background #0c151c, surface rgba(24,39,43,.94), ink #e1ebe5, muted #acc0b5, edge rgba(216,232,221,.16). Scene earth #dce0c8, forest #6c8861, tree #557958, water #669cba, road #fbf7e8, building #d4d4c5, roof #a7b3a5. Sunset light #ffcf9b; winter branches #8e8c7b. Spring trees #dbbdc0; autumn #ba8651. These are explicit map/material additions, not claimed as exact source values. UI spacing scale 4/8/12/16/20/24/32/40. Small type 11px, body 13/14px, section 15/18px, metric 26px. Focus outline 2px with 3px offset. New motion: camera eased 1000ms, hover 160ms, reduced-motion immediate camera, no particles.

## 4. Layout and responsive
Viewport owns canvas, no document scrolling. Panel body owns scroll; max height viewport minus header/footer. Header x38 y32; explore x32 y173. Environment right32 top32. Bottom controls centered 55px from bottom. Location right32 bottom72. Mobile ≤700: header x16 y16, 30px title; weather below header, season beneath; collapsed explore opened from bottom toolbar; full-width drawer with own scrolling; compact place card lower left; toolbar width calc(100%-24px). Tablet 701–1000: narrow 280px panel, compact weather. No clipped data, buttons minimum 40px (primary mobile 44px).

## 5. Reusable primitives and states
GlassPanel: base/night, scroll header/body. IconButton: resting/hover/pressed/focus/disabled. SegmentedTabs: selected/hover/focus with aria-selected. PlaceRow: index/name/English/arrow, selected wash. SelectField: label/native select/focus. MapLabel: keyboard button + geographic anchor, selected. MetricRows: label/value/unit/source. Disclosure: details/summary. Dialog: close/Escape/focus return. Loading: progress/error/retry. Equivalent state harness at /?showcase=1 exposes UI primitives for responsive checks.

## 6. Accessibility and interaction
Keyboard-operable controls, labeled canvas and non-canvas place selection, visible focus, modal focus behavior, native input/select, tabs expose selection, color plus text for data status. Map pointer gesture handled by OrbitControls; user manipulation interrupts flight. Labels culled for collision. Prefers reduced motion stops tour auto-advance and weather movement. Weather is scenic, time input is survey-based; unknown remains unknown.

## 7. Quality and debt
Target: site-specific visual fidelity and true geospatial data. Entire scene is live Three.js geometry, no screenshot backdrop. Any missing OSM footprint or estimated height disclosed. No claim of complete measured buildings or real-time traffic. Performance to be measured in browser; numerical FPS cannot be assumed. No accepted interaction/accessibility blockers.
