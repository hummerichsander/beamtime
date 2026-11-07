// One value per run, drawn on uPlot's axes: `scatter` (with seeds as means and a fit), `bar`
// (grouped, with error bars) and `histogram` (logged distributions as outlines per run).

import { html } from "htm/preact";
import { useContext, useRef, useState } from "preact/hooks";

import { fieldTitle, metricTitle } from "../bt/axes.ts";
import { png, useChart } from "../bt/chart.ts";
import { host } from "../bt/host.ts";
import { hovered, useData, useRunColors, useTheme, useVisible, ViewCtx, type Node } from "../bt/index.ts";
import { label, step, value } from "../bt/fmt.ts";
import { plotChart, type PlotSpec } from "../bt/plot.ts";
import { bars, extent, fit, histograms, logSplits, points, type Bar, type Point } from "../bt/shapes.ts";
import { linthresh } from "../bt/curves.ts";
import { fileName, light, paper, recolor, type Background } from "../bt/export.ts";
import { alpha, chartStyle, groupColors, palette, swatch, type Theme } from "../bt/theme.ts";
import { groupUrl, navigate } from "../router.ts";
import type { TipRow } from "../bt/uplot.ts";
import { ChartFrame, expandedHeight, Legend, type LegendItem } from "../bt/frame.ts";
import { Notice, Panel } from "./common.ts";

const HEIGHT = 260;

export function Scatter({ node }: { node: Node }) {
  const p = node.props;
  const result = useData("main");
  const view = useContext(ViewCtx);
  const colors = useRunColors();
  const pts = points(result.data, p.x, p.y, p.color);
  const xLog = p.x_scale === "log";
  const yLog = p.y_scale === "log";
  const xSym = p.x_scale === "symlog" ? linthresh([pts.map((q) => q.x)]) : undefined;
  const ySym = p.y_scale === "symlog" ? linthresh([pts.map((q) => q.y)]) : undefined;
  const xlabel = p.xlabel ?? fieldTitle(p.x, view.metrics);
  const ylabel = p.ylabel ?? fieldTitle(p.y, view.metrics);
  const make = (theme: Theme, height: number): PlotSpec | null => {
    const xr = extent(pts.map((q) => q.x), xLog);
    const yr = extent(pts.flatMap((q) => (q.err ? [q.y - q.err, q.y + q.err] : [q.y])), yLog);
    if (!xr || !yr) return null;
    const byValue = p.color ? groupColors(pts.map((q) => q.color), theme) : null;
    const colorOf = (q: Point): string =>
      byValue?.get(JSON.stringify(q.color)) ?? theme.colors["data-1"];
    const line = p.fit ? fit(pts, p.fit) : null;
    const bg = theme.colors.paper;
    return {
      style: chartStyle(theme),
      height,
      x: { range: xr, log: xLog, symlog: xSym, format: value, label: xlabel, ...(xLog ? { splits: logSplits(xr) } : {}) },
      y: { range: yr, log: yLog, symlog: ySym, format: value, label: ylabel, ...(yLog ? { splits: logSplits(yr) } : {}) },
      draw: ({ ctx, x, y, px, focused }) => {
        if (line) {
          ctx.beginPath();
          ctx.setLineDash([5 * px, 4 * px]);
          ctx.strokeStyle = String(theme.colors.muted);
          ctx.lineWidth = 1.25 * px;
          samples(xr, xLog).forEach((v, i) => (i ? ctx.lineTo(x(v), y(line(v))) : ctx.moveTo(x(v), y(line(v)))));
          ctx.stroke();
          ctx.setLineDash([]);
        }
        for (const q of pts) {
          const c = colorOf(q);
          const dim = focused !== null && !q.runs.includes(focused);
          ctx.globalAlpha = dim ? chartStyle(theme).dim + 0.15 : 1;
          if (q.err) {
            ctx.beginPath();
            ctx.strokeStyle = c;
            ctx.lineWidth = 1.5 * px;
            ctx.moveTo(x(q.x), y(q.y - q.err));
            ctx.lineTo(x(q.x), y(q.y + q.err));
            ctx.stroke();
          }
          ctx.beginPath();
          ctx.arc(x(q.x), y(q.y), (q.runs.includes(focused ?? "") ? 6 : 4.5) * px, 0, 2 * Math.PI);
          ctx.fillStyle = c;
          ctx.fill();
          ctx.lineWidth = 2 * px;
          ctx.strokeStyle = bg;
          ctx.stroke();
        }
        ctx.globalAlpha = 1;
      },
      hit: (left, top, x, y) => {
        let best: Point | null = null;
        let d = 14;
        for (const q of pts) {
          const dq = Math.hypot(x(q.x) - left, y(q.y) - top);
          if (dq < d) [best, d] = [q, dq];
        }
        if (!best) return null;
        const rows: TipRow[] = [
          { label: best.runs.length > 1 ? `mean of ${best.n} seeds` : view.names.get(best.key) ?? best.key, value: "", color: colorOf(best), strong: true },
          { label: label(p.x), value: value(best.x), color: null },
          { label: label(p.y), value: `${value(best.y)}${best.err ? ` ± ${value(best.err)}` : ""}`, color: null },
          ...(p.color ? [{ label: label(p.color), value: value(best.color), color: null }] : []),
        ];
        return { key: best.key, rows };
      },
      onFocus: (key) => hovered.set(key),
      onClick: (key) => navigate(groupUrl(view.path, { run: key }), { replace: true }),
    };
  };
  const figure = () => {
    const groups = new Map<string, Point[]>();
    for (const q of pts) groups.set(JSON.stringify(q.color), [...(groups.get(JSON.stringify(q.color)) ?? []), q]);
    const line = p.fit ? fit(pts, p.fit) : null;
    const xr = extent(pts.map((q) => q.x), xLog);
    return {
      kind: "scatter",
      xlabel,
      ylabel,
      xscale: p.x_scale,
      yscale: p.y_scale,
      series: [...groups.entries()].map(([k, qs]) => ({
        label: p.color ? `${label(p.color)}=${value(JSON.parse(k))}` : null,
        x: qs.map((q) => q.x),
        y: qs.map((q) => q.y),
        err: qs.map((q) => q.err),
      })),
      fit: line && xr ? { x: samples(xr, xLog), y: samples(xr, xLog).map(line) } : null,
    };
  };
  const few = result.data && pts.length < 2;
  const legend = p.color && pts.length ? html`<${ValueLegend} values=${pts.map((q) => q.color)} field=${p.color} />` : null;
  return html`<${PlotFrame} node=${node} result=${result} make=${few ? null : make} figure=${few ? undefined : figure}
      deps=${[result.data, colors]} empty=${few ? `Fewer than two runs log ${label(p.x)} and ${label(p.y)}.` : null}
      legend=${legend} />`;
}

