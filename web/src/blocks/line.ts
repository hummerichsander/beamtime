// `line`: metric curves on uPlot, W&B-style: synced crosshair, hover focus, legend toggles,
// drag-zoom with an exact refetch of the window, smoothing, and settings per chart or view.

import { html } from "htm/preact";
import { useContext, useEffect, useRef, useState } from "preact/hooks";

import { type Call, useCall } from "../api.ts";
import { hovered, useRunColors, useTheme, useVisible, ViewCtx, type Node } from "../bt/index.ts";
import { align, reshape, robustRange, smooth, type Curves } from "../bt/curves.ts";
import { duration, label, step, value } from "../bt/fmt.ts";
import { lineChart, type LineChart, type LineSpec } from "../bt/plot.ts";
import { effective, setChart, toggleRun, update, usePrefs, type ChartPrefs } from "../bt/prefs.ts";
import { chartStyle, groupColors, type Theme } from "../bt/theme.ts";
import { Icon } from "../ui/icons.ts";
import { IconButton, Popover } from "../ui/primitives.ts";
import { Notice, Panel } from "./common.ts";

const HEIGHT = 220;
const LEGEND_MAX = 12;
const X_AXES = [
  ["_step", "step"],
  ["_t", "wall time"],
  ["_elapsed", "elapsed"],
] as const;

export function Line({ node }: { node: Node }) {
  const view = useContext(ViewCtx);
  const [expanded, setExpanded] = useState(false);
  return html`<div class="block chart-block">
    <${Chart} node=${node} path=${view.path} height=${HEIGHT} onExpand=${() => setExpanded(true)} />
    ${expanded ? html`<${Expanded} node=${node} path=${view.path} onClose=${() => setExpanded(false)} />` : null}
  </div>`;
}

function Expanded(props: { node: Node; path: string; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = dialog.current!;
    d.showModal();
    d.addEventListener("close", props.onClose);
    return () => d.removeEventListener("close", props.onClose);
  }, []);
  return html`<dialog class="sheet wide chart-dialog" ref=${dialog} aria-label=${props.node.props.y} closedby="any">
    <${Chart} node=${props.node} path=${props.path} height=${Math.round(innerHeight * 0.62)} expanded
      onClose=${() => dialog.current?.close()} />
  </dialog>`;
}

// the series call a chart makes: the node's call with the viewer's settings applied.
export function seriesCall(node: Node, prefs: ReturnType<typeof effective>, zoom: [number, number] | null, width: number): Call {
  const base = node.data!.main;
  const params: Record<string, unknown> = { ...base.params };
  params.y = prefs.y?.length ? prefs.y : [node.props.y];
  params.x = prefs.x;
  params.points = Math.max(100, Math.min(1500, Math.round(width || 600)));
  params.band = prefs.band;
  delete params.seeds;
  delete params.by;
  if (prefs.by === "seeds") params.seeds = "config.seed";
  else if (prefs.by) params.by = [prefs.by];
  if (zoom && prefs.x === "_step") params.steps = [Math.floor(zoom[0]), Math.ceil(zoom[1])];
  return { ...base, params };
}

function defaultsOf(node: Node): ChartPrefs {
  const params = node.data?.main.params ?? {};
  return {
    scale: node.props.scale === "log" ? "log" : "linear",
    by: params.seeds ? "seeds" : Array.isArray(params.by) ? (params.by as string[])[0] : null,
    band: (params.band as ChartPrefs["band"]) ?? "minmax",
  };
}

