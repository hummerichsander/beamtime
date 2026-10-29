// Data shaping for the one-value-per-run charts: scatter points with fits, bars with error bars,
// histogram outlines. Pure functions, so they are tested without a browser.

export type Answer = { columns: string[]; rows: unknown[][] };
export type Point = { key: string; runs: string[]; x: number; y: number; err: number | null; color: unknown; n: number };

// a value as a number: plain, or the mean of a seed aggregate {mean, std, n}.
export function num(v: unknown): number | null {
  if (typeof v === "number") return Number.isFinite(v) ? v : null;
  if (v && typeof v === "object" && "mean" in v) return num((v as { mean: unknown }).mean);
  return null;
}

function spread(v: unknown): number | null {
  return v && typeof v === "object" && "std" in v ? num((v as { std: unknown }).std) : null;
}

function count(v: unknown): number {
  return v && typeof v === "object" && "n" in v ? Number((v as { n: unknown }).n) : 1;
}

// one point per row (a run, or a seed mean with its spread); rows without both values are left out.
export function points(answer: Answer | null, x: string, y: string, color?: string | null): Point[] {
  if (!answer) return [];
  const at = (c: string) => answer.columns.indexOf(c);
  const [ix, iy, ic, id, runs] = [at(x), at(y), color ? at(color) : -1, at("run.id"), at("runs")];
  const out: Point[] = [];
  for (const r of answer.rows) {
    const px = num(r[ix]);
    const py = num(r[iy]);
    if (px === null || py === null) continue;
    const ids = runs >= 0 ? (r[runs] as string[]) : id >= 0 ? [String(r[id])] : [];
    out.push({ key: ids[0] ?? `${px},${py}`, runs: ids, x: px, y: py, err: spread(r[iy]), color: ic >= 0 ? r[ic] : null, n: count(r[iy]) });
  }
  return out;
}

// least squares in the fit's space: linear y = a + b x, log y = a + b ln x, power ln y = a + b ln x.
export function fit(pts: Point[], kind: "linear" | "log" | "power"): ((x: number) => number) | null {
  const tx = kind === "linear" ? (x: number) => x : Math.log;
  const ty = kind === "power" ? Math.log : (y: number) => y;
  const usable = pts.filter((p) => (kind === "linear" || p.x > 0) && (kind !== "power" || p.y > 0));
  if (usable.length < 2) return null;
  const xs = usable.map((p) => tx(p.x));
  const ys = usable.map((p) => ty(p.y));
  const mx = mean(xs);
  const my = mean(ys);
  const sxx = xs.reduce((s, v) => s + (v - mx) ** 2, 0);
  if (sxx === 0) return null;
  const b = xs.reduce((s, v, i) => s + (v - mx) * (ys[i] - my), 0) / sxx;
  const a = my - b * mx;
  return kind === "power" ? (x) => Math.exp(a + b * Math.log(x)) : (x) => a + b * tx(x);
}

export type Bar = { label: string; group: string | null; value: number; lo: number; hi: number; n: number; runs: string[] };

// bars per category (and per group within it): the mean with an error from the values' spread.
export function bars(
  answer: Answer | null,
  x: string,
  y: string,
  by: string | null,
  error: "std" | "stderr" | "minmax" | "none",
  sort: "x" | "y" | "-y",
): Bar[] {
  if (!answer) return [];
  const at = (c: string) => answer.columns.indexOf(c);
  const [ix, iy, ib, id] = [at(x), at(y), by ? at(by) : -1, at("run.id")];
  const cells = new Map<string, { label: string; group: string | null; values: number[]; runs: string[] }>();
  for (const r of answer.rows) {
    const v = num(r[iy]);
    if (v === null) continue;
    const label = text(r[ix]);
    const group = ib >= 0 ? text(r[ib]) : null;
    const key = JSON.stringify([label, group]);
    const cell = cells.get(key) ?? { label, group, values: [], runs: [] };
    cell.values.push(v);
    if (id >= 0) cell.runs.push(String(r[id]));
    cells.set(key, cell);
  }
  const out = [...cells.values()].map((c) => {
    const m = mean(c.values);
    const sd = c.values.length > 1 ? Math.sqrt(c.values.reduce((s, v) => s + (v - m) ** 2, 0) / (c.values.length - 1)) : 0;
    const [lo, hi] =
      error === "minmax" ? [Math.min(...c.values), Math.max(...c.values)]
      : error === "std" ? [m - sd, m + sd]
      : error === "stderr" ? [m - sd / Math.sqrt(c.values.length), m + sd / Math.sqrt(c.values.length)]
      : [m, m];  // prettier-ignore
    return { label: c.label, group: c.group, value: m, lo, hi, n: c.values.length, runs: c.runs };
  });
  const byLabel = (a: Bar, b: Bar) => natural(a.label, b.label) || natural(a.group ?? "", b.group ?? "");
  if (sort === "x") return out.sort(byLabel);
  // categories are ordered by their best bar; bars within a category keep the group order.
  const best = new Map<string, number>();
  for (const b of out) best.set(b.label, Math.max(best.get(b.label) ?? -Infinity, b.value));
  const dir = sort === "-y" ? -1 : 1;
  return out.sort((a, b) => dir * (best.get(a.label)! - best.get(b.label)!) || byLabel(a, b));
}

