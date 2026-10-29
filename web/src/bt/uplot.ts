// The chart runtime, loaded when a chart is on screen: line charts and drawn plots on uPlot.

import uPlot from "uplot";

import { align, logRange, logTicks, type Curve } from "./curves.ts";
import type { ChartStyle } from "./theme.ts";

export type LineSpec = {
  curves: Curve[];
  // unsmoothed curves, drawn faint behind smoothed ones; null when not smoothing.
  raw: Curve[] | null;
  colors: string[];
  hidden: Set<string>;
  style: ChartStyle;
  height: number;
  log: boolean;
  band: boolean;
  range: [number, number] | null;
  // the zoomed x range; when the data was fetched for it, the data's own range already is it.
  zoom: [number, number] | null;
  zoomFetched: boolean;
  sync: string;
  formatX: (v: number) => string;
  formatY: (v: number) => string;
  onFocus?: (curve: Curve | null) => void;
  onZoom?: (window: [number, number] | null) => void;
};

export type LineChart = {
  update(spec: LineSpec): boolean;
  focus(key: string | null): void;
  png(background: string): string;
  destroy(): void;
};

const ZOOM_EVENTS = new Set(["mousedown", "mouseup", "dblclick"]);

// series: 0 is x; 1..n the curves; then n raw curves when smoothing; then lo, hi per curve.
export function lineChart(el: HTMLElement, spec: LineSpec): LineChart {
  let current = spec;
  const tip = document.createElement("div");
  tip.className = "bt-tip";
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
      spanGaps: true,
      points: { show: false },
    })),
  ];
  if (spec.raw) {
    spec.curves.forEach((_, i) => {
      series.push({ stroke: tint(spec.colors[i], 0.22), width: 1, spanGaps: true, points: { show: false } });
    });
  }
  const bands: uPlot.Band[] = [];
  if (spec.band) {
    spec.curves.forEach((_, i) => {
      series.push({ stroke: "transparent", width: 0, spanGaps: true, points: { show: false } });
      series.push({ stroke: "transparent", width: 0, spanGaps: true, points: { show: false } });
      bands.push({ series: [bandAt + 1 + i * 2, bandAt + i * 2], fill: tint(spec.colors[i], spec.style.band) });
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
        x: { time: false },
        y: {
          ...(spec.log ? { distr: 3 } : {}),
          range: (_self, min, max) =>
            current.range ??
            (current.log && min > 0 ? logRange(min, max) : uPlot.rangeNum(min, max, 0.06, true)),
        },
      },
      axes: [
        { ...axisOf(spec.style, spec.formatX), size: 30 },
        { ...axisOf(spec.style, spec.formatY), size: 52, splits: (_u, _i, min, max) => (current.log ? logTicks(min, max) : niceTicks(min, max)),
          // uPlot thins log ticks to 1 and 5 per decade by default; ours are already chosen.
          filter: (_u, splits) => splits },
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
            self.over.append(tip);
            self.over.addEventListener("dblclick", () => current.onZoom?.(null));
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
    const idx = self.cursor.idx;
    const top = self.cursor.top ?? -1;
    // only the chart under the pointer decides the focus; synced charts follow the view's hover.
    const active = self.over.matches(":hover");
    if (idx === null || idx === undefined || top < 0) {
      tip.hidden = true;
      // a chart that only follows the synced cursor leaves the shared focus alone.
      if (active) report(null);
      return;
    }
    const x = self.data[0][idx];
    const rows: { i: number; v: number }[] = [];
    let nearest: number | null = null;
    let best = 14;
    for (let i = 0; i < n; i++) {
      const v = self.data[i + 1][idx];
      if (v === null || v === undefined || !self.series[i + 1].show) continue;
      rows.push({ i, v });
      const d = Math.abs(self.valToPos(v, "y") - top);
      if (d < best) {
        best = d;
        nearest = i;
      }
    }
    if (active) report(nearest);
    if (!rows.length) {
      tip.hidden = true;
      return;
    }
    rows.sort((a, b) => b.v - a.v);
    tip.replaceChildren(line("step", current.formatX(x), null, true));
    for (const { i, v } of rows.slice(0, 12)) {
      tip.append(line(current.curves[i].label, current.formatY(v), current.colors[i], i === nearest));
    }
    if (rows.length > 12) tip.append(line(`and ${rows.length - 12} more`, "", null, false));
    place(tip, self, self.cursor.left ?? 0, top);
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
        next.log === current.log &&
        !!next.raw === !!current.raw &&
        next.height === current.height;
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
      const i = key === null ? -1 : current.curves.findIndex((c) => c.key === key || c.run === key ||
        (c.group !== null && key === `by:${c.group}`) || c.runs.includes(key));  // prettier-ignore
      setFocus(i < 0 ? null : i);
    },
    png(background: string): string {
      const src = u.ctx.canvas;
      const out = document.createElement("canvas");
      out.width = src.width;
      out.height = src.height;
      const ctx = out.getContext("2d")!;
      ctx.fillStyle = background;
      ctx.fillRect(0, 0, out.width, out.height);
      ctx.drawImage(src, 0, 0);
      return out.toDataURL("image/png");
    },
    destroy(): void {
      ro.disconnect();
      u.destroy();
    },
  };
}

function axisOf(style: ChartStyle, format: (v: number) => string, splits?: number[]): uPlot.Axis {
  return {
    stroke: style.axis,
    font: style.font,
    grid: { stroke: style.grid, width: 1 },
    ticks: { show: false },
    border: { show: false },
    gap: 6,
    ...(splits ? { splits: () => splits } : {}),
    values: (_u, at) => at.map((v) => (v === null ? "" : format(v))),
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
  format: (v: number) => string;
  // fixed tick positions, e.g. one per category.
  splits?: number[];
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
export type Plot = { update(spec: PlotSpec): void; focus(key: string | null): void; png(background: string): string; destroy(): void };

// a chart whose marks are drawn by the caller (points, bars, outlines) on uPlot's axes and grid.
export function plotChart(el: HTMLElement, spec: PlotSpec): Plot {
  let current = spec;
  let focused: string | null = null;
  let under: string | null = null;
  const tip = document.createElement("div");
  tip.className = "bt-tip";
  tip.hidden = true;
  const width = () => Math.max(120, Math.floor(el.getBoundingClientRect().width));
  const scale = (axis: () => PlotAxis): uPlot.Scale => ({
    time: false,
    ...(axis().log ? { distr: 3 } : {}),
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
        { ...axisOf(spec.style, (v) => current.x.format(v), spec.x.splits), size: 30 },
        { ...axisOf(spec.style, (v) => current.y.format(v), spec.y.splits), size: 52 },
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
      u.setData([next.x.range, [null, null]] as unknown as uPlot.AlignedData, true);
    },
    focus: setFocus,
    png(background: string): string {
      const src = u.ctx.canvas;
      const out = document.createElement("canvas");
      out.width = src.width;
      out.height = src.height;
      const ctx = out.getContext("2d")!;
      ctx.fillStyle = background;
      ctx.fillRect(0, 0, out.width, out.height);
      ctx.drawImage(src, 0, 0);
      return out.toDataURL("image/png");
    },
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

export function tint(hex: string, alpha: number): string {
  const h = hex.replace("#", "");
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
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
