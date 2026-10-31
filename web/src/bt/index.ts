// What blocks share: the view's context, the data hook, the theme, run colors and the hovered run.

import { createContext, type RefObject } from "preact";
import { useContext, useEffect, useRef, useState } from "preact/hooks";

import { type Call, type Result, useCall } from "../api.ts";
import { Store, stored, store, useStore } from "../state.ts";
import { assignColors, paint, type Mode, type Pair, type Theme } from "./theme.ts";

export type Node = {
  block: string;
  id: string;
  props: Record<string, any>;
  data?: Record<string, Call>;
  children?: Node[];
};

export const pair = new Store<Pair | null>(null);
// the run under the pointer anywhere in the view; tables, legends and charts highlight it.
export const hovered = new Store<string | null>(null);
export const mode = new Store<Mode>(stored<Mode>("mode", "system"));
export const theme = new Store<Theme | null>(null);
const dark = matchMedia("(prefers-color-scheme: dark)");

export function applyTheme(): void {
  const p = pair.value;
  if (!p) return;
  const wanted = mode.value === "system" ? (dark.matches ? "dark" : "light") : mode.value;
  const t = p[wanted];
  paint(t);
  store("theme", t);
  theme.set(t);
}

export function setMode(m: Mode): void {
  store("mode", m);
  mode.set(m);
  applyTheme();
}

dark.addEventListener("change", applyTheme);

// the last theme is applied before the first answer arrives, so pages don't flash.
const last = stored<Theme | null>("theme", null);
if (last) {
  paint(last);
  theme.value = last;
}

export type MetricInfo = { label?: string; unit?: string; scale?: "linear" | "log"; higher_is_better?: boolean };
// what every block of a view shares: the page, run colors and names, and the view's metrics.
export type ViewContext = {
  path: string;
  colors: Map<string, string>;
  names: Map<string, string>;
  metrics: Record<string, MetricInfo>;
};
export const ViewCtx = createContext<ViewContext>({ path: ".", colors: new Map(), names: new Map(), metrics: {} });
export const BlockCtx = createContext<Node | null>(null);

export function useData<T = any>(name: string): Result<T> {
  const node = useContext(BlockCtx);
  return useCall<T>(node?.data?.[name] ?? null);
}

export function useTheme(): Theme | null {
  return useStore(theme);
}

export function useRunColors(): Map<string, string> {
  return useContext(ViewCtx).colors;
}

export function runColors(ids: string[], t: Theme | null): Map<string, string> {
  return assignColors(ids, t?.data.categorical ?? ["#0969da"]);
}

export function useVisible(margin = "200px"): [RefObject<HTMLDivElement>, boolean] {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    if (visible || !ref.current) return;
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setVisible(true);
          io.disconnect();
        }
      },
      { rootMargin: margin },
    );
    io.observe(ref.current);
    return () => io.disconnect();
  }, [visible]);
  return [ref, visible];
}