function Chart(props: {
  node: Node;
  path: string;
  height: number;
  expanded?: boolean;
  onExpand?: () => void;
  onClose?: () => void;
}) {
  const { node, path } = props;
  const all = usePrefs(path);
  const prefs = effective(defaultsOf(node), all, node.id);
  const [box, visible] = useVisible();
  const [width, setWidth] = useState(0);
  const [zoom, setZoom] = useState<[number, number] | null>(null);
  const call = visible ? seriesCall(node, prefs, zoom, Math.round(width / 50) * 50) : null;
  const result = useCall(call);
  const theme = useTheme();
  const colors = useRunColors();
  const el = useRef<HTMLDivElement>(null);
  const chart = useRef<LineChart | null>(null);
  const log = prefs.scale === "log";
  // while a new call (a zoom, a setting) loads, the legend keeps the last answer; the chart
  // waits for the new data, so a zoom never snaps back in between.
  const last = useRef<any>(null);
  if (result.data) last.current = result.data;
  const curves = last.current ? reshape(last.current, { log }) : null;
  const smoothed = curves && prefs.smooth > 0 ? smooth(curves, prefs.smooth) : curves;
  const hidden = new Set(all.hidden);
  const palette = curves && theme ? colorsFor(curves, theme, colors) : [];

  useEffect(() => {
    if (!el.current) return;
    const ro = new ResizeObserver(([e]) => setWidth(e.contentRect.width));
    ro.observe(el.current);
    return () => ro.disconnect();
  }, [el.current]);

  useEffect(() => {
    if (!result.data || !smoothed || !theme || !el.current || !smoothed.curves.length) return;
    const shown = smoothed.curves.filter((c) => !hidden.has(c.key) && !(c.run && hidden.has(c.run)));
    const range = prefs.outliers ? robustRange(align(shown).y, log) : null;
    const spec: LineSpec = {
      curves: smoothed.curves,
      raw: prefs.smooth > 0 ? curves!.curves : null,
      colors: palette,
      hidden,
      style: chartStyle(theme),
      height: props.height,
      log,
      band: (smoothed.aggregated || smoothed.curves.length === 1) && prefs.band !== "none",
      range,
      zoom,
      zoomFetched: prefs.x === "_step",
      sync: `view:${path}`,
      formatX: formatterFor(prefs.x),
      formatY: (v) => value(v),
      onFocus: (c) => hovered.set(c?.run ?? null),
      onZoom: (w) => setZoom(w),
    };
    if (chart.current?.update(spec)) return;
    let cancelled = false;
    chart.current?.destroy();
    chart.current = null;
    el.current.replaceChildren();
    void lineChart(el.current, spec).then((c) => {
      if (cancelled) c.destroy();
      else chart.current = c;
    });
    return () => {
      cancelled = true;
    };
  }, [result.data, theme, colors, JSON.stringify(prefs), all.hidden, zoom]);

  useEffect(() => () => chart.current?.destroy(), []);
  useEffect(
    () =>
      hovered.subscribe((run) => {
        if (chart.current && !el.current?.matches(":hover")) chart.current.focus(run);
      }),
    [],
  );

  const title = (prefs.y?.length ? prefs.y : [node.props.y]).join(", ");
  const notes = [
    prefs.by === "seeds" ? "seed mean" : prefs.by ? `by ${label(prefs.by)}` : null,
    prefs.smooth > 0 ? `smoothed ${prefs.smooth.toFixed(2)}` : null,
    prefs.x !== "_step" ? X_AXES.find(([k]) => k === prefs.x)?.[1] : null,
    node.props.note && !prefs.by && !node.props.note.startsWith("seed") ? node.props.note : null,
  ].filter(Boolean);
  const keys = curves?.curves.map((c) => c.run ?? c.key) ?? [];
  const empty = curves && !curves.curves.length;
  const download = (kind: "png" | "csv") => {
    if (!smoothed) return;
    const name = title.replace(/[^\w.-]+/g, "_");
    const href = kind === "png" ? chart.current?.png(String(theme?.colors.bg ?? "#fff")) : csv(smoothed);
    if (!href) return;
    const a = document.createElement("a");
    a.href = href;
    a.download = `${name}.${kind}`;
    a.click();
  };

  return html`<div ref=${box} class=${`chart-frame${props.expanded ? " expanded" : ""}`}>
    <div class="chart-head">
      <span class="chart-title">${title}</span>
      ${notes.length ? html`<span class="muted small">${notes.join(" · ")}</span>` : null}
      <span class="chart-tools">
        ${zoom ? html`<${IconButton} icon="reset" label="Reset zoom (double-click)" onClick=${() => setZoom(null)} />` : null}
        <${Settings} node=${node} path=${path} prefs=${prefs} />
        <${Popover} icon="download" label="Download" title="Download">
          <div class="menu-list">
            <button type="button" onClick=${() => download("png")}><${Icon} name="image" size=${15} /> PNG image</button>
            <button type="button" onClick=${() => download("csv")}><${Icon} name="file-text" size=${15} /> CSV data</button>
          </div>
        <//>
        ${props.onExpand ? html`<${IconButton} icon="maximize" label="Expand" onClick=${props.onExpand} />` : null}
        ${props.onClose ? html`<${IconButton} icon="x" label="Close (Esc)" onClick=${props.onClose} />` : null}
        ${node.props.added
          ? html`<${IconButton} icon="x" label="Remove this chart" onClick=${() => update(path, (p) => ({ added: p.added.filter((m) => m !== node.props.y) }))} />`
          : null}
      </span>
    </div>
    <${Panel} result=${result}>
      ${empty
        ? html`<${Notice}>No run in scope logs ${title}.<//>`
        : html`<div class=${`chart${result.status === "ready" && !result.refreshing ? "" : " pending"}`} ref=${el}
            style=${`min-block-size:${props.height}px`}></div>`}
    <//>
    ${curves && curves.curves.length > 1 && curves.curves.length <= LEGEND_MAX
      ? html`<div class="legend" role="group" aria-label="Show or hide curves">
          ${curves.curves.map((c, i) => {
            const k = c.run ?? c.key;
            const off = hidden.has(k);
            return html`<button type="button" class=${`legend-item${off ? " off" : ""}`} aria-pressed=${!off}
                data-tip="Click to hide or show; shift-click to show only this"
                onPointerEnter=${() => c.run && hovered.set(c.run)} onPointerLeave=${() => hovered.set(null)}
                onClick=${(e: MouseEvent) => toggleRun(path, k, keys, e.shiftKey)}>
              <span class="legend-dot" style=${`background:${palette[i]}`}></span>${c.label}</button>`;
          })}
        </div>`
      : null}
  </div>`;
}

function Settings(props: { node: Node; path: string; prefs: ReturnType<typeof effective> }) {
  const { node, path, prefs } = props;
  const [opened, setOpened] = useState(false);
  // what to offer comes from keys, asked only once the settings are opened.
  const keys = useCall(opened ? { method: "keys", params: { from: path }, scope: path } : null).data;
  const metrics: string[] = keys?.metrics?.rows.map((r: unknown[]) => r[0]) ?? [];
  const varying: string[] = (keys?.config?.rows ?? [])
    .filter((r: any[]) => Array.isArray(r[2]) && r[2].length > 1)
    .map((r: any[]) => r[0])
    .filter((k: string) => k !== "config.seed");
  const set = (p: ChartPrefs) => setChart(path, node.id, p);
  const y = prefs.y?.length ? prefs.y : [node.props.y];
  const toggleMetric = (m: string) => {
    const next = y.includes(m) ? y.filter((x) => x !== m) : [...y, m];
    if (next.length) set({ y: next });
  };
  return html`<${Popover} icon="sliders" label="Chart settings" title="This chart" class="chart-settings"
      onOpen=${() => setOpened(true)}>
    <div class="field"><span class="field-label">Metrics</span>
      <div class="checks">${metrics.map((m) => html`<label><input type="checkbox" checked=${y.includes(m)} onChange=${() => toggleMetric(m)} /> ${m}</label>`)}</div>
    </div>
    <${Controls} prefs=${prefs} varying=${varying} set=${set} />
    <button type="button" class="link small" onClick=${() => setChart(path, node.id, null)}>Reset this chart</button>
  <//>`;
}

