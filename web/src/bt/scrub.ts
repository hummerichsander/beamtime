// Stepping through the loggings of a key: the stops a scrubber offers, where a figure sits at a
// stop, and the label that says so. Pure, so it is tested without a page.

import { step as fmtStep, value } from "./fmt.ts";

export type By = "step" | "clock";
// the loggings of a key as the data answer lists them: every step, and the clock's value at each.
export type Meta = { steps?: number[]; clocks?: (number | null)[] };
// ascending: the scrubber's positions (`values`) and the step each one shows.
export type Stops = { values: number[]; steps: number[] };
export type Entry = { run: string; step: number; path: string; caption?: string };
export type Tile = { entry: Entry; earlier: boolean };

// how many stops back a run's latest earlier image is looked for.
export const BACK = 8;

export function stopsOf(meta: Meta | undefined, by: By): Stops {
  const steps = meta?.steps ?? [];
  if (by === "step") return { values: steps, steps };
  const last = new Map<number, number>();
  steps.forEach((s, i) => {
    const c = meta?.clocks?.[i];
    if (c != null && Number.isFinite(c)) last.set(c, Math.max(last.get(c) ?? s, s));
  });
  const values = [...last.keys()].sort((a, b) => a - b);
  return { values, steps: values.map((v) => last.get(v)!) };
}

// whether the clock separates loggings enough to space them by it.
export function hasClock(meta: Meta | undefined): boolean {
  return stopsOf(meta, "clock").values.length > 1;
}

// the index of the position closest to a value.
export function nearest(values: number[], v: number): number {
  let best = 0;
  values.forEach((x, i) => {
    if (Math.abs(x - v) < Math.abs(values[best] - v)) best = i;
  });
  return best;
}

// the index of the last stop at or before a step; the first when there is none.
export function indexAt(stops: Stops, at: number): number {
  let found = 0;
  stops.steps.forEach((s, i) => {
    if (s <= at) found = i;
  });
  return found;
}

// the steps a run's figure may come from for a stop: the BACK stops before it and itself.
export function windowOf(stops: Stops, i: number): [number, number] {
  return [stops.steps[Math.max(0, i - BACK)], stops.steps[i]];
}

// every run's entries at its latest step at or before `at`; one logged earlier is `earlier`.
export function shownAt(entries: Entry[], at: number): Tile[] {
  const latest = new Map<string, number>();
  for (const e of entries) if (e.step <= at && e.step > (latest.get(e.run) ?? -Infinity)) latest.set(e.run, e.step);
  return entries.filter((e) => latest.get(e.run) === e.step).map((entry) => ({ entry, earlier: entry.step < at && at !== Infinity }));
}

// "epoch 12 · step 4 000", or "step 4 000" on a page without a clock.
export function scrubLabel(clock: string | null, at: number | null, s: number): string {
  const name = clock?.split(/[/.]/).at(-1);
  const parts = name && name !== "step" && at != null ? [`${name} ${value(at)}`] : [];
  return [...parts, `step ${fmtStep(s)}`].join(" · ");
}

// the clock's value at a step of the answer.
export function clockAt(meta: Meta | undefined, s: number): number | null {
  const i = meta?.steps?.indexOf(s) ?? -1;
  return i < 0 ? null : (meta?.clocks?.[i] ?? null);
}
