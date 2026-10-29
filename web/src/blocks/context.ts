// Research context blocks: proposal, memory, groups, notes, output and note.

import { html } from "htm/preact";
import { useState } from "preact/hooks";

import { useData, type Node } from "../bt/index.ts";
import { ago, value } from "../bt/fmt.ts";
import { addNote, deleteNote, editMemory, editNote } from "../bt/writes.ts";
import { groupUrl, isRunId, runUrl } from "../router.ts";
import { Icon, Sym } from "../ui/icons.ts";
import { Markdown } from "../ui/markdown.ts";
import { Editable } from "../ui/editable.ts";
import { Disclosure, IconButton } from "../ui/primitives.ts";
import { symbolFor } from "../ui/symbols.ts";
import { prefetchGroup } from "../shell/calls.ts";
import { Collapsible, Notice, Panel, rows } from "./common.ts";

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

// one memory per group: a short text rewritten as new versions, summarizing the notes below.
export function Memory({ node }: { node: Node }) {
  const result = useData("main");
  const group = (node.data?.main.params.group as string) ?? ".";
  const chain: any[] = result.data?.chain ?? [];
  const own = chain.find((m) => m.group === group) ?? null;
  const above = chain.filter((m) => m.group !== group);
  const count = own?.notes_since ? "out of date" : own ? `version ${own.versions ?? 1}` : "none yet";
  return html`<${Collapsible} id=${`memory:${node.data?.main.scope ?? node.id}`} title=${node.props.title ?? "Memory"}
      count=${result.data ? count : undefined} open=${false} result=${result} class="memory-block"
      action=${html`<${Sym} spec=${{ icon: "circle-help", tone: "muted", label: MEMORY_HELP }} />`}>
    <${Editable} value=${own?.body ?? ""} label="the memory" multiline class="markdown"
      placeholder="No memory yet: write what this group has established, in a few lines."
      render=${(text: string) => html`<${Markdown} text=${text} />`} onSave=${(body: string) => editMemory(group, body)} />
    ${own
      ? html`<p class="memory-meta">${own.author} · covers notes until ${own.covers_until?.slice(0, 10)}
          ${own.notes_since ? html` · <span class="warn-text">${own.notes_since} newer note${own.notes_since > 1 ? "s" : ""}</span>` : null}</p>`
      : null}
    ${above.length
      ? html`<p class="memory-meta">Memory above this group: ${above.map((m, i) => html`${i ? ", " : ""}<a href=${groupUrl(m.group)}>${m.group === "." ? "local" : m.group}</a>`)}</p>`
      : null}
  <//>`;
}

const MEMORY_HELP =
  "One memory per group: a short summary of what its notes established, rewritten as new versions (the newest counts). Groups above have their own.";
const NOTES_HELP =
  "Notes at or below this page: each is its own file. Editing writes a new version that replaces it; deleting moves it to the trash.";

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
        return html`<a class="group-row" key=${r.path} href=${groupUrl(r.path)}
            onPointerEnter=${() => prefetchGroup(r.path)} onFocus=${() => prefetchGroup(r.path)}>
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
  const group = (node.data?.main.params.from as string) ?? ".";
  const [adding, setAdding] = useState(false);
  // an edited note is superseded by its new version; only the newest shows.
  const entries: any[] = (result.data?.entries ?? []).filter((n: any) => !String(n.state ?? "").startsWith("superseded"));
  return html`<${Collapsible} id=${`notes:${node.data?.main.scope ?? node.id}`} title=${node.props.title ?? "Notes"}
      count=${result.data ? String(entries.length) : undefined} result=${result}
      action=${html`<${Sym} spec=${{ icon: "circle-help", tone: "muted", label: NOTES_HELP }} />
        <${IconButton} icon="plus" label="Add a note" onClick=${() => setAdding(true)} />`}>
    <div class="notes">
      ${adding ? html`<${NewNote} group=${group} onDone=${() => setAdding(false)} />` : null}
      ${result.data && !entries.length && !adding ? html`<p class="muted small">No notes yet.</p>` : null}
      ${entries.map((n) => html`<${NoteItem} key=${n.id} note=${n} scope=${group} />`)}
    </div>
  <//>`;
}

const NEW_TYPES = ["observation", "idea", "question", "decision"];