export function BarBlock({ node }: { node: Node }) {
  const p = node.props;
  const result = useData("main");
  const view = useContext(ViewCtx);
  const xlabel = p.xlabel ?? fieldTitle(p.x, view.metrics);
  const ylabel = p.ylabel ?? fieldTitle(p.y, view.metrics);
  const items = bars(result.data, p.x, p.y, p.by ?? null, p.error ?? "std", p.sort ?? "x");
  const cats = [...new Set(items.map((b) => b.label))];
  const groups = [...new Set(items.map((b) => b.group))];
  const make = (theme: Theme, height: number): PlotSpec | null => {
    const values = items.flatMap((b) => [b.lo, b.hi, b.value]);
    if (!items.length) return null;
    const lo = Math.min(0, ...values);
    const hi = Math.max(0, ...values);
    const pad = (hi - lo || 1) * 0.06;
    // without by, each category takes its value's color, as lines aggregated by the same field do.
    const byValue = groupColors(p.by ? groups : cats.map(numberOr), theme);
    const colorOf = (b: Bar) => byValue.get(JSON.stringify(p.by ? b.group : numberOr(b.label))) ?? theme.colors["data-1"];
    const w = 0.76 / groups.length;
    const center = (b: Bar) => cats.indexOf(b.label) - 0.38 + (groups.indexOf(b.group) + 0.5) * w;
    return {
      style: chartStyle(theme),
      height,
      x: { range: [-0.6, cats.length - 0.4], log: false, format: (v) => cats[Math.round(v)] ?? "", label: xlabel, splits: cats.map((_, i) => i) },
      y: { range: [lo < 0 ? lo - pad : 0, hi + pad], log: false, format: value, label: ylabel },
      draw: ({ ctx, x, y, px, focused }) => {
        for (const b of items) {
          const c = colorOf(b);
          const [x0, x1] = [x(center(b) - w * 0.44), x(center(b) + w * 0.44)];
          // focused is this chart's own bar, or a run hovered anywhere on the page.
          const lit = focused === keyOf(b) || (focused !== null && b.runs.includes(focused));
          ctx.globalAlpha = focused !== null && !lit ? 0.45 : 1;
          ctx.fillStyle = c;
          ctx.beginPath();
          ctx.roundRect(x0, Math.min(y(b.value), y(0)), x1 - x0, Math.abs(y(0) - y(b.value)), 3 * px);
          ctx.fill();
          if (b.hi > b.lo) {
            const xm = x(center(b));
            const cap = Math.min(6 * px, (x1 - x0) / 4);
            ctx.beginPath();
            ctx.strokeStyle = theme.colors.ink;
            ctx.lineWidth = 1.25 * px;
            ctx.moveTo(xm, y(b.lo));
            ctx.lineTo(xm, y(b.hi));
            ctx.moveTo(xm - cap, y(b.lo));
            ctx.lineTo(xm + cap, y(b.lo));
            ctx.moveTo(xm - cap, y(b.hi));
            ctx.lineTo(xm + cap, y(b.hi));
            ctx.stroke();
          }
        }
        ctx.globalAlpha = 1;
      },
      hit: (left, _top, x) => {
        const b = items.find((it) => Math.abs(x(center(it)) - left) <= Math.abs(x(center(it) + w / 2) - x(center(it))));
        if (!b) return null;
        const err = p.error === "none" || b.n < 2 ? "" : ` (${value(b.lo)} to ${value(b.hi)})`;
        return {
          key: keyOf(b),
          rows: [
            { label: `${label(p.x)} ${b.label}${b.group !== null ? ` · ${label(p.by)} ${b.group}` : ""}`, value: "", color: colorOf(b), strong: true },
            { label: `${label(p.y)}, mean of ${b.n}`, value: `${value(b.value)}${err}`, color: null },
          ],
        };
      },
    };
  };
  const figure = () => {
    return {
      kind: "bar",
      xlabel,
      ylabel,
      categories: cats,
      groups: groups.map((g) => {
        const of = (c: string) => items.find((b) => b.label === c && b.group === g) ?? null;
        return {
          label: p.by ? `${label(p.by)}=${g}` : null,
          value: cats.map((c) => of(c)?.value ?? null),
          lo: cats.map((c) => (p.error === "none" ? null : of(c)?.lo ?? null)),
          hi: cats.map((c) => (p.error === "none" ? null : of(c)?.hi ?? null)),
        };
      }),
    };
  };
  const legend = p.by ? html`<${ValueLegend} values=${groups} field=${p.by} />` : null;
  return html`<${PlotFrame} node=${node} result=${result} make=${make} figure=${figure} deps=${[result.data]}
      empty=${result.data && !items.length ? `No run logs ${label(p.y)}.` : null} legend=${legend} />`;
}

