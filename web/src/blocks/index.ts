// The block registry: block names to components, with the block's node in context.

import { html } from "htm/preact";

import type { Node } from "../bt/index.ts";
import { Box, type Registry } from "./box.ts";
import { Groups, MarkdownBlock, Memory, NoteBlock, Notes, Output, Proposal } from "./context.ts";
import { Custom } from "./custom.ts";
import { Images, Text } from "./logged.ts";
import { DataTable, Timeline } from "./data.ts";
import { Grid, Row, Section, Tabs } from "./layout.ts";
import { Line } from "./line.ts";
import { BarBlock, HistogramBlock, Scatter } from "./plots.ts";
import { Stat } from "./stat.ts";
import { Table } from "./table.ts";

const BLOCKS: Registry = {
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

export function Block({ node }: { node: Node }) {
  return html`<${Box} node=${node} blocks=${BLOCKS} />`;
}
