// Layout blocks: section, row, grid and tabs.

import { html } from "htm/preact";
import { useContext, useState } from "preact/hooks";

import { useCall } from "../api.ts";
import { ViewCtx, type Node } from "../bt/index.ts";
import { update, usePrefs } from "../bt/prefs.ts";
import { Icon } from "../ui/icons.ts";
import { MultiSelect } from "../ui/multiselect.ts";
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
  const view = useContext(ViewCtx);
  const prefs = usePrefs(view.path);
  const min = node.props.min_width ?? 320;
  const cols = node.props.columns;
  const style = cols
    ? `grid-template-columns: repeat(${cols}, minmax(0, 1fr))`
    : `grid-template-columns: repeat(auto-fill, minmax(min(${min}px, 100%), 1fr))`;
  const shown = (node.children ?? []).flatMap((c) => c.props.y ?? []);
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
  return html`<div class="grid" style=${style}>
    ${[...(node.children ?? []), ...added].map((c) => html`<${Block} key=${c.id} node=${c} />`)}
    ${node.props.addable ? html`<${AddChart} path=${view.path} shown=${[...shown, ...prefs.added]} />` : null}
  </div>`;
}

// the last cell of a grid of curves: pick a metric to add a chart for it.
function AddChart(props: { path: string; shown: string[] }) {
  const keys = useCall({ method: "keys", params: { from: props.path }, scope: props.path }).data;
  const more: string[] = (keys?.metrics?.rows ?? []).map((r: unknown[]) => r[0] as string).filter((m: string) => !props.shown.includes(m));
  if (keys && !more.length) return null;
  return html`<div class="add-chart">
    <span class="add-chart-label"><${Icon} name="plus" size=${16} /> Add a chart</span>
    <${MultiSelect} single options=${more} value=${[]} label="Metric for a new chart" placeholder="Search metrics"
      onChange=${([m]: string[]) => update(props.path, (p) => ({ added: [...p.added, m] }))} />
  </div>`;
}

// sections as tabs; only the open tab renders (and fetches). The open tab is in the URL: #tab=<id>.
export function Tabs({ node }: { node: Node }) {
  const kids = node.children ?? [];
  const fromUrl = () => new URLSearchParams(location.hash.slice(1)).get("tab");
  const [open, setOpen] = useState(() => kids.find((k) => k.id === fromUrl())?.id ?? kids[0]?.id);
  const choose = (id: string) => {
    history.replaceState(history.state, "", `${location.pathname}${location.search}#tab=${encodeURIComponent(id)}`);
    setOpen(id);
  };
  const active = kids.find((k) => k.id === open) ?? kids[0];
  return html`<div class="tabs">
    <div class="tab-list" role="tablist" aria-label=${node.props.title ?? "Tabs"}>
      ${kids.map((k) => html`<button type="button" role="tab" id=${`tab-${k.id}`} aria-selected=${k.id === active?.id}
          aria-controls=${`panel-${k.id}`} onClick=${() => choose(k.id)}>${k.props.title ?? k.id}</button>`)}
    </div>
    ${active
      ? html`<div class="stack" role="tabpanel" id=${`panel-${active.id}`} aria-labelledby=${`tab-${active.id}`}>
          ${(active.children ?? []).map((c) => html`<${Block} key=${c.id} node=${c} />`)}
        </div>`
      : null}
  </div>`;
}
