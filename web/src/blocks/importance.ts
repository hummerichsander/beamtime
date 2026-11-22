// `importance`: one row per config field with two measures against the target, a bar each: the rank
// correlation (bar = magnitude, sign in the number) and the share of variance explained (η²).
// Below ten runs the answer carries a notice and the block shows it instead of bars.

import { html } from "htm/preact";

import { useData, type Node } from "../bt/index.ts";
import { label } from "../bt/fmt.ts";
import { importanceBars, signed, type ImportanceAnswer } from "../bt/shapes.ts";
import { Notice, Panel } from "./common.ts";

export function Importance({ node }: { node: Node }) {
  const result = useData<ImportanceAnswer>("main");
  const p = node.props;
  const answer = result.data;
  const rows = answer ? importanceBars(answer.rows) : [];
  const runs = answer?.meta?.matched;
  const caveat = `Each field is rated on its own, so interactions between fields are not shown${runs === undefined ? "" : `; the measures rest on ${runs} finished run${runs === 1 ? "" : "s"}`}.`;
  return html`<${Panel} title=${p.title} caption=${p.caption} result=${result}>
    ${!answer
      ? html`<div class="skeleton late" style="block-size: 120px"></div>`
      : answer.notice
        ? html`<${Notice}>${answer.notice}<//>`
        : rows.length
          ? html`<div class="table-wrap"><table class="runs importance">
              <thead><tr class="small">
                <th data-tip=${answer.target}>${label(answer.target)}</th>
                <th class="num" data-tip="Spearman rank correlation with the target; the bar is its magnitude, a minus means the target falls as the field rises">rank correlation</th>
                <th class="num" data-tip="share of the target's variance explained by grouping on the field (η², numeric fields in quantile bins)">variance explained</th>
                <th class="num" data-tip="runs that set the field">runs</th>
              </tr></thead>
              <tbody>
                ${rows.map(
                  (r) => html`<tr key=${r.field}>
                    <td data-tip=${r.field}>${label(r.field)}</td>
                    <td class="num progress" data-tip=${r.rho === null ? "not a numeric field" : undefined}>${signed(r.rho)}<span class="bar" style=${`--fraction: ${r.rhoFraction}`}></span></td>
                    <td class="num progress">${signed(r.eta)}<span class="bar" style=${`--fraction: ${r.etaFraction}`}></span></td>
                    <td class="num">${r.n}</td>
                  </tr>`,
                )}
              </tbody>
            </table></div>`
          : html`<${Notice}>No config field varies across these runs.<//>`}
    ${rows.length && !answer?.notice ? html`<p class="caption">${caveat}</p>` : null}
  <//>`;
}
