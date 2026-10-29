// The context drawer: the selected run's card, config, metrics and output; else the group's notes.

import { html } from "htm/preact";
import { useMemo } from "preact/hooks";

import { useCall } from "../api.ts";
import { NoteItem } from "../blocks/context.ts";
import { rows } from "../blocks/common.ts";
import { runColors, useTheme } from "../bt/index.ts";
import { ago, duration, step, value } from "../bt/fmt.ts";
import { groupUrl, navigate, runUrl } from "../router.ts";
import { Icon, Sym } from "../ui/icons.ts";
import { IconButton } from "../ui/primitives.ts";
import { eventIcon, symbolFor } from "../ui/symbols.ts";
import * as calls from "./calls.ts";

export function Drawer(props: { path: string; run: string | null }) {
  const close = () => navigate(groupUrl(props.path), { replace: true });
  return html`<aside class="drawer" aria-label=${props.run ? "Run" : "Notes and timeline"}>
    <div class="drawer-head">
      <span class="status-item"><${Icon} name=${props.run ? "activity" : "file-text"} size=${15} />
        ${props.run ? "Run" : "Notes and timeline"}</span>
      <${IconButton} icon="x" label="Close (Esc)" onClick=${close} />
    </div>
    ${props.run ? html`<${RunContext} id=${props.run} scope=${props.path} />` : html`<${GroupContext} path=${props.path} />`}
  </aside>`;
}

function RunContext({ id, scope }: { id: string; scope: string }) {
  const card = useCall(calls.card(id, scope)).data;
  const output = useCall(calls.output(id, scope)).data;
  const ids = useCall(calls.runIds(scope)).data;
  const theme = useTheme();
  const color = useMemo(() => runColors(rows(ids).map((r) => r["run.id"]), theme).get(id), [ids, theme, id]);
  if (!card) return html`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;
  const r = card.run;
  const metrics = Object.entries(card.metrics ?? {}) as [string, any][];
  return html`<div class="drawer-body">
    <h3><span class="run-dot" style=${`background:${color ?? "var(--bt-subtle)"}`}></span>
      <a href=${runUrl(id)}>${r.name}</a></h3>
    <p class="facts small">
      <${Sym} spec=${symbolFor("run", r.status)} word />
      <span class="fact"><b>${step(r.steps)}</b> steps</span>
      <span class="fact"><b>${duration(r.duration_s)}</b></span>
      <span class="fact" data-tip=${r.created_at}>${ago(r.created_at)}</span>
    </p>
    ${r.error ? html`<pre class="log bad-text">${r.error}</pre>` : null}
    <h4>Config</h4>
    <table class="kv">${Object.entries(card.config ?? {}).map(([k, v]) => html`<tr><td>${k}</td><td class="num">${value(v)}</td></tr>`)}</table>
    ${metrics.length
      ? html`<h4>Metrics</h4>
          <table class="kv">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${metrics.map(([k, m]) => html`<tr><td>${k}</td><td class="num"><b>${value(m.last)}</b></td>
              <td class="num">${value(m.min)}</td><td class="num">${value(m.max)}</td></tr>`)}
          </table>`
      : null}
    ${card.cited_by?.length
      ? html`<h4>Cited by</h4>${card.cited_by.map((n: any) => html`<p class="small"><${Sym} spec=${symbolFor("note", n.type)} /> ${n.description}</p>`)}`
      : null}
    <h4>Events</h4>
    ${(card.events ?? []).slice(-8).map(
      (e: any) => html`<div class="event"><span class="muted num">${e.t?.slice(5, 16).replace("T", " ")}</span>
        <${Icon} name=${eventIcon(e.type)} size=${14} /><span>${e.description}</span></div>`,
    )}
    <h4>Output</h4>
    <pre class="log">${(output?.lines ?? []).join("\n")}</pre>
  </div>`;
}

function GroupContext({ path }: { path: string }) {
  const notes = useCall(calls.notes(path)).data;
  const timeline = useCall(calls.timeline(path)).data;
  return html`<div class="drawer-body">
    <h4 style="margin-block-start: 0">Notes</h4>
    ${notes && !notes.entries.length ? html`<p class="muted small">No notes yet.</p>` : null}
    <div class="notes">${(notes?.entries ?? [])
      .filter((n: any) => !String(n.state ?? "").startsWith("superseded"))
      .map((n: any) => html`<${NoteItem} key=${n.id} note=${n} />`)}</div>
    <h4>Timeline</h4>
    ${(timeline?.entries ?? []).slice().reverse().map(
      (e: any) => html`<div class="event"><span class="muted num">${e.t?.slice(5, 16).replace("T", " ")}</span>
        <${Icon} name=${e.kind === "note" ? "file-text" : eventIcon(e.type)} size=${14} />
        <span>${e.run ? html`<a href=${runUrl(e.run)}>${e.run.slice(-8)}</a> ` : null}${e.description ?? e.type}</span></div>`,
    )}
  </div>`;
}