export function HistogramBlock({ node }: { node: Node }) {
  const result = useData("main");
  const view = useContext(ViewCtx);
  const colors = useRunColors();
  const page = useTheme();
  const hs = histograms(result.data);
  const xlabel = node.props.xlabel ?? metricTitle(node.props.key, view.metrics);
  const ylabel = node.props.ylabel ?? "count";
  // run colors are the page theme's; an exported figure takes the same slots of its own.
  const runColor = (run: string, i: number, t: Theme) => {
    const c = colors.get(run);
    return c && page ? recolor(c, page, t) : palette(t)[i % palette(t).length];
  };
  const figure = () => ({
    kind: "histogram",
    xlabel,
    ylabel,
    series: hs.map((h) => ({ label: view.names.get(h.run) ?? h.run, start: h.start, end: h.end, count: h.count })),
  });
  const make = (theme: Theme, height: number): PlotSpec | null => {
    const xr = extent(hs.flatMap((h) => [...h.start, ...h.end]), false, 0);
    const top = Math.max(0, ...hs.flatMap((h) => h.count));
    if (!xr || !top) return null;
    const colorOf = (run: string, i: number) => runColor(run, i, theme);
    return {
      style: chartStyle(theme),
      height,
      x: { range: xr, log: false, format: value, label: xlabel },
      y: { range: [0, top * 1.06], log: false, format: value, label: ylabel },
      draw: ({ ctx, x, y, px, focused }) => {
        hs.forEach((h, i) => {
          const c = colorOf(h.run, i);
          const dim = focused !== null && focused !== h.run;
          ctx.beginPath();
          ctx.moveTo(x(h.start[0]), y(0));
          h.count.forEach((n, k) => {
            ctx.lineTo(x(h.start[k]), y(n));
            ctx.lineTo(x(h.end[k]), y(n));
          });
          ctx.lineTo(x(h.end[h.end.length - 1]), y(0));
          ctx.fillStyle = alpha(c, dim ? 0.03 : hs.length > 1 ? 0.1 : 0.25);
          ctx.fill();
          ctx.strokeStyle = dim ? alpha(c, 0.3) : c;
          ctx.lineWidth = (focused === h.run ? 2.5 : 1.5) * px;
          ctx.stroke();
        });
      },
      hit: (left, _top, x) => {
        const rows: TipRow[] = [];
        let first: string | null = null;
        hs.forEach((h, i) => {
          const k = h.start.findIndex((s, j) => x(s) <= left && left <= x(h.end[j]));
          if (k < 0) return;
          if (!rows.length) rows.push({ label: `${value(h.start[k])} to ${value(h.end[k])}`, value: "", color: null, strong: true });
          first ??= h.run;
          rows.push({ label: view.names.get(h.run) ?? h.run, value: value(h.count[k]), color: colorOf(h.run, i) });
        });
        return rows.length ? { key: hs.length === 1 ? first : null, rows: rows.slice(0, 13) } : null;
      },
      onFocus: (key) => hovered.set(key),
    };
  };
  const steps = [...new Set(hs.map((h) => h.step))];
  const note = steps.length === 1 && steps[0] !== null ? `step ${step(steps[0])}` : null;
  return html`<${PlotFrame} node=${node} result=${result} make=${make} figure=${figure} deps=${[result.data, colors]} note=${note}
      empty=${result.data && !hs.length ? `No run logs ${node.props.key} as a histogram (bin_start, bin_end, count).` : null} />`;
}

