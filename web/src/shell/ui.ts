// Shell state that isn't in the URL: sidebar, palette, help, project meta.

import { Store, stored, store } from "../state.ts";

export const sidebar = new Store<boolean>(stored("sidebar", true));
// the palette is closed (null) or open with a starting query.
export const palette = new Store<string | null>(null);
export const help = new Store<boolean>(false);
export const meta = new Store<any>(null);

sidebar.subscribe((v) => store("sidebar", v));

// the previous visit, for "failed since your last visit"; this visit becomes the next one's.
export const lastVisit: number = stored<number>("visit", Date.now());
store("visit", Date.now());

export function typing(e: Event): boolean {
  const t = e.target as HTMLElement | null;
  return !!t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable);
}

export const SHORTCUTS: [string, string][] = [
  ["⌘K, /", "search groups, runs and commands"],
  ["↑ ↓ ← →", "move in the group tree"],
  ["[  ]", "previous and next sibling group"],
  ["i", "open or close the context drawer"],
  ["⌘B, b", "show or hide the sidebar"],
  ["p", "pause or resume live updates"],
  ["Esc", "clear the selection, close the drawer"],
  ["?", "this list"],
];