// the controls shared by a chart's settings and the view-wide bar.
export function Controls(props: { prefs: ChartPrefs; varying: string[]; set: (p: ChartPrefs) => void; compact?: boolean }) {
  const { prefs, set } = props;
  const by = prefs.by ?? "";
  return html`
    <label class="field"><span class="field-label">Smoothing <b class="num">${(prefs.smooth ?? 0).toFixed(2)}</b></span>
      <input type="range" min="0" max="0.99" step="0.01" value=${prefs.smooth ?? 0}
        onInput=${(e: Event) => set({ smooth: Number((e.target as HTMLInputElement).value) })} /></label>
    <label class="field"><span class="field-label">x axis</span>
      <select value=${prefs.x ?? "_step"} onChange=${(e: Event) => set({ x: (e.target as HTMLSelectElement).value as ChartPrefs["x"] })}>
        ${X_AXES.map(([k, l]) => html`<option value=${k}>${l}</option>`)}
      </select></label>
    <label class="field"><span class="field-label">Aggregate</span>
      <select value=${by} onChange=${(e: Event) => set({ by: (e.target as HTMLSelectElement).value || null })}>
        <option value="">each run</option>
        <option value="seeds">mean over seeds</option>
        ${props.varying.map((k) => html`<option value=${k}>by ${label(k)}</option>`)}
      </select></label>
    ${by && !props.compact
      ? html`<label class="field"><span class="field-label">Band</span>
          <select value=${prefs.band ?? "minmax"} onChange=${(e: Event) => set({ band: (e.target as HTMLSelectElement).value as ChartPrefs["band"] })}>
            <option value="minmax">min to max</option><option value="std">± std</option>
            <option value="stderr">± std error</option><option value="none">none</option>
          </select></label>`
      : null}
    ${props.compact
      ? null
      : html`<label class="field inline"><input type="checkbox" checked=${prefs.scale === "log"}
          onChange=${(e: Event) => set({ scale: (e.target as HTMLInputElement).checked ? "log" : "linear" })} /> log scale</label>`}
    <label class="field inline"><input type="checkbox" checked=${!!prefs.outliers}
      onChange=${(e: Event) => set({ outliers: (e.target as HTMLInputElement).checked })} /> ignore outliers</label>`;
}

function formatterFor(x: string): (v: number) => string {
  switch (x) {
    case "_elapsed":
      return (v) => duration(v);
    case "_t":
      return (v) => new Date(v * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    default:
      return step;
  }
}

function colorsFor(curves: Curves, theme: Theme, colors: Map<string, string>): string[] {
  if (curves.aggregated) {
    const byLabel = groupColors(curves.curves.map((c) => c.label), theme);
    return curves.curves.map((c) => byLabel.get(JSON.stringify(c.label))!);
  }
  const cat = theme.data.categorical;
  return curves.curves.map((c, i) => (c.run && colors.get(c.run)) || cat[i % cat.length]);
}

export function csv(c: Curves): string {
  const al = align(c.curves);
  const quote = (s: string) => (/[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s);
  const head = ["x", ...c.curves.map((cv) => quote(cv.label))].join(",");
  const body = al.x.map((x, i) => [x, ...al.y.map((ys) => ys[i] ?? "")].join(","));
  return `data:text/csv;charset=utf-8,${encodeURIComponent([head, ...body].join("\n"))}`;
}
