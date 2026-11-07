// `line`: metric curves on uPlot, W&B-style: synced crosshair, shared hover focus, legend
// toggles, drag-zoom with an exact refetch of the window, smoothing, and settings per chart.

import { html } from "htm/preact";
import { useContext, useEffect, useMemo, useRef, useState } from "preact/hooks";

import { type Call, useCall } from "../api.ts";
import { hovered, useRunColors, useTheme, useVisible, ViewCtx, type Node } from "../bt/index.ts";
import { xTitle, yTitle } from "../bt/axes.ts";
import { align, linthresh, reshape, robustRange, smooth, type Curve, type Curves } from "../bt/curves.ts";
import { png, useChart } from "../bt/chart.ts";
import { fileName, light, paper, recolor, type Background } from "../bt/export.ts";
import { ChartFrame, expandedHeight, HEIGHT, Legend, type LegendItem } from "../bt/frame.ts";
import { host } from "../bt/host.ts";
import { duration, label, step, value } from "../bt/fmt.ts";
import { lineChart, type LineSpec } from "../bt/plot.ts";
import { effective, toggleRun, update, usePrefs, type ChartPrefs, type Effective } from "../bt/prefs.ts";
import { chartStyle, dashOf, groupColors, palette as paletteOf, swatch, type Theme } from "../bt/theme.ts";
import { groupUrl, navigate } from "../router.ts";
import { IconButton } from "../ui/primitives.ts";
import { Notice, Panel } from "./common.ts";
import { LINE_FIELDS, Settings } from "./line-settings.ts";
import { EXPORTED } from "../snapshot.ts";

const LEGEND_MAX = 12;

export function Line({ node }: { node: Node }) {
  const view = useContext(ViewCtx);
  return html`<div class="block chart-block">
    ${node.props.expanded
      ? html`<${Chart} node=${node} path=${view.path} height=${expandedHeight()} expanded />`
      : html`<${Chart} node=${node} path=${view.path} height=${HEIGHT} onExpand=${() => host().expand(node, view)} />`}
  </div>`;
}

// the series call a chart makes: the node's call with the viewer's settings applied.
export function seriesCall(node: Node, prefs: Effective, zoom: [number, number] | null, width: number): Call {
  const base = node.data!.main;
  const params: Record<string, unknown> = { ...base.params };
  params.y = prefs.y?.length ? prefs.y : metricsOf(node);
  params.x = prefs.x;
  params.points = Math.max(100, Math.min(1500, Math.round(width || 600)));
  params.band = prefs.band;
  delete params.seeds;
  delete params.by;
  delete params.steps;
  if (prefs.by === "seeds") params.seeds = "config.seed";
  else if (prefs.by) params.by = [prefs.by];
  // an exported page has no server to ask for the window: it zooms into the stored curve.
  if (zoom && prefs.x === "_step" && !EXPORTED) params.steps = [Math.floor(zoom[0]), Math.ceil(zoom[1])];
  else if (prefs.steps && (prefs.steps[0] !== null || prefs.steps[1] !== null)) params.steps = prefs.steps;
  return { ...base, params };
}

// a line node's metrics: one key, or several in an authored view.
export function metricsOf(node: Node): string[] {
  return Array.isArray(node.props.y) ? node.props.y : [node.props.y];
}

function defaultsOf(node: Node): ChartPrefs {
  const params = node.data?.main.params ?? {};
  const p = node.props;
  return {
    smooth: p.smooth ?? undefined,
    x: p.x ?? undefined,
    outliers: p.outliers ?? undefined,
    raw: p.raw ?? undefined,
    legend: p.legend ?? undefined,
    ymin: p.ymin ?? undefined,
    ymax: p.ymax ?? undefined,
    scale: p.scale === "log" || p.scale === "symlog" ? p.scale : "linear",
    by: params.seeds ? "seeds" : Array.isArray(params.by) ? (params.by as string[])[0] : null,
    band: (params.band as ChartPrefs["band"]) ?? "minmax",
    steps: Array.isArray(params.steps) ? (params.steps as [number | null, number | null]) : null,
  };
}

