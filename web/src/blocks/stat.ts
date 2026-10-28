// `stat`: one number over the block's runs: a count, the best value, the last value.

import { html } from "htm/preact";

import { useData, type Node } from "../bt/index.ts";
import { value } from "../bt/fmt.ts";
import { matches, rows } from "./common.ts";

export function aggregate(values: unknown[], how: string): unknown {
  const nums = values.filter((v): v is number => typeof v === "number" && Number.isFinite(v));
  switch (how) {
    case "count":
      return values.length;
    case "max":
    case "best":
      return nums.length ? Math.max(...nums) : null;
    case "min":
      return nums.length ? Math.min(...nums) : null;
    case "mean":
      return nums.length ? nums.reduce((a, b) => a + b, 0) / nums.length : null;
    case "last":
      return values.length ? values[values.length - 1] : null;
    default:
      throw new Error(`unknown aggregate ${how}`);
  }
}

export function Stat({ node }: { node: Node }) {
  const result = useData("main");
  const p = node.props;
  const selected = rows(result.data).filter((r) => matches(r, p.where));
  const v = result.data ? aggregate(p.field ? selected.map((r) => r[p.field]) : selected, p.aggregate ?? "count") : null;
  const live = selected.some((r) => r["run.status"] === "running") && p.aggregate !== "count";
  return html`<div class="stat" data-tip=${v === null ? undefined : String(v)}>
    <div class="stat-label">${p.title ?? p.field}</div>
    <div class=${`stat-value${live ? " live" : ""}${result.status === "loading" ? " pending" : ""}`}>
      ${result.status === "loading" ? " " : value(v)}
    </div>
  </div>`;
}

