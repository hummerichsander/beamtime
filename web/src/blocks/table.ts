// `table`: runs as rows, fields as columns; click a row to open the run in the drawer.

import { html } from "htm/preact";
import { useContext, useState } from "preact/hooks";

import { hovered, useData, useRunColors, useTheme, ViewCtx, type MetricInfo, type Node } from "../bt/index.ts";
import { swatch, type Theme } from "../bt/theme.ts";
import { toggleRun, usePrefs } from "../bt/prefs.ts";
import { ago, compare, label, lowerIsBetter, value } from "../bt/fmt.ts";
import { groupUrl, navigate, route, runUrl } from "../router.ts";
import { useStore } from "../state.ts";
import { Sym } from "../ui/icons.ts";
import { symbolFor } from "../ui/symbols.ts";
import { Panel, rows } from "./common.ts";

export function Table({ node }: { node: Node }) {
  const result = useData("main");
  const spark = useData(node.props.sparkline ? "spark" : "");
  const view = useContext(ViewCtx);
  const colors = useRunColors();
  const hover = useStore(hovered);
  const theme = useTheme();
  const hidden = new Set(usePrefs(view.path).hidden);
  const [sort, setSort] = useState<{ field: string; desc: boolean } | null>(null);
  const answer = result.data;
  const columns: string[] = (node.props.columns ?? answer?.columns ?? []).filter((c: string) => c !== "run.id");
  let data = rows(answer);
  if (sort) data = [...data].sort((a, b) => compare(a[sort.field], b[sort.field]) * (sort.desc ? -1 : 1));
  const best = node.props.highlight_best === false ? new Map() : bestValues(data, columns, view.metrics);
  const trends = sparks(spark.data);
  const selected = route.value.page === "group" ? route.value.run : null;
  const total = answer?.meta?.matched ?? data.length;
  const open = (id: string) => navigate(groupUrl(view.path, { run: id }), { replace: selected !== null });
  const toggle = (c: string) =>
    setSort(sort?.field === c && !sort.desc ? { field: c, desc: true } : { field: c, desc: false });
  return html`<${Panel} title=${node.props.title} count=${answer ? String(total) : undefined}
      caption=${node.props.caption} numbered result=${result}>
    ${answer
      ? html`<div class="table-wrap"><table class="runs">
          <thead><tr class="small">
            ${columns.map(
              (c) => html`<th class=${numeric(data, c) ? "num" : ""} data-tip=${c} onClick=${() => toggle(c)}
                  aria-sort=${sort?.field === c ? (sort.desc ? "descending" : "ascending") : undefined}>
                ${c === "run.status" ? "status" : label(c)}${sort?.field === c ? (sort.desc ? " ↓" : " ↑") : ""}</th>`,
            )}
            ${node.props.sparkline ? html`<th data-tip=${`${node.props.sparkline} over steps`}>trend</th>` : null}
          </tr></thead>
          <tbody onPointerLeave=${() => hovered.set(null)}>
            ${data.map((r) => {
              const id = r["run.id"];
              const live = r["run.status"] === "running";
              const cls = `${id === selected ? "selected" : ""}${id === hover ? " hovered" : ""}${hidden.has(id) ? " hidden-run" : ""}`;
              const toggle = (e: MouseEvent) => {
                e.stopPropagation();
                toggleRun(view.path, id, data.map((x) => x["run.id"]), e.shiftKey);
              };
              return html`<tr key=${id} class=${cls} onClick=${() => open(id)}
                  onPointerEnter=${() => hovered.set(id)}>
                ${columns.map((c) => cell(c, r[c], id, live, colors.get(id), theme, best.get(c) === r[c], toggle, hidden.has(id)))}
                ${node.props.sparkline ? html`<td class="spark"><${Spark} values=${trends.get(id)} color=${colors.get(id)} /></td>` : null}
              </tr>`;
            })}
          </tbody>
        </table></div>
        ${total > data.length ? html`<p class="more-rows small">${data.length} of ${total} runs shown</p>` : null}`
      : html`<div class="skeleton late" style="block-size: 160px"></div>`}
  <//>`;
}

