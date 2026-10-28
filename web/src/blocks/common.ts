// What every block shares: an optional title and caption, errors where they happen, notices.

import type { ComponentChildren } from "preact";
import { html } from "htm/preact";
import { useState } from "preact/hooks";

import type { Result } from "../api.ts";
import { stored, store } from "../state.ts";
import { Icon } from "../ui/icons.ts";

export function Panel(props: {
  title?: string;
  count?: string;
  caption?: string;
  result?: Result;
  class?: string;
  children?: ComponentChildren;
}) {
  const { title, caption, result } = props;
  return html`<section class=${`block ${props.class ?? ""}`}>
    ${title
      ? html`<h3 class="block-title">${title}${props.count ? html`<span class="count">${props.count}</span>` : null}</h3>`
      : null}
    ${result?.status === "error" ? html`<${Notice} kind="error">${result.error}<//>` : props.children}
    ${result?.status === "ready" && result.error ? html`<p class="block-error">Refresh failed: ${result.error}</p>` : null}
    ${caption ? html`<p class="caption">${caption}</p>` : null}
  </section>`;
}

export function Notice(props: { kind?: string; children?: ComponentChildren }) {
  return html`<p class=${`notice ${props.kind ?? "info"}`}>${props.children}</p>`;
}

export function rows(answer: { columns: string[]; rows: unknown[][] } | null): Record<string, any>[] {
  if (!answer) return [];
  return answer.rows.map((r) => Object.fromEntries(answer.columns.map((c, i) => [c, r[i]])));
}

export function matches(row: Record<string, any>, where: Record<string, any> | undefined): boolean {
  if (!where) return true;
  return Object.entries(where).every(([k, v]) => (Array.isArray(v) ? v.includes(row[k]) : row[k] === v));
}

// a titled section that opens and closes; each viewer's choice is remembered per section id.
export function Collapsible(props: {
  id: string;
  title: string;
  count?: string;
  open?: boolean;
  result?: Result;
  class?: string;
  children?: ComponentChildren;
}) {
  const key = `section.${props.id}`;
  const [open, setOpen] = useState<boolean>(() => stored(key, props.open ?? true));
  const toggle = () => {
    store(key, !open);
    setOpen(!open);
  };
  return html`<section class=${`block collapsible ${props.class ?? ""}`}>
    <h3 class="block-title">
      <button type="button" class="collapse-toggle" aria-expanded=${open} onClick=${toggle}>
        <${Icon} name=${open ? "chevron-down" : "chevron-right"} size=${16} />${props.title}
        ${props.count ? html`<span class="count">${props.count}</span>` : null}
      </button>
    </h3>
    ${open ? (props.result?.status === "error" ? html`<${Notice} kind="error">${props.result.error}<//>` : props.children) : null}
  </section>`;
}