export type Histogram = { run: string; step: number | null; start: number[]; end: number[]; count: number[] };

// the logged tables with bin_start, bin_end and count, one per run; others are left out.
export function histograms(answer: { entries: any[] } | null): Histogram[] {
  const out: Histogram[] = [];
  for (const e of answer?.entries ?? []) {
    const c = e.columns;
    if (!c || !Array.isArray(c.bin_start) || !Array.isArray(c.bin_end) || !Array.isArray(c.count)) continue;
    out.push({ run: e.run, step: e.step ?? null, start: c.bin_start, end: c.bin_end, count: c.count });
  }
  return out;
}

// a logged table or data file as columns and rows: from {columns: {name: values}} or an answer.
export function tableOf(source: any): Answer | null {
  if (!source) return null;
  if (Array.isArray(source.columns) && Array.isArray(source.rows)) return source as Answer;
  const cols = source.columns;
  if (!cols || typeof cols !== "object") return null;
  const names = Object.keys(cols);
  const n = Math.max(0, ...names.map((k) => (Array.isArray(cols[k]) ? cols[k].length : 0)));
  return { columns: names, rows: Array.from({ length: n }, (_, i) => names.map((k) => cols[k]?.[i] ?? null)) };
}

// an axis range with a little room, on a log axis in whole decades of the positive values.
export function extent(values: number[], log: boolean, pad = 0.06): [number, number] | null {
  const vs = values.filter((v) => Number.isFinite(v) && (!log || v > 0));
  if (!vs.length) return null;
  let lo = Math.min(...vs);
  let hi = Math.max(...vs);
  if (log) {
    // padded in log space, so points at the ends stay whole.
    const [a, b] = [Math.log10(lo), Math.log10(hi)];
    const d = Math.max(b - a, 1) * pad * 2;
    return [10 ** (a - d), 10 ** (b + d)];
  }
  if (lo === hi) [lo, hi] = [lo - Math.abs(lo || 1) * 0.5, hi + Math.abs(hi || 1) * 0.5];
  const d = (hi - lo) * pad;
  return [lo - d, hi + d];
}

function mean(vs: number[]): number {
  return vs.reduce((a, b) => a + b, 0) / vs.length;
}

function text(v: unknown): string {
  return v === null || v === undefined ? "–" : typeof v === "object" ? JSON.stringify(v) : String(v);
}

function natural(a: string, b: string): number {
  const na = Number(a);
  const nb = Number(b);
  if (a !== "" && b !== "" && Number.isFinite(na) && Number.isFinite(nb)) return na - nb;
  return a.localeCompare(b);
}

// ticks on a log axis: each decade, with 2 and 5 between when there are few decades.
export function logSplits(range: [number, number]): number[] {
  const [a, b] = [Math.floor(Math.log10(range[0])), Math.ceil(Math.log10(range[1]))];
  const steps = Math.log10(range[1] / range[0]) <= 2 ? [1, 2, 5] : [1];
  const out: number[] = [];
  for (let e = a; e <= b; e++) for (const m of steps) out.push(m * 10 ** e);
  return out.filter((v) => v >= range[0] && v <= range[1]);
}

const STEPS_S = [60, 300, 900, 1800, 3600, 3 * 3600, 6 * 3600, 12 * 3600, 86400, 2 * 86400, 7 * 86400, 14 * 86400, 30 * 86400];

// ticks on a time axis (seconds): about six, at round minutes, hours or days in local time.
export function timeTicks(min: number, max: number): { at: number[]; step: number } {
  const step = STEPS_S.find((s) => (max - min) / s <= 7) ?? STEPS_S[STEPS_S.length - 1];
  const offset = step >= 86400 ? new Date(min * 1000).getTimezoneOffset() * 60 : 0;
  const at: number[] = [];
  for (let t = Math.ceil((min - offset) / step) * step + offset; t <= max; t += step) at.push(t);
  return { at, step };
}

export function timeLabel(t: number, step: number): string {
  const d = new Date(t * 1000);
  if (step >= 86400) return d.toLocaleDateString([], { month: "short", day: "numeric" });
  if (step >= 6 * 3600) return `${d.toLocaleDateString([], { month: "short", day: "numeric" })} ${d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
  const hm = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  return d.getHours() === 0 && d.getMinutes() === 0 ? d.toLocaleDateString([], { month: "short", day: "numeric" }) : hm;
}