// a form that stays open until saved or cancelled: type, title and an optional Markdown body.
function NewNote(props: { group: string; onDone: () => void }) {
  const [type, setType] = useState("observation");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const save = async (e: Event) => {
    e.preventDefault();
    if (!title.trim()) return setError("give the note a title");
    setBusy(true);
    try {
      await addNote(props.group, type, title.trim(), body.trim());
      props.onDone();
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  };
  const keys = (e: KeyboardEvent) => {
    if (e.key === "Escape") props.onDone();
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) void save(e);
  };
  return html`<form class="note new-note" onSubmit=${save} onKeyDown=${keys}>
    <div class="note-line">
      <select class="note-type" value=${type} aria-label="Note type" onChange=${(e: Event) => setType((e.target as HTMLSelectElement).value)}>
        ${NEW_TYPES.map((t) => html`<option value=${t}>${t}</option>`)}
      </select>
      <input class="new-note-title" value=${title} placeholder="What did you see, decide or wonder?" aria-label="Title"
        autofocus onInput=${(e: Event) => setTitle((e.target as HTMLInputElement).value)} />
    </div>
    <textarea class="new-note-body" rows="4" value=${body} placeholder="Details in Markdown (optional); [[run-id]] links a run"
      aria-label="Details" onInput=${(e: Event) => setBody((e.target as HTMLTextAreaElement).value)}></textarea>
    <div class="save-actions">
      <button type="submit" class="button primary" disabled=${busy}>${busy ? "Adding…" : "Add note"}</button>
      <button type="button" class="link small" onClick=${props.onDone}>cancel</button>
      <span class="muted small">⌘Enter adds, Esc cancels</span>
      ${error ? html`<span class="bad-text small">${error}</span>` : null}
    </div>
  </form>`;
}

// one line per note: type, title, who and when; the body opens below. Both edit in place.
export function NoteItem(props: { note: any; open?: boolean; scope?: string }) {
  const n = props.note;
  const [open, setOpen] = useState(!!props.open);
  const [confirming, setConfirming] = useState(false);
  // a note from a subgroup (or a run) says where it is from.
  const from = props.scope !== undefined && n.group && n.group !== props.scope ? n.group : null;
  const when = n.id.slice(0, 15).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/, "$1-$2-$3T$4:$5:$6Z");
  const author = n.meta?.author;
  return html`<article class=${`note${open ? " open" : ""}`}>
    <div class="note-line" onClick=${(e: MouseEvent) => !(e.target as Element).closest(".editable, a") && setOpen(!open)}>
      <button type="button" class="note-toggle" aria-expanded=${open} aria-label=${open ? "Close the note" : "Open the note"}>
        <${Icon} name=${open ? "chevron-down" : "chevron-right"} size=${14} /></button>
      <${Sym} spec=${symbolFor("note", n.type)} />
      <${Editable} value=${n.description} label="the note's title" class="note-title" render=${inline}
        onSave=${(description: string) => editNote(n, { description })} />
      ${n.overall ? html`<${Sym} spec=${symbolFor("verdict", n.overall)} />` : null}
      ${n.state ? html`<span class="tag tone-warn">${n.state}</span>` : null}
      ${from ? html`<a class="note-group" href=${groupUrl(from)} data-tip="from this group">${shortPath(from, props.scope!)}</a>` : null}
      <span class="note-meta">${author ? `${author} · ` : ""}${ago(when)}</span>
      ${confirming
        ? html`<span class="note-confirm">delete?
            <button type="button" class="link small bad-text" onClick=${() => void deleteNote(n)}>yes</button>
            <button type="button" class="link small" onClick=${() => setConfirming(false)}>no</button></span>`
        : html`<${IconButton} icon="trash" label="Delete this note (moves it to the trash)" class="note-delete"
            onClick=${(e: MouseEvent) => { e.stopPropagation(); setConfirming(true); }} />`}
    </div>
    ${open
      ? html`<${Editable} value=${n.body ?? ""} label="the note" multiline class="note-body markdown"
          placeholder="Add details in Markdown" render=${(text: string) => html`<${Markdown} text=${text} />`}
          onSave=${(body: string) => editNote(n, { body })} />`
      : null}
  </article>`;
}

// a subgroup's path below the page's group, or a run's id, shortly.
function shortPath(path: string, scope: string): string {
  const rel = scope === "." ? path : path.startsWith(`${scope}/`) ? path.slice(scope.length + 1) : path;
  const last = rel.split("/").pop() ?? rel;
  return isRunId(last) ? last.slice(-8) : rel;
}

export function Output({ node }: { node: Node }) {
  const result = useData("main");
  const lines: string[] = result.data?.lines ?? [];
  const meta = result.data?.meta ?? {};
  const summary = html`<${Icon} name="terminal" size=${15} /> ${node.props.title ?? "Output"}
    <span class="muted small">${result.data ? `${meta.total_lines ?? lines.length} lines${(meta.shown ?? 0) < (meta.total_lines ?? 0) ? `, last ${meta.shown}` : ""}` : ""}</span>`;
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

