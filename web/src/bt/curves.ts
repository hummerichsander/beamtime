// Reshape `series` answers into long rows for charts: one row per point and curve.

export type Point = {
  key: string;
  label: string;
  run: string | null;
  x: number;
  y: number | null;
  lo: number | null;
  hi: number | null;
  n: number | null;
};

export type Curves = { points: Point[]; keys: string[]; labels: Map<string, string>; grouped: boolean };

export function reshape(answer: { curves: any[] }, opts: { log?: boolean } = {}): Curves {
  const curves = answer.curves ?? [];
  const grouped = curves.some((c) => "by" in c);
  const labels = grouped ? groupLabels(curves.map((c) => c.by)) : runLabels(curves);
  const points: Point[] = [];
  const keys: string[] = [];
  curves.forEach((c, i) => {
    const key = grouped ? `g${i}:${c.metric}` : `${c.run}:${c.metric}`;
    const label = labels[i] + (new Set(curves.map((d) => d.metric)).size > 1 ? ` · ${c.metric}` : "");
    keys.push(key);
    const xs: number[] = c.x ?? [];
    xs.forEach((x, j) => {
      const p: Point = { key, label, run: grouped ? null : c.run, x, y: null, lo: null, hi: null, n: null };
      if (grouped) {
        p.y = c.mean[j];
        p.lo = c.lo?.[j] ?? null;
        p.hi = c.hi?.[j] ?? null;
        p.n = c.n?.[j] ?? null;
      } else if (c.raw) {
        p.y = c.y[j];
      } else {
        p.y = c.last[j];
        p.lo = c.min[j];
        p.hi = c.max[j];
        p.n = c.count[j];
      }
      if (opts.log) {
        if (p.y !== null && p.y <= 0) p.y = null;
        if (p.lo !== null && p.lo <= 0) p.lo = null;
      }
      points.push(p);
    });
  });
  return { points, keys, labels: new Map(keys.map((k, i) => [k, points.find((p) => p.key === k)?.label ?? labels[i]])), grouped };
}

export function groupLabels(groups: Record<string, unknown>[]): string[] {
  const fields = [...new Set(groups.flatMap((g) => Object.keys(g ?? {})))];
  const varying = fields.filter((f) => new Set(groups.map((g) => JSON.stringify(g?.[f]))).size > 1);
  const shown = varying.length ? varying : fields;
  return groups.map((g) =>
    shown.map((f) => `${f.replace(/^config\./, "")}=${format(g?.[f])}`).join(", ") || "all runs",
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
