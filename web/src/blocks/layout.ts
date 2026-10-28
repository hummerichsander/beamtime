// Layout blocks: section, row and grid.

import { html } from "htm/preact";
import { useState } from "preact/hooks";

import type { Node } from "../bt/index.ts";
import { Icon } from "../ui/icons.ts";
import { Block } from "./index.ts";

export function Section({ node }: { node: Node }) {
  const [open, setOpen] = useState(node.props.open !== false);
  const children = html`${(node.children ?? []).map((c) => html`<${Block} key=${c.id} node=${c} />`)}`;
  if (!node.props.title) return html`<div class="stack">${children}</div>`;
  return html`<section class="section">
    <button type="button" class="section-title" aria-expanded=${open} onClick=${() => setOpen(!open)}>
      <${Icon} name=${open ? "chevron-down" : "chevron-right"} size=${16} />${node.props.title}
    </button>
    ${open ? html`<div class="stack">${children}</div>` : null}
  </section>`;
}

export function Row({ node }: { node: Node }) {
  return html`<div class="row">
    ${(node.children ?? []).map((c) => html`<${Block} key=${c.id} node=${c} />`)}
  </div>`;
}

export function Grid({ node }: { node: Node }) {
  const min = node.props.min_width ?? 320;
  const cols = node.props.columns;
  const style = cols
    ? `grid-template-columns: repeat(${cols}, minmax(0, 1fr))`
    : `grid-template-columns: repeat(auto-fill, minmax(min(${min}px, 100%), 1fr))`;
  return html`<div class="grid" style=${style}>
    ${(node.children ?? []).map((c) => html`<${Block} key=${c.id} node=${c} />`)}
  </div>`;
}
