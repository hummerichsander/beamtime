// The page header, the same on every view: where you are, what was proposed, how it stands.

import { html } from "htm/preact";

import { useCall } from "../api.ts";
import { describe, progressText } from "../blocks/context.ts";
import { rows } from "../blocks/common.ts";
import { ago, duration, step, value } from "../bt/fmt.ts";
import { groupUrl, isRunId, runUrl } from "../router.ts";
import { Icon, Sym } from "../ui/icons.ts";
import { IconButton, Meter } from "../ui/primitives.ts";
import { symbolFor } from "../ui/symbols.ts";
import * as calls from "./calls.ts";

const ENDED = ["failed", "killed", "lost"];

export function Header(props: { path: string; finding?: string | null }) {
  const parts = props.path === "." ? [] : props.path.split("/");
  const runId = parts.length && isRunId(parts[parts.length - 1]) ? parts[parts.length - 1] : null;
  const crumbs = parts.slice(0, -1);
  return html`<header class="header">
    <nav class="crumbs" aria-label="Breadcrumb">
      ${parts.length ? html`<a href=${groupUrl(".")}>local</a>` : null}
      ${crumbs.map((p, i) => html`<span class="sep">/</span><a href=${groupUrl(crumbs.slice(0, i + 1).join("/"))}>${p}</a>`)}
    </nav>
    ${runId ? html`<${RunHeader} id=${runId} scope=${props.path} />` : html`<${GroupHeader} path=${props.path} />`}
    ${props.finding ? html`<p class="finding">${props.finding}</p>` : null}
  </header>`;
}

function GroupHeader({ path }: { path: string }) {
  const row = rows(useCall(calls.group(path)).data)[0] ?? null;
  const check = useCall(row?.proposal ? calls.check(path) : null).data;
  const rationale = useCall(row?.proposal ? calls.proposal(path) : null).data?.proposal?.rationale;
  const name = path === "." ? "local" : path.split("/").pop();
  if (!row) {
    return html`<h1 class="title" tabindex="-1">${name}</h1><div class="skeleton late" style="block-size: 52px"></div>`;
  }
  const [progress, more] = progressText(check?.progress?.text ?? row.progress);
  const ended = ENDED.reduce((n, k) => n + (row[k] ?? 0), 0);
  return html`
    <h1 class="title" tabindex="-1">${name} <${Sym} spec=${symbolFor("research", row.status)} word /></h1>
    ${row.proposal ? html`<p class="statement" data-tip=${rationale}>${row.proposal}</p>` : null}
    ${row.proposal
      ? html`<div class="preds">
          ${(check?.predictions ?? []).map(
            (p: any) => html`<span class="pred" key=${p.name} data-tip=${describe(p)}>
              <${Sym} spec=${symbolFor("result", p.result)} /><b>${p.name}</b></span>`,
          )}
          ${check?.provisional ? html`<span class="tag tone-warn" data-tip="the plan is not complete yet">provisional</span>` : null}
          ${progress
            ? html`<span class="pred"><${Meter} fraction=${check?.progress?.fraction ?? null} label=${more ?? progress} />
                <span data-tip=${more}>${progress}</span></span>`
            : null}
          ${row.verdict ? html`<span class="pred"><${Sym} spec=${symbolFor("verdict", row.verdict)} word /></span>` : null}
        </div>`
      : null}
    <div class="facts">
      <span class="fact"><b>${row.runs}</b> run${row.runs === 1 ? "" : "s"}</span>
      ${row.running ? html`<span class="fact"><${Sym} spec=${symbolFor("run", "running")} /><b>${row.running}</b> running</span>` : null}
      ${row.finished ? html`<span class="fact"><${Sym} spec=${symbolFor("run", "finished")} /><b>${row.finished}</b> finished</span>` : null}
      ${ended
        ? html`<span class="fact tone-bad" data-tip=${ENDED.filter((k) => row[k]).map((k) => `${row[k]} ${k}`).join(", ")}>
            <${Icon} name="circle-x" size=${15} /><b class="tone-bad">${ended}</b> ${ended === 1 ? ENDED.find((k) => row[k]) : "ended early"}</span>`
        : null}
      ${row.notes ? html`<span class="fact"><${Icon} name="file-text" size=${15} /><b>${row.notes}</b> note${row.notes === 1 ? "" : "s"}</span>` : null}
      <${Best} path=${path} />
    </div>`;
}

function RunHeader({ id, scope }: { id: string; scope: string }) {
  const card = useCall(calls.card(id, scope)).data;
  if (!card) return html`<h1 class="title" tabindex="-1">${id}</h1><div class="skeleton late" style="block-size: 52px"></div>`;
  const r = card.run;
  const copy = () => void navigator.clipboard?.writeText(r.id);
  return html`
    <h1 class="title" tabindex="-1">${r.name ?? r.id} <${Sym} spec=${symbolFor("run", r.status)} word /></h1>
    ${r.error ? html`<p class="statement bad-text" data-tip=${r.error}>${r.error.split("\n")[0].slice(0, 160)}</p>` : null}
    <div class="facts">
      <span class="fact"><b>${step(r.steps)}</b> steps</span>
      <span class="fact"><b>${duration(r.duration_s)}</b></span>
      <span class="fact" data-tip=${r.created_at}>${ago(r.created_at)}</span>
      <${Best} path=${scope} />
      <span class="fact">
        <${IconButton} icon="copy" label=${`Copy the run id ${r.id}`} onClick=${copy} />
        <span class="icon-button" tabindex="0" aria-label="Details" data-tip=${details(r)}><${Icon} name="ellipsis" size=${16} /></span>
      </span>
    </div>
    ${(card.proposals ?? []).length
      ? html`<div class="preds" style="margin-block-start: 10px">
          ${card.proposals.map(
            (p: any) => html`<a class="pred" href=${groupUrl(p.group)} data-tip=${p.statement}>
              <${Sym} spec=${symbolFor("result", p.check)} /><b>${p.group === "." ? "own proposal" : p.group}</b>
              ${p.verdict ? html`<${Sym} spec=${symbolFor("verdict", p.verdict)} />` : null}</a>`,
          )}
        </div>`
      : null}`;
}

// the main metric's best value, and for a group which run reached it with what config.
function Best({ path }: { path: string }) {
  const best = useCall(calls.view(path)).data?.summary;
  if (!best) return null;
  const config = Object.entries(best.config ?? {}).map(([k, v]) => `${k} ${value(v)}`).join(", ");
  const isRun = isRunId(path.split("/").pop() ?? "");
  return html`<span class="fact" data-tip=${`${best.stat} of ${best.metric} over ${isRun ? "the run" : "all runs"}`}>
    best <b>${best.metric} ${value(best.value)}</b>
    ${isRun ? null : html`<span>· <a href=${runUrl(best.run)}>${best.name}</a>${config ? html` <em>(${config})</em>` : null}</span>`}
  </span>`;
}

function details(r: any): string {
  return [
    r.id,
    r.host && `host ${r.host}`,
    r.git?.commit && `commit ${r.git.commit}${r.git.dirty ? " (dirty)" : ""}${r.git.branch ? ` on ${r.git.branch}` : ""}`,
    r.scheduler?.job_id && `${r.scheduler.kind} job ${r.scheduler.job_id}`,
    r.attempts > 1 && `${r.attempts} attempts`,
  ].filter(Boolean).join(" · ");
}
