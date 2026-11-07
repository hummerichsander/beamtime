// The chart runtime, loaded when a chart is on screen: line charts and drawn plots on uPlot.

import uPlot from "uplot";

import { align, logDomain, logRange, logTicks, markers, nearest, type Curve } from "./curves.ts";
import { extent, logSplits, timeLabel, timeTicks } from "./shapes.ts";
import { alpha, type ChartStyle } from "./theme.ts";

export type LineSpec = {
  curves: Curve[];
  // unsmoothed curves, drawn faint behind smoothed ones; null when not smoothing.
  raw: Curve[] | null;
  colors: string[];
  // each curve's line style, in CSS pixels: run n is drawn in data-n with dash-n.
  dashes: number[][];
  hidden: Set<string>;
  style: ChartStyle;
  height: number;
  scale: "linear" | "log" | "symlog";
  // symlog: values within ± this stay linear.
  asinh: number;
  band: boolean;
  // fixed y limits; null ends follow the data.
  range: [number | null, number | null] | null;
  // the zoomed x range; when the data was fetched for it, the data's own range already is it.
  zoom: [number, number] | null;
  zoomFetched: boolean;
  sync: string;
  // the axis titles; empty for none.
  xlabel: string;
  ylabel: string;
  // x is seconds since the epoch: ticks at round times.
  xTime: boolean;
  // some curve's x goes back on itself: drawn as paths, not as functions of x.
  trajectory: boolean;
  formatX: (v: number) => string;
  formatY: (v: number) => string;
  formatStep: (v: number) => string;
  onFocus?: (curve: Curve | null) => void;
  onZoom?: (window: [number, number] | null) => void;
  onClick?: (curve: Curve) => void;
};

export type LineChart = {
  update(spec: LineSpec): boolean;
  focus(key: string | null): void;
  // the canvas as a PNG data URL; null keeps the background transparent.
  png(background: string | null): string;
  destroy(): void;
};

const ZOOM_EVENTS = new Set(["mousedown", "mouseup", "dblclick"]);

