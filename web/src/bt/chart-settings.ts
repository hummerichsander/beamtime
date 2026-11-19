// A line chart's settings in one place: the defaults (generated from `m.Line`), the node's own settings,
// the series call a chart makes, and how an exported page finds a stored answer.

import type { Call } from "../api.ts";
import { EXPORTED } from "../snapshot.ts";
import { label } from "./fmt.ts";
import type { Node } from "./index.ts";
import { cascade, type ChartPrefs, type Effective, type ViewPrefs } from "./prefs.ts";
import { DEFAULTS, SEEDS_FIELD } from "./chart-defaults.ts";

// a chart's settings when nobody chose any; `scale` is always resolved on the wire, so its default is the UI's fallback.
export const BASE: Effective = { ...DEFAULTS.line, scale: "linear" };

// sparklines ask for fewer points than this; charts for more.
export const SPARK = 100;

// a line node's metrics: one key, or several in an authored view.
export function metricsOf(node: Node): string[] {
  return Array.isArray(node.props.y) ? node.props.y : [node.props.y];
}

// the settings a chart uses: its node's, the viewer's for the whole page, then for this chart.
export function effective(node: Node, prefs: ViewPrefs): Effective {
  return cascade(nodeSettings(node), prefs, node.id);
}

// the series call a chart makes: the node's call with the viewer's settings applied; `seed` is the group's seed key
// (`keys.config.seed`), which "mean over seeds" averages over unless the node names its own.
export function seriesCall(
  node: Node,
  prefs: Effective,
  opts: { zoom: [number, number] | null; width: number; seed?: string | null },
): Call {
  const base = node.data!.main;
  const params: Record<string, unknown> = { ...base.params };
  params.y = prefs.y?.length ? prefs.y : metricsOf(node);
  params.x = prefs.x;
  params.points = Math.max(SPARK, Math.min(1500, Math.round(opts.width || 600)));
  params.band = prefs.band;
  delete params.seeds;
  delete params.by;
  delete params.steps;
  if (prefs.by === "seeds") params.seeds = base.params.seeds ?? opts.seed ?? SEEDS_FIELD;
  else if (prefs.by) params.by = [prefs.by];
  // an exported page has no server to ask for the window: it zooms into the stored curve.
  if (opts.zoom && prefs.x === "_step" && !EXPORTED) params.steps = [Math.floor(opts.zoom[0]), Math.ceil(opts.zoom[1])];
  else if (prefs.steps && (prefs.steps[0] !== null || prefs.steps[1] !== null)) params.steps = prefs.steps;
  return { ...base, params };
}

// a series call as an exported page finds it: curves come at the export's resolution whatever width a chart
// has now (sparklines apart), a zoom shows the stored curve's range, and a setting at its default counts as not given.
export function normalizeSeries(params: Record<string, unknown>): Record<string, unknown> {
  const p: Record<string, unknown> = { ...params };
  p.points = typeof p.points === "number" && p.points < SPARK ? "spark" : undefined;
  delete p.steps;
  for (const [key, value] of Object.entries(DEFAULTS.line)) if (p[key] === value) delete p[key];
  return p;
}

// what the node says: settings on its props, the grouping, band and window on its series call.
function nodeSettings(node: Node): Effective {
  const params = node.data?.main.params ?? {};
  const settings: Record<string, unknown> = { ...BASE };
  for (const key of Object.keys(BASE)) if (node.props[key] != null) settings[key] = node.props[key];
  if (params.seeds) settings.by = "seeds";
  else if (Array.isArray(params.by)) settings.by = params.by[0];
  if (params.band) settings.band = params.band;
  if (Array.isArray(params.steps)) settings.steps = params.steps;
  return settings as Effective;
}

// the fields a chart can be colored by, in groups: the keys that vary, what a run is, and the keys that
// split the runs like another one (aliases) or that a finer key sets (dropped), with the reason.
export function colorOptions(keys: any): [string, [string, string][]][] {
  const { varying = [], aliases = {}, dropped = {} } = keys?.config ?? {};
  const why = (map: Record<string, string>, text: string): [string, string][] =>
    Object.entries(map).map(([k, by]) => [k, `${label(k)} · ${text} ${label(by)}`]);
  const groups: [string, [string, string][]][] = [
    ["Config", varying.map((k: string): [string, string] => [k, label(k)])],
    ["Run", [["run.status", "status"], ["run.tags", "tags"], ["run.name", "name"], ["run.group", "folder"]]],
    ["Same split", [...why(aliases, "same split as"), ...why(dropped, "set by")]],
  ];
  return groups.filter(([, options]) => options.length);
}
