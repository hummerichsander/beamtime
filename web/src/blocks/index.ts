// The block registry: block names to components, with the block's node in context.

import type { FunctionComponent } from "preact";
import { html } from "htm/preact";

import { BlockCtx, type Node } from "../bt/index.ts";
import { Notice } from "./common.ts";
import { Groups, Memory, NoteBlock, Output, Proposal } from "./context.ts";
import { Images, Text } from "./logged.ts";
import { Grid, Row, Section } from "./layout.ts";
import { Line } from "./line.ts";
import { Stat } from "./stat.ts";
import { Table } from "./table.ts";

const BLOCKS: Record<string, FunctionComponent<{ node: Node }>> = {
  section: Section,
  row: Row,
  grid: Grid,
  line: Line,
  table: Table,
  stat: Stat,
  images: Images,
  text: Text,
  proposal: Proposal,
  note: NoteBlock,
  output: Output,
  memory: Memory,
  groups: Groups,
};

export function Block({ node }: { node: Node }) {
  const Component = BLOCKS[node.block];
  if (!Component) return html`<${Notice} kind="warning">Unknown block ${node.block}<//>`;
  return html`<${BlockCtx.Provider} value=${node}><${Component} node=${node} /><//>`;
}
