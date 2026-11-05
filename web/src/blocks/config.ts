// `config`: a run's config as a tree, or a group's hyperparameters: the keys that differ between runs.

import { html } from "htm/preact";

import { useData, type Node } from "../bt/index.ts";
import { varyingKeys } from "../bt/configtree.ts";
import { value } from "../bt/fmt.ts";
import { ConfigTree } from "../ui/config.ts";
import { Collapsible } from "./common.ts";

// a value list is cut here; the tooltip has all of it.
const LINE = 80;

export function ConfigBlock({ node }: { node: Node }) {
  const result = useData("main");
  const keys = useData(node.data?.keys ? "keys" : "");
  const run = node.props.mode === "run";
  const title = node.props.title ?? (run ? "Config" : "Hyperparameters");
  return html`<${Collapsible} id=${`config:${node.id}`} title=${title} open=${node.props.open} result=${result}>
    ${result.data
      ? run
        ? html`<${ConfigTree} config=${result.data.config} varying=${varyingKeys(keys.data)} />`
        : html`<${Hyperparameters} rows=${result.data.config?.rows ?? []} />`
      : html`<div class="skeleton late" style="block-size: 80px"></div>`}
  <//>`;
}

// each key that varies with its values, cut at a line; a long sweep as its range.
function Hyperparameters({ rows }: { rows: [string, number, unknown][] }) {
  const varying = new Set(varyingKeys({ config: { rows } }));
  const shown = rows.filter(([k]) => varying.has(k.replace(/^config\./, "")));
  if (!shown.length) return html`<p class="muted small">No config differs between the runs.</p>`;
  return html`<table class="kv small">${shown.map(([k, , v]) => {
    const text = Array.isArray(v) ? v.map(value).join(", ") : `${value((v as any).min)} … ${value((v as any).max)} · ${(v as any).distinct} values`;
    return html`<tr><td data-tip=${k}>${k.replace(/^config\./, "")}</td>
      <td data-tip=${text.length > LINE ? text : undefined}>${text.length > LINE ? `${text.slice(0, LINE - 1)}…` : text}</td></tr>`;
  })}</table>`;
}
