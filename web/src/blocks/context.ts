// Research context blocks: proposal, memory, groups, notes, output and note.

import { html } from "htm/preact";

import { useData, type Node } from "../bt/index.ts";
import { ago, value } from "../bt/fmt.ts";
import { groupUrl, isRunId, runUrl } from "../router.ts";
import { Icon, Sym } from "../ui/icons.ts";
import { Markdown } from "../ui/markdown.ts";
import { Disclosure } from "../ui/primitives.ts";
import { symbolFor } from "../ui/symbols.ts";
import { Notice, Panel, rows } from "./common.ts";

export function describe(pr: any): string {
  const parts: string[] = [];
  if (pr.effect !== undefined && pr.effect !== null) {
    const ci = pr.ci ? ` [${value(pr.ci[0])}, ${value(pr.ci[1])}]` : "";
    parts.push(`${pr.effect >= 0 ? "+" : ""}${value(pr.effect)}${ci}`);
  }
  if (pr.threshold !== undefined && pr.threshold !== null) parts.push(`needs ${pr.op} ${value(pr.threshold)}`);
  if (pr.points) parts.push(`${pr.points} point${pr.points > 1 ? "s" : ""}`);
  if (pr.detail) parts.push(pr.detail);
  return parts.join(" · ");
}

// the plan's progress: "15 of 15 grid points", with what was left out in the tooltip.
export function progressText(text: string | null | undefined): [string, string | undefined] {
  if (!text) return ["", undefined];
  const [head, ...rest] = text.split("; ");
  return [head, rest.length ? text : undefined];
}

export function Proposal({ node }: { node: Node }) {
  const proposal = useData("proposal");
  const check = useData("check");
  const p = proposal.data;
  const c = check.data;
  if (!p) return html`<${Panel} result=${proposal}><div class="skeleton late" style="block-size: 90px"></div><//>`;
  const doc = p.proposal ?? {};
  const older = (p.versions ?? []).filter((v: any) => v.version !== p.version);
  // the header already states the viewed group's proposal; a block about another group repeats it.
  const own = !node.props.of || node.props.of === ".";
  return html`<${Panel} title="Predictions" result=${proposal} class="proposal-block">
    ${own ? null : html`<p class="statement">${doc.statement}</p>`}
    ${doc.rationale ? html`<p class="rationale">${doc.rationale}</p>` : null}
    <div class="predictions">
      ${(c?.predictions ?? []).map(
        (pr: any) => html`<div class="prediction" key=${pr.name}>
          <${Sym} spec=${symbolFor("result", pr.result)} />
          <span class="pname">${pr.name}</span>
          <span class="pdetail num">${describe(pr)}</span>
        </div>`,
      )}
    </div>
    ${older.length
      ? html`<${Disclosure} summary=${`${older.length} earlier version${older.length > 1 ? "s" : ""}`}>
          ${older.map((v: any) => html`<p class="small"><code>${v.version}</code> ${v.statement}
            <span class="muted">(${v.runs} runs, check ${v.check ?? "–"})</span></p>`)}
        <//>`
      : null}
  <//>`;
}

export function Memory({ node }: { node: Node }) {
  const result = useData("main");
  const chain: any[] = result.data?.chain ?? [];
  const own = chain.filter((m) => m.group === result.data?.group || chain.length === 1);
  return html`<${Panel} title=${node.props.title ?? "Memory"} result=${result} class="memory-block">
    ${own.map(
      (m) => html`<div key=${m.version}>
        <${Markdown} text=${m.body} clamp=${12} />
        <p class="memory-meta">${m.author} · covers notes until ${m.covers_until?.slice(0, 10)}
          ${m.notes_since ? html` · <span class="warn-text">${m.notes_since} newer note${m.notes_since > 1 ? "s" : ""}</span>` : null}</p>
      </div>`,
    )}
  <//>`;
}

