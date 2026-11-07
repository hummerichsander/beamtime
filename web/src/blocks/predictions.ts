// A proposal's predictions, each with its live check: the rows of the `proposal` block, which the
// kit offers custom blocks too.

import { html } from "htm/preact";

import { value } from "../bt/fmt.ts";
import { Sym } from "../ui/icons.ts";
import { symbolFor } from "../ui/symbols.ts";

export function describe(pr: any): string {
  const parts: string[] = [];
  if (pr.effect !== undefined && pr.effect !== null) {
    const ci = pr.ci ? ` [${value(pr.ci[0])}, ${value(pr.ci[1])}]` : "";
    parts.push(`${pr.effect >= 0 ? "+" : ""}${value(pr.effect)}${ci}`);
  }
  if (pr.threshold !== undefined && pr.threshold !== null) parts.push(`needs ${pr.op} ${value(pr.threshold)}`);
  if (pr.points) parts.push(`${pr.points} point${pr.points > 1 ? "s" : ""}`);
  if (pr.detail) parts.push(pr.detail);
  return parts.join(" · ");
}

export function Predictions(props: { predictions?: any[] }) {
  return html`<div class="predictions">
    ${(props.predictions ?? []).map(
      (pr) => html`<div class="prediction" key=${pr.name}>
        <${Sym} spec=${symbolFor("result", pr.result)} />
        <span class="pname">${pr.name}</span>
        <span class="pdetail num small">${describe(pr)}</span>
      </div>`,
    )}
  </div>`;
}

