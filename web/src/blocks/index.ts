// The block registry: block names to components, with the block's node in context.

import type { FunctionComponent } from "preact";
import { html } from "htm/preact";

import { BlockCtx, type Node } from "../bt/index.ts";
import { Notice } from "./common.ts";
import { Groups, MarkdownBlock, Memory, NoteBlock, Notes, Output, Proposal } from "./context.ts";
import { Custom } from "./custom.ts";
import { Images, Text } from "./logged.ts";
import { DataTable, Timeline } from "./data.ts";
import { Grid, Row, Section, Tabs } from "./layout.ts";
import { Line } from "./line.ts";
import { BarBlock, HistogramBlock, Scatter } from "./plots.ts";
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
  notes: Notes,
  tabs: Tabs,
  scatter: Scatter,
  bar: BarBlock,
  histogram: HistogramBlock,
  data_table: DataTable,
  timeline: Timeline,
  custom: Custom,
  markdown: MarkdownBlock,
};

const SPAN: Record<string, string> = { 2: "span-2", full: "span-full" };

// every block sits in a node element that names it, for screenshots, layout checks and spans.
export function Block({ node }: { node: Node }) {
  const Component = BLOCKS[node.block];
  const span = SPAN[String(node.props.span ?? 1)] ?? "";
  return html`<div class=${`node ${span}`} data-block=${node.block} data-block-id=${node.id}>
    ${Component
      ? html`<${BlockCtx.Provider} value=${node}><${Component} node=${node} /><//>`
      : html`<${Notice} kind="warning">Unknown block ${node.block}<//>`}
  </div>`;
}
