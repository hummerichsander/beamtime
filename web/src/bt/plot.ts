// `bt.plot`: Vega-Lite with the theme merged in, loading Vega on first use.

import type { View } from "vega";

let runtime: Promise<typeof import("./vega.ts")> | null = null;

export function vega(): Promise<typeof import("./vega.ts")> {
  runtime ??= import("./vega.ts");
  return runtime;
}

export async function plot(
  el: HTMLElement,
  spec: Record<string, any>,
  config: Record<string, unknown>,
  data: Record<string, unknown[]>,
): Promise<View> {
  return (await vega()).render(el, spec, config, data);
}

export async function update(view: View, data: Record<string, unknown[]>): Promise<void> {
  (await vega()).replace(view, data);
}