// series: 0 is x; 1..n the curves; then n raw curves when smoothing; then lo, hi per curve.
export function lineChart(el: HTMLElement, spec: LineSpec): LineChart {
  let current = spec;
  const tip = document.createElement("div");
  tip.className = "bt-tip small";
  tip.hidden = true;
  const n = spec.curves.length;
  const rawAt = spec.raw ? n + 1 : -1;
  const bandAt = n + 1 + (spec.raw ? n : 0);
  const width = () => Math.max(120, Math.floor(el.getBoundingClientRect().width));

  const series: uPlot.Series[] = [
    {},
    ...spec.curves.map((c, i) => ({
      label: c.label,
      stroke: spec.colors[i],
      width: spec.style.line,
      // uPlot takes dashes in canvas pixels.
      dash: spec.dashes[i]?.map((v) => v * devicePixelRatio),
      spanGaps: true,
      // few points are marked, read from the data as it is now: a live update keeps the chart.
      points: { show: true, size: spec.style.line * 3, fill: spec.colors[i], filter: (self: uPlot, at: number) => markers(self.data[at]) },
    })),
  ];
  if (spec.raw) {
    spec.curves.forEach((_, i) => {
      series.push({ stroke: alpha(spec.colors[i], 0.22), width: 1, spanGaps: true, points: { show: false } });
    });
  }
  const bands: uPlot.Band[] = [];
  if (spec.band) {
    spec.curves.forEach((_, i) => {
      series.push({ stroke: "transparent", width: 0, spanGaps: true, points: { show: false } });
      series.push({ stroke: "transparent", width: 0, spanGaps: true, points: { show: false } });
      bands.push({ series: [bandAt + 1 + i * 2, bandAt + i * 2], fill: alpha(spec.colors[i], spec.style.band) });
    });
  }
  let focused: number | null = null;
  let applying = false;
  const u = new uPlot(
    {
      width: width(),
      height: spec.height,
      series,
      bands,
      legend: { show: false },
      padding: [8, 8, 0, 0],
      scales: {
        // one x value would collapse the range to nothing.
        x: { time: false, range: (_self, min, max) => (min === max ? [min - (Math.abs(min) * 0.01 || 1), max + (Math.abs(max) * 0.01 || 1)] : [min, max]) },
        y: {
          ...(spec.scale === "log" ? { distr: 3 } : spec.scale === "symlog" ? { distr: 4, asinh: spec.asinh } : {}),
          range: (self, min, max) => {
            // the band layers are transparent and clip at a floor: they must not stretch a log axis.
            const domain =
              current.scale === "log"
                ? logDomain(
                    [...current.curves, ...(current.raw ?? [])].filter((c) => !current.hidden.has(c.key) && !(c.run !== null && current.hidden.has(c.run))),
                    [self.scales.x.min ?? null, self.scales.x.max ?? null],
                  )
                : null;
            const auto =
              domain !== null
                ? logRange(domain[0], domain[1])
                : current.scale === "log" && min > 0
                  ? logRange(min, max)
                  : current.scale === "symlog"
                    ? uPlot.rangeAsinh(min, max, 10, true)
                    : uPlot.rangeNum(min, max, 0.06, true);
            const [lo, hi] = current.range ?? [null, null];
            return [lo ?? auto[0], hi ?? auto[1]] as uPlot.Range.MinMax;
          },
        },
      },
      axes: [
        // read through `current`: a chart kept in place on update still formats the new x axis.
        {
          ...(spec.xTime ? timeAxis(spec.style) : axisOf(spec.style, (v) => current.formatX(v))),
          size: 30,
          ...titled(spec.style, spec.xlabel),
        },
        {
          ...axisOf(spec.style, (v) => current.formatY(v)),
          size: tickWidth(spec.style),
          ...titled(spec.style, spec.ylabel),
          // symlog keeps uPlot's own ticks; log and linear get ours, which uPlot mustn't thin.
          ...(spec.scale === "symlog"
            ? {}
            : {
                splits: (_u: uPlot, _i: number, min: number, max: number) =>
                  current.scale === "log" ? logTicks(min, max) : niceTicks(min, max),
                filter: (_u: uPlot, splits: number[]) => splits,
              }),
        },
      ],
      focus: { alpha: spec.style.dim },
      cursor: {
        // the crosshair follows across the view; dragging and double-clicking zoom one chart only.
        sync: { key: spec.sync, setSeries: false, filters: { pub: (type) => !ZOOM_EVENTS.has(type) } },
        points: { show: false },
        drag: { x: true, y: false },
      },
      hooks: {
        setCursor: [(self) => cursorMoved(self)],
        setSelect: [
          (self) => {
            if (applying || self.select.width < 4) return;
            const a = self.posToVal(self.select.left, "x");
            const b = self.posToVal(self.select.left + self.select.width, "x");
            current.onZoom?.([a, b]);
          },
        ],
        ready: [
          (self) => {
            titles(self, spec.xlabel, spec.ylabel);
            self.over.append(tip);
            self.over.addEventListener("dblclick", () => current.onZoom?.(null));
            // a click (not the end of a drag-zoom) opens the curve under the pointer.
            let down: [number, number] | null = null;
            self.over.addEventListener("mousedown", (e) => (down = [e.clientX, e.clientY]));
            self.over.addEventListener("click", (e) => {
              const still = down && Math.hypot(e.clientX - down[0], e.clientY - down[1]) < 4;
              if (still && focused !== null) current.onClick?.(current.curves[focused]);
            });
          },
        ],
      },
    },
    data(spec),
    el,
  );
  applyHidden(spec);
  applyZoom(spec);

  function data(s: LineSpec): uPlot.AlignedData {
    const all = s.raw ? [...s.curves, ...s.raw] : s.curves;
    const al = align(all);
    const out: (number | null)[][] = [al.x, ...al.y];
    if (s.band) s.curves.forEach((_, i) => out.push(al.lo[i], al.hi[i]));
    return out as uPlot.AlignedData;
  }

  function applyZoom(s: LineSpec): void {
    if (s.zoom && !s.zoomFetched) u.setScale("x", { min: s.zoom[0], max: s.zoom[1] });
  }

  function applyHidden(s: LineSpec): void {
    applying = true;
    s.curves.forEach((c, i) => {
      const show = !(s.hidden.has(c.key) || (c.run !== null && s.hidden.has(c.run)));
      const set = (idx: number) => u.series[idx].show !== show && u.setSeries(idx, { show }, false);
      set(i + 1);
      if (rawAt > 0) set(rawAt + i);
      if (s.band) {
        set(bandAt + i * 2);
        set(bandAt + i * 2 + 1);
      }
    });
    applying = false;
  }

  function cursorMoved(self: uPlot): void {
    const left = self.cursor.left ?? -1;
    const top = self.cursor.top ?? -1;
    // only the chart under the pointer decides the focus; synced charts follow the view's hover.
    const active = self.over.matches(":hover");
    if (left < 0 || top < 0) {
      tip.hidden = true;
      // a chart that only follows the synced cursor leaves the shared focus alone.
      if (active) report(null);
      return;
    }
    const at = self.posToVal(left, "x");
    const rows: { i: number; v: number; x: number }[] = [];
    let nearestRow: number | null = null;
    let best = 14;
    for (let i = 0; i < n; i++) {
      const c = current.curves[i];
      if (!self.series[i + 1].show) continue;
      // each curve answers with its own nearest point, whatever x the other curves were logged at.
      const k = nearest(c.x, at);
      const v = k < 0 ? null : c.y[k];
      if (v === null || v === undefined) continue;
      // beyond its first or last point a curve answers only close by.
      const outside = at < c.x[0] || at > c.x[c.x.length - 1];
      if (outside && Math.abs(self.valToPos(c.x[k], "x") - left) > 14) continue;
      rows.push({ i, v, x: c.x[k] });
      const d = Math.abs(self.valToPos(v, "y") - top);
      if (d < best) {
        best = d;
        nearestRow = i;
      }
    }
    if (active) report(nearestRow);
    if (!rows.length) {
      tip.hidden = true;
      return;
    }
    const head = rows.find((r) => r.i === nearestRow) ?? rows[0];
    rows.sort((a, b) => b.v - a.v);
    tip.replaceChildren(line(current.xlabel || "x", current.formatX(head.x), null, true));
    for (const { i, v } of rows.slice(0, 12)) {
      tip.append(line(current.curves[i].label, current.formatY(v), current.colors[i], i === nearestRow));
    }
    if (rows.length > 12) tip.append(line(`and ${rows.length - 12} more`, "", null, false));
    if (nearestRow !== null && current.curves[nearestRow].run && current.onClick) {
      const hint = document.createElement("div");
      hint.className = "bt-tip-hint";
      hint.textContent = "click for the run's details";
      tip.append(hint);
    }
    place(tip, self, left, top);
  }

  function setFocus(i: number | null): void {
    if (i === focused) return;
    focused = i;
    u.setSeries(i === null ? null : i + 1, { focus: true }, false);
  }

  function report(i: number | null): void {
    if (i === focused) return;
    setFocus(i);
    current.onFocus?.(i === null ? null : current.curves[i]);
  }

  const ro = new ResizeObserver(() => u.setSize({ width: width(), height: current.height }));
  ro.observe(el);

  return {
    // same curves, colors and layers: new data in place, keeping zoom; otherwise the caller rebuilds.
    update(next: LineSpec): boolean {
      const same =
        next.curves.length === current.curves.length &&
        next.curves.every((c, i) => c.key === current.curves[i].key && next.colors[i] === current.colors[i]) &&
        next.band === current.band &&
        next.scale === current.scale &&
        next.asinh === current.asinh &&
        !!next.raw === !!current.raw &&
        next.height === current.height &&
        next.xlabel === current.xlabel &&
        next.ylabel === current.ylabel &&
        next.xTime === current.xTime &&
        !next.trajectory &&
        sameStyle(next.style, current.style);
      if (!same) return false;
      current = next;
      // setData without resetting scales keeps index ranges of the old data, and later redraws
      // draw stale paths; so always reset, then re-apply a zoom the data wasn't fetched for.
      u.batch(() => {
        u.setData(data(next), true);
        applyZoom(next);
      });
      applyHidden(next);
      return true;
    },
    focus(key: string | null): void {
      const i = key === null ? -1 : current.curves.findIndex((c) => isCurve(c, key));
      setFocus(i < 0 ? null : i);
    },
    png: (background) => png(u, background),
    destroy(): void {
      ro.disconnect();
      u.destroy();
    },
  };
}

