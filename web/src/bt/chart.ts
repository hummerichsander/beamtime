// What every chart shares: building it once its element exists, updating it in place or
// rebuilding, following the theme and the page's hovered run, and its PNG.

import { type RefObject } from "preact";
import { useEffect, useRef } from "preact/hooks";

import { hovered } from "./index.ts";
import { offscreen, type Background } from "./export.ts";

export type Chartlike<S> = {
  // false when the chart can't take the spec in place and must be built again.
  update(spec: S): boolean | void;
  focus(key: string | null): void;
  png(background: string | null): string;
  destroy(): void;
};

// builds the chart in el when spec arrives, updates it as deps change, rebuilds it for a new theme.
export function useChart<S, C extends Chartlike<S>>(
  el: RefObject<HTMLElement>,
  build: (el: HTMLElement, spec: S) => Promise<C>,
  spec: S | null,
  deps: unknown[],
  theme: unknown,
): RefObject<C | null> {
  const chart = useRef<C | null>(null);
  useEffect(() => {
    if (!spec || !el.current) return;
    if (chart.current && chart.current.update(spec) !== false) return;
    chart.current?.destroy();
    chart.current = null;
    el.current.replaceChildren();
    let cancelled = false;
    void build(el.current, spec).then((c) => {
      if (cancelled) c.destroy();
      else chart.current = c;
    });
    return () => {
      cancelled = true;
    };
  }, [spec === null, theme, ...deps]);
  // axes and grid take their colors when a chart is built: another theme builds it again.
  useEffect(
    () => () => {
      chart.current?.destroy();
      chart.current = null;
      el.current?.replaceChildren();
    },
    [theme],
  );
  // a run hovered anywhere on the page is highlighted here, unless the pointer is on this chart.
  useEffect(
    () =>
      hovered.subscribe((run) => {
        if (chart.current && !el.current?.matches(":hover")) chart.current.focus(run);
      }),
    [],
  );
  return chart;
}

// a chart's PNG, drawn offscreen in the given spec (the light theme for figures).
export function png<S, C extends Chartlike<S>>(
  width: number,
  build: (el: HTMLElement, spec: S) => Promise<C>,
  spec: S,
  background: Background,
): Promise<string> {
  return offscreen(width, (div) => build(div, spec), background);
}
