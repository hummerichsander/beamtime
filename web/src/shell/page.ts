// Pages: a group or run with its view, the /r/<id> redirect, and settings.

import { html } from "htm/preact";
import { useEffect, useMemo } from "preact/hooks";

import { fetchCall, useCall } from "../api.ts";
import { Block } from "../blocks/index.ts";
import { Notice, rows } from "../blocks/common.ts";
import { runColors, setMode, useTheme, ViewCtx, mode } from "../bt/index.ts";
import { groupUrl, navigate, restoreScroll } from "../router.ts";
import { useStore } from "../state.ts";
import * as calls from "./calls.ts";
import { Frame } from "./frame.ts";
import { meta, SHORTCUTS } from "./ui.ts";

export function GroupPage(props: { path: string }) {
  const view = useCall(calls.view(props.path));
  const ids = useCall(calls.runIds(props.path));
  const theme = useTheme();
  const colors = useMemo(
    () => runColors(rows(ids.data).map((r) => r["run.id"]), theme),
    [ids.data, theme],
  );
  useEffect(() => {
    if (view.status === "ready") requestAnimationFrame(restoreScroll);
  }, [view.status === "ready"]);
  useEffect(() => {
    document.title = `${props.path === "." ? "local" : props.path} · Beamtime`;
  }, [props.path]);
  return html`<div class="page">
    <${Frame} path=${props.path} />
    ${view.status === "error"
      ? html`<${Notice} kind="error">${view.error}<//>`
      : view.data
        ? html`<div class="view"><${ViewCtx.Provider} value=${{ path: props.path, colors }}>
            <${Block} node=${view.data.view} />
          <//></div>
          <p class="view-meta muted small">Built-in default view · authored views come with M6</p>`
        : html`<div class="view"><div class="skeleton late" style="height: 320px"></div></div>`}
  </div>`;
}

export function RunRedirect(props: { id: string }) {
  useEffect(() => {
    fetchCall(calls.view(props.id))
      .then((v) => navigate(groupUrl(v.path), { replace: true }))
      .catch(() => {});
  }, [props.id]);
  const view = useCall(calls.view(props.id));
  if (view.status === "error") return html`<div class="page"><${Notice} kind="error">${view.error}<//></div>`;
  return html`<div class="page"><div class="skeleton late" style="height: 320px"></div></div>`;
}

export function Settings() {
  const m = useStore(mode);
  const theme = useTheme();
  const info = useStore(meta);
  return html`<div class="page settings">
    <h2>Appearance</h2>
    <div class="segmented" role="radiogroup" aria-label="Theme mode">
      ${(["system", "light", "dark"] as const).map(
        (k) => html`<button role="radio" aria-checked=${m === k} class=${m === k ? "on" : ""} onClick=${() => setMode(k)}>${k}</button>`,
      )}
    </div>
    <p class="muted small">Theme: ${theme?.name ?? "–"} · set <code>theme:</code> in beamtime.yaml or
      ~/.config/beamtime/settings.yaml; theme files live in <code>themes/</code>.</p>
    ${(info?.theme?.problems ?? []).map((p: string) => html`<${Notice} kind="warning">${p}<//>`)}
    <h2>Keyboard</h2>
    <table class="kv">${SHORTCUTS.map(([k, d]) => html`<tr><td><kbd>${k}</kbd></td><td>${d}</td></tr>`)}</table>
    <h2>About</h2>
    <table class="kv">
      <tr><td>version</td><td>${info?.version}</td></tr>
      <tr><td>root</td><td><code>${info?.root}</code></td></tr>
      <tr><td>log dir</td><td><code>${info?.logdir}</code></td></tr>
    </table>
  </div>`;
}