// the frame every drawn plot shares: the chart frame around a canvas, or a notice.
function PlotFrame(props: {
  node: Node;
  result: any;
  make: ((theme: Theme, height: number) => PlotSpec | null) | null;
  // the figure the server draws as PDF, in the given (light) theme's colors.
  figure?: (theme: Theme) => Record<string, unknown> | null;
  deps: unknown[];
  empty?: string | null;
  note?: string | null;
  legend?: unknown;
}) {
  const { node, result } = props;
  const theme = useTheme();
  const view = useContext(ViewCtx);
  const [box, visible] = useVisible();
  const el = useRef<HTMLDivElement>(null);
  const height = node.props.expanded ? expandedHeight() : HEIGHT;
  const spec = visible && theme && props.make ? props.make(theme, height) : null;
  useChart(el, plotChart, spec, [visible, height, ...props.deps], theme);
  const [problem, setProblem] = useState<string | null>(null);
  const title = node.props.title ?? defaultTitle(node);
  const exportPng = async (background: Background) => {
    const t = light();
    const figure = t && props.make ? props.make(t, paper.size?.height ?? height) : null;
    if (!figure || !el.current) return;
    host().download(await png(el.current.clientWidth, plotChart, figure, background), fileName(title, "png"));
  };
  const exportPdf = async () => {
    const t = light();
    const figure = t && props.figure ? props.figure(t) : null;
    if (!figure) return;
    setProblem(null);
    try {
      await host().figure({ title, ...figure }, fileName(title, "pdf"));
    } catch (err) {
      setProblem((err as Error).message);
    }
  };
  return html`<${ChartFrame} id=${node.id} title=${title} notes=${props.note ? [props.note] : []} box=${box} class="block"
      expanded=${node.props.expanded} onExpand=${() => host().expand(node, view)}
      downloads=${{ png: exportPng, pdf: props.figure ? exportPdf : undefined }}
      legend=${props.empty || result.status === "error" ? null : props.legend} caption=${node.props.caption}>
    ${problem ? html`<p class="block-error small">${problem}</p>` : null}
    <${Panel} result=${result}>
      ${props.empty
        ? html`<${Notice}>${props.empty}<//>`
        : html`<div class=${`chart-plot${result.status === "ready" ? "" : " pending"}`} ref=${el} style=${`min-block-size:${height}px`}></div>`}
    <//>
  <//>`;
}

function ValueLegend(props: { values: unknown[]; field: string }) {
  const theme = useTheme();
  if (!theme) return null;
  const entries = [...groupColors(props.values, theme).entries()];
  const mark = ([k, c]: [string, string]): LegendItem => ({ label: value(JSON.parse(k)), mark: swatch(c, theme) });
  const items = entries.length > 10 ? [mark(entries[0]), null, mark(entries[entries.length - 1])] : entries.map(mark);
  return html`<${Legend} items=${items} label=${`Colors by ${label(props.field)}`} name=${label(props.field)} />`;
}

function defaultTitle(node: Node): string {
  const p = node.props;
  switch (node.block) {
    case "scatter":
      return `${label(p.y)} against ${label(p.x)}`;
    case "bar":
      return `${label(p.y)} by ${label(p.x)}`;
    default:
      return p.key ?? node.id;
  }
}

function keyOf(b: Bar): string {
  return JSON.stringify([b.label, b.group]);
}

function samples(range: [number, number], log: boolean): number[] {
  const [a, b] = log ? [Math.log10(range[0]), Math.log10(range[1])] : range;
  return Array.from({ length: 65 }, (_, i) => {
    const v = a + ((b - a) * i) / 64;
    return log ? 10 ** v : v;
  });
}

function numberOr(text: string | null): unknown {
  const n = Number(text);
  return text !== null && text !== "" && Number.isFinite(n) ? n : text;
}
