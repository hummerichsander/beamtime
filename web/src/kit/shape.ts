// Results as custom blocks see them: runs as rows keyed by field, curves as plain lists.

import type { Call, Result } from "../api.ts";

export type KitCurve = {
  run: string | null;
  key: string;
  group: unknown;
  x: number[];
  y?: (number | null)[];
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

function curve(c: any): KitCurve {
  const out: KitCurve = { run: c.run ?? null, key: c.metric, group: c.by ?? null, x: c.x ?? [] };
  const fields: [keyof KitCurve, unknown][] = [
    ["y", c.y],
    ["min", c.min ?? c.lo],
    ["max", c.max ?? c.hi],
    ["last", c.last],
    ["mean", c.mean],
    ["count", c.count ?? c.n],
  ];
  for (const [k, v] of fields) if (v !== undefined) (out as any)[k] = v;
  return out;
}
