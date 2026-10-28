// Charts load their runtime (uPlot) on first use and stay cached afterwards.

import type { LineChart, LineSpec } from "./uplot.ts";

export type { LineChart, LineSpec };

let runtime: Promise<typeof import("./uplot.ts")> | null = null;

export function charts(): Promise<typeof import("./uplot.ts")> {
  runtime ??= import("./uplot.ts");
  return runtime;
}

export async function lineChart(el: HTMLElement, spec: LineSpec): Promise<LineChart> {
  return (await charts()).lineChart(el, spec);
}
