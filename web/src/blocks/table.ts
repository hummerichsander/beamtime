// `table`: runs as rows, fields as columns; click a row to open the run in the drawer.

import { html } from "htm/preact";
import { useContext, useState } from "preact/hooks";

import { useData, useRunColors, ViewCtx, type Node } from "../bt/index.ts";
import { label, value } from "../bt/fmt.ts";
import { groupUrl, navigate, route, runUrl } from "../router.ts";
import { Dot, Panel, rows } from "./common.ts";

export function Table({ node }: { node: Node }) {
  const result = useData("main");
  const view = useContext(ViewCtx);
  const colors = useRunColors();
  const [sort, setSort] = useState<{ field: string; desc: boolean } | null>(null);
  const answer = result.data;
  const columns: string[] = (node.props.columns ?? answer?.columns ?? []).filter((c: string) => c !== "run.id");
  let data = rows(answer);
  if (sort) {
    data = [...data].sort((a, b) => compare(a[sort.field], b[sort.field]) * (sort.desc ? -1 : 1));
  }
  const selected = route.value.page === "group" ? route.value.run : null;
  const total = answer?.meta?.matched ?? data.length;
  const open = (id: string) => navigate(groupUrl(view.path, { run: id }), { replace: selected !== null });
  return html`<${Panel} title=${node.props.title} caption=${node.props.caption} result=${result} wide>
    ${answer
      ? html`<div class="table-wrap"><table class="runs">
          <thead><tr>
            ${columns.map(
              (c) => html`<th class=${numeric(data, c) ? "num" : ""} title=${c}
                onClick=${() => setSort(sort?.field === c && !sort.desc ? { field: c, desc: true } : { field: c, desc: false })}>
                ${label(c)}${sort?.field === c ? (sort.desc ? " ↓" : " ↑") : ""}</th>`,
            )}
          </tr></thead>
          <tbody>
            ${data.map((r) => {
              const id = r["run.id"];
              const live = r["run.status"] === "running";
              return html`<tr key=${id} class=${id === selected ? "selected" : ""} onClick=${() => open(id)}>
                ${columns.map((c) => cell(c, r[c], id, live, colors.get(id)))}
              </tr>`;
            })}
          </tbody>
        </table></div>
        ${total > data.length ? html`<p class="more">${data.length} of ${total} runs shown</p>` : null}`
      : html`<div class="skeleton" style="height: 120px"></div>`}
  <//>`;
}

function cell(column: string, v: unknown, id: string, live: boolean, color: string | undefined) {
  if (column === "run.name") {
    return html`<td class="name"><span class="swatch" style=${`background:${color ?? "transparent"}`}></span>
      <a href=${runUrl(id)} onClick=${(e: Event) => e.stopPropagation()}>${v ?? id}</a></td>`;
  }
  if (column === "run.status") return html`<td><${Dot} status=${v as string} /> ${v}</td>`;
  const isNum = typeof v === "number";
  const changing = live && column.startsWith("metric.");
  return html`<td class=${`${isNum ? "num" : ""}${changing ? " live" : ""}`} title=${v === null ? "" : String(v)}>${value(v)}</td>`;
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
