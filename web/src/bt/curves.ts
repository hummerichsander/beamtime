// Reshape `series` answers into curves and align them on one x axis for uPlot.

import { value } from "./fmt.ts";

export type Curve = {
  key: string;
  label: string;
  run: string | null;
  metric: string;
  x: number[];
  y: (number | null)[];
  lo: (number | null)[] | null;
  hi: (number | null)[] | null;
  n: (number | null)[] | null;
  // aggregated curves: the group's label and its runs, so hover can match them across charts.
  group: string | null;
  runs: string[];
};

export type Curves = { curves: Curve[]; aggregated: boolean };

export function reshape(answer: { curves: any[] }, opts: { log?: boolean } = {}): Curves {
  const raw = answer.curves ?? [];
  const aggregated = raw.some((c) => "by" in c);
  const labels = aggregated ? byLabels(raw.map((c) => c.by)) : runLabels(raw);
  const metrics = new Set(raw.map((c) => c.metric)).size > 1;
  const positive = (v: number | null) => (opts.log && v !== null && v <= 0 ? null : v);
  const curves = raw.map((c, i): Curve => {
    const out: Curve = {
      key: aggregated ? `g${i}:${c.metric}` : `${c.run}:${c.metric}`,
      label: labels[i] + (metrics ? ` · ${c.metric}` : ""),
      run: aggregated ? null : c.run,
      metric: c.metric,
      x: c.x ?? [],
      y: [],
      lo: null,
      hi: null,
      n: null,
      group: aggregated ? labels[i] : null,
      runs: aggregated ? (c.runs ?? []) : [c.run],
    };
    if (aggregated) {
      out.y = c.mean ?? [];
      out.lo = c.lo ?? null;
      out.hi = c.hi ?? null;
      out.n = c.n ?? null;
    } else if (c.raw) {
      out.y = c.y ?? [];
    } else {
      out.y = c.last ?? [];
      out.lo = c.min ?? null;
      out.hi = c.max ?? null;
      out.n = c.count ?? null;
    }
    out.y = out.y.map(positive);
    out.lo = out.lo?.map(positive) ?? null;
    out.hi = out.hi?.map(positive) ?? null;
    return out;
  });
  return { curves, aggregated };
}

export type Aligned = { x: number[]; y: (number | null)[][]; lo: (number | null)[][]; hi: (number | null)[][] };

// uPlot wants one sorted x array; every curve gets null where it has no point.
export function align(curves: Curve[]): Aligned {
  const xs = [...new Set(curves.flatMap((c) => c.x))].sort((a, b) => a - b);
  const at = new Map(xs.map((x, i) => [x, i]));
  const spread = (c: Curve, values: (number | null)[] | null) => {
    const out: (number | null)[] = new Array(xs.length).fill(null);
    if (values) c.x.forEach((x, j) => (out[at.get(x)!] = values[j] ?? null));
    return out;
  };
  return {
    x: xs,
    y: curves.map((c) => spread(c, c.y)),
    lo: curves.map((c) => spread(c, c.lo)),
    hi: curves.map((c) => spread(c, c.hi)),
  };
}

export function byLabels(values: Record<string, unknown>[]): string[] {
  const fields = [...new Set(values.flatMap((g) => Object.keys(g ?? {})))];
  const varying = fields.filter((f) => new Set(values.map((g) => JSON.stringify(g?.[f]))).size > 1);
  const shown = varying.length ? varying : fields;
  return values.map(
    (g) => shown.map((f) => `${f.replace(/^config\./, "")}=${format(g?.[f])}`).join(", ") || "all runs",
  );
}

function runLabels(curves: any[]): string[] {
  const names = curves.map((c) => c.name ?? c.run);
  const counts = new Map<string, number>();
  for (const n of names) counts.set(n, (counts.get(n) ?? 0) + 1);
  return curves.map((c, i) => (counts.get(names[i])! > 1 ? `${names[i]} (${String(c.run).slice(-4)})` : names[i]));
}

