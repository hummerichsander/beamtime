// `scorecard`: one row per value of a field, one column per metric, mean ± std over the row's runs,
// shaded per column by the metric's direction. Hover and click work as in `table`; a row with no run is queued.

import { html } from "htm/preact";
import { useContext } from "preact/hooks";

import { hovered, useData, ViewCtx, type Node } from "../bt/index.ts";
import { fieldTitle } from "../bt/axes.ts";
import { full, label, value } from "../bt/fmt.ts";
import { scorecard, type Score } from "../bt/shapes.ts";
import { groupUrl, navigate, route } from "../router.ts";
import { useStore } from "../state.ts";
import { Tag } from "../ui/primitives.ts";
import { Panel } from "./common.ts";

export function Scorecard({ node }: { node: Node }) {
  const result = useData("main");
  const view = useContext(ViewCtx);
  const hover = useStore(hovered);
  const p = node.props;
  const rows = scorecard(result.data, p.rows, p.columns, p.lower ?? {}, p.expected ?? []);
  const selected = route.value.page === "group" ? route.value.run : null;
  const base = p.baseline === null || p.baseline === undefined ? null : rows.find((r) => r.label === String(p.baseline));
  const open = (id: string) => navigate(groupUrl(view.path, { run: id }), { replace: selected !== null });
  return html`<${Panel} title=${p.title} caption=${p.caption} numbered result=${result}>
    ${result.data
      ? html`<div class="table-wrap"><table class="runs scorecard">
          <thead><tr class="small">
            <th data-tip=${p.rows}>${label(p.rows)}</th>
            ${p.columns.map((c: string) => html`<th class="num" data-tip=${c}>${fieldTitle(c, view.metrics)}</th>`)}
          </tr></thead>
          <tbody onPointerLeave=${() => hovered.set(null)}>
            ${rows.map((r) => {
              const cls = `${r.runs.includes(selected ?? "") ? "selected" : ""}${r.runs.includes(hover ?? "") ? " hovered" : ""}${r.queued ? " queued" : ""}`;
              return html`<tr key=${r.label} class=${cls} data-tip=${r.runs.length ? `${r.runs.length} run${r.runs.length > 1 ? "s" : ""}` : undefined}
                  onClick=${r.runs.length ? () => open(r.runs[0]) : undefined}
                  onPointerEnter=${() => hovered.set(r.runs[0] ?? null)}>
                <td>${r.label}${r === base ? html` <${Tag} tip="the others are compared to this row">baseline<//>` : null}${r.queued ? html` <${Tag}>queued<//>` : null}</td>
                ${r.scores.map((s, i) => cell(s, r.live, base?.scores[i] ?? null))}
              </tr>`;
            })}
          </tbody>
        </table></div>`
      : html`<div class="skeleton late" style="block-size: 120px"></div>`}
  <//>`;
}

function cell(s: Score | null, live: boolean, base: Score | null) {
  if (!s) return html`<td class="num muted">–</td>`;
  const delta = base && base !== s ? `${s.mean - base.mean >= 0 ? "+" : "−"}${value(Math.abs(s.mean - base.mean))} against the baseline` : "";
  const tip = `${full(s.mean)}${s.std === null ? "" : ` ± ${full(s.std)}`}, ${s.n} run${s.n > 1 ? "s" : ""}${delta ? `. ${delta}` : ""}`;
  const cls = `num score${s.best ? " best" : ""}${live ? " live" : ""}`;
  return html`<td class=${cls} style=${s.shade === null ? undefined : `--shade: ${s.shade}`} data-tip=${tip}>
    ${value(s.mean)}${s.std === null ? null : html`<span class="spread"> ± ${value(s.std)}</span>`}</td>`;
}
