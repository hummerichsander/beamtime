// Small building blocks: buttons, icon buttons, fields, tags, disclosures and anchored popover panels.

import type { ComponentChildren } from "preact";
import { html } from "htm/preact";
import { useEffect, useId, useRef } from "preact/hooks";

import { Icon } from "./icons.ts";

export function IconButton(props: {
  icon: string;
  label: string;
  onClick?: (e: MouseEvent) => void;
  pressed?: boolean;
  class?: string;
  popovertarget?: string;
}) {
  return html`<button type="button" class=${`icon-button ${props.class ?? ""}`} aria-label=${props.label}
      data-tip=${props.label} aria-pressed=${props.pressed} onClick=${props.onClick}
      popovertarget=${props.popovertarget}>
    <${Icon} name=${props.icon} size=${16} />
  </button>`;
}

export function Tag(props: { tone?: string; tip?: string; children?: ComponentChildren }) {
  return html`<span class=${`tag small tone-${props.tone ?? "muted"}`} data-tip=${props.tip}>${props.children}</span>`;
}

// one row of the page: a short label in the margin and the content, between hairlines.
export function Section(props: { label?: string; class?: string; children?: ComponentChildren }) {
  return html`<section class=${`section ${props.class ?? ""}`}>
    <div class="section-label code">${props.label}</div>
    <div class="section-body">${props.children}</div>
  </section>`;
}

// an action with an icon and a short label, no fill: accent text; danger is bad, quiet is muted.
export function Button(props: {
  icon: string;
  kind?: "danger" | "quiet";
  type?: "button" | "submit";
  disabled?: boolean;
  onClick?: (e: MouseEvent) => void;
  class?: string;
  tip?: string;
  children?: ComponentChildren;
}) {
  const cls = ["button body", props.kind, props.class].filter(Boolean).join(" ");
  return html`<button type=${props.type ?? "button"} class=${cls} disabled=${props.disabled} onClick=${props.onClick} data-tip=${props.tip}>
    <${Icon} name=${props.icon} size=${16} />${props.children}
  </button>`;
}

// a label in small above an input; an error or a hint below. The child is the control itself.
export function Field(props: { label: string; inline?: boolean; error?: string | null; icon?: string; class?: string; children?: ComponentChildren }) {
  return html`<label class=${`field small${props.inline ? " inline" : ""} ${props.class ?? ""}`}>
    <span class="field-label">${props.label}</span>
    <span class="input body">${props.icon ? html`<${Icon} name=${props.icon} size=${15} />` : null}${props.children}</span>
    ${props.error ? html`<span class="field-hint error">${props.error}</span>` : null}
  </label>`;
}

export function Disclosure(props: {
  summary: ComponentChildren;
  open?: boolean;
  onToggle?: (open: boolean) => void;
  children?: ComponentChildren;
}) {
  return html`<details class="disclosure" open=${props.open} onToggle=${(e: Event) => props.onToggle?.((e.currentTarget as HTMLDetailsElement).open)}>
    <summary><${Icon} name="chevron-right" size=${14} class="disclosure-chevron" />${props.summary}</summary>
    <div class="disclosure-body">${props.children}</div>
  </details>`;
}

// a panel that opens from a button, light-dismisses, and sits next to its trigger. Anchor
// positioning isn't available everywhere yet, so the panel is placed when it opens. With `beside`
// (a selector of an ancestor) it sits to the right of that element, else to its left, else against
// the viewport's right edge, so what it changes stays visible; it follows scrolling and resizing.
export function Popover(props: {
  icon: string;
  label: string;
  title?: string;
  children?: ComponentChildren;
  class?: string;
  onOpen?: () => void;
  beside?: string;
}) {
  const id = `pop-${useId()}`.replace(/:/g, "");
  const panel = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = panel.current;
    if (!el) return;
    const place = () => {
      const button = trigger.current?.querySelector("button");
      if (!button) return;
      const r = button.getBoundingClientRect();
      const p = el.getBoundingClientRect();
      const around = props.beside ? trigger.current?.closest(props.beside)?.getBoundingClientRect() : undefined;
      let left: number;
      let top: number;
      if (around) {
        const docked = Math.max(8, innerWidth - p.width - 8);
        if (around.right + 8 + p.width <= innerWidth - 8) left = around.right + 8;
        else left = around.left - 8 - p.width >= 8 ? around.left - 8 - p.width : docked;
        top = around.top;
      } else {
        left = Math.min(Math.max(8, r.right - p.width), innerWidth - p.width - 8);
        top = r.bottom + 6 + p.height > innerHeight - 8 ? r.top - p.height - 6 : r.bottom + 6;
      }
      el.style.left = `${left}px`;
      el.style.top = `${Math.max(8, Math.min(top, innerHeight - p.height - 8))}px`;
    };
    const watch = new ResizeObserver(place);
    const onToggle = (e: Event) => {
      if ((e as ToggleEvent).newState === "open") {
        props.onOpen?.();
        place();
        watch.observe(el);
        addEventListener("scroll", place, true);
        addEventListener("resize", place);
      } else {
        watch.disconnect();
        removeEventListener("scroll", place, true);
        removeEventListener("resize", place);
      }
    };
    el.addEventListener("toggle", onToggle);
    return () => {
      el.removeEventListener("toggle", onToggle);
      watch.disconnect();
      removeEventListener("scroll", place, true);
      removeEventListener("resize", place);
    };
  }, []);
  return html`<div class="popover-wrap" ref=${trigger}>
    <${IconButton} icon=${props.icon} label=${props.label} popovertarget=${id} />
    <div id=${id} popover="auto" class=${`panel-popover ${props.class ?? ""}`} ref=${panel}
        aria-label=${props.title ?? props.label}>
      ${props.title ? html`<h4 class="popover-title small">${props.title}</h4>` : null}
      ${props.children}
    </div>
  </div>`;
}
