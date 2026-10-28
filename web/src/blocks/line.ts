// `line`: metric curves over steps; new points update the chart in place, keeping zoom.

import { html } from "htm/preact";
import { useEffect, useRef } from "preact/hooks";
import type { View } from "vega";

import { useData, useRunColors, useTheme, useVisible, type Node } from "../bt/index.ts";
import { reshape, type Curves } from "../bt/curves.ts";
import { plot, update } from "../bt/plot.ts";
import { groupColors, vegaConfig, type Theme } from "../bt/theme.ts";
import { Notice, Panel } from "./common.ts";

const HEIGHT = 200;
// steps as 0, 500, 1.5k, 12k: SI prefixes without "0k".
const STEPS = "abs(datum.value) >= 1000 ? format(datum.value / 1000, '~g') + 'k' : format(datum.value, '~g')";
const LEGEND_MAX = 8;

export function Line({ node }: { node: Node }) {
  const [box, visible] = useVisible();
  const result = useData(visible ? "main" : "");
  const theme = useTheme();
  const colors = useRunColors();
  const el = useRef<HTMLDivElement>(null);
  const chart = useRef<{ view: View; signature: string } | null>(null);
  const log = node.props.scale === "log";
  const curves = result.data ? reshape(result.data, { log }) : null;

  useEffect(() => {
    if (!curves || !theme || !el.current || !curves.points.length) return;
    const domain = curves.keys.map((k) => curves.labels.get(k)!);
    const range = palette(curves, theme, colors);
    const signature = JSON.stringify([domain, range, theme.name, theme.type, log]);
    const data = { points: curves.points };
    if (chart.current?.signature === signature) {
      void update(chart.current.view, data);
      return;
    }
    let cancelled = false;
    chart.current?.view.finalize();
    chart.current = null;
    void plot(el.current, spec(node, curves, domain, range), vegaConfig(theme), data).then((view) => {
      if (cancelled) view.finalize();
      else chart.current = { view, signature };
    });
    return () => {
      cancelled = true;
    };
  }, [result.data, theme, colors]);

  useEffect(() => () => chart.current?.view.finalize(), []);

  const empty = curves && !curves.points.length;
  return html`<div ref=${box}><${Panel} title=${node.props.title} caption=${node.props.caption} result=${result}>
    ${empty
      ? html`<${Notice}>No run in scope logs ${node.props.y}.<//>`
      : html`<div class=${`chart${result.status === "ready" ? "" : " pending"}`} ref=${el} style=${`height:${HEIGHT}px`}></div>`}
  <//></div>`;
}

function palette(curves: Curves, theme: Theme, colors: Map<string, string>): string[] {
  if (curves.grouped) {
    const byLabel = groupColors(curves.keys.map((k) => curves.labels.get(k)), theme);
    return curves.keys.map((k) => byLabel.get(JSON.stringify(curves.labels.get(k)))!);
  }
  const cat = theme.data.categorical;
  return curves.keys.map((k, i) => colors.get(k.split(":")[0]) ?? cat[i % cat.length]);
}

function spec(node: Node, curves: Curves, domain: string[], range: string[]): Record<string, any> {
  const x = { field: "x", type: "quantitative", title: node.props.x ?? "step", axis: { labelExpr: STEPS } };
  const y = {
    field: "y",
    type: "quantitative",
    title: node.props.y,
    scale: node.props.scale === "log" ? { type: "log" } : { zero: false },
    axis: { format: "~g" },
  };
  const color = {
    field: "label",
    type: "nominal",
    scale: { domain, range },
    legend: domain.length > 1 && domain.length <= LEGEND_MAX ? { title: null, orient: "right" } : null,
  };
  const band = curves.grouped || curves.keys.length === 1;
  const layers: Record<string, any>[] = [];
  if (band && curves.points.some((p) => p.lo !== null)) {
    layers.push({
      mark: { type: "area", opacity: 0.15, interpolate: "linear" },
      encoding: { x, y: { field: "lo", type: "quantitative" }, y2: { field: "hi" }, color, detail: { field: "key" } },
    });
  }
  layers.push({
    mark: { type: "line", interpolate: "linear", clip: true },
    encoding: { x, y, color, detail: { field: "key" } },
    params: [{ name: "zoom", select: { type: "interval", encodings: ["x"] }, bind: "scales" }],
  });
  layers.push({
    mark: { type: "point", opacity: 0, size: 80 },
    encoding: {
      x,
      y,
      tooltip: [
        { field: "label", title: curves.grouped ? "aggregate" : "run" },
        { field: "x", title: "step", format: "," },
        { field: "y", title: node.props.y, format: ".4~g" },
        ...(curves.grouped ? [{ field: "n", title: "runs" }] : []),
      ],
    },
  });
  return {
    $schema: "https://vega.github.io/schema/vega-lite/v6.json",
    width: "container",
    height: HEIGHT - 44,
    autosize: { type: "fit-x", contains: "padding" },
    data: { name: "points" },
    transform: [{ filter: "isValid(datum.y)" }],
    layer: layers,
  };
}
