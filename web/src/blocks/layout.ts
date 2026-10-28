// Layout blocks: section, row and grid.

import { html } from "htm/preact";
import { useContext, useState } from "preact/hooks";

import { ViewCtx, type Node } from "../bt/index.ts";
import { setView, update, usePrefs, type ChartPrefs } from "../bt/prefs.ts";
import { Icon } from "../ui/icons.ts";
import { Popover } from "../ui/primitives.ts";
import { Block } from "./index.ts";
import { Controls } from "./line.ts";

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
  const view = useContext(ViewCtx);
  const prefs = usePrefs(view.path);
  const min = node.props.min_width ?? 320;
  const cols = node.props.columns;
  const style = cols
    ? `grid-template-columns: repeat(${cols}, minmax(0, 1fr))`
    : `grid-template-columns: repeat(auto-fill, minmax(min(${min}px, 100%), 1fr))`;
  const shown = (node.children ?? []).map((c) => c.props.y);
  // charts a viewer added copy the template call of the grid with their own metric.
  const added: Node[] = node.props.addable
    ? prefs.added
        .filter((m) => !shown.includes(m))
        .map((m) => ({
          block: "line",
          id: `added-${m}`,
          props: { y: m, added: true },
          data: { main: { ...node.props.template, params: { ...node.props.template.params, y: [m] } } },
        }))
    : [];
  return html`${node.props.addable
      ? html`<${ViewBar} path=${view.path} shown=${[...shown, ...prefs.added]} metrics=${node.props.metrics ?? []}
          varying=${node.props.varying ?? []} />`
      : null}
    <div class="grid" style=${style}>
      ${[...(node.children ?? []), ...added].map((c) => html`<${Block} key=${c.id} node=${c} />`)}
    </div>`;
}

// options for every chart of the view, hidden runs, and adding a chart.
function ViewBar(props: { path: string; shown: string[]; metrics: string[]; varying: string[] }) {
  const prefs = usePrefs(props.path);
  const varying = props.varying;
  const more = props.metrics.filter((m) => !props.shown.includes(m));
  const add = (m: string) => update(props.path, (p) => ({ added: [...p.added, m] }));
  return html`<div class="view-bar" role="toolbar" aria-label="All charts">
    <${Controls} prefs=${prefs.view} varying=${varying} compact set=${(v: ChartPrefs) => setView(props.path, v)} />
    ${prefs.hidden.length
      ? html`<button type="button" class="link small" onClick=${() => update(props.path, () => ({ hidden: [] }))}>
          <${Icon} name="eye" size=${14} /> show ${prefs.hidden.length} hidden</button>`
      : null}
    ${Object.keys(prefs.view).length || Object.keys(prefs.charts).length
      ? html`<button type="button" class="link small" onClick=${() => update(props.path, () => ({ view: {}, charts: {} }))}>reset</button>`
      : null}
    ${more.length
      ? html`<${Popover} icon="plus" label="Add a chart" title="Add a chart">
          <div class="menu-list">${more.map((m) => html`<button type="button" onClick=${() => add(m)}>${m}</button>`)}</div>
        <//>`
      : null}
  </div>`;
}
