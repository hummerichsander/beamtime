// `window.bt` inside a custom block's frame: data hooks over the bridge, the built-in blocks as
// components that take their data as a prop, the theme, formatting, links and the declared libraries.

import { h, render, toChildArray, type ComponentChildren, type RefObject, type VNode } from "preact";
import * as hooks from "preact/hooks";
import { useContext, useEffect, useId, useRef, useState } from "preact/hooks";
import { html } from "htm/preact";

import { fetchCall, useCall, watch, type Call } from "../api.ts";
import { Box, type Registry } from "../blocks/box.ts";
import { DataTable } from "../blocks/data.ts";
import { Line } from "../blocks/line.ts";
import { BarBlock, HistogramBlock, Scatter } from "../blocks/plots.ts";
import { Stat } from "../blocks/stat.ts";
import { Table } from "../blocks/table.ts";
import { Notice } from "../blocks/common.ts";
import { Predictions } from "../blocks/predictions.ts";
import { ConfigTree } from "../ui/config.ts";
import { Icon, Sym } from "../ui/icons.ts";
import { Tag } from "../ui/primitives.ts";
import { symbolFor, type Kind, type Tone } from "../ui/symbols.ts";
import { hovered, runColors, theme, ViewCtx, type Node, type ViewContext } from "../bt/index.ts";
import * as fmt from "../bt/fmt.ts";
import { lineChart } from "../bt/plot.ts";
import { dashOf, groupColors, palette, ramp, stopsOf } from "../bt/theme.ts";
import { groupUrl, runUrl } from "../router.ts";
import { Store, useStore } from "../state.ts";
import { makeFigure } from "./figure.ts";
import { fill, placeholders } from "./protocol.ts";
import { shape, type KitResult } from "./shape.ts";

// the built-in blocks a custom block can use: only these come into its frame.
const KIT_BLOCKS: Registry = {
  line: Line,
  scatter: Scatter,
  bar: BarBlock,
  histogram: HistogramBlock,
  table: Table,
  stat: Stat,
  data_table: DataTable,
};

export type Host = {
  queries: Record<string, Call>;
  params: Record<string, unknown>;
  view: Store<ViewContext>;
  libs: Record<string, unknown>;
  warn(message: string): void;
  // the block draws its own chart head (a `Figure`); the page leaves out its own.
  own(): void;
};

