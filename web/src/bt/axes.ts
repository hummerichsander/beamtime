// The titles a chart's axes get when its view doesn't write them.

import { label } from "./fmt.ts";
import type { MetricInfo } from "./index.ts";

type Metrics = Record<string, MetricInfo>;

const CLOCKS: Record<string, string> = { _step: "step", epoch: "epoch", _t: "wall time", _elapsed: "elapsed" };

// a metric as its label and unit from the view's `metrics`, else its key.
export function metricTitle(key: string, metrics: Metrics): string {
  const info = metrics[key];
  return `${info?.label ?? key}${info?.unit ? ` (${info.unit})` : ""}`;
}

// the x axis: a clock by name, else the metric that is x.
export function xTitle(x: string, metrics: Metrics): string {
  return CLOCKS[x] ?? metricTitle(x, metrics);
}

// the y axis: one metric by its title, several by the path they share, or none.
export function yTitle(keys: string[], metrics: Metrics): string {
  if (keys.length === 1) return metricTitle(keys[0], metrics);
  const paths = keys.map((k) => k.split("/").slice(0, -1));
  const shared: string[] = [];
  for (const [i, part] of (paths[0] ?? []).entries()) {
    if (!paths.every((p) => p[i] === part)) break;
    shared.push(part);
  }
  return shared.join("/");
}

// a run field (`metric.val/loss.min`, `config.lr`) as an axis title.
export function fieldTitle(field: string, metrics: Metrics): string {
  const m = /^metric\.(.+)\.(last|first|min|max|mean|count|ema_last|last_step)$/.exec(field);
  const info = m ? metrics[m[1]] : undefined;
  if (!m || !info) return label(field);
  const name = info.label ?? m[1];
  return `${m[2] === "last" ? name : `${name} ${m[2].replace("_", " ")}`}${info.unit ? ` (${info.unit})` : ""}`;
}
