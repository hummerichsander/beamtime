// A nested config to read: collapsible branches, what varies between runs marked, a filter, and
// long strings cut with a button to copy them.

import { html } from "htm/preact";
import { useMemo, useState } from "preact/hooks";

import { configTree, filterTree, leaves, type ConfigNode } from "../bt/configtree.ts";
import { full, value } from "../bt/fmt.ts";
import { Icon } from "./icons.ts";
import { IconButton } from "./primitives.ts";

const LONG = 48;
// a tree this small starts open.
const SMALL = 16;

export function ConfigTree(props: { config: Record<string, unknown>; varying?: string[]; filter?: string }) {
  const [text, setText] = useState(props.filter ?? "");
  const [only, setOnly] = useState(false);
  const varying = props.varying ?? [];
  const tree = useMemo(() => configTree(props.config ?? {}, new Set(varying)), [props.config, varying.join("\n")]);
  const shown = filterTree(tree, text, only);
  const open = text.trim() !== "" || only || leaves(tree) <= SMALL;
  return html`<div class="config-tree">
    <div class="config-tools small">
      <span class="input"><${Icon} name="search" size=${14} />
        <input type="search" value=${text} placeholder="Filter keys and values" aria-label="Filter the config"
          onInput=${(e: Event) => setText((e.target as HTMLInputElement).value)} /></span>
      ${varying.length
        ? html`<label class="config-only"><input type="checkbox" checked=${only} onChange=${(e: Event) => setOnly((e.target as HTMLInputElement).checked)} />
            only what varies</label>`
        : null}
    </div>
    ${shown.length
      ? html`<ul class="config-list">${shown.map((n) => html`<${Branch} key=${n.path} node=${n} open=${open} />`)}</ul>`
      : html`<p class="muted small">${tree.length ? "Nothing matches." : "No config logged."}</p>`}
  </div>`;
}

function Branch({ node, open }: { node: ConfigNode; open: boolean }) {
  const [shown, setShown] = useState(open);
  // the filter and the toggle decide again whenever they change.
  const [was, setWas] = useState(open);
  if (was !== open) {
    setWas(open);
    setShown(open);
  }
  const mark = node.varies ? html`<span class="config-varies" data-tip="differs between runs"></span>` : null;
  if (!node.children.length) return html`<li class="config-leaf small"><${Leaf} node=${node} />${mark}</li>`;
  return html`<li class="config-branch">
    <button type="button" class="config-toggle small" aria-expanded=${shown} onClick=${() => setShown(!shown)}>
      <${Icon} name=${shown ? "chevron-down" : "chevron-right"} size=${14} />
      <span class="config-key" data-tip=${node.path}>${node.name}</span>${mark}
      <span class="muted">${leaves(node.children)}</span>
    </button>
    ${shown ? html`<ul class="config-list">${node.children.map((c) => html`<${Branch} key=${c.path} node=${c} open=${open} />`)}</ul>` : null}
  </li>`;
}

function Leaf({ node }: { node: ConfigNode }) {
  const v = node.value;
  const long = typeof v === "string" && v.length > LONG;
  const text = long ? `${v.slice(0, LONG - 1)}…` : value(v);
  return html`<span class="config-key" data-tip=${node.path}>${node.name}</span>
    <span class=${`config-value${typeof v === "number" ? " num" : ""}`} data-tip=${full(v)}>${text}</span>
    ${long || typeof v === "object" && v !== null
      ? html`<${IconButton} icon="copy" label="Copy the value" class="config-copy" onClick=${() => void navigator.clipboard?.writeText(typeof v === "string" ? v : full(v))} />`
      : null}`;
}
