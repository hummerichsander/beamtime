// The frame: breadcrumb and status, the proposal with its check, the counts. Same on every view.

import { html } from "htm/preact";

import { useCall } from "../api.ts";
import { Badge, Progress } from "../blocks/context.ts";
import { Dot, rows } from "../blocks/common.ts";
import { duration, value } from "../bt/fmt.ts";
import { groupUrl, isRunId } from "../router.ts";
import * as calls from "./calls.ts";

const COUNTS = ["running", "finished", "failed", "killed", "lost"];

export function Frame(props: { path: string; finding?: string | null; source?: string }) {
  const parts = props.path === "." ? [] : props.path.split("/");
  const runId = parts.length && isRunId(parts[parts.length - 1]) ? parts[parts.length - 1] : null;
  const groupPath = runId ? parts.slice(0, -1).join("/") || "." : props.path;
  return html`<header class="frame">
    <div class="frame-line">
      <nav class="breadcrumb" aria-label="Breadcrumb">
        <a href=${groupUrl(".")}>local</a>
        ${parts.map((p, i) => html`<span class="sep">/</span>${i === parts.length - 1
          ? html`<span aria-current="page">${runId && i === parts.length - 1 ? html`<${RunName} id=${runId} scope=${props.path} />` : p}</span>`
          : html`<a href=${groupUrl(parts.slice(0, i + 1).join("/"))}>${p}</a>`}`)}
      </nav>
      ${runId ? html`<${RunStatus} id=${runId} scope=${props.path} />` : html`<${GroupStatus} path=${groupPath} />`}
    </div>
    ${runId ? html`<${RunLine} id=${runId} scope=${props.path} />` : html`<${GroupLines} path=${groupPath} />`}
    ${props.finding ? html`<p class="finding">${props.finding}</p>` : null}
  </header>`;
}

function useGroup(path: string): Record<string, any> | null {
  const result = useCall(calls.group(path));
  return rows(result.data)[0] ?? null;
}

function GroupStatus({ path }: { path: string }) {
  const row = useGroup(path);
  if (!row) return null;
  return html`<span class=${`chip status-${row.status}`}>${row.status}</span>`;
}

function GroupLines({ path }: { path: string }) {
  const row = useGroup(path);
  const check = useCall(row?.proposal ? calls.check(path) : null);
  if (!row) return html`<div class="frame-line placeholder"></div>`;
  const c = check.data;
  return html`
    ${row.proposal
      ? html`<div class="frame-line">
          <span class="statement">${row.proposal}</span>
          ${(c?.predictions ?? []).map((p: any) => html`<${Badge} key=${p.name} prediction=${p} />`)}
          <${Progress} progress=${c?.progress} />
          ${row.verdict ? html`<span class=${`chip verdict-${row.verdict}`}>verdict: ${row.verdict}</span>` : null}
        </div>`
      : null}
    <div class="frame-line counts">
      <span>${row.runs} run${row.runs === 1 ? "" : "s"}</span>
      ${COUNTS.filter((k) => row[k]).map((k) => html`<span><${Dot} status=${k} /> ${row[k]} ${k}</span>`)}
      ${row.notes ? html`<span class="muted">${row.notes} note${row.notes === 1 ? "" : "s"}</span>` : null}
    </div>`;
}

function useCard(id: string, scope: string): any {
  return useCall(calls.card(id, scope)).data;
}

function RunName({ id, scope }: { id: string; scope: string }) {
  const card = useCard(id, scope);
  return html`<span title=${id}>${card?.run.name ?? id}</span>`;
}

function RunStatus({ id, scope }: { id: string; scope: string }) {
  const card = useCard(id, scope);
  if (!card) return null;
  return html`<span class=${`chip run-${card.run.status}`}><${Dot} status=${card.run.status} /> ${card.run.status}</span>`;
}

function RunLine({ id, scope }: { id: string; scope: string }) {
  const card = useCard(id, scope);
  if (!card) return html`<div class="frame-line placeholder"></div>`;
  const r = card.run;
  return html`<div class="frame-line counts">
    <code class="muted">${r.id}</code>
    <span>${value(r.steps)} steps</span>
    <span>${duration(r.duration_s)}</span>
    ${r.host ? html`<span class="muted">${r.host}</span>` : null}
    ${r.git?.commit ? html`<span class="muted">git ${r.git.commit}${r.git.dirty ? " (dirty)" : ""}</span>` : null}
    ${(card.proposals ?? []).map((p: any) => html`<span class=${`chip result-${p.check}`} title=${p.statement}>
      ${p.group}${p.check ? `: check ${p.check}` : ""}${p.verdict ? `, ${p.verdict}` : ""}</span>`)}
    ${r.error ? html`<span class="bad-text" title=${r.error}>${r.error.split("\n")[0].slice(0, 120)}</span>` : null}
  </div>`;
}