// curves whose x goes back on itself, as paths in step order with an arrow at the end, on plotChart.
export function trajectoryChart(el: HTMLElement, spec: LineSpec): LineChart {
  let current = spec;
  const plot = plotChart(el, trajectorySpec(spec, () => current));
  return {
    update(next: LineSpec): boolean {
      if (!next.trajectory || next.height !== current.height) return false;
      current = next;
      plot.update(trajectorySpec(next, () => current));
      return true;
    },
    focus(key: string | null): void {
      const c = key === null ? undefined : current.curves.find((k) => isCurve(k, key));
      plot.focus(c ? (c.run ?? c.key) : null);
    },
    png: (background) => plot.png(background),
    destroy: () => plot.destroy(),
  };
}

function trajectorySpec(s: LineSpec, now: () => LineSpec): PlotSpec {
  const shown = s.curves
    .map((c, i) => ({ c, i }))
    .filter(({ c }) => !s.hidden.has(c.key) && !(c.run !== null && s.hidden.has(c.run)));
  const log = s.scale === "log";
  const xr = extent(shown.flatMap(({ c }) => c.x), false) ?? [0, 1];
  const auto = extent(shown.flatMap(({ c }) => c.y.filter((v): v is number => v !== null)), log) ?? [log ? 0.1 : 0, 1];
  const yr: [number, number] = [s.range?.[0] ?? auto[0], s.range?.[1] ?? auto[1]];
  const keyOf = (c: Curve) => c.run ?? c.key;
  return {
    style: s.style,
    height: s.height,
    x: { range: xr, log: false, format: s.formatX, label: s.xlabel },
    y: {
      range: yr,
      log,
      symlog: s.scale === "symlog" ? s.asinh : undefined,
      format: s.formatY,
      label: s.ylabel,
      ...(log ? { splits: logSplits(yr) } : {}),
    },
    draw: ({ ctx, x, y, px, focused }) => {
      for (const { c, i } of shown) {
        const pts: [number, number][] = [];
        c.x.forEach((xv, k) => {
          const yv = c.y[k];
          if (yv !== null && yv !== undefined && !(log && yv <= 0)) pts.push([x(xv), y(yv)]);
        });
        ctx.globalAlpha = focused !== null && focused !== keyOf(c) ? s.style.dim + 0.15 : 1;
        ctx.strokeStyle = s.colors[i];
        ctx.fillStyle = s.colors[i];
        ctx.lineWidth = s.style.line * px;
        ctx.setLineDash((s.dashes[i] ?? []).map((v) => v * px));
        ctx.beginPath();
        pts.forEach(([a, b], k) => (k ? ctx.lineTo(a, b) : ctx.moveTo(a, b)));
        ctx.stroke();
        ctx.setLineDash([]);
        if (pts.length > 1) {
          const [[x0, y0], [x1, y1]] = pts.slice(-2);
          const angle = Math.atan2(y1 - y0, x1 - x0);
          const size = s.style.line * 4 * px;
          ctx.beginPath();
          ctx.moveTo(x1 + Math.cos(angle) * size, y1 + Math.sin(angle) * size);
          ctx.lineTo(x1 + Math.cos(angle + 2.5) * size, y1 + Math.sin(angle + 2.5) * size);
          ctx.lineTo(x1 + Math.cos(angle - 2.5) * size, y1 + Math.sin(angle - 2.5) * size);
          ctx.fill();
        } else if (pts.length === 1) {
          ctx.beginPath();
          ctx.arc(pts[0][0], pts[0][1], s.style.line * 1.5 * px, 0, 2 * Math.PI);
          ctx.fill();
        }
      }
      ctx.globalAlpha = 1;
    },
    hit: (left, top, x, y) => {
      let best: { c: Curve; i: number; k: number } | null = null;
      let d = 14;
      for (const { c, i } of shown) {
        for (let k = 0; k < c.x.length; k++) {
          const yv = c.y[k];
          if (yv === null || yv === undefined || (log && yv <= 0)) continue;
          const dk = Math.hypot(x(c.x[k]) - left, y(yv) - top);
          if (dk < d) [best, d] = [{ c, i, k }, dk];
        }
      }
      if (!best) return null;
      const { c, i, k } = best;
      const rows: TipRow[] = [{ label: c.label, value: "", color: s.colors[i], strong: true }];
      if (c.step) rows.push({ label: "step", value: s.formatStep(c.step[k]), color: null });
      rows.push({ label: s.xlabel || "x", value: s.formatX(c.x[k]), color: null });
      rows.push({ label: s.ylabel || "y", value: s.formatY(c.y[k]!), color: null });
      return { key: keyOf(c), rows };
    },
    onFocus: (key) => now().onFocus?.(key === null ? null : (now().curves.find((c) => keyOf(c) === key) ?? null)),
    onClick: (key) => {
      const c = now().curves.find((k) => keyOf(k) === key);
      if (c) now().onClick?.(c);
    },
  };
}

