// `line`: metric curves over steps on uPlot; new points update the chart in place, keeping zoom.

import { html } from "htm/preact";
import { useContext, useEffect, useRef } from "preact/hooks";

import { hovered, useData, useRunColors, useTheme, useVisible, ViewCtx, type Node } from "../bt/index.ts";
import { reshape, type Curves } from "../bt/curves.ts";
import { step, value } from "../bt/fmt.ts";
import { lineChart, type LineChart, type LineSpec } from "../bt/plot.ts";
import { chartStyle, groupColors, type Theme } from "../bt/theme.ts";
import { Notice, Panel } from "./common.ts";

const HEIGHT = 220;

export function Line({ node }: { node: Node }) {
  const [box, visible] = useVisible();
  const result = useData(visible ? "main" : "");
  const theme = useTheme();
  const colors = useRunColors();
  const view = useContext(ViewCtx);
  const el = useRef<HTMLDivElement>(null);
  const chart = useRef<LineChart | null>(null);
  const log = node.props.scale === "log";
  const curves = result.data ? reshape(result.data, { log }) : null;

  useEffect(() => {
    if (!curves || !theme || !el.current || !curves.curves.length) return;
    const spec: LineSpec = {
      curves: curves.curves,
      colors: palette(curves, theme, colors),
      style: chartStyle(theme),
      height: HEIGHT,
      log,
      band: curves.aggregated || curves.curves.length === 1,
      sync: `view:${view.path}`,
      formatX: step,
      formatY: (v) => value(v),
      onFocus: (c) => hovered.set(c?.run ?? null),
    };
    if (chart.current?.update(spec)) return;
    let cancelled = false;
    chart.current?.destroy();
    chart.current = null;
    el.current.replaceChildren();
    void lineChart(el.current, spec).then((c) => {
      if (cancelled) c.destroy();
      else chart.current = c;
    });
    return () => {
      cancelled = true;
    };
  }, [result.data, theme, colors]);

  useEffect(() => () => chart.current?.destroy(), []);

  useEffect(
    () =>
      hovered.subscribe((run) => {
        if (chart.current && !el.current?.matches(":hover")) chart.current.focus(run);
      }),
    [],
  );

  const empty = curves && !curves.curves.length;
  return html`<div ref=${box} class="block chart-block">
    <div class="chart-head"><span class="chart-title">${node.props.title ?? node.props.y}</span>
      ${node.props.note ? html`<span class="muted small">${node.props.note}</span>` : null}</div>
    <${Panel} caption=${node.props.caption} result=${result}>
      ${empty
        ? html`<${Notice}>No run in scope logs ${node.props.y}.<//>`
        : html`<div class=${`chart${result.status === "ready" ? "" : " pending"}`} ref=${el} style=${`min-height:${HEIGHT}px`}></div>`}
    <//>
  </div>`;
}

function palette(curves: Curves, theme: Theme, colors: Map<string, string>): string[] {
  if (curves.aggregated) {
    const byLabel = groupColors(curves.curves.map((c) => c.label), theme);
    return curves.curves.map((c) => byLabel.get(JSON.stringify(c.label))!);
  }
  const cat = theme.data.categorical;
  return curves.curves.map((c, i) => (c.run && colors.get(c.run)) || cat[i % cat.length]);
}
