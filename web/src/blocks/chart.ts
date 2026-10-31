// What chart blocks share: the download menu, and the height of a chart in the page's dialog.

import { html } from "htm/preact";

import { type Background } from "../bt/export.ts";
import { Icon } from "../ui/icons.ts";
import { Popover } from "../ui/primitives.ts";

export const HEIGHT = 220;

// a chart's height in the page's dialog.
export function expandedHeight(): number {
  return Math.round(innerHeight * 0.62);
}

export function Downloads(props: { png: (b: Background) => void; pdf?: () => void; csv?: () => void }) {
  // a choice closes the menu.
  const close = (e: Event) => (e.target as Element).closest<HTMLElement>("[popover]")?.hidePopover();
  return html`<${Popover} icon="download" label="Download" title="Download">
    <div class="menu-list" onClick=${close}>
      <button type="button" onClick=${() => props.png("transparent")}><${Icon} name="image" size=${15} /> PNG, transparent</button>
      <button type="button" onClick=${() => props.png("white")}><${Icon} name="image" size=${15} /> PNG, white background</button>
      ${props.pdf ? html`<button type="button" onClick=${props.pdf}><${Icon} name="file-text" size=${15} /> PDF (vector)</button>` : null}
      ${props.csv ? html`<button type="button" onClick=${props.csv}><${Icon} name="file-text" size=${15} /> CSV data</button>` : null}
    </div>
  <//>`;
}
