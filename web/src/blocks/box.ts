// The element every block sits in: it names the block, for screenshots, layout checks and spans.

import type { FunctionComponent } from "preact";
import { html } from "htm/preact";

import { BlockCtx, type Node } from "../bt/index.ts";
import { Notice } from "./common.ts";

const SPAN: Record<string, string> = { 2: "span-2", full: "span-full" };

export type Registry = Record<string, FunctionComponent<{ node: Node }>>;

export function Box(props: { node: Node; blocks: Registry }) {
  const { node } = props;
  const Component = props.blocks[node.block];
  const span = SPAN[String(node.props.span ?? 1)] ?? "";
  return html`<div class=${`node ${span}`} data-block=${node.block} data-block-id=${node.id}>
    ${Component
      ? html`<${BlockCtx.Provider} value=${node}><${Component} node=${node} /><//>`
      : html`<${Notice} kind="warning">Unknown block ${node.block}<//>`}
  </div>`;
}
