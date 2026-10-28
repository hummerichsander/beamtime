// `table`: runs as rows, fields as columns; click a row to open the run in the drawer.

import { html } from "htm/preact";
import { useContext, useState } from "preact/hooks";

import { hovered, useData, useRunColors, ViewCtx, type Node } from "../bt/index.ts";
import { label, lowerIsBetter, value } from "../bt/fmt.ts";
import { groupUrl, navigate, route, runUrl } from "../router.ts";
import { useStore } from "../state.ts";
import { Sym } from "../ui/icons.ts";
import { symbolFor } from "../ui/symbols.ts";
import { Panel, rows } from "./common.ts";

export function Table({ node }: { node: Node }) {
  const result = useData("main");
  const view = useContext(ViewCtx);
  const colors = useRunColors();
  const hover = useStore(hovered);
  const [sort, setSort] = useState<{ field: string; desc: boolean } | null>(null);
  const answer = result.data;
  const columns: string[] = (node.props.columns ?? answer?.columns ?? []).filter((c: string) => c !== "run.id");
  let data = rows(answer);
  if (sort) data = [...data].sort((a, b) => compare(a[sort.field], b[sort.field]) * (sort.desc ? -1 : 1));
  const best = bestValues(data, columns);
  const selected = route.value.page === "group" ? route.value.run : null;
  const total = answer?.meta?.matched ?? data.length;
  const open = (id: string) => navigate(groupUrl(view.path, { run: id }), { replace: selected !== null });
  const toggle = (c: string) =>
    setSort(sort?.field === c && !sort.desc ? { field: c, desc: true } : { field: c, desc: false });
  return html`<${Panel} title=${node.props.title} count=${answer ? String(total) : undefined}
      caption=${node.props.caption} result=${result}>
    ${answer
      ? html`<div class="table-wrap"><table class="runs">
          <thead><tr>
            ${columns.map(
              (c) => html`<th class=${numeric(data, c) ? "num" : ""} data-tip=${c} onClick=${() => toggle(c)}
                  aria-sort=${sort?.field === c ? (sort.desc ? "descending" : "ascending") : undefined}>
                ${c === "run.status" ? "" : label(c)}${sort?.field === c ? (sort.desc ? " ↓" : " ↑") : ""}</th>`,
            )}
          </tr></thead>
          <tbody onPointerLeave=${() => hovered.set(null)}>
            ${data.map((r) => {
              const id = r["run.id"];
              const live = r["run.status"] === "running";
              const cls = `${id === selected ? "selected" : ""}${id === hover ? " hovered" : ""}`;
              return html`<tr key=${id} class=${cls} onClick=${() => open(id)}
                  onPointerEnter=${() => hovered.set(id)}>
                ${columns.map((c) => cell(c, r[c], id, live, colors.get(id), best.get(c) === r[c]))}
              </tr>`;
            })}
          </tbody>
        </table></div>
        ${total > data.length ? html`<p class="more-rows">${data.length} of ${total} runs shown</p>` : null}`
      : html`<div class="skeleton late" style="block-size: 160px"></div>`}
  <//>`;
}

function cell(column: string, v: unknown, id: string, live: boolean, color: string | undefined, best: boolean) {
  if (column === "run.name") {
    return html`<td class="name"><span class="swatch" style=${`background:${color ?? "transparent"}`}></span>
      <a href=${runUrl(id)} onClick=${(e: Event) => e.stopPropagation()}>${v ?? id}</a></td>`;
  }
  if (column === "run.status") return html`<td><${Sym} spec=${symbolFor("run", v as string)} /></td>`;
  const isNum = typeof v === "number";
  const changing = live && column.startsWith("metric.");
  const cls = `${isNum ? "num" : ""}${changing ? " live" : ""}${best ? " best" : ""}`;
  return html`<td class=${cls} data-tip=${v === null || v === undefined ? undefined : String(v)}>${value(v)}</td>`;
}

// the best value of each metric column, by the metric's direction; ties and single rows don't count.
function bestValues(data: Record<string, any>[], columns: string[]): Map<string, unknown> {
  const out = new Map<string, unknown>();
  if (data.length < 2) return out;
  for (const c of columns) {
    if (!c.startsWith("metric.")) continue;
    const nums = data.map((r) => r[c]).filter((v): v is number => typeof v === "number" && Number.isFinite(v));
    if (nums.length < 2) continue;
    out.set(c, lowerIsBetter(c) ? Math.min(...nums) : Math.max(...nums));
  }
  return out;
}

function numeric(data: Record<string, any>[], c: string): boolean {
  return data.some((r) => typeof r[c] === "number");
}

function compare(a: unknown, b: unknown): number {
  if (a === b) return 0;
  if (a === null || a === undefined) return 1;
  if (b === null || b === undefined) return -1;
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b));
}
