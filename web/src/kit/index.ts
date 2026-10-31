// `window.bt` inside a custom block's frame: data hooks over the bridge, the built-in blocks as
// components that take their data as a prop, the theme, formatting, links and the declared libraries.

import { h, render, toChildArray, type ComponentChildren, type RefObject, type VNode } from "preact";
import * as hooks from "preact/hooks";
import { useContext, useEffect, useId, useRef, useState } from "preact/hooks";
import { html } from "htm/preact";

import { fetchCall, useCall, watch, type Call } from "../api.ts";
import { Block } from "../blocks/index.ts";
import { Notice } from "../blocks/common.ts";
import { runColors, theme, ViewCtx, type Node, type ViewContext } from "../bt/index.ts";
import * as fmt from "../bt/fmt.ts";
import { lineChart } from "../bt/plot.ts";
import { groupColors, ramp } from "../bt/theme.ts";
import { groupUrl, runUrl } from "../router.ts";
import { Store, useStore } from "../state.ts";
import { fill, placeholders } from "./protocol.ts";
import { shape, type KitResult } from "./shape.ts";

export type Host = {
  queries: Record<string, Call>;
  params: Record<string, unknown>;
  view: Store<ViewContext>;
  libs: Record<string, unknown>;
  warn(message: string): void;
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
      return html`<${ViewCtx.Provider} value=${useStore(host.view)}><${Block} node=${node} /><//>`;
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
    version: 1,
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
      Note: (props: { kind?: string; children?: ComponentChildren }) => html`<${Notice} kind=${props.kind}>${props.children}<//>`,
    },
    chart: {
      Line: component("line", metricsFrom),
      Scatter: component("scatter"),
      Bar: component("bar"),
      Histogram: component("histogram"),
      line: lineChart,
    },
    theme: {
      get tokens() {
        return theme.value;
      },
      get mode() {
        return theme.value?.type ?? "light";
      },
      onChange: (cb: (t: unknown) => void) => theme.subscribe(cb),
      runColor: (id: string) => host.view.value.colors.get(id) ?? runColors([id], theme.value).get(id),
      groupColor: (values: unknown[], value: unknown): string | undefined => (theme.value ? groupColors(values, theme.value).get(JSON.stringify(value)) : undefined),
      scale(kind: "sequential" | "diverging" | "categorical") {
        const d: any = theme.value?.data ?? {};
        switch (kind) {
          case "categorical":
            return (i: number) => d.categorical[i % d.categorical.length];
          case "sequential":
          case "diverging":
            return (t: number) => ramp(d[kind], Math.min(1, Math.max(0, t)));
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
    warn: (message: string) => host.warn(message),
    lib: host.libs,
  };
}
