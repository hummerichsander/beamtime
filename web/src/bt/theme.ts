// Theme tokens as CSS variables, light/dark mode, stable run colors and the Vega-Lite config.

export type Theme = {
  name: string;
  type: "light" | "dark";
  colors: Record<string, string | number>;
  data: {
    categorical: string[];
    sequential: string[];
    diverging: string[];
    baseline: { color: string; dash: number[] };
  };
  fonts: Record<string, string>;
  sizes: Record<string, number>;
  shape: Record<string, unknown>;
};
export type Pair = { light: Theme; dark: Theme; problems: string[] };
export type Mode = "system" | "light" | "dark";

export function cssVariables(theme: Theme): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(theme.colors)) out[`--bt-${k.replace(/\./g, "-")}`] = String(v);
  for (const [k, v] of Object.entries(theme.fonts)) out[`--bt-font-${k}`] = v;
  for (const [k, v] of Object.entries(theme.sizes)) out[`--bt-size-${k}`] = `${v}px`;
  out["--bt-radius"] = `${Number(theme.shape.radius ?? 6)}px`;
  return out;
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

export function groupColors(values: unknown[], theme: Theme): Map<string, string> {
  const distinct = [...new Set(values.map((v) => JSON.stringify(v)))];
  const numeric = distinct.every((v) => typeof JSON.parse(v) === "number");
  const sorted = numeric
    ? distinct.sort((a, b) => JSON.parse(a) - JSON.parse(b))
    : distinct.sort();
  const out = new Map<string, string>();
  sorted.forEach((v, i) => {
    out.set(
      v,
      numeric && sorted.length > theme.data.categorical.length
        ? ramp(theme.data.sequential, sorted.length === 1 ? 1 : i / (sorted.length - 1))
        : theme.data.categorical[i % theme.data.categorical.length],
    );
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

function rgb(hex: string): number[] {
  const h = hex.replace("#", "");
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
}

export function vegaConfig(theme: Theme): Record<string, unknown> {
  const c = theme.colors;
  const font = theme.fonts.sans;
  const axis = {
    domainColor: c.border,
    gridColor: c.grid,
    tickColor: c.border,
    labelColor: c.muted,
    titleColor: c.muted,
    labelFont: font,
    titleFont: font,
    labelFontSize: theme.sizes.xs,
    titleFontSize: theme.sizes.xs,
    titleFontWeight: "normal",
  };
  return {
    background: null,
    font,
    view: { stroke: null },
    axis,
    legend: {
      labelColor: c.muted,
      titleColor: c.muted,
      labelFont: font,
      titleFont: font,
      labelFontSize: theme.sizes.xs,
      titleFontSize: theme.sizes.xs,
      titleFontWeight: "normal",
      symbolType: "stroke",
      labelLimit: 120,
    },
    line: { strokeWidth: Number(theme.shape.line ?? 1.5) },
    point: { size: Number(theme.shape.point ?? 3) ** 2 * 4 },
    range: {
      category: theme.data.categorical,
      ramp: theme.data.sequential,
      diverging: theme.data.diverging,
    },
  };
}