function cell(column: string, v: unknown, id: string, live: boolean, color: string | undefined, theme: Theme | null, best: boolean,
              toggle: (e: MouseEvent) => void, off: boolean) {  // prettier-ignore
  if (column === "run.name") {
    const mark = swatch(color, theme);
    return html`<td class="name"><button type="button" class="swatch-toggle"
        aria-pressed=${!off} aria-label=${off ? "Show in charts" : "Hide in charts"}
        data-tip=${off ? "Show in charts (shift: only this)" : "Hide in charts (shift: only this)"} onClick=${toggle}><span class=${mark.class} style=${mark.style}></span></button>
      <a href=${runUrl(id)} onClick=${(e: Event) => e.stopPropagation()}>${v ?? id}</a></td>`;
  }
  if (column === "run.status") return html`<td><${Sym} spec=${symbolFor("run", v as string)} word /></td>`;
  if (column === "run.group") {
    return html`<td><a href=${groupUrl(String(v))} onClick=${(e: Event) => e.stopPropagation()}>${v}</a></td>`;
  }
  if (column === "run.created_at" || column === "run.ended_at") {
    return html`<td class="muted" data-tip=${v ? String(v) : undefined}>${ago(v as string)}</td>`;
  }
  const isNum = typeof v === "number";
  const changing = live && column.startsWith("metric.");
  const cls = `${isNum ? "num" : ""}${changing ? " live" : ""}${best ? " best" : ""}`;
  return html`<td class=${cls} data-tip=${v === null || v === undefined ? undefined : String(v)}>${value(v)}</td>`;
}

// the best value of each metric column, by the metric's direction; ties and single rows don't count.
function bestValues(data: Record<string, any>[], columns: string[], metrics: Record<string, MetricInfo>): Map<string, unknown> {
  const out = new Map<string, unknown>();
  if (data.length < 2) return out;
  for (const c of columns) {
    if (!c.startsWith("metric.")) continue;
    const nums = data.map((r) => r[c]).filter((v): v is number => typeof v === "number" && Number.isFinite(v));
    if (nums.length < 2) continue;
    const given = metrics[c.replace(/^metric\.(.+)\.[a-z_]+$/, "$1")]?.higher_is_better;
    const lower = given === undefined ? lowerIsBetter(c) : !given;
    out.set(c, lower ? Math.min(...nums) : Math.max(...nums));
  }
  return out;
}

function numeric(data: Record<string, any>[], c: string): boolean {
  return data.some((r) => typeof r[c] === "number");
}

function sparks(answer: { curves: any[] } | null): Map<string, (number | null)[]> {
  const out = new Map<string, (number | null)[]>();
  for (const c of answer?.curves ?? []) out.set(c.run, c.raw ? c.y : c.last);
  return out;
}

// a small trend line from the preview's buckets; the last point is marked.
export function Spark(props: { values: (number | null)[] | undefined; color?: string }) {
  const W = 84;
  const H = 20;
  const v = (props.values ?? []).map((x, i) => [i, x] as const).filter((p): p is [number, number] => p[1] !== null && Number.isFinite(p[1]));
  if (v.length < 2) return html`<svg width=${W} height=${H} aria-hidden="true"></svg>`;
  const ys = v.map((p) => p[1]);
  const lo = Math.min(...ys);
  const hi = Math.max(...ys);
  const n = (props.values ?? []).length - 1 || 1;
  const pts = v.map(([i, y]) => [(i / n) * (W - 4) + 2, H - 3 - ((y - lo) / (hi - lo || 1)) * (H - 6)]);
  const color = props.color ?? "var(--muted)";
  const [lx, ly] = pts[pts.length - 1];
  return html`<svg width=${W} height=${H} viewBox=${`0 0 ${W} ${H}`} aria-hidden="true">
    <polyline fill="none" stroke=${color} stroke-width="1.4" stroke-linejoin="round" points=${pts.map((p) => p.join(",")).join(" ")} />
    <circle cx=${lx} cy=${ly} r="2" fill=${color} />
  </svg>`;
}
