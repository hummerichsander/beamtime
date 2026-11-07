// What every chart shares around its drawing: the head, the tools, the download menu, the legend
// and the caption. A chart supplies its title, its tools and its plot.

import { html } from "htm/preact";
import type { ComponentChildren, RefObject } from "preact";

import { EXPORTED } from "../snapshot.ts";
import { Icon } from "../ui/icons.ts";
import { IconButton, Popover } from "../ui/primitives.ts";
import { type Background } from "./export.ts";
import { register } from "./figures.ts";
import { expanded as dialog } from "./host.ts";

export const HEIGHT = 240;

// a chart's height in the page's dialog.
export function expandedHeight(): number {
  return Math.round(innerHeight * 0.62);
}

export type DownloadSet = { png: (b: Background) => unknown; pdf?: () => unknown; csv?: () => unknown };

export function Downloads(props: DownloadSet & { id?: string }) {
  register(props.id, props);
  // a choice closes the menu.
  const close = (e: Event) => (e.target as Element).closest<HTMLElement>("[popover]")?.hidePopover();
  return html`<${Popover} icon="download" label="Download" title="Download">
    <div class="menu-list" onClick=${close}>
      <button type="button" onClick=${() => props.png("transparent")}><${Icon} name="image" size=${15} /> PNG, transparent</button>
      <button type="button" onClick=${() => props.png("white")}><${Icon} name="image" size=${15} /> PNG, white background</button>
      ${props.pdf && !EXPORTED ? html`<button type="button" onClick=${props.pdf}><${Icon} name="file-text" size=${15} /> PDF (vector)</button>` : null}
      ${props.csv ? html`<button type="button" onClick=${props.csv}><${Icon} name="file-text" size=${15} /> CSV data</button>` : null}
    </div>
  <//>`;
}

export type LegendItem = {
  label: string;
  mark: { class: string; style?: string };
  off?: boolean;
  // an item with handlers is a button that toggles; without any it is a static key.
  tip?: string;
  onClick?: (e: MouseEvent) => void;
  onDblClick?: () => void;
  onHover?: (on: boolean) => void;
};

// the swatches of a chart's colors; a null item stands for the entries left out.
export function Legend(props: { items: (LegendItem | null)[]; label: string; name?: string; role?: string }) {
  return html`<div class="legend small" role=${props.role} aria-label=${props.label}>
    ${props.name ? html`<span class="muted">${props.name}</span>` : null}
    ${props.items.map((it) =>
      it === null
        ? html`<span class="muted">…</span>`
        : it.onClick
          ? html`<button type="button" class=${`legend-item${it.off ? " off" : ""}`} aria-pressed=${!it.off} data-tip=${it.tip}
              onPointerEnter=${() => it.onHover?.(true)} onPointerLeave=${() => it.onHover?.(false)}
              onClick=${it.onClick} onDblClick=${it.onDblClick}>
              <span class=${it.mark.class} style=${it.mark.style}></span>${it.label}</button>`
          : html`<span class="legend-item static"><span class=${it.mark.class} style=${it.mark.style}></span>${it.label}</span>`,
    )}
  </div>`;
}

export function ChartFrame(props: {
  id: string;
  title: string;
  notes?: string[];
  // beside the notes in the head, always visible.
  status?: ComponentChildren;
  // buttons before the download menu.
  tools?: ComponentChildren;
  downloads: DownloadSet;
  legend?: ComponentChildren;
  caption?: string;
  expanded?: boolean;
  onExpand?: () => void;
  onRemove?: () => void;
  // the element the page watches to draw the chart once it is on screen.
  box?: RefObject<HTMLDivElement>;
  // how many curves the renderer's layout check counts.
  curves?: number;
  class?: string;
  children?: ComponentChildren;
}) {
  const classes = ["chart", "chart-frame", props.expanded ? "expanded" : "", props.class ?? ""].filter(Boolean).join(" ");
  return html`<figure ref=${props.box} class=${classes} data-curves=${props.curves}>
    <div class="chart-head">
      <b class="chart-title">${props.title}</b>
      ${props.notes?.length ? html`<span class="muted small">${props.notes.join(" · ")}</span>` : null}
      ${props.status ?? null}
      <span class="chart-tools">
        ${props.tools ?? null}
        <${Downloads} id=${props.id} ...${props.downloads} />
        ${props.expanded
          ? html`<${IconButton} icon="x" label="Close (Esc)" onClick=${() => dialog.set(null)} />`
          : props.onExpand
            ? html`<${IconButton} icon="maximize" label="Expand" onClick=${props.onExpand} />`
            : null}
        ${props.onRemove && !props.expanded ? html`<${IconButton} icon="x" label="Hide this chart" onClick=${props.onRemove} />` : null}
      </span>
    </div>
    ${props.children}
    ${props.legend ?? null}
    ${props.caption ? html`<figcaption class="caption"><b></b> ${props.caption}</figcaption>` : null}
  </figure>`;
}