function Chart(props: {
  node: Node;
  path: string;
  height: number;
  expanded?: boolean;
  onExpand?: () => void;
}) {
  const { node, path } = props;
  const all = usePrefs(path);
  const prefs = effective(defaultsOf(node), all, node.id);
  const [box, visible] = useVisible();
  const [width, setWidth] = useState(0);
  const [zoom, setZoom] = useState<[number, number] | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const call = visible ? seriesCall(node, prefs, zoom, Math.round(width / 50) * 50) : null;
  const result = useCall(call);
  const theme = useTheme();
  const runs = useRunColors();
  // colored by a field: each run takes the color of its value.
  const byField = useCall(node.props.color && visible ? node.data?.colors ?? null : null).data;
  const colors = useMemo(() => (byField && theme ? fieldColors(byField, node.props.color, theme) : runs), [byField, theme, runs]);
  const el = useRef<HTMLDivElement>(null);
  const log = prefs.scale === "log";
  // while a new call (a zoom, a setting) loads, the legend keeps the last answer; the chart
  // waits for the new data, so a zoom never snaps back in between.
  const last = useRef<any>(null);
  if (result.data) last.current = result.data;
  const curves = last.current ? reshape(last.current, { log }) : null;
  const smoothed = curves && prefs.smooth > 0 ? smooth(curves, prefs.smooth) : curves;
  const hidden = new Set(all.hidden);
  const isShown = (c: Curve) => !hidden.has(c.key) && !(c.run && hidden.has(c.run));

  const metrics = useContext(ViewCtx).metrics;
  const shownMetrics = prefs.y?.length ? prefs.y : metricsOf(node);
  // a title the view wrote stands until the viewer picks another x or other metrics.
  const xlabel = (prefs.x === (node.props.x ?? "_step") ? node.props.xlabel : undefined) ?? xTitle(prefs.x, metrics);
  const ylabel = (prefs.y?.length ? undefined : node.props.ylabel) ?? yTitle(shownMetrics, metrics);
  const trajectory = !!curves?.curves.some((c) => !c.monotone);

  // the spec for a theme: the page's, or the light one for exported figures.
  const specFor = (t: Theme, height: number, palette: string[]): LineSpec | null => {
    if (!smoothed || !curves || !smoothed.curves.length) return null;
    const shown = smoothed.curves.filter(isShown);
    const fixed = prefs.ymin !== undefined && prefs.ymin !== null || prefs.ymax !== undefined && prefs.ymax !== null;
    const range = fixed ? [prefs.ymin ?? null, prefs.ymax ?? null] as [number | null, number | null]
      : prefs.outliers ? robustRange(align(shown).y, log) : null;  // prettier-ignore
    return {
      curves: smoothed.curves,
      raw: prefs.smooth > 0 && prefs.raw ? curves.curves : null,
      colors: palette,
      dashes: palette.map((c) => dashOf(c, t)),
      hidden,
      style: chartStyle(t),
      height,
      scale: prefs.scale,
      asinh: prefs.scale === "symlog" ? linthresh(align(shown).y) : 1,
      band: (smoothed.aggregated || smoothed.curves.length === 1) && prefs.band !== "none" && !trajectory,
      range,
      zoom,
      zoomFetched: prefs.x === "_step" && !EXPORTED,
      sync: `view:${path}`,
      xlabel,
      ylabel,
      xTime: prefs.x === "_t",
      trajectory,
      formatX: formatterFor(prefs.x),
      formatY: (v) => value(v),
      formatStep: step,
    };
  };
  const palette = curves && theme ? colorsFor(curves, theme, colors) : [];

  useEffect(() => {
    if (!el.current) return;
    const ro = new ResizeObserver(([e]) => setWidth(e.contentRect.width));
    ro.observe(el.current);
    return () => ro.disconnect();
  }, [el.current]);

  const base = result.data && theme ? specFor(theme, props.height, palette) : null;
  const spec: LineSpec | null = base && {
    ...base,
    onFocus: (c) => hovered.set(c ? (c.run ?? (c.group !== null ? `by:${c.group}` : null)) : null),
    onZoom: (w) => setZoom(w),
    onClick: (c) => c.run && navigate(groupUrl(path, { run: c.run }), { replace: true }),
  };
  useChart(el, lineChart, spec, [result.data, colors, JSON.stringify(prefs), all.hidden, zoom], theme);

  const named = shownMetrics.map((m) => metrics[m]?.label ?? m).join(", ");
  const title = prefs.y?.length ? named : node.props.title ?? named;
  const keys = curves?.curves.map((c) => c.run ?? c.key) ?? [];
  const off = curves ? curves.curves.filter((c) => !isShown(c)).length : 0;
  const notes = [
    prefs.by === "seeds" ? "seed mean" : prefs.by ? `by ${label(prefs.by)}` : null,
    prefs.smooth > 0 ? `smoothed ${prefs.smooth.toFixed(2)}` : null,
    prefs.x !== "_step" ? xTitle(prefs.x, metrics) : null,
    prefs.scale !== "linear" ? prefs.scale : null,
    node.props.note && !prefs.by && !node.props.note.startsWith("seed") ? node.props.note : null,
    node.props.color ? `colored by ${label(node.props.color)}` : null,
  ].filter(Boolean);
  const empty = curves && !curves.curves.length;

  const exportPng = async (background: Background) => {
    const t = light();
    if (!t || !theme || !el.current) return;
    const figure = specFor(t, paper.size?.height ?? props.height, palette.map((c) => recolor(c, theme, t)));
    if (!figure) return;
    host().download(await png(el.current.clientWidth, lineChart, figure, background), fileName(title, "png"));
  };
  const exportPdf = async () => {
    const t = light();
    if (!t || !theme || !smoothed) return;
    const band = (smoothed.aggregated || smoothed.curves.length === 1) && prefs.band !== "none" && !trajectory;
    const series = smoothed.curves.filter(isShown);
    setProblem(null);
    try {
      await host().figure({
        kind: "line",
        title,
        xlabel,
        ylabel,
        yscale: prefs.scale,
        ylim: [prefs.ymin ?? null, prefs.ymax ?? null],
        series: series.map((c) => ({ label: c.label, x: c.x, y: c.y, ...(band ? { lo: c.lo, hi: c.hi } : {}) })),
      }, fileName(title, "pdf"));  // prettier-ignore
    } catch (err) {
      setProblem((err as Error).message);
    }
  };
  const exportCsv = () => smoothed && host().download(csv(smoothed), fileName(title, "csv"));

  // what the renderer's layout check counts; aggregated or colored charts tame many runs.
  const visibleCurves = curves?.aggregated || node.props.color ? 0 : curves?.curves.filter(isShown).length;
  const items: LegendItem[] =
    prefs.legend && curves && curves.curves.length > 1 && curves.curves.length <= LEGEND_MAX
      ? curves.curves.map((c, i) => {
          const k = c.run ?? c.key;
          const target = c.run ?? (c.group !== null ? `by:${c.group}` : null);
          return {
            label: c.label,
            mark: swatch(palette[i], theme),
            off: hidden.has(k),
            tip: "Click to hide or show; double-click to show only this",
            onHover: (on) => hovered.set(on ? target : null),
            onClick: (e) => e.detail < 2 && toggleRun(path, k, keys),
            onDblClick: () => toggleRun(path, k, keys, true),
          };
        })
      : [];
  return html`<${ChartFrame} id=${node.id} title=${title} notes=${notes} box=${box} curves=${visibleCurves}
      expanded=${props.expanded} onExpand=${props.onExpand}
      onRemove=${node.props.added ? () => update(path, (p) => ({ added: p.added.filter((m) => m !== node.props.y) })) : undefined}
      downloads=${{ png: exportPng, pdf: exportPdf, csv: exportCsv }}
      status=${off ? html`<button type="button" class="link small" onClick=${() => update(path, () => ({ hidden: [] }))}>${off} hidden · show all</button>` : null}
      tools=${html`${zoom ? html`<${IconButton} icon="reset" label="Reset zoom (double-click)" onClick=${() => setZoom(null)} />` : null}
        <${Settings} node=${node} path=${path} prefs=${prefs} y=${shownMetrics} fields=${LINE_FIELDS} />`}
      legend=${items.length ? html`<${Legend} items=${items} label="Show or hide curves" role="group" />` : null}
      caption=${props.expanded ? undefined : node.props.caption}>
    ${problem ? html`<p class="block-error small">${problem}</p>` : null}
    <${Panel} result=${result}>
      ${empty
        ? html`<${Notice}>No run in scope logs ${title}.<//>`
        : html`<div class=${`chart-plot${result.status === "ready" && !result.refreshing ? "" : " pending"}`} ref=${el}
            style=${`min-block-size:${props.height}px`}></div>`}
    <//>
  <//>`;
}