function png(u: uPlot, background: string | null): string {
  const src = u.ctx.canvas;
  const out = document.createElement("canvas");
  out.width = src.width;
  out.height = src.height;
  const ctx = out.getContext("2d")!;
  if (background) {
    ctx.fillStyle = background;
    ctx.fillRect(0, 0, out.width, out.height);
  }
  ctx.drawImage(src, 0, 0);
  return out.toDataURL("image/png");
}

// axis and grid colors are set when a chart is built: another theme rebuilds it.
function sameStyle(a: ChartStyle, b: ChartStyle): boolean {
  return (Object.keys(a) as (keyof ChartStyle)[]).every((k) => a[k] === b[k]);
}

function axisOf(style: ChartStyle, format: (v: number) => string, splits?: () => number[]): uPlot.Axis {
  return {
    stroke: style.axis,
    font: style.font,
    grid: { stroke: style.grid, width: 1 },
    ticks: { show: false },
    border: { show: false },
    gap: 6,
    // fixed ticks are ours (categories, decades, times); uPlot mustn't thin them.
    ...(splits ? { splits, filter: (_u: uPlot, at: number[]) => at } : {}),
    values: (_u, at) => at.map((v) => (v === null ? "" : format(v))),
  };
}

// the page's hover and legend name a curve by its key, its run, its group or a run in it.
function isCurve(c: Curve, key: string): boolean {
  return c.key === key || c.run === key || (c.group !== null && key === `by:${c.group}`) || c.runs.includes(key);
}

