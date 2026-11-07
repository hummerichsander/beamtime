// The label of a block's Section: a short word in the page's margin, from what the block is.

type LabelNode = { block: string; props: Record<string, any>; children?: LabelNode[] };

const KINDS: Record<string, string> = {
  stat: "readings", line: "charts", scatter: "charts", bar: "charts", histogram: "charts",
  table: "runs", data_table: "table", images: "images", text: "text", markdown: "text", note: "note",
  notes: "notes", memory: "memory", groups: "groups", output: "output", config: "config", timeline: "timeline", proposal: "predictions",
};  // prettier-ignore

export function labelOf(node: LabelNode): string {
  if (KINDS[node.block]) return KINDS[node.block];
  if (node.block === "row" || node.block === "grid") {
    const kinds = new Set((node.children ?? []).map((c) => KINDS[c.block]));
    const [only] = kinds;
    if (kinds.size === 1 && only) return only;
  }
  // tabs, custom blocks, mixed layouts: the title, if it is one or two words.
  const title = String(node.props.title ?? "").trim();
  return title && title.split(/\s+/).length <= 2 ? title.toLowerCase() : "";
}
