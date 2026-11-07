// The page header, the same on every view: where you are, the name with its status, one line of
// facts; and the proposal, in its own Section right after it.

import { html } from "htm/preact";

import { useCall } from "../api.ts";
import { describe, progressText } from "../blocks/context.ts";
import { rows } from "../blocks/common.ts";
import { usePrefs } from "../bt/prefs.ts";
import { ago, duration, label, step, value, versionTime } from "../bt/fmt.ts";
import { groupUrl, isRoot, isRunId, navigate, rootOf, runUrl } from "../router.ts";
import { Icon, Sym } from "../ui/icons.ts";
import { Editable } from "../ui/editable.ts";
import { IconButton, Popover, Section } from "../ui/primitives.ts";
import { editStatement, renameRun } from "../bt/writes.ts";
import { symbolFor } from "../ui/symbols.ts";
import * as calls from "./calls.ts";
import { useCallKept } from "./kept.ts";

const ENDED = ["failed", "killed", "lost"];

export function Header(props: { path: string; finding?: string | null }) {
  // the crumbs start at the source's root: local, or a remote such as @box.
  const root = rootOf(props.path);
  const below = root === "." ? props.path : props.path.slice(root.length + 1);
  const parts = isRoot(props.path) ? [] : below.split("/");
  const runId = parts.length && isRunId(parts[parts.length - 1]) ? parts[parts.length - 1] : null;
  const crumbs = parts.slice(0, -1);
  const under = (i: number) => [...(root === "." ? [] : [root]), ...crumbs.slice(0, i + 1)].join("/");
  return html`<header class="header">
    <nav class="crumbs small" aria-label="Breadcrumb">
      ${parts.length ? html`<a href=${groupUrl(root)}>${root === "." ? "local" : root}</a>` : null}
      ${crumbs.map((p, i) => html`<span>/</span><a href=${groupUrl(under(i))}>${p}</a>`)}
    </nav>
    ${runId ? html`<${RunHeader} id=${runId} scope=${props.path} />` : html`<${GroupHeader} path=${props.path} />`}
    ${props.finding ? html`<p class="finding prose">${props.finding}</p>` : null}
  </header>`;
}

function GroupHeader({ path }: { path: string }) {
  const row = rows(useCall(calls.group(path)).data)[0] ?? null;
  const name = path === "." ? "local" : path.split("/").pop();
  if (!row) {
    return html`<h1 class="page-title title" tabindex="-1">${name}</h1><div class="skeleton late" style="block-size: 24px"></div>`;
  }
  const ended = ENDED.reduce((n, k) => n + (row[k] ?? 0), 0);
  return html`
    <h1 class="page-title title" tabindex="-1">${name} <${Sym} spec=${symbolFor("research", row.status)} word /></h1>
    <p class="facts">
      <span><b>${row.runs}</b> run${row.runs === 1 ? "" : "s"}</span>
      ${row.running ? html`<span><b>${row.running}</b> running</span>` : null}
      ${row.finished ? html`<span><b>${row.finished}</b> finished</span>` : null}
      ${ended
        ? html`<span class="tone-bad" data-tip=${ENDED.filter((k) => row[k]).map((k) => `${row[k]} ${k}`).join(", ")}>
            <${Icon} name="circle-x" size=${15} /> <b>${ended}</b> ${ended === 1 ? ENDED.find((k) => row[k]) : "ended early"}</span>`
        : null}
      ${row.notes ? html`<span><b>${row.notes}</b> note${row.notes === 1 ? "" : "s"}</span>` : null}
      <${Best} path=${path} />
    </p>`;
}

