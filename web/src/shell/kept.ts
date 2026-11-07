// What the shell keeps steady while a page's calls change under it.

import { useRef } from "preact/hooks";

import { type Call, type Result, useCall } from "../api.ts";

// like useCall, but while a new call of the same scope loads, the scope's last answer stays: a
// page whose params changed (a viewer's pins) keeps what it shows, and its scroll position, until
// the new answer is in. Another scope starts from nothing.
export function useCallKept<T = any>(call: Call, scope: string): Result<T> {
  const result = useCall<T>(call);
  const last = useRef<{ scope: string; result: Result<T> } | null>(null);
  if (result.status !== "loading") last.current = { scope, result };
  return result.status === "loading" && last.current?.scope === scope ? last.current.result : result;
}

// a change above the viewer's place (a section appearing, a fact line growing) must not move what
// they look at: hold an element's place while the page settles, until they scroll themselves.
let release: (() => void) | null = null;

export function holdPlace(el: Element | null): void {
  release?.();
  const main = document.querySelector<HTMLElement>(".main");
  if (!el || !main) return;
  const top = el.getBoundingClientRect().top;
  const observer = new ResizeObserver(() => {
    if (el.isConnected) main.scrollTop += el.getBoundingClientRect().top - top;
  });
  for (const child of main.children) observer.observe(child);
  const events = ["wheel", "touchmove", "keydown", "pointerdown"];
  const stop = () => {
    observer.disconnect();
    clearTimeout(timer);
    for (const e of events) removeEventListener(e, stop);
    release = null;
  };
  const timer = setTimeout(stop, 5000);
  for (const e of events) addEventListener(e, stop, { passive: true });
  release = stop;
}
