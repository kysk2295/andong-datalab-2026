import * as THREE from 'three';
import { mapPointStyle, declutterMapPoints } from './map-point-model.js';

export class MapPoints {
  constructor(atlas, onSelect) {
    this.atlas = atlas;
    this.onSelect = onSelect;
    this.records = [];
    this.element = document.createElement('div');
    this.element.className = 'gis-point-layer';
    this.element.setAttribute('role', 'group');
    this.element.setAttribute('aria-label', '지도 위 식당·체험·혜택 지점');
    this.element.hidden = true;
    document.body.append(this.element);
    this.projected = new THREE.Vector3();
  }
  setPlaces(places, additions, selected) {
    const focused = this.element.contains(document.activeElement) ? document.activeElement.dataset.placeId : null;
    const added = new Set(additions.map(p => p.id));
    this.records = places.map(place => {
      const style = mapPointStyle(place, { selected:place.id === selected, added:added.has(place.id) });
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'gis-point';
      button.dataset.placeId = place.id;
      button.dataset.symbol = style.type;
      button.dataset.proposed = String(Boolean(place.proposed));
      button.setAttribute('aria-label', `${place.name} · ${style.label} 정보`);
      button.setAttribute('aria-pressed', String(style.selected));
      const symbol = document.createElement('span');
      symbol.className = 'gis-symbol';
      symbol.setAttribute('aria-hidden','true');
      const label = document.createElement('span');
      label.className = 'gis-point-name';
      label.textContent = `${place.name} · ${style.label}`;
      label.setAttribute('aria-hidden','true');
      button.append(symbol,label);
      button.onclick = () => this.onSelect(place);
      return { place, style, button };
    });
    this.element.replaceChildren(...this.records.map(r => r.button));
    this.update(!this.element.hidden);
    if (focused) this.records.find(r => r.place.id === focused)?.button.focus({preventScroll:true});
  }
  update(visible) {
    this.element.hidden = !visible;
    if (!visible) return;
    const a = this.atlas, canvas = a.renderer.domElement.getBoundingClientRect();
    const selectors = '.atlas-masthead, #explore, #atlas-route, .location, .toolbar, .map-scope, #atlas-environment, #journey-place, #journey-player, #detail-status, .map-label, #heritage-sheet, #heritage-player, #scenario-map-summary, .tourism-info';
    const obstacles = [...document.querySelectorAll(selectors)].flatMap(el => {
      if (!el.checkVisibility()) return [];
      const r = el.getBoundingClientRect();
      return r.width && r.height ? [{left:r.left, right:r.right, top:r.top, bottom:r.bottom}] : [];
    });
    const projected = this.records.map(record => {
      this.projected.copy(a.point(record.place.coordinates, .004)).applyMatrix4(a.world.matrixWorld).project(a.camera);
      return { ...record, x:canvas.left + (this.projected.x + 1) * canvas.width / 2,
        y:canvas.top + (1 - this.projected.y) * canvas.height / 2, z:this.projected.z,
        priority: record.button === document.activeElement ? 200 : record.style.priority };
    });
    const shown = declutterMapPoints(projected, {width:innerWidth, height:innerHeight, obstacles});
    const ids = new Set(shown.map(r => r.place.id));
    for (const r of projected) {
      r.button.hidden = !ids.has(r.place.id);
      if (r.button.hidden) continue;
      r.button.style.transform = `translate(${r.x - 12}px, ${r.y - 12}px)`;
      r.button.dataset.labelSide = r.x > innerWidth - 240 ? 'left' : 'right';
    }
    this.element.dataset.visibleCount = String(shown.length);
    this.element.dataset.totalCount = String(projected.length);
  }
}
