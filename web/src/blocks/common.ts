// What every block shares: the panel with title and caption, notices, status dots.

import type { ComponentChildren } from "preact";
import { html } from "htm/preact";

import type { Result } from "../api.ts";

export function Panel(props: {
  title?: string;
  caption?: string;
  height?: number;
  result?: Result;
  wide?: boolean;
  children?: ComponentChildren;
}) {
  const { title, caption, result } = props;
  return html`<section class=${`panel${props.wide ? " wide" : ""}`}>
    ${title ? html`<h3 class="panel-title">${title}</h3>` : null}
    <div class="panel-body" style=${props.height ? `min-height:${props.height}px` : ""}>
      ${result?.status === "error" ? html`<${Notice} kind="error">${result.error}<//>` : props.children}
    </div>
    ${result?.status === "ready" && result.error
      ? html`<p class="panel-error">Refresh failed: ${result.error}</p>`
      : null}
    ${caption ? html`<p class="caption">${caption}</p>` : null}
  </section>`;
}

export function Notice(props: { kind?: string; children?: ComponentChildren }) {
  return html`<p class=${`notice ${props.kind ?? "info"}`}>${props.children}</p>`;
}

export function Dot(props: { status: string | null | undefined }) {
  return html`<span class=${`dot ${props.status ?? ""}`} title=${props.status ?? ""}></span>`;
}

export function rows(answer: { columns: string[]; rows: unknown[][] } | null): Record<string, any>[] {
  if (!answer) return [];
  return answer.rows.map((r) => Object.fromEntries(answer.columns.map((c, i) => [c, r[i]])));
}

export function matches(row: Record<string, any>, where: Record<string, any> | undefined): boolean {
  if (!where) return true;
  return Object.entries(where).every(([k, v]) => (Array.isArray(v) ? v.includes(row[k]) : row[k] === v));
}
