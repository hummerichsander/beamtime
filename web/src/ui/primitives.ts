// Small building blocks: icon buttons, tags, meters, disclosures and anchored popover panels.

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
  return html`<span class=${`tag tone-${props.tone ?? "muted"}`} data-tip=${props.tip}>${props.children}</span>`;
}

export function Meter(props: { fraction: number | null; label: string }) {
  const pct = props.fraction === null ? 0 : Math.round(Math.min(1, Math.max(0, props.fraction)) * 100);
  return html`<span class="meter" role="meter" aria-valuemin="0" aria-valuemax="100" aria-valuenow=${pct}
      aria-label=${props.label} data-tip=${props.label}>
    <span class="meter-fill" style=${`inline-size:${pct}%`}></span>
  </span>`;
}

export function Disclosure(props: { summary: ComponentChildren; open?: boolean; children?: ComponentChildren }) {
  return html`<details class="disclosure" open=${props.open}>
    <summary><${Icon} name="chevron-right" size=${14} class="disclosure-chevron" />${props.summary}</summary>
    <div class="disclosure-body">${props.children}</div>
  </details>`;
}

// a panel that opens from a button, light-dismisses, and sits next to its trigger. Anchor
// positioning isn't available everywhere yet, so the panel is placed when it opens.
export function Popover(props: {
  icon: string;
  label: string;
  title?: string;
  children?: ComponentChildren;
  class?: string;
  onOpen?: () => void;
}) {
  const id = `pop-${useId()}`.replace(/:/g, "");
  const panel = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = panel.current;
    if (!el) return;
    const place = (e: Event) => {
      if ((e as ToggleEvent).newState !== "open") return;
      props.onOpen?.();
      const button = trigger.current?.querySelector("button");
      if (!button) return;
      const r = button.getBoundingClientRect();
      const p = el.getBoundingClientRect();
      const left = Math.min(Math.max(8, r.right - p.width), innerWidth - p.width - 8);
      const below = r.bottom + 6;
      el.style.left = `${left}px`;
      el.style.top = `${below + p.height > innerHeight - 8 ? Math.max(8, r.top - p.height - 6) : below}px`;
    };
    el.addEventListener("toggle", place);
    return () => el.removeEventListener("toggle", place);
  }, []);
  return html`<div class="popover-wrap" ref=${trigger}>
    <${IconButton} icon=${props.icon} label=${props.label} popovertarget=${id} />
    <div id=${id} popover="auto" class=${`panel-popover ${props.class ?? ""}`} ref=${panel}
        aria-label=${props.title ?? props.label}>
      ${props.title ? html`<h4 class="popover-title">${props.title}</h4>` : null}
      ${props.children}
    </div>
  </div>`;
}