// a curve with at most this many points marks each of them, so a single point or a sparse metric shows.
export const SPARSE = 30;

// the indices of the points to mark: all the finite ones when there are few, else none.
export function markers(ys: ArrayLike<number | null | undefined>): number[] {
  const finite: number[] = [];
  for (let i = 0; i < ys.length; i++) if (typeof ys[i] === "number" && Number.isFinite(ys[i])) finite.push(i);
  return finite.length <= SPARSE ? finite : [];
}

function format(v: unknown): string {
  if (typeof v === "number") return String(Number(v.toPrecision(4)));
  return typeof v === "object" && v !== null ? value(v) : String(v);
}

// TensorBoard-style debiased exponential moving average; gaps stay gaps. weight 0 is no smoothing.
export function ema(values: (number | null)[], weight: number): (number | null)[] {
  if (weight <= 0) return values;
  let last = 0;
  let n = 0;
  return values.map((v) => {
    if (v === null || !Number.isFinite(v)) return v;
    last = last * weight + (1 - weight) * v;
    n += 1;
    return last / (1 - weight ** n);
  });
}

export function smooth(c: Curves, weight: number): Curves {
  if (weight <= 0) return c;
  // the band is smoothed like the curve, so it stays around it.
  const band = (v: (number | null)[] | null) => (v ? ema(v, weight) : null);
  return { ...c, curves: c.curves.map((cv) => ({ ...cv, y: ema(cv.y, weight), lo: band(cv.lo), hi: band(cv.hi) })) };
}

// a log axis padded in log space around the data, not rounded out to whole decades.
export function logRange(min: number, max: number): [number, number] {
  const span = Math.max(Math.log10(max / min), 0.3);
  const f = 10 ** (span * 0.06);
  return [min / f, max * f];
}

// a y range that ignores the most extreme 1 % on each side, so one diverging run doesn't
// flatten every other curve; padded a little.
export function robustRange(series: (number | null)[][], log = false): [number, number] | null {
  const vals = series.flat().filter((v): v is number => v !== null && Number.isFinite(v) && (!log || v > 0));
  if (vals.length < 10) return null;
  vals.sort((a, b) => a - b);
  const q = (p: number) => vals[Math.min(vals.length - 1, Math.max(0, Math.round(p * (vals.length - 1))))];
  let [lo, hi] = [q(0.01), q(0.99)];
  if (log) return [lo / 1.15, hi * 1.15];
  const pad = (hi - lo) * 0.06 || Math.abs(hi) * 0.05 || 1;
  [lo, hi] = [lo - pad, hi + pad];
  return [lo, hi];
}

// ticks on a log axis: decades, with more marks between them the shorter the range.
export function logTicks(min: number, max: number): number[] {
  const span = Math.log10(max / min);
  const steps = span <= 0.6 ? [1, 2, 3, 4, 5, 6, 7, 8, 9] : span <= 1.3 ? [1, 2, 3, 5] : span <= 2.5 ? [1, 2, 5] : [1];
  const out: number[] = [];
  for (let e = Math.floor(Math.log10(min)); e <= Math.ceil(Math.log10(max)); e++) {
    for (const m of steps) out.push(Number((m * 10 ** e).toPrecision(6)));
  }
  return out.filter((v) => v >= min && v <= max);
}

// a symlog threshold: the power of ten at about the smallest tenth of the absolute values, so
// small values stay readable and large ones are compressed.
export function linthresh(series: (number | null)[][]): number {
  const abs = series.flat().filter((v): v is number => v !== null && Number.isFinite(v) && v !== 0).map(Math.abs);
  if (!abs.length) return 1;
  abs.sort((a, b) => a - b);
  return 10 ** Math.floor(Math.log10(abs[Math.floor(abs.length * 0.1)]));
}
