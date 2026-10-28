// Research context blocks: proposal, memory, groups, output and note.

import { html } from "htm/preact";

import { useData, type Node } from "../bt/index.ts";
import { value } from "../bt/fmt.ts";
import { groupUrl, runUrl, isRunId } from "../router.ts";
import { Markdown } from "../ui/markdown.ts";
import { Dot, Notice, Panel, rows } from "./common.ts";

export function Badge(props: { prediction: any }) {
  const p = props.prediction;
  const ci = p.ci ? ` [${value(p.ci[0])}, ${value(p.ci[1])}]` : "";
  const effect = p.effect !== undefined && p.effect !== null ? `effect ${value(p.effect)}${ci}` : (p.detail ?? "");
  return html`<span class=${`badge result-${p.result}`} title=${`${p.name}: ${p.result}${effect ? `, ${effect}` : ""}`}>
    ${p.name} · ${p.result}
  </span>`;
}

export function Progress(props: { progress: any }) {
  const p = props.progress;
  if (!p) return null;
  const fraction = p.fraction ?? null;
  return html`<span class="progress" title=${p.text}>
    ${fraction !== null ? html`<span class="bar"><span style=${`width:${Math.round(fraction * 100)}%`}></span></span>` : null}
    <span class="muted">${p.text}</span>
  </span>`;
}

export function Proposal({ node }: { node: Node }) {
  const proposal = useData("proposal");
  const check = useData("check");
  const p = proposal.data;
  const c = check.data;
  if (!p) return html`<${Panel} result=${proposal}><div class="skeleton" style="height: 64px"></div><//>`;
  const doc = p.proposal ?? {};
  const older = (p.versions ?? []).filter((v: any) => v.version !== p.version);
  // the frame already states the viewed group's proposal; a block about another group repeats it.
  const own = !node.props.of || node.props.of === ".";
  return html`<${Panel} title="Proposal" result=${proposal} wide>
    ${own ? null : html`<p class="statement">${doc.statement}</p>`}
    ${doc.rationale ? html`<p class="muted">${doc.rationale}</p>` : null}
    <div class="predictions">
      ${(c?.predictions ?? []).map(
        (pr: any) => html`<div class="prediction" key=${pr.name}>
          <${Badge} prediction=${pr} />
          <span class="muted small">${describe(pr)}</span>
        </div>`,
      )}
    </div>
    <div class="meta-line">
      <span class=${`chip status-${p.status}`}>${p.status}</span>
      ${c ? html`<span class=${`chip result-${c.result}`}>check ${c.result}${c.provisional ? " (provisional)" : ""}</span>` : null}
      <${Progress} progress=${c?.progress} />
      ${doc.confidence !== undefined ? html`<span class="muted small">confidence ${value(doc.confidence)}</span>` : null}
    </div>
    ${older.length
      ? html`<details class="versions"><summary>${older.length} earlier version${older.length > 1 ? "s" : ""}</summary>
          ${older.map((v: any) => html`<p class="small"><code>${v.version}</code> ${v.statement} <span class="muted">(${v.runs} runs, check ${v.check ?? "–"})</span></p>`)}
        </details>`
      : null}
  <//>`;
}

function describe(pr: any): string {
  const parts: string[] = [];
  if (pr.effect !== undefined && pr.effect !== null) parts.push(`effect ${value(pr.effect)}`);
  if (pr.ci) parts.push(`95% CI [${value(pr.ci[0])}, ${value(pr.ci[1])}]`);
  if (pr.threshold !== undefined && pr.threshold !== null) parts.push(`needs ${pr.op} ${value(pr.threshold)}`);
  if (pr.points) parts.push(`${pr.points} point${pr.points > 1 ? "s" : ""}`);
  if (pr.detail) parts.push(pr.detail);
  return parts.join(" · ");
}

export function Memory({ node }: { node: Node }) {
  const result = useData("main");
  const chain: any[] = result.data?.chain ?? [];
  const own = chain.filter((m) => m.group === result.data?.group || chain.length === 1);
  return html`<${Panel} title=${node.props.title ?? "Memory"} result=${result} wide>
    ${own.map(
      (m) => html`<div class="memory" key=${m.version}>
        <${Markdown} text=${m.body} />
        <p class="muted small">covers notes until ${m.covers_until?.slice(0, 16).replace("T", " ")} · ${m.author}
          ${m.notes_since ? html` · <span class="warn-text">${m.notes_since} newer note${m.notes_since > 1 ? "s" : ""}</span>` : null}</p>
      </div>`,
    )}
  <//>`;
}

export function Groups({ node }: { node: Node }) {
  const result = useData("main");
  const self = (node.data?.main.params.from as string) ?? ".";
  const data = rows(result.data).filter((r) => r.path !== self);
  return html`<${Panel} title=${node.props.title} result=${result} wide>
    ${result.data && !data.length ? html`<${Notice}>No subgroups.<//>` : null}
    ${data.length
      ? html`<div class="table-wrap"><table class="runs">
          <thead><tr><th>group</th><th>status</th><th>check</th><th>verdict</th><th class="num">runs</th><th>progress</th></tr></thead>
          <tbody>${data.map(
            (r) => html`<tr key=${r.path}>
              <td class="name"><a href=${groupUrl(r.path)}>${r.path}</a>
                ${r.proposal ? html`<div class="muted small clip">${r.proposal}</div>` : null}</td>
              <td><span class=${`chip status-${r.status}`}>${r.status}</span></td>
              <td>${r.check ? html`<span class=${`chip result-${r.check.split(" ")[0]}`}>${r.check}</span>` : null}</td>
              <td>${r.verdict ?? ""}</td>
              <td class="num">${r.runs}
                ${r.running ? html` <${Dot} status="running" />` : null}
                ${r.failed || r.killed || r.lost ? html` <${Dot} status="failed" />` : null}</td>
              <td class="muted small">${r.progress ?? ""}</td>
            </tr>`,
          )}</tbody>
        </table></div>`
      : null}
  <//>`;
}

export function Output({ node }: { node: Node }) {
  const result = useData("main");
  const lines: string[] = result.data?.lines ?? [];
  const meta = result.data?.meta ?? {};
  return html`<${Panel} result=${result} wide>
    <details class="output" open=${node.props.open}>
      <summary>${node.props.title ?? "Output"} <span class="muted small">
        ${result.data ? `last ${meta.shown ?? lines.length} of ${meta.total_lines ?? lines.length} lines` : ""}</span></summary>
      <pre class="log">${lines.join("\n")}</pre>
    </details>
  <//>`;
}

export function NoteBlock({ node }: { node: Node }) {
  return html`<${Notice} kind=${node.props.kind ?? "info"}>${node.props.text}<//>`;
}

// [[run-id]], [[group]] and [[group#prediction]] become links; `code` stays code.
export function inline(text: string) {
  const parts = text.split(/(\[\[[^\]]+\]\]|`[^`]+`)/g);
  return parts.map((part) => {
    if (part.startsWith("[[")) {
      const target = part.slice(2, -2);
      const [path] = target.split(/[#@]/);
      const href = isRunId(path.split("/").pop() ?? "") ? runUrl(path.split("/").pop()!) : groupUrl(path);
      return html`<a href=${href}>${target}</a>`;
    }
    if (part.startsWith("`")) return html`<code>${part.slice(1, -1)}</code>`;
    return part;
  });
}

