// Chart preferences per viewer, kept in the browser by group: the view-wide settings, each
// chart's own overrides, hidden runs and added charts. Views (M6) can save them as block props.

import { Store, stored, store, useStore } from "../state.ts";

export type ChartPrefs = {
  y?: string[];
  x?: "_step" | "_t" | "_elapsed";
  smooth?: number;
  by?: string | null;
  band?: "minmax" | "std" | "stderr" | "none";
  scale?: "linear" | "log";
  outliers?: boolean;
};

export type ViewPrefs = { charts: Record<string, ChartPrefs>; view: ChartPrefs; hidden: string[]; added: string[] };

const empty = (): ViewPrefs => ({ charts: {}, view: {}, hidden: [], added: [] });
const cache = new Map<string, Store<ViewPrefs>>();

export function prefsOf(path: string): Store<ViewPrefs> {
  let s = cache.get(path);
  if (!s) {
    s = new Store<ViewPrefs>({ ...empty(), ...stored<Partial<ViewPrefs>>(`prefs.${path}`, {}) });
    s.subscribe((v) => store(`prefs.${path}`, v));
    cache.set(path, s);
  }
  return s;
}

export function usePrefs(path: string): ViewPrefs {
  return useStore(prefsOf(path));
}

export function update(path: string, change: (p: ViewPrefs) => Partial<ViewPrefs>): void {
  const s = prefsOf(path);
  s.set({ ...s.value, ...change(s.value) });
}

export function setChart(path: string, id: string, prefs: ChartPrefs | null): void {
  update(path, (p) => {
    const charts = { ...p.charts };
    if (prefs === null) delete charts[id];
    else charts[id] = { ...charts[id], ...prefs };
    return { charts };
  });
}

export function setView(path: string, prefs: ChartPrefs): void {
  update(path, (p) => ({ view: { ...p.view, ...prefs } }));
}

// a click hides or shows a run; with shift, only that run stays visible (again: all return).
export function toggleRun(path: string, key: string, all: string[], solo = false): void {
  update(path, (p) => {
    const hidden = new Set(p.hidden);
    if (solo) {
      const alone = all.every((k) => k === key || hidden.has(k)) && !hidden.has(key);
      return { hidden: alone ? [] : all.filter((k) => k !== key) };
    }
    if (hidden.has(key)) hidden.delete(key);
    else hidden.add(key);
    return { hidden: [...hidden] };
  });
}

// the settings a chart uses: its node's defaults, then the view's, then its own.
export function effective(defaults: ChartPrefs, prefs: ViewPrefs, id: string): Required<Omit<ChartPrefs, "y" | "by">> & ChartPrefs {
  const merged = { smooth: 0, x: "_step", band: "minmax", scale: "linear", outliers: false, ...strip(defaults), ...strip(prefs.view), ...strip(prefs.charts[id] ?? {}) };
  return merged as Required<Omit<ChartPrefs, "y" | "by">> & ChartPrefs;
}

function strip(p: ChartPrefs): ChartPrefs {
  return Object.fromEntries(Object.entries(p).filter(([, v]) => v !== undefined)) as ChartPrefs;
}
