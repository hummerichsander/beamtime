// Reshape `series` answers into curves and align them on one x axis for uPlot.

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

function format(v: unknown): string {
  return typeof v === "number" ? String(Number(v.toPrecision(4))) : String(v);
}
