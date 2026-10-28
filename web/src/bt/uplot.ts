// The chart runtime, loaded when a chart is on screen: line charts on uPlot.

import uPlot from "uplot";

import { align, type Curve } from "./curves.ts";
import type { ChartStyle } from "./theme.ts";

export type LineSpec = {
  curves: Curve[];
  colors: string[];
  style: ChartStyle;
  height: number;
  log: boolean;
  band: boolean;
  sync: string;
  formatX: (v: number) => string;
  formatY: (v: number) => string;
  onFocus?: (curve: Curve | null) => void;
};

export type LineChart = {
  update(spec: LineSpec): boolean;
  focus(key: string | null): void;
  destroy(): void;
};

// series 0 is x; then one per curve; then lo and hi per curve when bands are drawn.
export function lineChart(el: HTMLElement, spec: LineSpec): LineChart {
  let current = spec;
  const tip = document.createElement("div");
  tip.className = "bt-tip";
  tip.hidden = true;
  const n = spec.curves.length;
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
  const bands: uPlot.Band[] = [];
  if (spec.band) {
    spec.curves.forEach((_, i) => {
      series.push({ stroke: "transparent", width: 0, spanGaps: true, points: { show: false } });
      series.push({ stroke: "transparent", width: 0, spanGaps: true, points: { show: false } });
      bands.push({ series: [n + 2 + i * 2, n + 1 + i * 2], fill: tint(spec.colors[i], spec.style.band) });
    });
  }
  const axis = (formatter: (v: number) => string): uPlot.Axis => ({
    stroke: spec.style.axis,
    font: spec.style.font,
    grid: { stroke: spec.style.grid, width: 1 },
    ticks: { show: false },
    border: { show: false },
    gap: 6,
    values: (_u, splits) => splits.map((v) => (v === null ? "" : formatter(v))),
  });
  let focused: number | null = null;
  const u = new uPlot(
    {
      width: width(),
      height: spec.height,
      series,
      bands,
      legend: { show: false },
      padding: [8, 8, 0, 0],
      scales: { x: { time: false }, y: spec.log ? { distr: 3 } : {} },
      axes: [axis(spec.formatX), { ...axis(spec.formatY), size: 52 }],
      focus: { alpha: spec.style.dim },
      cursor: {
        sync: { key: spec.sync, setSeries: false },
        points: { show: false },
        drag: { x: true, y: false },
      },
      hooks: {
        setCursor: [(self) => cursorMoved(self)],
        ready: [(self) => self.over.append(tip)],
      },
    },
    data(spec),
    el,
  );

  function data(s: LineSpec): uPlot.AlignedData {
    const al = align(s.curves);
    const out: (number | null)[][] = [al.x, ...al.y];
    if (s.band) s.curves.forEach((_, i) => out.push(al.lo[i], al.hi[i]));
    return out as uPlot.AlignedData;
  }

  function cursorMoved(self: uPlot): void {
    const idx = self.cursor.idx;
    const top = self.cursor.top ?? -1;
    if (idx === null || idx === undefined || top < 0) {
      tip.hidden = true;
      setFocus(null);
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
    setFocus(nearest);
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
    tip.hidden = false;
    const left = self.cursor.left ?? 0;
    const flip = left > self.over.clientWidth / 2;
    tip.style.left = flip ? "" : `${left + 14}px`;
    tip.style.right = flip ? `${self.over.clientWidth - left + 14}px` : "";
    tip.style.top = `${Math.max(0, Math.min(top - 10, self.over.clientHeight - tip.offsetHeight))}px`;
  }

  function setFocus(i: number | null): void {
    if (i === focused) return;
    focused = i;
    u.setSeries(i === null ? null : i + 1, { focus: true }, false);
    current.onFocus?.(i === null ? null : current.curves[i]);
  }

  const ro = new ResizeObserver(() => u.setSize({ width: width(), height: current.height }));
  ro.observe(el);

  return {
    // same curves and colors: new data in place, keeping zoom; otherwise the caller rebuilds.
    update(next: LineSpec): boolean {
      const same =
        next.curves.length === current.curves.length &&
        next.curves.every((c, i) => c.key === current.curves[i].key && next.colors[i] === current.colors[i]) &&
        next.band === current.band &&
        next.log === current.log;
      if (!same) return false;
      current = next;
      const zoomed = u.scales.x.min !== undefined && isZoomed(u);
      u.setData(data(next), !zoomed);
      return true;
    },
    focus(key: string | null): void {
      const i = key === null ? -1 : current.curves.findIndex((c) => c.key === key || c.run === key);
      setFocus(i < 0 ? null : i);
    },
    destroy(): void {
      ro.disconnect();
      u.destroy();
    },
  };
}

function isZoomed(u: uPlot): boolean {
  const xs = u.data[0];
  return xs.length > 1 && (u.scales.x.min! > xs[0] || u.scales.x.max! < xs[xs.length - 1]);
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

function tint(hex: string, alpha: number): string {
  const h = hex.replace("#", "");
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
