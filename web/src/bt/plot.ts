// Charts load their runtime (uPlot) on first use and stay cached afterwards.

import { busy } from "../api.ts";
import type { LineChart, LineSpec, Plot, PlotSpec } from "./uplot.ts";

export type { LineChart, LineSpec, Plot, PlotSpec };

let runtime: Promise<typeof import("./uplot.ts")> | null = null;

export function charts(): Promise<typeof import("./uplot.ts")> {
  runtime ??= import("./uplot.ts");
  return runtime;
}

export async function lineChart(el: HTMLElement, spec: LineSpec): Promise<LineChart> {
  busy.n++;
  try {
    const runtime = await charts();
    return spec.trajectory ? runtime.trajectoryChart(el, spec) : runtime.lineChart(el, spec);
  } finally {
    busy.n--;
  }
}

export async function plotChart(el: HTMLElement, spec: PlotSpec): Promise<Plot> {
  busy.n++;
  try {
    return (await charts()).plotChart(el, spec);
  } finally {
    busy.n--;
  }
}
