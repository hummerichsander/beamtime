// The block registry: block names to components, with the block's node in context.

import { html } from "htm/preact";
import { useContext } from "preact/hooks";

import { ViewCtx, type Node } from "../bt/index.ts";
import { showCharts, usePrefs } from "../bt/prefs.ts";
import { Box, type Registry } from "./box.ts";
import { Groups, MarkdownBlock, Memory, NoteBlock, Notes, Output, Proposal } from "./context.ts";
import { ConfigBlock } from "./config.ts";
import { Custom } from "./custom.ts";
import { Images, Text } from "./logged.ts";
import { DataTable, Timeline } from "./data.ts";
import { Grid, Row, Section, Tabs } from "./layout.ts";
import { Line } from "./line.ts";
import { BarBlock, HistogramBlock, Scatter } from "./plots.ts";
import { Scorecard } from "./scorecard.ts";
import { Stat } from "./stat.ts";
import { Table } from "./table.ts";

const BLOCKS: Registry = {
  section: Section,
  row: Row,
  grid: Grid,
  line: Line,
  table: Table,
  scorecard: Scorecard,
  stat: Stat,
  images: Images,
  text: Text,
  proposal: Proposal,
  note: NoteBlock,
  output: Output,
  config: ConfigBlock,
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

const CHARTS = new Set(["line", "scatter", "bar", "histogram"]);

export function Block({ node }: { node: Node }) {
  return CHARTS.has(node.block) ? html`<${Hideable} node=${node} />` : html`<${Box} node=${node} blocks=${BLOCKS} />`;
}

// a chart the viewer hid outside a grid (grids filter their own): a link brings it back.
function Hideable({ node }: { node: Node }) {
  const view = useContext(ViewCtx);
  const prefs = usePrefs(view.path);
  if (!prefs.removed.includes(node.id)) return html`<${Box} node=${node} blocks=${BLOCKS} />`;
  return html`<div class="grid-note"><button type="button" class="link small" onClick=${() => showCharts(view.path, [node.id])}>1 hidden · show</button></div>`;
}
