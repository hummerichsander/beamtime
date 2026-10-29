// `data_table` (a logged table or a view's data file) and `timeline` (notes and run events).

import { html } from "htm/preact";
import { useContext, useState } from "preact/hooks";

import { useData, ViewCtx, type Node } from "../bt/index.ts";
import { label, step, value } from "../bt/fmt.ts";
import { tableOf } from "../bt/shapes.ts";
import { runUrl } from "../router.ts";
import { Icon } from "../ui/icons.ts";
import { eventIcon } from "../ui/symbols.ts";
import { Notice, Panel } from "./common.ts";

export function DataTable({ node }: { node: Node }) {
  const result = useData("main");
  const view = useContext(ViewCtx);
  const [pick, setPick] = useState(0);
  const [sort, setSort] = useState<{ i: number; desc: boolean } | null>(null);
  const entries: any[] = result.data?.entries ?? [];
  // a logged key has one table per run (and step); a data file is one table.
  const entry = entries.length ? entries[Math.min(pick, entries.length - 1)] : null;
  const table = tableOf(entries.length ? entry : result.data);
  const limit = node.props.limit ?? 50;
  let rows = table?.rows ?? [];
  if (sort) rows = [...rows].sort((a, b) => compare(a[sort.i], b[sort.i]) * (sort.desc ? -1 : 1));
  const toggle = (i: number) => setSort(sort?.i === i && !sort.desc ? { i, desc: true } : { i, desc: false });
  return html`<${Panel} title=${node.props.title ?? node.props.key} caption=${node.props.caption} result=${result}
      count=${table ? String(table.rows.length) : undefined}>
    ${entries.length > 1
      ? html`<label class="field inline"><span class="field-label">Run</span>
          <select value=${pick} onChange=${(e: Event) => setPick(Number((e.target as HTMLSelectElement).value))}>
            ${entries.map((e, i) => html`<option value=${i}>${view.names.get(e.run) ?? e.run} · step ${step(e.step)}</option>`)}
          </select></label>`
      : null}
    ${result.data && !table
      ? html`<${Notice}>${entries.length ? "This entry is stored as a file that isn't shown here (Parquet)." : "No table logged."}<//>`
      : null}
    ${table
      ? html`<div class="table-wrap"><table class="runs data">
          <thead><tr>${table.columns.map((c, i) => html`<th class=${rows.some((r) => typeof r[i] === "number") ? "num" : ""}
              onClick=${() => toggle(i)} aria-sort=${sort?.i === i ? (sort.desc ? "descending" : "ascending") : undefined}>
              ${label(c)}${sort?.i === i ? (sort.desc ? " ↓" : " ↑") : ""}</th>`)}</tr></thead>
          <tbody>${rows.slice(0, limit).map((r) => html`<tr>${r.map((v) => html`<td class=${typeof v === "number" ? "num" : ""}
              data-tip=${v === null || v === undefined ? undefined : String(v)}>${value(v)}</td>`)}</tr>`)}</tbody>
        </table></div>
        ${rows.length > limit ? html`<p class="more-rows">${limit} of ${rows.length} rows shown</p>` : null}`
      : null}
  <//>`;
}

export function Timeline({ node }: { node: Node }) {
  const result = useData("main");
  const entries: any[] = result.data?.entries ?? [];
  return html`<${Panel} title=${node.props.title ?? "Timeline"} caption=${node.props.caption} result=${result}>
    ${result.data && !entries.length ? html`<${Notice}>Nothing happened here yet.<//>` : null}
    <div class="timeline">
      ${entries.slice().reverse().map(
        (e) => html`<div class="event">
          <span class="muted num" data-tip=${e.t}>${e.t?.slice(5, 16).replace("T", " ")}</span>
          <${Icon} name=${e.kind === "note" ? "file-text" : eventIcon(e.type)} size=${14} />
          <span>${e.run ? html`<a href=${runUrl(e.run)}>${e.run.slice(-8)}</a> ` : null}${e.description ?? e.type}</span>
        </div>`,
      )}
    </div>
  <//>`;
}

function compare(a: unknown, b: unknown): number {
  if (a === b) return 0;
  if (a === null || a === undefined) return 1;
  if (b === null || b === undefined) return -1;
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b));
}
