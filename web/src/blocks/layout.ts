// Layout blocks: section, row, grid and tabs.

import { html } from "htm/preact";
import { useContext, useState } from "preact/hooks";

import { useCall } from "../api.ts";
import { ViewCtx, type Node } from "../bt/index.ts";
import { ordered, setOrder, setSpan, update, usePrefs, type Span } from "../bt/prefs.ts";
import { recording } from "../router.ts";
import { EXPORTED } from "../snapshot.ts";
import { Icon } from "../ui/icons.ts";
import { MultiSelect } from "../ui/multiselect.ts";
import { LabelCtx } from "./common.ts";
import { Block } from "./index.ts";

export function Section({ node }: { node: Node }) {
  const [open, setOpen] = useState(recording || node.props.open !== false);
  const children = html`${(node.children ?? []).map((c) => html`<${Block} key=${c.id} node=${c} />`)}`;
  const label = useContext(LabelCtx);
  if (!node.props.title) return html`<div class="stack">${children}</div>`;
  const repeated = label === node.props.title.toLowerCase();
  return html`<div class="view-section">
    <button type="button" class="view-section-title heading" aria-expanded=${open} aria-label=${repeated ? `${open ? "Close" : "Open"} ${node.props.title}` : undefined}
        onClick=${() => setOpen(!open)}>
      <${Icon} name=${open ? "chevron-down" : "chevron-right"} size=${16} />${repeated ? null : node.props.title}
    </button>
    ${open ? html`<div class="stack">${children}</div>` : null}
  </div>`;
}

export function Row({ node }: { node: Node }) {
  const stats = (node.children ?? []).every((c) => c.block === "stat");
  return html`<div class=${stats ? "stats" : "row"}>
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
  const cells = ordered([...(node.children ?? []), ...added], prefs.order[node.id]);
  const move = (dragged: string, before: string) => {
    const ids = cells.map((c) => c.id).filter((id) => id !== dragged);
    ids.splice(ids.indexOf(before), 0, dragged);
    setOrder(view.path, node.id, ids);
  };
  return html`<div class="grid" style=${style}>
    ${cells.map((c) => html`<${Cell} key=${c.id} node=${c} path=${view.path} span=${prefs.spans[c.id] ?? c.props.span ?? 1}
      columns=${cols} onDrop=${(dragged: string) => dragged !== c.id && move(dragged, c.id)} />`)}
    ${node.props.addable && !EXPORTED ? html`<${AddChart} path=${view.path} shown=${[...shown, ...prefs.added]} />` : null}
  </div>`;
}

const WIDTHS: Span[] = [1, 2, "full"];

// a grid cell: its block, a handle to drag it elsewhere in the grid, and its width.
function Cell(props: { node: Node; path: string; span: Span; columns?: number; onDrop: (dragged: string) => void }) {
  const [over, setOver] = useState(false);
  const next = WIDTHS[(WIDTHS.indexOf(props.span) + 1) % WIDTHS.length];
  const name = (s: Span) => (s === "full" ? "full width" : `${s} column${s === 1 ? "" : "s"}`);
  return html`<div class=${`cell span-${props.span}${over ? " drop" : ""}`}
      onDragOver=${(e: DragEvent) => { e.preventDefault(); setOver(true); }}
      onDragLeave=${() => setOver(false)}
      onDrop=${(e: DragEvent) => { e.preventDefault(); setOver(false); props.onDrop(e.dataTransfer?.getData("text/x-block") ?? ""); }}>
    <div class="cell-tools">
      <span class="cell-handle" draggable="true" role="button" tabindex="-1" aria-label="Drag to move"
        data-tip="Drag to move" onDragStart=${(e: DragEvent) => e.dataTransfer?.setData("text/x-block", props.node.id)}>
        <${Icon} name="grip" size=${14} /></span>
      <button type="button" class="cell-width small" data-tip=${`Width: ${name(props.span)}; click for ${name(next)}`}
        aria-label=${`Width ${name(props.span)}`} onClick=${() => setSpan(props.path, props.node.id, next)}>
        ${props.span === "full" ? "↔" : props.span}</button>
    </div>
    <${Block} node=${{ ...props.node, props: { ...props.node.props, span: 1 } }} />
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
  // an export records every tab, so each one opens in the snapshot.
  if (recording) return html`<div class="stack">${kids.map((k) => html`<${Block} key=${k.id} node=${k} />`)}</div>`;
  return html`<div class="tabs">
    <div class="tab-list heading" role="tablist" aria-label=${node.props.title ?? "Tabs"}>
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