export function makeKit(host: Host) {
  // a declared query with its placeholders filled; null while one is still open.
  const resolve = (name: string, values: Record<string, unknown> = {}): Call => {
    const declared = host.queries[name];
    if (!declared) {
      const known = Object.keys(host.queries);
      throw new Error(`no query '${name}' is declared; the block declares ${known.length ? known.join(", ") : "none"}`);
    }
    const call = fill(declared, values);
    const open = [...placeholders(call.params)];
    if (open.length) throw new Error(`query '${name}' needs ${open.map((p) => `$${p}`).join(", ")}: bt.useData("${name}", {${open[0]}: …})`);
    return call;
  };

  function useData(name: string, values?: Record<string, unknown>): KitResult {
    let call: Call | null = null;
    let problem: string | null = null;
    try {
      call = resolve(name, values);
    } catch (e) {
      problem = (e as Error).message;
    }
    const result = useCall(call);
    if (problem) return shape({ status: "error", data: null, error: problem, refreshing: false }, null);
    return shape(result, call);
  }

  // the built-in block of that name, with YAML props and the result of a declared query as `data`.
  const component = (block: string, fill?: (props: any, data: KitResult | undefined) => void) =>
    function KitBlock(props: Record<string, any>) {
      const { data, id, ...rest } = props;
      fill?.(rest, data);
      // each chart its own id, so two charts of a block keep their own settings.
      const own = `${block}-${useId().replace(/\W/g, "")}`;
      const node: Node = { block, id: id ?? own, props: rest, data: data?.call ? { main: data.call } : undefined };
      return html`<${ViewCtx.Provider} value=${useStore(host.view)}><${Box} node=${node} blocks=${KIT_BLOCKS} /><//>`;
    };
  const metricsFrom = (props: any, data: KitResult | undefined) => {
    props.y ??= data?.call?.params.y;
  };

  function Grid(props: { columns?: number; min_width?: number; children?: ComponentChildren }) {
    const style = props.columns
      ? `grid-template-columns: repeat(${props.columns}, minmax(0, 1fr))`
      : `grid-template-columns: repeat(auto-fill, minmax(min(${props.min_width ?? 320}px, 100%), 1fr))`;
    return html`<div class="grid" style=${style}>${props.children}</div>`;
  }
  const Row = (props: { children?: ComponentChildren }) => html`<div class="row">${props.children}</div>`;
  function Section(props: { title?: string; children?: ComponentChildren }) {
    if (!props.title) return html`<div class="stack">${props.children}</div>`;
    return html`<section class="section"><h3 class="section-title">${props.title}</h3><div class="stack">${props.children}</div></section>`;
  }
  const Tab = (props: { title: string; children?: ComponentChildren }) => html`<div class="stack">${props.children}</div>`;
  function Tabs(props: { children?: ComponentChildren }) {
    const tabs = toChildArray(props.children) as VNode<{ title: string }>[];
    const [open, setOpen] = useState(0);
    return html`<div class="tabs">
      <div class="tab-list" role="tablist">
        ${tabs.map((t, i) => html`<button type="button" role="tab" aria-selected=${i === open} onClick=${() => setOpen(i)}>${t.props.title}</button>`)}
      </div>
      ${tabs[open] ?? null}
    </div>`;
  }

  function PredictionRows(props: { of?: string }) {
    const path = props.of ?? host.view.value.path;
    const check = useCall({ method: "check", params: { group: path }, scope: path });
    return html`<${Predictions} predictions=${check.data?.predictions} />`;
  }

  function useSize(): [RefObject<HTMLDivElement>, number] {
    const ref = useRef<HTMLDivElement>(null);
    const [width, setWidth] = useState(0);
    useEffect(() => {
      if (!ref.current) return;
      const ro = new ResizeObserver(([e]) => setWidth(Math.round(e.contentRect.width)));
      ro.observe(ref.current);
      return () => ro.disconnect();
    }, []);
    return [ref, width];
  }

  return {
    version: 2,
    preact: { h, render, html, ...hooks },
    useData,
    // a library block's params, as the view gives them (defaults filled in).
    params: host.params,
    data: (name: string, values?: Record<string, unknown>) => fetchCall(resolve(name, values)),
    subscribe(name: string, callback: (r: KitResult) => void, values?: Record<string, unknown>) {
      const call = resolve(name, values);
      return watch(call, (r) => callback(shape(r, call)));
    },
    ui: {
      Grid,
      Row,
      Section,
      Tabs,
      Tab,
      Table: component("table"),
      Stat: component("stat"),
      DataTable: component("data_table"),
      Config: ConfigTree,
      // the app's symbol for a value of a kind: run status, prediction result, verdict, note type, research status.
      Sym: (props: { kind: Kind; value?: string | null; word?: boolean; size?: number }) =>
        html`<${Sym} spec=${symbolFor(props.kind, props.value)} word=${props.word} size=${props.size} />`,
      Icon,
      Tag,
      // the predictions of a group (default: the view's) with their live check, like the `proposal` block's.
      Predictions: PredictionRows,
      Note: (props: { kind?: string; children?: ComponentChildren }) => html`<${Notice} kind=${props.kind}>${props.children}<//>`,
    },
    chart: {
      Line: component("line", metricsFrom),
      Scatter: component("scatter"),
      Bar: component("bar"),
      Histogram: component("histogram"),
      line: lineChart,
      Figure: makeFigure(host),
    },
    theme: {
      get tokens() {
        return theme.value;
      },
      get mode() {
        return theme.value?.type ?? "light";
      },
      onChange: (cb: (t: unknown) => void) => theme.subscribe(cb),
      // the color of good, bad, warn, muted or accent in the current theme.
      tone(name: Tone): string {
        const t = theme.value;
        if (!t) throw new Error("no theme yet");
        const color = t.colors[name];
        if (!color) throw new Error(`no tone ${name}; use good, bad, warn, muted or accent`);
        return color;
      },
      runColor: (id: string) => host.view.value.colors.get(id) ?? runColors([id], theme.value).get(id),
      groupColor: (values: unknown[], value: unknown): string | undefined => (theme.value ? groupColors(values, theme.value).get(JSON.stringify(value)) : undefined),
      runDash(id: string): number[] {
        const color = host.view.value.colors.get(id) ?? runColors([id], theme.value).get(id);
        return theme.value ? dashOf(color, theme.value) : [];
      },
      // the built-in ramp of a kind, or a named colormap (any family) from the chart's settings.
      scale(kind: "sequential" | "diverging" | "categorical", name?: string | null) {
        const t = theme.value;
        if (!t) throw new Error("no theme yet");
        switch (kind) {
          case "categorical": {
            const colors = palette(t);
            return (i: number) => colors[i % colors.length];
          }
          case "sequential":
          case "diverging": {
            const stops = name ? stopsOf(name) : t.ramps[kind];
            if (!stops) throw new Error(`no colormap ${name}`);
            return (x: number) => ramp(stops, Math.min(1, Math.max(0, x)));
          }
          default:
            throw new Error(`no scale ${kind}`);
        }
      },
    },
    fmt,
    label: fmt.label,
    name: (run: string) => host.view.value.names.get(run) ?? run,
    link: { run: runUrl, group: groupUrl },
    useSize,
    useContext,
    // the run hovered anywhere on the page: set it to highlight a run in every chart, read it to follow.
    hover: (run: string | null) => hovered.set(run),
    useHovered: () => useStore(hovered),
    warn: (message: string) => host.warn(message),
    lib: host.libs,
  };
}
