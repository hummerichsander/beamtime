// Shell state that isn't in the URL: sidebar, palette, help, project meta.

import { Store, stored, store } from "../state.ts";

export const sidebar = new Store<boolean>(stored("sidebar", true));
export const palette = new Store<boolean>(false);
export const help = new Store<boolean>(false);
export const meta = new Store<any>(null);

sidebar.subscribe((v) => store("sidebar", v));

export function typing(e: Event): boolean {
  const t = e.target as HTMLElement | null;
  return !!t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable);
}

export const SHORTCUTS: [string, string][] = [
  ["⌘K, /", "search folders, runs and commands"],
  ["↑ ↓ ← →", "move in the folder tree"],
  ["[  ]", "previous and next sibling folder"],
  ["i", "open or close the context drawer"],
  ["⌘B", "show or hide the sidebar"],
  ["p", "pause or resume live updates"],
  ["Esc", "clear the selection, close the drawer"],
  ["?", "this list"],
];
