// A chart's settings panel. A chart kind declares which fields it offers; the panel lays them out in
// their sections and writes the choices as that chart's preferences.

import { html } from "htm/preact";
import { useState } from "preact/hooks";

import { useCall } from "../api.ts";
import type { Node } from "../bt/index.ts";
import { label } from "../bt/fmt.ts";
import { setChart, setView, type ChartPrefs, type Effective } from "../bt/prefs.ts";
import { MultiSelect } from "../ui/multiselect.ts";
import { Popover } from "../ui/primitives.ts";

export const X_AXES = [
  ["_step", "step"],
  ["epoch", "epoch"],
  ["_t", "wall time"],
  ["_elapsed", "elapsed"],
] as const;

// the x axes on offer: the progress clocks (epoch only when logged), then every other metric.
function xGroups(metrics: string[]): [string, string[]][] {
  const clocks = X_AXES.filter(([k]) => k !== "epoch" || metrics.includes("epoch")).map(([k]) => k);
  return [["Progress", clocks], ["Metrics", metrics.filter((k) => !clocks.includes(k as never))]];
}

export type Field = "metrics" | "x" | "steps" | "runs" | "band" | "smooth" | "scale" | "range" | "outliers" | "legend";

export const LINE_FIELDS: Field[] = ["metrics", "x", "steps", "runs", "band", "smooth", "scale", "range", "outliers", "legend"];

const SECTIONS: [string, Field[]][] = [
  ["Data", ["metrics", "x", "steps"]],
  ["Aggregation", ["runs", "band"]],
  ["Smoothing", ["smooth"]],
  ["Axes", ["scale", "range", "outliers", "legend"]],
];

type Context = {
  prefs: Effective;
  set: (p: ChartPrefs) => void;
  setAll: (p: ChartPrefs) => void;
  y: string[];
  metrics: string[];
  varying: string[];
};

const num = (v: string) => (v.trim() === "" || !Number.isFinite(Number(v)) ? null : Number(v));

