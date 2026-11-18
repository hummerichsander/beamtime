// Results as custom blocks see them: runs as rows keyed by field, curves as plain lists.

import type { Call, Result } from "../api.ts";

export type KitCurve = {
  run: string | null;
  key: string;
  group: unknown;
  x: number[];
  y?: (number | null)[];
  lo?: (number | null)[];
  hi?: (number | null)[];
  n?: (number | null)[];
  min?: (number | null)[];
  max?: (number | null)[];
  last?: (number | null)[];
  mean?: (number | null)[];
  count?: (number | null)[];
};

export type KitResult = {
  status: Result["status"];
  error: string | null;
  meta: { refreshing: boolean };
  // the call behind the result, so a kit component given it as `data` subscribes to the same answer.
  call: Call | null;
  data: any;
  columns: string[];
  rows: Record<string, any>[];
  curves: KitCurve[];
};

export function shape(result: Result, call: Call | null): KitResult {
  const d = result.data;
  const columns: string[] = Array.isArray(d?.columns) ? d.columns : [];
  const rows = columns.length && Array.isArray(d?.rows)
    ? d.rows.map((r: unknown[]) => Object.fromEntries(columns.map((c, i) => [c, r[i]])))
    : [];  // prettier-ignore
  const curves: KitCurve[] = Array.isArray(d?.curves) ? d.curves.map(curve) : [];
  return { status: result.status, error: result.error, meta: { refreshing: result.refreshing }, call, data: d, columns, rows, curves };
}

// why a kit component can't draw its `data`, or null: it takes a `bt.useData` result, not hand-built rows.
export function dataProblem(data: unknown): string | null {
  if (data === undefined) return null;
  const given = data as Partial<KitResult> | null;
  if (typeof given !== "object" || given === null || Array.isArray(given) || !("call" in given)) return "data must be a bt.useData result";
  if (given.call) return null;
  return given.error ?? "data must be a bt.useData result";
}

function curve(c: any): KitCurve {
  const out: KitCurve = { run: c.run ?? null, key: c.metric, group: c.by ?? null, x: c.x ?? [] };
  const fields: [keyof KitCurve, unknown][] = [
    ["y", c.y],
    ["lo", c.lo],
    ["hi", c.hi],
    ["n", c.n],
    ["min", c.min ?? c.lo],
    ["max", c.max ?? c.hi],
    ["last", c.last],
    ["mean", c.mean],
    ["count", c.count ?? c.n],
  ];
  for (const [k, v] of fields) if (v !== undefined) (out as any)[k] = v;
  return out;
}