// the axis titles are drawn on the canvas; the root carries them for readers of the page.
function titles(u: uPlot, x: string, y: string): void {
  u.root.dataset.xlabel = x;
  u.root.dataset.ylabel = y;
}

// an axis title in the chart's font; none takes no room.
function titled(style: ChartStyle, text: string): Partial<uPlot.Axis> {
  return text ? { label: text, labelFont: style.font, labelSize: 22 } : {};
}

let probe: CanvasRenderingContext2D | null = null;

// the room a y axis needs: its widest tick label, measured, so `1.2e-05` isn't cut.
function tickWidth(style: ChartStyle): (u: uPlot, values: string[] | null) => number {
  return (_u, values) => {
    probe ??= document.createElement("canvas").getContext("2d")!;
    probe.font = style.font;
    // the axis' gap on top of the text.
    return Math.ceil(Math.max(20, ...(values ?? []).map((v) => probe!.measureText(v).width))) + 8;
  };
}

// ticks at round times; the labels name the date where the range is long.
function timeAxis(style: ChartStyle): uPlot.Axis {
  return {
    ...axisOf(style, String),
    splits: (_u, _i, min, max) => timeTicks(min, max).at,
    filter: (_u, at) => at,
    values: (self, at) => {
      const { step } = timeTicks(self.scales.x.min!, self.scales.x.max!);
      return at.map((v) => timeLabel(v, step));
    },
  };
}

