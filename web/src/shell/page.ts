// Pages: a group or run with its view, the /r/<id> redirect, and settings.

import { html } from "htm/preact";
import { useEffect } from "preact/hooks";

import { fetchCall, useCall } from "../api.ts";
import { Notice } from "../blocks/common.ts";
import { mode, setMode, useTheme } from "../bt/index.ts";
import { groupUrl, navigate, restoreScroll } from "../router.ts";
import { useStore } from "../state.ts";
import { Icon } from "../ui/icons.ts";
import * as calls from "./calls.ts";
import { Header } from "./header.ts";
import { History, ViewBody, ViewSource } from "./views.ts";
import { meta, SHORTCUTS } from "./ui.ts";

export function GroupPage(props: { path: string; version?: string | null; draft?: string | null; history?: boolean }) {
  useEffect(() => {
    document.title = `${props.path === "." ? "local" : props.path} · Beamtime`;
  }, [props.path]);
  if (props.history) return html`<div class="page"><${Header} path=${props.path} /><${History} path=${props.path} /></div>`;
  return html`<div class="page">
    <${ViewPage} path=${props.path} version=${props.version ?? null} draft=${props.draft ?? null} />
  </div>`;
}

function ViewPage(props: { path: string; version: string | null; draft: string | null }) {
  const view = useCall(calls.view(props.path, props.version, props.draft));
  useEffect(() => {
    if (view.status === "ready") requestAnimationFrame(restoreScroll);
  }, [view.status === "ready"]);
  return html`
    <${Header} path=${props.path} finding=${view.data?.finding} />
    ${view.data ? html`<${ViewSource} path=${props.path} view=${view.data} />` : null}
    ${view.status === "error"
      ? html`<${Notice} kind="error">${view.error}<//>`
      : html`<${ViewBody} path=${props.path} view=${view.data} />`}`;
}

export function RunRedirect(props: { id: string }) {
  useEffect(() => {
    fetchCall(calls.view(props.id))
      .then((v) => navigate(groupUrl(v.path), { replace: true }))
      .catch(() => {});
  }, [props.id]);
  const view = useCall(calls.view(props.id));
  if (view.status === "error") return html`<div class="page"><${Notice} kind="error">${view.error}<//></div>`;
  return html`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`;
}

const MODES = [
  ["system", "monitor", "System"],
  ["light", "sun", "Light"],
  ["dark", "moon", "Dark"],
] as const;

export function Settings() {
  const m = useStore(mode);
  const theme = useTheme();
  const info = useStore(meta);
  useEffect(() => {
    document.title = "Settings · Beamtime";
  }, []);
  return html`<div class="page settings">
    <header class="header"><h1 class="title" tabindex="-1">Settings</h1></header>
    <h2>Appearance</h2>
    <div class="segmented" role="radiogroup" aria-label="Theme mode">
      ${MODES.map(([k, icon, label]) => html`<button type="button" role="radio" aria-checked=${m === k} onClick=${() => setMode(k)}>
        <${Icon} name=${icon} size=${15} />${label}</button>`)}
    </div>
    <p class="muted small">Theme <b>${theme?.name ?? "–"}</b>. Set <code>theme:</code> in beamtime.yaml or
      ~/.config/beamtime/settings.yaml; your own theme files go in <code>themes/</code>.</p>
    ${(info?.theme?.problems ?? []).map((p: string) => html`<${Notice} kind="warning">${p}<//>`)}
    <h2>Keyboard</h2>
    <table class="kv">${SHORTCUTS.map(([k, d]) => html`<tr><td><kbd>${k}</kbd></td><td>${d}</td></tr>`)}</table>
    <h2>About</h2>
    <table class="kv">
      <tr><td class="muted">version</td><td>${info?.version}</td></tr>
      <tr><td class="muted">root</td><td><code>${info?.root}</code></td></tr>
      <tr><td class="muted">log dir</td><td><code>${info?.logdir}</code></td></tr>
    </table>
  </div>`;
}