// the hypothesis of a group, its checks and its verdict: the first thing after the header.
export function ProposalSection({ path }: { path: string }) {
  const row = rows(useCall(calls.group(path)).data)[0] ?? null;
  const check = useCall(row?.proposal ? calls.check(path) : null).data;
  // the rationale (the statement's tooltip) and whether the statement is frozen.
  const shown = useCall(row?.proposal ? calls.proposal(path) : null).data;
  if (!row?.proposal) return null;
  const rationale = shown?.proposal?.rationale;
  // runs recorded a frozen version; a changed statement would be a version none of them ran under.
  const frozen = shown?.versions?.find((v: any) => v.version === shown.version)?.frozen
    ? "Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`."
    : undefined;
  const [progress, more] = progressText(check?.progress?.text ?? row.progress);
  return html`<${Section} label="proposal">
    <div class="proposal">
      <div class="statement">
        <${Editable} value=${row.proposal} label="the proposal's statement" locked=${shown ? frozen : "Loading the proposal…"}
          render=${(text: string) => html`<span data-tip=${frozen ? undefined : rationale}>${text}</span>`}
          onSave=${(statement: string) => editStatement(path, statement)} />
      </div>
      <div class="checks">
        ${(check?.predictions ?? []).map((p: any) => {
          const spec = symbolFor("result", p.result);
          const found = describe(p);
          const text = found ? `${spec.label}: ${found}` : spec.label;
          return html`<span class=${`check small tone-${spec.tone}`} key=${p.name} data-tip=${text}
              aria-label=${`${p.name}: ${text}`} tabindex="0"><${Icon} name=${spec.icon} size=${14} />${p.name}</span>`;
        })}
        ${check?.provisional || progress
          ? html`<span class="small">
              ${check?.provisional ? html`<span class="tone-warn" data-tip="the plan is not complete yet">provisional</span>` : null}
              ${progress ? html`<span class="muted" data-tip=${more}>${check?.provisional ? " · " : ""}${progress}</span>` : null}
            </span>`
          : null}
      </div>
      <${Verdict} path=${path} verdict=${row.verdict} />
    </div>
  <//>`;
}

function Verdict(props: { path: string; verdict: string | null }) {
  const notes = useCall(props.verdict ? calls.notes(props.path) : null).data;
  if (!props.verdict) return html`<p class="verdict-line muted">no verdict yet</p>`;
  const s = symbolFor("verdict", props.verdict);
  const note = (notes?.entries ?? []).find((n: any) => n.type === "verdict" && (n.group ?? props.path) === props.path);
  const when = note ? versionTime(note.id) : null;
  return html`<p class="verdict-line">
    <span class=${`sym tone-${s.tone}`}><${Icon} name=${s.icon} size=${16} /><span class="verdict-word">${s.label}</span></span>
    ${note
      ? html`<span class="small muted" data-tip=${when}>verdict${note.meta?.author ? ` by ${note.meta.author}` : ""}${when ? ` · ${ago(when)}` : ""}</span>`
      : null}
  </p>`;
}

