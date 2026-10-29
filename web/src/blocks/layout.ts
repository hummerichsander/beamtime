// Layout blocks: section, row, grid and tabs.

import { html } from "htm/preact";
import { useContext, useState } from "preact/hooks";

import { useCall } from "../api.ts";
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
  return html`${node.props.addable
      ? html`<${ViewBar} path=${view.path} shown=${[...shown, ...prefs.added]} metrics=${node.props.metrics ?? null}
          varying=${node.props.varying ?? null} />`
      : null}
    <div class="grid" style=${style}>
      ${[...(node.children ?? []), ...added].map((c) => html`<${Block} key=${c.id} node=${c} />`)}
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

// options for every chart of the view, hidden runs, and adding a chart.
function ViewBar(props: { path: string; shown: string[]; metrics: string[] | null; varying: string[] | null }) {
  const prefs = usePrefs(props.path);
  // an authored view doesn't list them; they are asked for once.
  const keys = useCall(props.metrics ? null : { method: "keys", params: { from: props.path }, scope: props.path }).data;
  const metrics: string[] = props.metrics ?? keys?.metrics?.rows.map((r: unknown[]) => r[0]) ?? [];
  const varying: string[] =
    props.varying ??
    (keys?.config?.rows ?? []).filter((r: any[]) => Array.isArray(r[2]) && r[2].length > 1 && r[0] !== "config.seed").map((r: any[]) => r[0]);
  const more = metrics.filter((m) => !props.shown.includes(m));
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