// the tooltip sits beside the pointer, on the side with more room.
function place(tip: HTMLElement, u: uPlot, left: number, top: number): void {
  tip.hidden = false;
  const flip = left > u.over.clientWidth / 2;
  tip.style.left = flip ? "" : `${left + 14}px`;
  tip.style.right = flip ? `${u.over.clientWidth - left + 14}px` : "";
  tip.style.top = `${Math.max(0, Math.min(top - 10, u.over.clientHeight - tip.offsetHeight))}px`;
}

export type PlotAxis = {
  range: [number, number];
  log: boolean;
  // linear near zero, logarithmic beyond this.
  symlog?: number;
  format: (v: number) => string;
  // the axis title; empty for none.
  label: string;
  // fixed tick positions, e.g. one per category.
  splits?: number[];
  // the axis' room in pixels (labels on the y axis).
  size?: number;
  // larger values downward (lanes listed top to bottom).
  reverse?: boolean;
};
export type TipRow = { label: string; value: string; color: string | null; strong?: boolean };
export type Painter = {
  ctx: CanvasRenderingContext2D;
  x: (v: number) => number;
  y: (v: number) => number;
  // canvas pixels per CSS pixel.
  px: number;
  focused: string | null;
};
export type PlotSpec = {
  style: ChartStyle;
  height: number;
  x: PlotAxis;
  y: PlotAxis;
  draw: (p: Painter) => void;
  // what is under the pointer (CSS pixels in the plot area): its key and the tooltip's rows.
  hit: (left: number, top: number, x: (v: number) => number, y: (v: number) => number) => { key: string | null; rows: TipRow[] } | null;
  onFocus?: (key: string | null) => void;
  onClick?: (key: string) => void;
};
export type Plot = {
  update(spec: PlotSpec): void;
  focus(key: string | null): void;
  png(background: string | null): string;
  // the x value under a pointer position (client pixels), for zooming and panning.
  xAt(clientX: number): number;
  // x values per CSS pixel.
  xPerPixel(): number;
  destroy(): void;
};

