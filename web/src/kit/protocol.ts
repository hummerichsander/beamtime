// The bridge between the page and a custom block's frame: the messages, the calls a frame may
// make, and placeholders in declared queries.

import type { Call, Result } from "../api.ts";
import type { MetricInfo, Node } from "../bt/index.ts";
import type { ViewPrefs } from "../bt/prefs.ts";
import type { Colormaps, Pair, Theme } from "../bt/theme.ts";

export type Init = {
  id: string;
  code: string;
  libs: string[];
  path: string;
  queries: Record<string, Call>;
  params: Record<string, unknown>;
  theme: Theme | null;
  // both themes: figures leave in the light one.
  pair: Pair | null;
  colormaps: Colormaps | null;
  prefs: ViewPrefs;
  names: [string, string][];
  colors: [string, string][];
  metrics: Record<string, MetricInfo>;
};

export type ToFrame =
  | { type: "ping" }
  | { type: "init"; init: Init }
  | { type: "theme"; theme: Theme }
  | { type: "context"; names: [string, string][]; colors: [string, string][]; metrics: Record<string, MetricInfo> }
  | { type: "result"; id: string; result: Result }
  | { type: "hover"; run: string | null }
  | { type: "prefs"; prefs: ViewPrefs }
  // the page's download button: the frame answers with an SVG or PNG of what it draws.
  | { type: "snapshot" };

export type ToPage =
  | { type: "hello" }
  | { type: "sub"; id: string; call: Call }
  | { type: "unsub"; id: string }
  | { type: "navigate"; url: string }
  | { type: "height"; height: number }
  | { type: "ready"; blank: boolean; overflow: boolean }
  | { type: "warn"; message: string }
  | { type: "error"; message: string }
  | { type: "hover"; run: string | null }
  | { type: "prefs"; prefs: ViewPrefs }
  | { type: "download"; href: string; name: string }
  | { type: "figure"; spec: Record<string, unknown>; name: string }
  | { type: "expand"; node: Node }
  | { type: "snapshot"; href: string | null; name: string };

// what a frame may ask the page for: reading operations only.
export const READS = new Set([
  "keys",
  "runs",
  "series",
  "data",
  "timeline",
  "groups",
  "file",
  "query",
  "notes",
  "check",
  "card",
  "output",
  "proposal_show",
  "memory_show",
]);

const PLACEHOLDER = /^\$([A-Za-z_][\w]*)$/;

// the placeholder names a call still has, e.g. ["run"] for {from: "$run"}.
export function placeholders(value: unknown, out: Set<string> = new Set()): Set<string> {
  if (typeof value === "string") {
    const m = PLACEHOLDER.exec(value);
    if (m) out.add(m[1]);
  } else if (Array.isArray(value)) {
    for (const v of value) placeholders(v, out);
  } else if (value && typeof value === "object") {
    for (const v of Object.values(value)) placeholders(v, out);
  }
  return out;
}

// a declared call with its placeholders replaced by values; strings that are exactly `$name`.
export function fill(call: Call, values: Record<string, unknown>): Call {
  const sub = (v: unknown): unknown => {
    if (typeof v === "string") {
      const m = PLACEHOLDER.exec(v);
      return m && m[1] in values ? values[m[1]] : v;
    }
    // a list value in a list is spliced: select: [run.id, $fields].
    if (Array.isArray(v)) return v.flatMap((x) => (typeof x === "string" && Array.isArray(sub(x)) ? (sub(x) as unknown[]) : [sub(x)]));
    if (v && typeof v === "object") return Object.fromEntries(Object.entries(v).map(([k, x]) => [k, sub(x)]));
    return v;
  };
  return { ...call, params: sub(call.params) as Record<string, unknown> };
}

// files a frame may hand the page to save: images and data, as data URLs, up to a size.
export const DOWNLOADS = /^data:(image\/png|image\/svg\+xml|text\/csv)[;,]/;
export const DOWNLOAD_LIMIT = 32 << 20;

// whether a download from a frame may be saved: a known type, a sane size and file name.
export function savable(href: string, name: string): boolean {
  return DOWNLOADS.test(href) && href.length <= DOWNLOAD_LIMIT && /^[\w.-]{1,120}\.(png|svg|csv)$/.test(name);
}

// a node a frame asks the page to expand: a built-in block whose calls only read.
export function expandable(node: Node): boolean {
  return node.block !== "custom" && Object.values(node.data ?? {}).every((c) => READS.has(c.method));
}

// a block whose height keeps changing is fixed at its last height.
export class ResizeGuard {
  times: number[] = [];
  frozen = false;
  limit: number;
  window: number;

  constructor(limit = 20, window = 2000) {
    this.limit = limit;
    this.window = window;
  }

  // whether to apply a new height reported at time t (ms).
  accept(t: number): boolean {
    if (this.frozen) return false;
    this.times = [...this.times.filter((x) => t - x < this.window), t];
    if (this.times.length > this.limit) this.frozen = true;
    return !this.frozen;
  }
}
