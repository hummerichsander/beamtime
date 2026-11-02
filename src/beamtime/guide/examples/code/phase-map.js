// A heatmap of a metric over two config fields, from the `runs` query's columns
// [run.id, x, y, value]; clicking a cell shows the curves of its best run (`detail`, from: $run).
const { html, useState } = bt.preact;
const d3 = bt.lib.d3;

const CELL = 30;
const MAX_WIDTH = 96;
const LEFT = 84;
const BOTTOM = 40;

function PhaseMap() {
  const runs = bt.useData("runs");
  const [ref, width] = bt.useSize();
  const [run, setRun] = useState(null);
  const hovered = bt.useHovered();
  if (runs.status === "error") return html`<p class="notice error">${runs.error}</p>`;
  const [, xf, yf, vf] = runs.columns;
  const lower = /\.min$|loss/.test(vf ?? "");
  const pick = lower ? d3.least : d3.greatest;
  const rows = runs.rows.filter((r) => typeof r[vf] === "number");
  const cells = d3
    .rollups(rows, (rs) => ({ value: d3.mean(rs, (r) => r[vf]), best: pick(rs, (r) => r[vf])["run.id"], n: rs.length }),
      (r) => r[xf], (r) => r[yf])
    .flatMap(([x, ys]) => ys.map(([y, c]) => ({ x, y, ...c })));
  const xs = [...new Set(cells.map((c) => c.x))].sort(d3.ascending);
  const ys = [...new Set(cells.map((c) => c.y))].sort(d3.ascending);
  const w = Math.max(0, Math.min(width - LEFT, xs.length * MAX_WIDTH));
  const x = d3.scaleBand(xs, [LEFT, LEFT + w]).padding(0.06);
  const y = d3.scaleBand(ys, [0, ys.length * CELL]).padding(0.06);
  const [lo, hi] = d3.extent(cells, (c) => c.value);
  const ramp = bt.theme.scale("sequential");
  const color = (v) => ramp(hi === lo ? 1 : lower ? (hi - v) / (hi - lo) : (v - lo) / (hi - lo));
  const height = ys.length * CELL + BOTTOM;
  return html`<div ref=${ref}>
    ${runs.status === "ready" && !cells.length ? html`<p class="notice info">No run has ${bt.label(vf)} yet.</p>` : null}
    ${w > 0 && cells.length
      ? html`<svg width=${LEFT + w} height=${height} role="img" style="display: block" aria-label=${`${bt.label(vf)} over ${bt.label(xf)} and ${bt.label(yf)}`}>
          ${cells.map((c) => html`<g key=${`${c.x}|${c.y}`} style="cursor: pointer" onClick=${() => setRun(c.best)}
              onPointerEnter=${() => bt.hover(c.best)} onPointerLeave=${() => bt.hover(null)}>
              <title>${bt.label(xf)} ${c.x} · ${bt.label(yf)} ${c.y}: ${bt.fmt.value(c.value)} (${c.n} run${c.n === 1 ? "" : "s"})</title>
              <rect x=${x(c.x)} y=${y(c.y)} width=${x.bandwidth()} height=${y.bandwidth()} rx="3" fill=${color(c.value)}
                stroke=${c.best === run || c.best === hovered ? "var(--ink)" : "none"} stroke-width="2" />
            </g>`)}
          ${ys.map((v) => html`<text x=${LEFT - 8} y=${y(v) + y.bandwidth() / 2} text-anchor="end" dominant-baseline="middle"
              fill="var(--muted)" class="small">${bt.fmt.value(v)}</text>`)}
          ${xs.map((v) => html`<text x=${x(v) + x.bandwidth() / 2} y=${ys.length * CELL + 16} text-anchor="middle"
              fill="var(--muted)" class="small">${bt.fmt.value(v)}</text>`)}
          <text x=${LEFT + w / 2} y=${height - 4} text-anchor="middle" fill="var(--muted)" class="small">${bt.label(xf)}</text>
          <text x="0" y=${(ys.length * CELL) / 2} dominant-baseline="middle" fill="var(--muted)" class="small">${bt.label(yf)}</text>
        </svg>`
      : null}
    <p class="muted small">Color runs from worst to best along the colormap.${run ? "" : " Click a cell to see the curves of its best run."}</p>
    ${run ? html`<${Detail} run=${run} />` : null}
  </div>`;
}

function Detail({ run }) {
  const detail = bt.useData("detail", { run });
  return html`<${bt.chart.Line} id="detail" data=${detail} title=${`Best run of the cell: ${bt.name(run)}`}
    caption="The selected cell's best run." />`;
}

export default function render(root) {
  bt.preact.render(html`<${PhaseMap} />`, root);
}