function formatterFor(x: string): (v: number) => string {
  switch (x) {
    case "_elapsed":
      return (v) => duration(v);
    case "_t":
      return (v) => new Date(v * 1000).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit" });
    default:
      return step;
  }
}

function fieldColors(answer: { columns: string[]; rows: unknown[][] }, field: string, theme: Theme): Map<string, string> {
  const id = answer.columns.indexOf("run.id");
  const at = answer.columns.indexOf(field);
  const byValue = groupColors(answer.rows.map((r) => r[at]), theme);
  return new Map(answer.rows.map((r) => [String(r[id]), byValue.get(JSON.stringify(r[at])) ?? theme.colors["data-1"]]));
}

function colorsFor(curves: Curves, theme: Theme, colors: Map<string, string>): string[] {
  if (curves.aggregated) {
    const byLabel = groupColors(curves.curves.map((c) => c.label), theme);
    return curves.curves.map((c) => byLabel.get(JSON.stringify(c.label))!);
  }
  const cat = paletteOf(theme);
  // one run's several metrics: the metric is what tells the curves apart.
  if (curves.curves.length > 1 && new Set(curves.curves.map((c) => c.run)).size === 1) return curves.curves.map((_, i) => cat[i % cat.length]);
  return curves.curves.map((c, i) => (c.run && colors.get(c.run)) || cat[i % cat.length]);
}

export function csv(c: Curves): string {
  const al = align(c.curves);
  const quote = (s: string) => (/[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s);
  const head = ["x", ...c.curves.map((cv) => quote(cv.label))].join(",");
  const body = al.x.map((x, i) => [x, ...al.y.map((ys) => ys[i] ?? "")].join(","));
  return `data:text/csv;charset=utf-8,${encodeURIComponent([head, ...body].join("\n"))}`;
}
