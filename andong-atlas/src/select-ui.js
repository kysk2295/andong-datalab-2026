import "./select-ui.css";
// Preserve native values/events for the existing forms, while giving every menu
// the same visual, search and keyboard behaviour (including menus in dialogs).
export function initSelectUI() {
  const fields = new Map();
  let active = null,
    serial = 0,
    scheduled = false;
  function close(restore = false) {
    if (!active) return;
    const field = active;
    active = null;
    field.popup.remove();
    field.popup = null;
    field.trigger.setAttribute("aria-expanded", "false");
    field.trigger.removeAttribute("aria-activedescendant");
    if (restore && field.trigger.isConnected) field.trigger.focus({ preventScroll: true });
  }
  function choose(field, option) {
    if (option.disabled) return;
    field.select.value = option.value;
    close(true);
    field.select.dispatchEvent(new Event("input", { bubbles: true }));
    field.select.dispatchEvent(new Event("change", { bubbles: true }));
    sync(field);
  }
  function position(field) {
    if (!field.popup) return;
    const r = field.trigger.getBoundingClientRect(),
      width = Math.min(Math.max(r.width, 250), innerWidth - 24);
    const below = innerHeight - r.bottom - 12,
      above = r.top - 12,
      down = below >= Math.min(320, above);
    const height = Math.max(100, Math.min(380, down ? below : above));
    Object.assign(field.popup.style, {
      width: width + "px",
      maxHeight: height + "px",
      left: Math.max(12, Math.min(r.left, innerWidth - width - 12)) + "px",
    });
    const actual = field.popup.getBoundingClientRect().height;
    field.popup.style.top =
      (down ? r.bottom + 6 : Math.max(12, r.top - actual - 6)) + "px";
    field.popup.dataset.direction = down ? "down" : "up";
  }
  function highlight(field, index, scroll = true) {
    if (!field.rows?.length) return;
    field.index = Math.max(0, Math.min(field.rows.length - 1, index));
    field.rows.forEach((row, i) =>
      row.classList.toggle("is-highlighted", i === field.index),
    );
    const row = field.rows[field.index];
    field.trigger.setAttribute("aria-activedescendant", row.id);
    field.input?.setAttribute("aria-activedescendant", row.id);
    if (scroll) row.scrollIntoView({ block: "nearest" });
  }
  function renderOptions(field, query = "") {
    field.list.replaceChildren();
    field.rows = [];
    const options = [...field.select.options].filter((o) =>
      o.textContent
        .toLocaleLowerCase()
        .includes(query.trim().toLocaleLowerCase()),
    );
    for (const option of options) {
      const row = document.createElement("button");
      row.type = "button";
      row.role = "option";
      row.tabIndex = -1;
      row.id = `${field.list.id}-option-${field.rows.length}`;
      row.className = "atlas-select-option";
      row.textContent = option.textContent;
      row.disabled = option.disabled;
      row.setAttribute("aria-selected", String(option.selected));
      row.onclick = () => choose(field, option);
      row.onpointermove = () =>
        highlight(field, field.rows.indexOf(row), false);
      field.list.append(row);
      field.rows.push(row);
    }
    if (!field.rows.length) {
      const empty = document.createElement("p");
      empty.className = "atlas-select-empty";
      empty.textContent = "검색 결과가 없습니다.";
      field.list.append(empty);
    }
    const selected = field.rows.findIndex(
      (r) => r.getAttribute("aria-selected") === "true",
    );
    highlight(field, Math.max(0, selected), false);
    field.count.textContent = `${options.length}개 항목`;
    position(field);
  }
  function key(event, field) {
    if (event.key === "Escape" && active === field) {
      event.preventDefault();
      event.stopPropagation();
      close(true);
      return;
    }
    if (event.key === "Tab" && active === field) {
      if (event.target === field.input) field.trigger.focus();
      close();
      return;
    }
    if (["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
      event.preventDefault();
      event.stopPropagation();
      if (active !== field) {
        open(field);
        return;
      }
      const delta = event.key === "ArrowDown" ? 1 : -1;
      let next =
        event.key === "Home"
          ? 0
          : event.key === "End"
            ? field.rows.length - 1
            : field.index + delta;
      while (next >= 0 && next < field.rows.length && field.rows[next].disabled)
        next += delta;
      highlight(field, next);
      return;
    }
    if (
      (event.key === "Enter" || event.key === " ") &&
      active === field &&
      event.target !== field.input
    ) {
      event.preventDefault();
      event.stopPropagation();
      field.rows[field.index]?.click();
    }
    if (
      event.key === "Enter" &&
      active === field &&
      event.target === field.input
    ) {
      event.preventDefault();
      field.rows[field.index]?.click();
    }
  }
  function open(field) {
    if (field.select.disabled) return;
    close();
    sync(field);
    active = field;
    const popup = document.createElement("div");
    popup.className = "atlas-select-popup";
    // A top-layer popover stays anchored to the viewport, even inside a
    // scrolling dialog whose backdrop filter creates a containing block.
    if (typeof popup.showPopover === "function") popup.popover = "manual";
    field.popup = popup;
    const head = document.createElement("div");
    head.className = "atlas-select-head";
    const label = document.createElement("span");
    label.textContent = field.label;
    const count = document.createElement("span");
    count.className = "atlas-select-count";
    field.count = count;
    head.append(label, count);
    popup.append(head);
    if (field.select.options.length > 7) {
      const input = document.createElement("input");
      input.type = "search";
      input.placeholder = "이름으로 검색";
      input.className = "atlas-select-search";
      input.setAttribute("aria-label", `${field.label} 검색`);
      input.setAttribute("aria-controls", field.listId);
      input.oninput = () => renderOptions(field, input.value);
      input.onkeydown = (e) => key(e, field);
      field.input = input;
      popup.append(input);
    } else field.input = null;
    const list = document.createElement("div");
    list.id = field.listId;
    list.role = "listbox";
    list.setAttribute("aria-label", field.label);
    list.className = "atlas-select-options";
    field.list = list;
    popup.append(list);
    (field.select.closest("dialog[open]") || document.body).append(popup);
    if (popup.popover) popup.showPopover();
    field.trigger.setAttribute("aria-expanded", "true");
    renderOptions(field);
    if (field.input) field.input.focus({ preventScroll: true });
  }
  function sync(field) {
    const text = field.select.selectedOptions[0]?.textContent || "선택하세요";
    if (field.value.textContent !== text) field.value.textContent = text;
    if (field.trigger.disabled !== field.select.disabled)
      field.trigger.disabled = field.select.disabled;
    field.trigger.setAttribute("aria-disabled", String(field.select.disabled));
    const signature = [...field.select.options]
      .map((o) => [o.value, o.textContent, o.disabled].join("|"))
      .join("\n");
    if (active === field && field.signature !== signature)
      renderOptions(field, field.input?.value || "");
    field.signature = signature;
  }
  function enhance() {
    scheduled = false;
    for (const [select, field] of fields)
      if (!select.isConnected) {
        if (active === field) close();
        field.trigger.remove();
        fields.delete(select);
      }
    document.querySelectorAll("select:not([multiple])").forEach((select) => {
      let field = fields.get(select);
      if (!field) {
        const labelNode = select.labels?.[0]?.cloneNode(true);
        labelNode
          ?.querySelectorAll("select,button,input")
          .forEach((n) => n.remove());
        const label =
          select.getAttribute("aria-label") ||
          labelNode?.textContent.trim() ||
          "항목 선택";
        const trigger = document.createElement("button");
        trigger.type = "button";
        trigger.className = "atlas-select-trigger";
        trigger.role = "combobox";
        trigger.id = `${select.id || "select-" + ++serial}-trigger`;
        trigger.setAttribute("aria-label", label);
        trigger.setAttribute("aria-haspopup", "listbox");
        trigger.setAttribute("aria-expanded", "false");
        const value = document.createElement("span");
        value.className = "atlas-select-value";
        const chevron = document.createElement("span");
        chevron.className = "atlas-select-chevron";
        chevron.setAttribute("aria-hidden", "true");
        trigger.append(value, chevron);
        field = {
          select,
          trigger,
          value,
          label,
          listId: trigger.id + "-list",
          signature: "",
        };
        trigger.setAttribute("aria-controls", field.listId);
        fields.set(select, field);
        select.dataset.atlasSelect = "true";
        select.hidden = true;
        select.tabIndex = -1;
        select.setAttribute("aria-hidden", "true");
        select.insertAdjacentElement("afterend", trigger);
        trigger.onclick = (event) => {
          event.preventDefault();
          active === field ? close() : open(field);
        };
        trigger.onkeydown = (e) => key(e, field);
        select.addEventListener("change", () => sync(field));
      }
      sync(field);
    });
    if (active && !active.trigger.getClientRects().length) close();
  }
  const observer = new MutationObserver((records) => {
    // Changes made by the custom menus need no further native-select discovery.
    if (
      records.every((r) =>
        r.target.closest?.(".atlas-select-popup,.atlas-select-trigger"),
      )
    )
      return;
    if (!scheduled) {
      scheduled = true;
      queueMicrotask(enhance);
    }
  });
  observer.observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true,
    attributes: true,
    attributeFilter: ["disabled", "selected", "label", "hidden"],
  });
  document.addEventListener(
    "pointerdown",
    (e) => {
      if (
        active &&
        !active.popup.contains(e.target) &&
        !active.trigger.contains(e.target)
      )
        close();
    },
    true,
  );
  document.addEventListener(
    "scroll",
    (e) => {
      if (active && !active.popup.contains(e.target)) close();
    },
    true,
  );
  document.addEventListener("close", () => close(), true);
  document.addEventListener("reset", () => queueMicrotask(enhance));
  window.addEventListener("resize", () => close());
  enhance();
  return { sync: enhance };
}