function RunHeader({ id, scope }: { id: string; scope: string }) {
  const card = useCall(calls.card(id, scope)).data;
  if (!card) return html`<h1 class="page-title title" tabindex="-1">${id}</h1><div class="skeleton late" style="block-size: 24px"></div>`;
  const r = card.run;
  const copy = () => void navigator.clipboard?.writeText(r.id);
  return html`
    <h1 class="page-title title" tabindex="-1"><${Editable} value=${r.name ?? r.id} label="the run's name" class="title-edit"
        onSave=${(next: string) => renameRun(r.id, scope, next.trim())} />
      <${Sym} spec=${symbolFor("run", r.status)} word /></h1>
    ${r.error ? html`<p class="bad-text" data-tip=${r.error}>${r.error.split("\n")[0].slice(0, 160)}</p>` : null}
    <div class="facts">
      <span><b>${step(r.steps)}</b> steps</span>
      <span><b>${duration(r.duration_s)}</b></span>
      ${card.progress ? html`<${EpochFact} run=${r} progress=${card.progress} />` : null}
      <span data-tip=${r.created_at}>${ago(r.created_at)}</span>
      <${Best} path=${scope} />
      <${IconButton} icon="copy" label=${`Copy the run id ${r.id}`} onClick=${copy} />
      <${Popover} icon="ellipsis" label="Details" title="Run details" class="run-details">
        <table class="kv small">${details(r).map(([k, v]) => html`<tr><td class="muted">${k}</td><td>${v}</td></tr>`)}</table>
        <div class="menu-list">
          <button type="button" onClick=${() => navigate(groupUrl(scope, { run: r.id }), { replace: true })}>
            <${Icon} name="panel-right" size=${15} /> Open in the side panel</button>
          <button type="button" onClick=${copy}><${Icon} name="copy" size=${15} /> Copy the run id</button>
          ${r.git?.commit ? html`<button type="button" onClick=${() => navigator.clipboard?.writeText(r.git.commit)}>
            <${Icon} name="git-commit" size=${15} /> Copy the commit</button>` : null}
        </div>
      <//>
    </div>
    ${(card.proposals ?? []).length
      ? html`<div class="checks">
          ${card.proposals.map((p: any) => {
            const s = symbolFor("result", p.check);
            return html`<a class=${`check small tone-${s.tone}`} href=${groupUrl(p.group)} data-tip=${p.statement}>
              <${Icon} name=${s.icon} size=${14} />${p.group === "." ? "own proposal" : p.group}
              ${p.verdict ? html`<${Sym} spec=${symbolFor("verdict", p.verdict)} size=${14} />` : null}</a>`;
          })}
        </div>`
      : null}`;
}

// where a run is in its epochs: "epoch 3 of 5 · 38 % through · about 2h 4m left"; the time left only for a
// running run that logged its speed, from the steps still to go.
function EpochFact({ run, progress }: { run: any; progress: any }) {
  const { epoch, total, fraction, steps_per_epoch: perEpoch } = progress;
  const left =
    run.status === "running" && fraction !== null && perEpoch && run.steps_per_s
      ? duration(((1 - fraction) * total * perEpoch) / run.steps_per_s)
      : null;
  return html`<span>epoch <b>${epoch}</b>${total ? ` of ${total}` : ""}${fraction === null ? "" : ` · ${Math.round(fraction * 100)} % through`}${left ? ` · about ${left} left` : ""}</span>`;
}

// the main metric's best value, and for a group which run reached it; its distinguishing
// config goes in the tooltip, not inline, so a wide sweep doesn't crowd the facts line.
function Best({ path }: { path: string }) {
  const main = usePrefs(path).main;
  const best = useCallKept(calls.summary(path, main), path).data?.summary;
  if (!best) return null;
  const config = Object.entries(best.config ?? {}).map(([k, v]) => `${label(k)} ${value(v)}`).join(", ");
  const isRun = isRunId(path.split("/").pop() ?? "");
  const tip = `${best.stat} of ${best.metric} over ${isRun ? "the run" : "all runs"}${config ? ` (${config})` : ""}`;
  return html`<span data-tip=${tip}>
    best <b>${best.label ?? label(`metric.${best.metric}.${best.stat}`)} ${value(best.value)}</b>
    ${isRun ? null : html` · <a href=${runUrl(best.run)}>${best.name}</a>`}
  </span>`;
}

// what a run's details popover lists: only what is known.
function details(r: any): [string, string][] {
  const rows: [string, unknown][] = [
    ["id", r.id],
    ["host", r.host],
    ["commit", r.git?.commit && `${r.git.commit.slice(0, 10)}${r.git.dirty ? " (dirty)" : ""}`],
    ["branch", r.git?.branch],
    ["job", r.scheduler?.job_id && `${r.scheduler.kind} ${r.scheduler.job_id}`],
    ["attempts", r.attempts > 1 ? String(r.attempts) : null],
    ["started", r.created_at],
    ["ended", r.ended_at],
  ];
  return rows.filter((x): x is [string, string] => !!x[1]).map(([k, v]) => [k, String(v)]);
}
