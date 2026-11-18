// Two scatter charts side by side: a data file's first two columns (`ref`) and the runs' swept field
// against the main metric (`runs`); axes come from each result's `columns`.
const { html } = bt.preact;

function ReferenceChart() {
  const ref = bt.useData("ref");
  const runs = bt.useData("runs");
  if (ref.status === "error") return html`<p class="notice error">${ref.error}</p>`;
  if (runs.status === "error") return html`<p class="notice error">${runs.error}</p>`;
  if (ref.status !== "ready" || runs.status !== "ready") return null;
  const [rx, ry] = ref.columns;
  const [, x, y] = runs.columns;
  return html`<${bt.ui.Grid} columns=${2}>
    <${bt.chart.Scatter} id="ref-chart" data=${ref} x=${rx} y=${ry} title="Reference" />
    <${bt.chart.Scatter} id="runs-chart" data=${runs} x=${x} y=${y} title="Runs" />
  <//>`;
}

export default function render(root) {
  bt.preact.render(html`<${ReferenceChart} />`, root);
}
