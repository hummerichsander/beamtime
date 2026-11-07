// The theme on the page: light/dark, a theme file's colors as CSS variables, stable run colors and
// line styles, and the chart style.

import { Store } from "../state.ts";

export type Theme = {
  name: string;
  type: "light" | "dark";
  colors: Record<string, string>;
  // line styles of runs, the same order as data-1 to data-6.
  dashes: number[][];
  stroke: number;
  font: string;
  ramps: { sequential: string[]; diverging: string[] };
};
export type Pair = { light: Theme; dark: Theme; problems: string[] };
export type Mode = "system" | "light" | "dark";

// put a theme on the document: tokens.css has the default values, a theme file's colors go on top.
export function paint(t: Theme): void {
  const root = document.documentElement;
  for (const [k, v] of Object.entries(cssVariables(t))) root.style.setProperty(k, v);
  root.dataset.theme = t.type;
}

export function cssVariables(theme: Theme): Record<string, string> {
  return Object.fromEntries(Object.entries(theme.colors).map(([k, v]) => [`--${k}`, v]));
}

// run n is drawn in data-n with dash-n.
export function palette(theme: Theme): string[] {
  return theme.dashes.map((_, i) => theme.colors[`data-${i + 1}`]);
}

// which run style a color is (1 to 6), or null for a color from a colormap.
export function slotOf(color: string | undefined, theme: Theme | null): number | null {
  if (!color || !theme) return null;
  const i = palette(theme).indexOf(color);
  return i < 0 ? null : i + 1;
}

export function dashOf(color: string | undefined, theme: Theme): number[] {
  const slot = slotOf(color, theme);
  return slot === null ? [] : theme.dashes[slot - 1];
}

// the class of a swatch, or its color when it isn't a run style.
export function swatch(color: string | undefined, theme: Theme | null): { class: string; style?: string } {
  const slot = slotOf(color, theme);
  return slot === null ? { class: "swatch", style: color ? `color:${color}` : undefined } : { class: `swatch run-${slot}` };
}

// a hash of the run id picks a preferred slot; in id order, later runs move to the next free one.
export function assignColors(ids: string[], palette: string[]): Map<string, string> {
  const out = new Map<string, string>();
  const taken = new Set<number>();
  for (const id of [...new Set(ids)].sort()) {
    let slot = hash(id) % palette.length;
    if (taken.size < palette.length) {
      while (taken.has(slot)) slot = (slot + 1) % palette.length;
    }
    taken.add(slot);
    out.set(id, palette[slot]);
  }
  return out;
}

export function hash(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

// matplotlib's colormaps, sampled by the server, by family and name; a chart picks one by name.
export type Colormaps = { sequential: Record<string, string[]>; diverging: Record<string, string[]> };
export const colormaps = new Store<Colormaps | null>(null);

// the colors of a named colormap of either family, or null for none or an unknown name.
export function stopsOf(name: string | null | undefined): string[] | null {
  const maps = colormaps.value;
  return (name && (maps?.sequential[name] ?? maps?.diverging[name])) || null;
}

// a color per distinct value. A chosen colormap always applies: numeric values by their order,
// categories at evenly spaced positions. Without one, categories take the theme's palette and
// more numeric values than it has colors take the default sequential ramp.
export function groupColors(values: unknown[], theme: Theme, stops: string[] | null = null): Map<string, string> {
  const distinct = [...new Set(values.map((v) => JSON.stringify(v)))];
  const numeric = distinct.every((v) => typeof JSON.parse(v) === "number");
  const sorted = numeric
    ? distinct.sort((a, b) => JSON.parse(a) - JSON.parse(b))
    : distinct.sort();
  const colors = palette(theme);
  const ramped = stops ?? (numeric && sorted.length > colors.length ? theme.ramps.sequential : null);
  const out = new Map<string, string>();
  sorted.forEach((v, i) => {
    out.set(v, ramped ? ramp(ramped, sorted.length === 1 ? 1 : i / (sorted.length - 1)) : colors[i % colors.length]);
  });
  return out;
}

export function ramp(stops: string[], t: number): string {
  const x = Math.min(1, Math.max(0, t)) * (stops.length - 1);
  const i = Math.min(stops.length - 2, Math.floor(x));
  const [a, b] = [rgb(stops[i]), rgb(stops[i + 1])];
  const f = x - i;
  return `#${a.map((c, k) => Math.round(c + (b[k] - c) * f).toString(16).padStart(2, "0")).join("")}`;
}

// a color with transparency, for fills under outlines and dimmed marks.
export function alpha(hex: string, a: number): string {
  const [r, g, b] = rgb(hex);
  return `rgba(${r}, ${g}, ${b}, ${a})`;
}

function rgb(hex: string): number[] {
  const h = hex.replace("#", "");
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
}

export type ChartStyle = {
  axis: string;
  grid: string;
  text: string;
  font: string;
  line: number;
  dim: number;
  band: number;
};

export function chartStyle(theme: Theme): ChartStyle {
  const c = theme.colors;
  return { axis: c.muted, grid: c.line, text: c.muted, font: theme.font, line: theme.stroke, dim: 0.2, band: 0.2 };
}
