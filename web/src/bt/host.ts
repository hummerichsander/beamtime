// What a block asks of the page it is on: saving a file, a figure the server draws, the expanded
// view of a chart. A custom block's frame has no downloads, network or room of its own, so it
// swaps in a host that asks the page over the bridge.

import { Store } from "../state.ts";
import { pdf, save } from "./export.ts";
import type { Node, ViewContext } from "./index.ts";

export type Host = {
  // a file from a data or blob URL.
  download(href: string, name: string): void;
  // a vector PDF the server draws with matplotlib.
  figure(spec: Record<string, unknown>, name: string): Promise<void>;
  // a chart in the page's dialog, at its full size.
  expand(node: Node, view: ViewContext): void;
};

// the chart the page's dialog shows, with the context of the view it came from.
export const expanded = new Store<{ node: Node; view: ViewContext } | null>(null);

let current: Host = {
  download: save,
  figure: pdf,
  expand: (node, view) => expanded.set({ node, view }),
};

export function host(): Host {
  return current;
}

export function setHost(next: Host): void {
  current = next;
}
