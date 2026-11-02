// What every block shares: an optional title and caption, errors where they happen, notices.

import type { ComponentChildren } from "preact";
import { html } from "htm/preact";
import { createContext } from "preact";
import { useContext, useState } from "preact/hooks";

import type { Result } from "../api.ts";
import { recording } from "../router.ts";
import { stored, store } from "../state.ts";
import { Icon } from "../ui/icons.ts";

// the label of the Section around a block: a title that only repeats it isn't shown again.
export const LabelCtx = createContext<string | null>(null);

function repeats(label: string | null, title: string | undefined): boolean {
  return !!title && label === title.toLowerCase();
}

export function Panel(props: {
  title?: string;
  count?: string;
  caption?: string;
  // a table's caption, numbered "Table n." down the page.
  numbered?: boolean;
  result?: Result;
  class?: string;
  children?: ComponentChildren;
}) {
  const { title, caption, result } = props;
  const label = useContext(LabelCtx);
  return html`<section class=${`block ${props.class ?? ""}`}>
    ${title && !repeats(label, title)
      ? html`<h3 class="block-title heading">${title}${props.count ? html`<span class="count small">${props.count}</span>` : null}</h3>`
      : null}
    ${result?.status === "error" ? html`<${Notice} kind="error">${result.error}<//>` : props.children}
    ${result?.status === "ready" && result.error ? html`<p class="block-error small">Refresh failed: ${result.error}</p>` : null}
    ${caption
      ? props.numbered
        ? html`<p class="caption table-caption"><b></b> ${caption}</p>`
        : html`<p class="caption">${caption}</p>`
      : null}
  </section>`;
}

export function Notice(props: { kind?: string; children?: ComponentChildren }) {
  const kind = props.kind ?? "info";
  const mark = kind === "warning" ? ["triangle-alert", "tone-warn"] : kind === "error" ? ["circle-x", "tone-bad"] : null;
  return html`<p class=${`notice body ${kind}`}>
    ${mark ? html`<${Icon} name=${mark[0]} size=${15} class=${mark[1]} />` : null}<span>${props.children}</span>
  </p>`;
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
  action?: ComponentChildren;
  children?: ComponentChildren;
}) {
  const key = `section.${props.id}`;
  const shown = repeats(useContext(LabelCtx), props.title) ? null : props.title;
  const [open, setOpen] = useState<boolean>(() => recording || stored(key, props.open ?? true));
  const toggle = () => {
    store(key, !open);
    setOpen(!open);
  };
  return html`<section class=${`block collapsible ${props.class ?? ""}`}>
    <h3 class="block-title heading">
      <button type="button" class="collapse-toggle" aria-expanded=${open} aria-label=${shown ? undefined : `${open ? "Close" : "Open"} ${props.title}`}
          data-tip=${shown ? undefined : `${open ? "Close" : "Open"} ${props.title}`} onClick=${toggle}>
        <${Icon} name=${open ? "chevron-down" : "chevron-right"} size=${16} />${shown}
        ${props.count ? html`<span class="count small">${props.count}</span>` : null}
      </button>
      ${props.action ? html`<span class="block-action body">${props.action}</span>` : null}
    </h3>
    ${open ? (props.result?.status === "error" ? html`<${Notice} kind="error">${props.result.error}<//>` : props.children) : null}
  </section>`;
}
