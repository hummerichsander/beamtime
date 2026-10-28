// The context drawer: the selected run's card, config, notes and output; else the group's notes.

import { html } from "htm/preact";

import { useCall } from "../api.ts";
import { Dot } from "../blocks/common.ts";
import { inline } from "../blocks/context.ts";
import { ago, duration, value } from "../bt/fmt.ts";
import { groupUrl, navigate, runUrl } from "../router.ts";
import * as calls from "./calls.ts";

export function Drawer(props: { path: string; run: string | null }) {
  const close = () => navigate(groupUrl(props.path), { replace: true });
  return html`<aside class="drawer" aria-label="Context">
    <div class="drawer-head">
      <span>${props.run ? "Run" : "Notes and timeline"}</span>
      <button class="icon" title="Close (Esc)" onClick=${close}>×</button>
    </div>
    ${props.run ? html`<${RunContext} id=${props.run} scope=${props.path} />` : html`<${GroupContext} path=${props.path} />`}
  </aside>`;
}

function RunContext({ id, scope }: { id: string; scope: string }) {
  const card = useCall(calls.card(id, scope)).data;
  const output = useCall(calls.output(id, scope)).data;
  if (!card) return html`<div class="skeleton" style="height: 200px"></div>`;
  const r = card.run;
  return html`<div class="drawer-body">
    <h3><a href=${runUrl(id)}>${r.name}</a></h3>
    <p class="small"><${Dot} status=${r.status} /> ${r.status} · ${duration(r.duration_s)} · ${value(r.steps)} steps · ${ago(r.created_at)}</p>
    ${r.error ? html`<pre class="log bad-text">${r.error}</pre>` : null}
    <h4>Config</h4>
    <table class="kv">${Object.entries(card.config ?? {}).map(([k, v]) => html`<tr><td>${k}</td><td class="num">${value(v)}</td></tr>`)}</table>
    <h4>Metrics</h4>
    <table class="kv">
      <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
      ${Object.entries(card.metrics ?? {}).map(([k, m]: [string, any]) => html`<tr><td>${k}</td>
        <td class="num">${value(m.last)}</td><td class="num">${value(m.min)}</td><td class="num">${value(m.max)}</td></tr>`)}
    </table>
    ${card.cited_by?.length
      ? html`<h4>Cited by</h4>${card.cited_by.map((n: any) => html`<p class="small">${n.type}: ${n.description}</p>`)}`
      : null}
    <h4>Events</h4>
    ${(card.events ?? []).slice(-8).map((e: any) => html`<p class="small"><span class="muted">${e.t?.slice(5, 16).replace("T", " ")}</span> ${e.description}</p>`)}
    <h4>Output</h4>
    <pre class="log">${(output?.lines ?? []).join("\n")}</pre>
  </div>`;
}

function GroupContext({ path }: { path: string }) {
  const notes = useCall(calls.notes(path)).data;
  const timeline = useCall(calls.timeline(path)).data;
  return html`<div class="drawer-body">
    <h4>Notes</h4>
    ${notes && !notes.entries.length ? html`<p class="muted small">No notes yet.</p>` : null}
    ${(notes?.entries ?? []).map((n: any) => html`<div class="note-item" key=${n.id}>
      <span class=${`chip note-${n.type}`}>${n.type}</span>${n.state ? html` <span class="muted small">${n.state}</span>` : null}
      <p>${inline(n.description)}</p>
      <p class="muted small">${n.group} · ${n.id.slice(0, 13).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})/, "$1-$2-$3 $4:$5")}</p>
    </div>`)}
    <h4>Timeline</h4>
    ${(timeline?.entries ?? []).map((e: any) => html`<p class="small">
      <span class="muted">${e.t?.slice(5, 16).replace("T", " ")}</span> ${e.type ?? e.kind}
      ${e.run ? html` <a href=${runUrl(e.run)}>${e.run.slice(-8)}</a>` : null} ${e.description && e.description !== e.type ? e.description : ""}</p>`)}
  </div>`;
}
