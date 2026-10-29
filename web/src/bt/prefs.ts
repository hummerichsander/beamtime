// Chart preferences per viewer, kept in the browser by group: each chart's own settings, hidden
// runs and added charts. "Save as view" writes them into the view as block props.

import { Store, stored, store, useStore } from "../state.ts";

export type Scale = "linear" | "log" | "symlog";

export type ChartPrefs = {
  y?: string[];
  x?: "_step" | "_t" | "_elapsed";
  steps?: [number | null, number | null] | null;
  smooth?: number;
  raw?: boolean;
  by?: string | null;
  band?: "minmax" | "std" | "stderr" | "none";
  scale?: Scale;
  ymin?: number | null;
  ymax?: number | null;
  outliers?: boolean;
  legend?: boolean;
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

export type Effective = Required<Pick<ChartPrefs, "x" | "smooth" | "raw" | "band" | "scale" | "outliers" | "legend">> & ChartPrefs;

// the settings a chart uses: its node's defaults, then the viewer's own for this chart.
export function effective(defaults: ChartPrefs, prefs: ViewPrefs, id: string): Effective {
  const base = { smooth: 0, raw: true, x: "_step", band: "minmax", scale: "linear", outliers: false, legend: true };
  return { ...base, ...strip(defaults), ...strip(prefs.charts[id] ?? {}) } as Effective;
}

// whether a viewer changed anything "Save as view" would keep.
export function changed(prefs: ViewPrefs): boolean {
  return Object.values(prefs.charts).some((c) => Object.keys(strip(c)).length > 0) || prefs.added.length > 0;
}

function strip(p: ChartPrefs): ChartPrefs {
  return Object.fromEntries(Object.entries(p).filter(([, v]) => v !== undefined)) as ChartPrefs;
}
