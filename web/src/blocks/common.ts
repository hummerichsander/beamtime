// What every block shares: an optional title and caption, errors where they happen, notices.

import type { ComponentChildren } from "preact";
import { html } from "htm/preact";

import type { Result } from "../api.ts";

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