export function Groups({ node }: { node: Node }) {
  const result = useData("main");
  const self = (node.data?.main.params.from as string) ?? ".";
  const data = rows(result.data).filter((r) => r.path !== self);
  return html`<${Panel} title=${node.props.title} count=${result.data ? String(data.length) : undefined} result=${result}>
    ${result.data && !data.length ? html`<${Notice}>No groups below.<//>` : null}
    <div class="group-list">
      ${data.map((r) => {
        const [progress, more] = progressText(r.progress);
        const ended = (r.failed ?? 0) + (r.killed ?? 0) + (r.lost ?? 0);
        return html`<a class="group-row" key=${r.path} href=${groupUrl(r.path)}>
          <${Sym} spec=${symbolFor("research", r.status)} />
          <span class="gname">${r.path.split("/").pop()}</span>
          <span class="gfacts">
            ${r.check ? html`<${Sym} spec=${symbolFor("result", r.check)} word />` : null}
            ${r.verdict ? html`<${Sym} spec=${symbolFor("verdict", r.verdict)} />` : null}
            ${progress ? html`<span data-tip=${more}>${progress}</span>` : null}
            <span class="num"><b>${r.runs}</b> runs</span>
            ${r.running ? html`<${Sym} spec=${symbolFor("run", "running")} />` : null}
            ${ended ? html`<span class="tone-bad num" data-tip="failed, killed or lost"><${Icon} name="circle-x" size=${14} /> ${ended}</span>` : null}
          </span>
          ${r.proposal ? html`<span class="gstatement">${r.proposal}</span>` : null}
        </a>`;
      })}
    </div>
  <//>`;
}

export function Notes({ node }: { node: Node }) {
  const result = useData("main");
  const entries: any[] = result.data?.entries ?? [];
  return html`<${Panel} title=${node.props.title ?? "Notes"} count=${result.data ? String(entries.length) : undefined} result=${result}>
    ${entries.map((n) => html`<${NoteItem} key=${n.id} note=${n} />`)}
  <//>`;
}

export function NoteItem(props: { note: any; clamp?: number }) {
  const n = props.note;
  const when = n.id.slice(0, 15).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/, "$1-$2-$3T$4:$5:$6Z");
  const author = n.meta?.author;
  return html`<article class="note">
    <div class="note-head">
      <${Sym} spec=${symbolFor("note", n.type)} word />
      ${n.overall ? html`<${Sym} spec=${symbolFor("verdict", n.overall)} word />` : null}
      ${n.state ? html`<span class="tag tone-warn">${n.state}</span>` : null}
      <span>${author ? `${author} · ` : ""}${ago(when)}</span>
    </div>
    <p class="note-title">${inline(n.description)}</p>
    ${n.body ? html`<${Markdown} text=${n.body} clamp=${props.clamp ?? 6} />` : null}
  </article>`;
}

export function Output({ node }: { node: Node }) {
  const result = useData("main");
  const lines: string[] = result.data?.lines ?? [];
  const meta = result.data?.meta ?? {};
  const summary = html`<${Icon} name="terminal" size=${15} /> ${node.props.title ?? "Output"}
    <span class="muted small">${result.data ? `last ${meta.shown ?? lines.length} of ${meta.total_lines ?? lines.length} lines` : ""}</span>`;
  return html`<${Panel} result=${result}>
    <${Disclosure} summary=${summary} open=${node.props.open}>
      <pre class="log">${lines.join("\n")}</pre>
    <//>
  <//>`;
}

export function NoteBlock({ node }: { node: Node }) {
  return html`<${Notice} kind=${node.props.kind ?? "info"}>${node.props.text}<//>`;
}

// [[run-id]], [[group]] and [[group#prediction]] become links; `code` stays code.
export function inline(text: string) {
  const parts = (text ?? "").split(/(\[\[[^\]]+\]\]|`[^`]+`)/g);
  return parts.map((part) => {
    if (part.startsWith("[[")) {
      const target = part.slice(2, -2);
      const [path] = target.split(/[#@]/);
      const last = path.split("/").pop() ?? "";
      return html`<a href=${isRunId(last) ? runUrl(last) : groupUrl(path)}>${target}</a>`;
    }
    if (part.startsWith("`")) return html`<code>${part.slice(1, -1)}</code>`;
    return part;
  });
}