// each field is its rows of the panel's two-column grid.
const FIELDS: Record<Field, (c: Context) => unknown> = {
  metrics: ({ y, metrics, set }) => html`
    <span class="field-label">Metrics</span>
    <${MultiSelect} options=${metrics} value=${y} label="Metrics" placeholder="Add a metric" onChange=${(v: string[]) => set({ y: v })} />`,

  x: ({ prefs, metrics, set, setAll }) => html`
    <span class="field-label">x axis</span>
    <${MultiSelect} single groups=${xGroups(metrics)} labels=${Object.fromEntries(X_AXES)} value=${[prefs.x]} label="x axis"
      placeholder=${Object.fromEntries(X_AXES)[prefs.x] ?? prefs.x} onChange=${(v: string[]) => set({ x: v[0] })} />
    <span></span>
    <button type="button" class="link small" onClick=${() => setAll({ x: prefs.x })}>Use this x axis on all charts on this page</button>`,

  steps: ({ prefs, set }) => {
    const steps = prefs.steps ?? [null, null];
    return html`
      <span class="field-label">Steps</span>
      <span class="pair">
        <span class="input"><input type="number" placeholder="first" value=${steps[0] ?? ""} aria-label="First step"
          onChange=${(e: Event) => set({ steps: [num((e.target as HTMLInputElement).value), steps[1]] })} /></span>
        <span class="muted">to</span>
        <span class="input"><input type="number" placeholder="last" value=${steps[1] ?? ""} aria-label="Last step"
          onChange=${(e: Event) => set({ steps: [steps[0], num((e.target as HTMLInputElement).value)] })} /></span>
      </span>`;
  },

  runs: ({ prefs, varying, set }) => html`
    <span class="field-label">Runs</span>
    <span class="input"><select value=${prefs.by ?? ""} onChange=${(e: Event) => set({ by: (e.target as HTMLSelectElement).value || null })}>
      <option value="">each run</option>
      <option value="seeds">mean over seeds</option>
      ${varying.map((k) => html`<option value=${k}>mean by ${label(k)}</option>`)}
    </select></span>`,

  band: ({ prefs, set }) => html`
    <span class="field-label">Band</span>
    <span class="input"><select value=${prefs.band} disabled=${!prefs.by} onChange=${(e: Event) => set({ band: (e.target as HTMLSelectElement).value as ChartPrefs["band"] })}>
      <option value="minmax">min to max</option><option value="std">± std</option>
      <option value="stderr">± std error</option><option value="none">none</option>
    </select></span>`,

  smooth: ({ prefs, set }) => html`
    <span class="field-label">EMA <b class="num">${prefs.smooth.toFixed(2)}</b></span>
    <input type="range" min="0" max="0.99" step="0.01" value=${prefs.smooth}
      onInput=${(e: Event) => set({ smooth: Number((e.target as HTMLInputElement).value) })} />
    <span></span>
    <label class="tick"><input type="checkbox" checked=${prefs.raw} disabled=${!prefs.smooth}
      onChange=${(e: Event) => set({ raw: (e.target as HTMLInputElement).checked })} /> show the raw curve faintly</label>`,

  scale: ({ prefs, set }) => html`
    <span class="field-label">y scale</span>
    <div class="segmented small" role="radiogroup" aria-label="y scale">
      ${(["linear", "log", "symlog"] as const).map((k) => html`<button type="button" role="radio" aria-checked=${prefs.scale === k}
          data-tip=${k === "symlog" ? "linear near zero, logarithmic beyond: for values that cross zero" : undefined}
          onClick=${() => set({ scale: k })}>${k}</button>`)}
    </div>`,

  range: ({ prefs, set }) => html`
    <span class="field-label">y range</span>
    <span class="pair">
      <span class="input"><input type="number" step="any" placeholder="auto" value=${prefs.ymin ?? ""} aria-label="y minimum"
        onChange=${(e: Event) => set({ ymin: num((e.target as HTMLInputElement).value) })} /></span>
      <span class="muted">to</span>
      <span class="input"><input type="number" step="any" placeholder="auto" value=${prefs.ymax ?? ""} aria-label="y maximum"
        onChange=${(e: Event) => set({ ymax: num((e.target as HTMLInputElement).value) })} /></span>
    </span>`,

  outliers: ({ prefs, set }) => html`
    <span></span>
    <label class="tick"><input type="checkbox" checked=${prefs.outliers}
      onChange=${(e: Event) => set({ outliers: (e.target as HTMLInputElement).checked })} /> ignore outliers in the auto range</label>`,

  legend: ({ prefs, set }) => html`
    <span></span>
    <label class="tick"><input type="checkbox" checked=${prefs.legend}
      onChange=${(e: Event) => set({ legend: (e.target as HTMLInputElement).checked })} /> legend</label>`,
};

export function Settings(props: { node: Node; path: string; prefs: Effective; y: string[]; fields: Field[] }) {
  const { node, path, prefs } = props;
  const [opened, setOpened] = useState(false);
  // what to offer comes from keys, asked only once the settings are opened.
  const keys = useCall(opened ? { method: "keys", params: { from: path }, scope: path } : null).data;
  const context: Context = {
    prefs,
    set: (p) => setChart(path, node.id, p),
    setAll: (p) => setView(path, p),
    y: props.y,
    metrics: keys?.metrics?.rows.map((r: unknown[]) => r[0]) ?? [],
    varying: (keys?.config?.varying ?? []).filter((k: string) => k !== "config.seed"),
  };
  return html`<${Popover} icon="sliders" label="Chart settings" title="This chart" class="chart-settings" beside=".chart-frame"
      onOpen=${() => setOpened(true)}>
    <div class="settings-grid small">
      ${SECTIONS.map(([name, members]) => {
        const shown = members.filter((f) => props.fields.includes(f));
        return shown.length ? html`<h5>${name}</h5>${shown.map((f) => FIELDS[f](context))}` : null;
      })}
    </div>
    <button type="button" class="link small reset" onClick=${() => setChart(path, node.id, null)}>Reset this chart</button>
  <//>`;
}
