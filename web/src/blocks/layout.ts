// Layout blocks: section, row, grid and tabs.

import { html } from "htm/preact";
import type { ComponentChildren } from "preact";
import { useContext, useState } from "preact/hooks";

import { useCall } from "../api.ts";
import { ViewCtx, type Node } from "../bt/index.ts";
import { MAIN_GRID, ordered, setMain, setOrder, setSpan, showCharts, update, usePrefs, type Pin, type Span } from "../bt/prefs.ts";
import { recording } from "../router.ts";
import { EXPORTED } from "../snapshot.ts";
import { stored, store } from "../state.ts";
import { Icon } from "../ui/icons.ts";
import { MultiSelect } from "../ui/multiselect.ts";
import { Section as PageSection } from "../ui/primitives.ts";
import { LabelCtx } from "./common.ts";
import { Block } from "./index.ts";

// each viewer's choice of open or closed is remembered per page and section.
export function Section({ node }: { node: Node }) {
  const view = useContext(ViewCtx);
  const key = `section.${view.path}:${node.id}`;
  const [open, setOpen] = useState<boolean>(() => recording || stored(key, node.props.open !== false));
  const toggle = () => {
    store(key, !open);
    setOpen(!open);
  };
  const children = html`${(node.children ?? []).map((c) => html`<${Block} key=${c.id} node=${c} />`)}`;
  const label = useContext(LabelCtx);
  if (!node.props.title) return html`<div class="stack">${children}</div>`;
  const repeated = label === node.props.title.toLowerCase();
  return html`<div class="view-section">
    <button type="button" class="view-section-title heading" aria-expanded=${open} aria-label=${repeated ? `${open ? "Close" : "Open"} ${node.props.title}` : undefined}
        data-tip=${repeated ? `${open ? "Close" : "Open"} ${node.props.title}` : undefined}
        onClick=${toggle}>
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

export function Grid({ node, after }: { node: Node; after?: ComponentChildren }) {
  const view = useContext(ViewCtx);
  const prefs = usePrefs(view.path);
  const min = node.props.min_width ?? 320;
  const cols = node.props.columns;
  const style = cols
    ? `grid-template-columns: repeat(${cols}, minmax(0, 1fr))`
    : `grid-template-columns: repeat(auto-fill, minmax(min(${min}px, 100%), 1fr))`;
  const kids = node.children ?? [];
  const hidden = kids.filter((c) => prefs.removed.includes(c.id)).map((c) => c.id);
  const cells = ordered(kids.filter((c) => !hidden.includes(c.id)), prefs.order[node.id]);
  const move = (dragged: string, before: string) => {
    const ids = cells.map((c) => c.id).filter((id) => id !== dragged);
    ids.splice(ids.indexOf(before), 0, dragged);
    setOrder(view.path, node.id, ids);
    // dragging inside Main orders the pins, the first of which leads the header and the table.
    if (node.id === MAIN_GRID) {
      const yOf = (id: string) => (kids.find((c) => c.id === id)?.data?.main?.params?.y as string[] | undefined)?.[0];
      const moved = ids.map((id) => view.pins.find((p) => p.y === yOf(id))).filter((p): p is Pin => !!p);
      setMain(view.path, [...moved, ...view.pins.filter((p) => !moved.includes(p))]);
    }
  };
  return html`<div class="grid" style=${style}>
    ${cells.map((c) => html`<${Cell} key=${c.id} node=${c} path=${view.path} span=${prefs.spans[c.id] ?? c.props.span ?? 1}
      columns=${cols} onDrop=${(dragged: string) => dragged !== c.id && move(dragged, c.id)} />`)}
    ${after ?? null}
    ${hidden.length
      ? html`<div class="grid-note"><button type="button" class="link small" onClick=${() => showCharts(view.path, hidden)}>${hidden.length} hidden · show</button></div>`
      : null}
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

// the end of the page's charts: the charts a viewer added, and a picker for any metric the page
// shows no chart of (a metric left out of an authored view, or a chart the viewer hid).
export function AddCharts({ root }: { root: Node }) {
  const view = useContext(ViewCtx);
  const prefs = usePrefs(view.path);
  const keys = useCall({ method: "keys", params: { from: view.path }, scope: view.path }).data;
  const template = root.props.template;
  if (!template || EXPORTED) return null;
  const hidden = new Set(prefs.removed);
  const placed = new Set([...view.charted].filter(([id]) => !hidden.has(id)).flatMap(([, ys]) => ys));
  const extra: Node[] = prefs.added
    .filter((m) => !placed.has(m))
    .map((m) => ({
      block: "line",
      id: `added-${m}`,
      props: { y: m },
      data: { main: { ...template, params: { ...template.params, y: [m] } } },
    }));
  const shown = new Set([...placed, ...extra.filter((n) => !hidden.has(n.id)).map((n) => n.props.y as string)]);
  const more: string[] = (keys?.metrics?.rows ?? []).map((r: unknown[]) => r[0] as string).filter((m: string) => !shown.has(m));
  if (!keys || !(more.length || extra.length)) return null;
  // a metric whose chart was hidden gets that chart back rather than a second one.
  const back = (m: string) => [...view.charted].find(([id, ys]) => hidden.has(id) && ys.includes(m))?.[0] ?? extra.find((n) => hidden.has(n.id) && n.props.y === m)?.id;
  const choose = (m: string) => {
    const id = back(m);
    if (id) showCharts(view.path, [id]);
    else update(view.path, (p) => ({ added: [...p.added, m] }));
  };
  const picker = more.length
    ? html`<div class="add-chart">
        <span class="add-chart-label"><${Icon} name="plus" size=${16} /> Add a chart</span>
        <${MultiSelect} single options=${more} value=${[]} label="Metric for a new chart" placeholder="Search metrics"
          onChange=${([m]: string[]) => choose(m)} />
      </div>`
    : null;
  return html`<${PageSection}><${Grid} node=${{ block: "grid", id: "added", props: {}, children: extra }} after=${picker} /><//>`;
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