// a chart whose marks are drawn by the caller (points, bars, outlines) on uPlot's axes and grid.
export function plotChart(el: HTMLElement, spec: PlotSpec): Plot {
  let current = spec;
  let focused: string | null = null;
  let under: string | null = null;
  const tip = document.createElement("div");
  tip.className = "bt-tip small";
  tip.hidden = true;
  const width = () => Math.max(120, Math.floor(el.getBoundingClientRect().width));
  const scale = (axis: () => PlotAxis): uPlot.Scale => ({
    time: false,
    ...(axis().log ? { distr: 3 } : axis().symlog ? { distr: 4, asinh: axis().symlog } : {}),
    ...(axis().reverse ? { dir: -1 as const } : {}),
    range: () => axis().range,
  });
  const u = new uPlot(
    {
      width: width(),
      height: spec.height,
      series: [{}, { show: false }],
      legend: { show: false },
      padding: [10, 10, 0, 0],
      scales: { x: scale(() => current.x), y: scale(() => current.y) },
      axes: [
        { ...axisOf(spec.style, (v) => current.x.format(v), spec.x.splits && (() => current.x.splits ?? [])), size: 30, ...titled(spec.style, spec.x.label) },
        {
          ...axisOf(spec.style, (v) => current.y.format(v), spec.y.splits && (() => current.y.splits ?? [])),
          size: spec.y.size ?? tickWidth(spec.style),
          ...titled(spec.style, spec.y.label),
        },
      ],
      cursor: { x: false, y: false, points: { show: false }, drag: { x: false, y: false } },
      hooks: {
        draw: [
          (self) => {
            const ctx = self.ctx;
            const { left, top, width: w, height: h } = self.bbox;
            ctx.save();
            ctx.beginPath();
            ctx.rect(left, top, w, h);
            ctx.clip();
            current.draw({
              ctx,
              x: (v) => self.valToPos(v, "x", true),
              y: (v) => self.valToPos(v, "y", true),
              px: uPlot.pxRatio,
              focused,
            });
            ctx.restore();
          },
        ],
        setCursor: [
          (self) => {
            const left = self.cursor.left ?? -1;
            const top = self.cursor.top ?? -1;
            const found = left < 0 ? null : current.hit(left, top, (v) => self.valToPos(v, "x"), (v) => self.valToPos(v, "y"));
            under = found?.key ?? null;
            self.over.style.cursor = under && current.onClick ? "pointer" : "";
            if (under !== focused) {
              setFocus(under);
              current.onFocus?.(under);
            }
            if (!found || !found.rows.length) {
              tip.hidden = true;
              return;
            }
            tip.replaceChildren(...found.rows.map((r) => line(r.label, r.value, r.color, !!r.strong)));
            place(tip, self, left, top);
          },
        ],
        ready: [
          (self) => {
            titles(self, spec.x.label, spec.y.label);
            self.over.append(tip);
            self.over.addEventListener("click", () => under && current.onClick?.(under));
          },
        ],
      },
    },
    [spec.x.range, [null, null]] as unknown as uPlot.AlignedData,
    el,
  );

  function setFocus(key: string | null): void {
    if (key === focused) return;
    focused = key;
    u.redraw(false, false);
  }

  const ro = new ResizeObserver(() => u.setSize({ width: width(), height: current.height }));
  ro.observe(el);
  return {
    update(next: PlotSpec): void {
      current = next;
      titles(u, next.x.label, next.y.label);
      u.setData([next.x.range, [null, null]] as unknown as uPlot.AlignedData, true);
    },
    focus: setFocus,
    png: (background) => png(u, background),
    xAt: (clientX) => u.posToVal(clientX - u.over.getBoundingClientRect().left, "x"),
    xPerPixel: () => (current.x.range[1] - current.x.range[0]) / Math.max(1, u.over.clientWidth),
    destroy(): void {
      ro.disconnect();
      u.destroy();
    },
  };
}

function line(label: string, value: string, color: string | null, strong: boolean): HTMLElement {
  const row = document.createElement("div");
  row.className = strong ? "bt-tip-row strong" : "bt-tip-row";
  const dot = document.createElement("span");
  dot.className = "bt-tip-dot";
  if (color) dot.style.background = color;
  const name = document.createElement("span");
  name.className = "bt-tip-label";
  name.textContent = label;
  const val = document.createElement("span");
  val.className = "bt-tip-value";
  val.textContent = value;
  row.append(dot, name, val);
  return row;
}

// linear ticks at 1, 2 or 5 times a power of ten, about five of them.
function niceTicks(min: number, max: number): number[] {
  const raw = (max - min) / 5 || 1;
  const p = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 5, 10].map((m) => m * p).find((s) => s >= raw)!;
  const out: number[] = [];
  for (let v = Math.ceil(min / step) * step; v <= max + step * 1e-9; v += step) out.push(Number(v.toPrecision(12)));
  return out;
}
