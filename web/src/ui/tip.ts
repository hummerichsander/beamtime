// One tooltip for every element with `data-tip`: on hover after a short delay, on keyboard focus at
// once; it can be hovered itself and Escape dismisses it (WCAG 1.4.13). No dependency: interest
// invokers are not yet in every browser, and anchor positioning neither, so it is placed from script.

const SHOW_MS = 350;
const HIDE_MS = 120;

let el: HTMLDivElement | null = null;
let source: Element | null = null;
let showTimer: ReturnType<typeof setTimeout> | undefined;
let hideTimer: ReturnType<typeof setTimeout> | undefined;

export function installTips(): void {
  el = document.createElement("div");
  el.className = "bt-hint small";
  el.setAttribute("popover", "manual");
  el.id = "bt-hint";
  document.body.append(el);
  el.addEventListener("pointerenter", () => clearTimeout(hideTimer));
  el.addEventListener("pointerleave", () => scheduleHide());
  document.addEventListener("pointerover", (e) => {
    const target = (e.target as Element).closest?.("[data-tip]");
    if (target && target !== source) {
      clearTimeout(showTimer);
      showTimer = setTimeout(() => show(target), source ? 0 : SHOW_MS);
    }
  });
  document.addEventListener("pointerout", (e) => {
    const target = (e.target as Element).closest?.("[data-tip]");
    if (!target) return;
    clearTimeout(showTimer);
    if (target === source) scheduleHide();
  });
  document.addEventListener("focusin", (e) => {
    const target = (e.target as Element).closest?.("[data-tip]");
    if (target && (e.target as Element).matches(":focus-visible")) show(target);
  });
  document.addEventListener("focusout", () => hide());
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && source) hide();
  });
  document.addEventListener("pointerdown", () => hide(), true);
}

function show(target: Element): void {
  const text = target.getAttribute("data-tip");
  if (!el || !text || !target.isConnected) return;
  clearTimeout(hideTimer);
  source = target;
  el.textContent = text;
  if (!el.matches(":popover-open")) el.showPopover();
  const r = target.getBoundingClientRect();
  const t = el.getBoundingClientRect();
  const gap = 6;
  const above = r.top - t.height - gap;
  const top = above >= 4 ? above : r.bottom + gap;
  const left = Math.min(Math.max(4, r.left + r.width / 2 - t.width / 2), innerWidth - t.width - 4);
  el.style.top = `${top}px`;
  el.style.left = `${left}px`;
}

function scheduleHide(): void {
  clearTimeout(hideTimer);
  hideTimer = setTimeout(hide, HIDE_MS);
}

function hide(): void {
  clearTimeout(showTimer);
  clearTimeout(hideTimer);
  source = null;
  if (el?.matches(":popover-open")) el.hidePopover();
}
