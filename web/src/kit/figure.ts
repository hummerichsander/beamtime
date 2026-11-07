// `bt.chart.Figure`: a drawing no block can make (d3, SVG or canvas) inside Beamtime's chart frame, which
// supplies the head, the settings, the legend with hide and solo, hover both ways, downloads and the
// viewer's preferences. The drawing is `draw(el, context)`; it runs again when its inputs change.

import { html } from "htm/preact";
import type { ComponentChildren } from "preact";
import { useEffect, useId, useRef, useState } from "preact/hooks";

import { Legend, ChartFrame, HEIGHT, type LegendItem } from "../bt/frame.ts";
import { fileName } from "../bt/export.ts";
import { host as page } from "../bt/host.ts";
import { hovered, useTheme, type ViewContext } from "../bt/index.ts";
import { effective, toggleRun, usePrefs, type ChartPrefs, type Effective } from "../bt/prefs.ts";
import { swatch } from "../bt/theme.ts";
import { Settings, type Field } from "../blocks/line-settings.ts";
import { Store, useStore } from "../state.ts";
import { pngOf, svgOf } from "./snapshot.ts";

export type FigureSeries = { key: string; label: string; color: string };

export type DrawContext = {
  width: number;
  height: number;
  prefs: Effective;
  // the run or key hovered anywhere on the page.
  hovered: string | null;
  // the keys the viewer hid in the legend.
  hidden: Set<string>;
  xlabel?: string;
  ylabel?: string;
};

export type FigureProps = {
  id?: string;
  title: string;
  xlabel?: string;
  ylabel?: string;
  series?: FigureSeries[];
  // the settings the chart offers: any of the line chart's panel fields ("x", "scale", "smooth", "colormap", …).
  settings?: Field[];
  // the choices the figure starts with, under the viewer's.
  defaults?: ChartPrefs;
  // a CSV download: rows as objects, or arrays with the header first.
  csv?: (Record<string, unknown> | unknown[])[];
  height?: number;
  caption?: string;
  draw: (el: HTMLDivElement, context: DrawContext) => void;
  children?: ComponentChildren;
};

type Env = { view: Store<ViewContext>; own(): void; warn(message: string): void };

export function makeFigure(env: Env) {
  return function Figure(props: FigureProps) {
    const own = `figure-${useId().replace(/\W/g, "")}`;
    const id = props.id ?? own;
    const path = env.view.value.path;
    const all = usePrefs(path);
    const prefs = effective(props.defaults ?? {}, all, id);
    const theme = useTheme();
    const active = useStore(hovered);
    const el = useRef<HTMLDivElement>(null);
    const [width, setWidth] = useState(0);
    const height = props.height ?? HEIGHT;
    const hidden = new Set(all.hidden);

    useEffect(() => env.own(), []);

    useEffect(() => {
      if (!el.current) return;
      const ro = new ResizeObserver(([e]) => setWidth(Math.round(e.contentRect.width)));
      ro.observe(el.current);
      return () => ro.disconnect();
    }, []);

    // a new `draw` means new data from the block; the rest is the figure's own inputs, so another chart's
    // settings never redraw this one.
    const inputs = JSON.stringify([prefs, active, all.hidden, width, height]);
    useEffect(() => {
      if (el.current && width) props.draw(el.current, { width, height, prefs, hovered: active, hidden, xlabel: props.xlabel, ylabel: props.ylabel });
    }, [props.draw, inputs, theme]);

    const series = props.series ?? [];
    const keys = series.map((s) => s.key);
    const items: LegendItem[] =
      prefs.legend && series.length > 1
        ? series.map((s) => ({
            label: s.label,
            mark: swatch(s.color, theme),
            off: hidden.has(s.key),
            tip: "Click to hide or show; double-click to show only this",
            onHover: (on) => hovered.set(on ? s.key : null),
            onClick: (e) => e.detail < 2 && toggleRun(path, s.key, keys),
            onDblClick: () => toggleRun(path, s.key, keys, true),
          }))
        : [];

    const save = (href: string | null, ext: string) => (href ? page().download(href, fileName(props.title, ext)) : env.warn("it draws no SVG or canvas to download"));
    const downloads = {
      png: async (background: "transparent" | "white") => save(await pngOf(el.current!, background), "png"),
      svg: () => save(svgOf(el.current!), "svg"),
      csv: props.csv?.length ? () => save(csvOf(props.csv!), "csv") : undefined,
    };

    return html`<${ChartFrame} id=${id} title=${props.title} downloads=${downloads} caption=${props.caption}
        tools=${props.settings?.length ? html`<${Settings} id=${id} path=${path} prefs=${prefs} y=${[]} fields=${props.settings} keepsRunColors=${false} />` : null}
        legend=${items.length ? html`<${Legend} items=${items} label="Show or hide series" role="group" />` : null}>
      <div class="chart-plot" ref=${el} style=${`min-block-size:${height}px`}></div>
      ${props.children}
    <//>`;
  };
}

function csvOf(rows: (Record<string, unknown> | unknown[])[]): string {
  const table = Array.isArray(rows[0]) ? (rows as unknown[][]) : [Object.keys(rows[0]), ...rows.map((r) => Object.values(r))];
  const cell = (v: unknown) => {
    const s = v === null || v === undefined ? "" : String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  return `data:text/csv;charset=utf-8,${encodeURIComponent(table.map((r) => r.map(cell).join(",")).join("\n"))}`;
}
