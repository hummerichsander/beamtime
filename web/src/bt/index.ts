// The `bt` kit core: data hooks, theme, colors, formatting, links and plotting.

import { createContext, h, render, type RefObject } from "preact";
import * as hooks from "preact/hooks";
import { useContext, useEffect, useRef, useState } from "preact/hooks";
import { html } from "htm/preact";

import { type Call, type Result, useCall } from "../api.ts";
import { groupUrl, runUrl } from "../router.ts";
import { Store, stored, store, useStore } from "../state.ts";
import * as fmt from "./fmt.ts";
import { lineChart } from "./plot.ts";
import { assignColors, cssVariables, groupColors, type Mode, type Pair, type Theme } from "./theme.ts";

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
  const root = document.documentElement;
  for (const [k, v] of Object.entries(cssVariables(t))) root.style.setProperty(k, v);
  root.dataset.mode = t.type;
  root.style.colorScheme = t.type;
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
  for (const [k, v] of Object.entries(cssVariables(last))) document.documentElement.style.setProperty(k, v);
  document.documentElement.dataset.mode = last.type;
  theme.value = last;
}

export type ViewContext = { path: string; colors: Map<string, string> };
export const ViewCtx = createContext<ViewContext>({ path: ".", colors: new Map() });
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

export function useSize(): [RefObject<HTMLDivElement>, number] {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);
  useEffect(() => {
    if (!ref.current) return;
    const ro = new ResizeObserver(([e]) => setWidth(Math.round(e.contentRect.width)));
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, []);
  return [ref, width];
}

export const bt = {
  preact: { h, render, html, ...hooks },
  useData,
  theme: {
    get tokens() {
      return theme.value;
    },
    get mode() {
      return theme.value?.type ?? "light";
    },
    onChange: (cb: (t: Theme | null) => void) => theme.subscribe(cb),
    runColor: (id: string) => runColors([id], theme.value).get(id),
    groupColors: (values: unknown[]) => (theme.value ? groupColors(values, theme.value) : new Map()),
  },
  fmt,
  label: fmt.label,
  chart: { line: lineChart },
  link: { run: runUrl, group: groupUrl },
  useSize,
};
