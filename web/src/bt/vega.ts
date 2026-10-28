// The Vega runtime, loaded only when a chart is on screen: CSP-safe and without URL loading.

import { loader, parse, View } from "vega";
import { expressionInterpreter } from "vega-interpreter";
import { compile } from "vega-lite";
import { Handler } from "vega-tooltip";

const refusing = loader();
refusing.load = () => Promise.reject(new Error("Beamtime charts load data only from declared queries"));
refusing.sanitize = () => Promise.reject(new Error("Beamtime charts load no URLs"));

const tooltip = new Handler({ disableDefaultStyle: true, theme: "bt", offsetX: 12, offsetY: 12 });

export function render(
  el: HTMLElement,
  spec: Record<string, any>,
  config: Record<string, unknown>,
  data: Record<string, unknown[]>,
): View {
  const vg = compile(spec as any, { config: config as any }).spec;
  const view = new View(parse(vg, undefined, { ast: true }), {
    expr: expressionInterpreter as any,
    loader: refusing,
    renderer: "canvas",
    container: el,
    hover: true,
    tooltip: tooltip.call,
  });
  for (const [name, values] of Object.entries(data)) view.data(name, values);
  void view.runAsync();
  return view;
}

export function replace(view: View, data: Record<string, unknown[]>): void {
  for (const [name, values] of Object.entries(data)) view.data(name, values);
  void view.runAsync();
}
