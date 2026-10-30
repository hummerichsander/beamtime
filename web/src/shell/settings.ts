// The settings page: the project's theme, mode and figure styles, written to its beamtime.yaml.

import { html } from "htm/preact";
import { useEffect, useState } from "preact/hooks";

import { Notice } from "../blocks/common.ts";
import { applyTheme, mode, pair, useTheme } from "../bt/index.ts";
import { saveSetting } from "../bt/writes.ts";
import { useStore } from "../state.ts";
import { Icon } from "../ui/icons.ts";
import { MultiSelect } from "../ui/multiselect.ts";
import { meta, SHORTCUTS } from "./ui.ts";

type Mode = "system" | "light" | "dark";

const MODES = [
  ["system", "monitor", "System"],
  ["light", "sun", "Light"],
  ["dark", "moon", "Dark"],
] as const;

// the shell takes a project's meta: its theme pair and mode.
export function applyMeta(m: any): void {
  meta.set(m);
  pair.set(m.theme);
  if (m.settings?.theme_mode) mode.set(m.settings.theme_mode as Mode);
  applyTheme();
}

// a setting changes beamtime.yaml, then the page follows the project's new meta.
export async function change(key: "theme" | "theme_mode" | "figure_style", value: unknown): Promise<void> {
  if (key === "theme_mode") {
    // the mode applies at once; the file follows.
    mode.set(value as Mode);
    applyTheme();
  }
  applyMeta(await saveSetting(key, value));
}

export function Settings() {
  const m = useStore(mode);
  const theme = useTheme();
  const info = useStore(meta);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    document.title = "Settings · Beamtime";
  }, []);
  const set = (key: "theme" | "theme_mode" | "figure_style", value: unknown) => {
    setError(null);
    change(key, value).catch((e: Error) => setError(e.message));
  };
  const s = info?.settings ?? {};
  return html`<div class="page settings">
    <header class="header"><h1 class="title" tabindex="-1">Settings</h1></header>
    <p class="muted small">Changes are written to <code>${s.file ?? "beamtime.yaml"}</code>, the project's settings.</p>
    ${error ? html`<${Notice} kind="error">${error}<//>` : null}
    <h2>Appearance</h2>
    <div class="settings-rows">
      <span class="field-label">Mode</span>
      <div class="segmented" role="radiogroup" aria-label="Theme mode">
        ${MODES.map(([k, icon, label]) => html`<button type="button" role="radio" aria-checked=${m === k} onClick=${() => set("theme_mode", k)}>
          <${Icon} name=${icon} size=${15} />${label}</button>`)}
      </div>
      <span class="field-label">Theme</span>
      <select value=${s.theme} onChange=${(e: Event) => set("theme", (e.target as HTMLSelectElement).value)}>
        ${(info?.themes ?? []).map((t: string) => html`<option value=${t}>${t}</option>`)}
      </select>
    </div>
    <p class="muted small">Shown: <b>${theme?.name ?? "–"}</b>. Your own theme files go in <code>themes/</code> next to beamtime.yaml.</p>
    ${(info?.theme?.problems ?? []).map((p: string) => html`<${Notice} kind="warning">${p}<//>`)}
    <h2>Figures</h2>
    <div class="settings-rows">
      <span class="field-label">Style sheets</span>
      ${(info?.figure_styles ?? []).length
        ? html`<${MultiSelect} options=${info.figure_styles} value=${s.figure_style ?? []} label="Style sheets"
            placeholder="Add a style" onChange=${(v: string[]) => set("figure_style", v)} />`
        : html`<span class="muted small"><code>${JSON.stringify(s.figure_style ?? [])}</code>; choosing others needs the figures
            extra: <code>uv add matplotlib scienceplots</code></span>`}
    </div>
    <p class="muted small">PDF downloads are drawn with <code>plt.style.use(${JSON.stringify(s.figure_style ?? [])})</code>, in this order
      (later sheets override earlier ones). Without LaTeX, <code>no-latex</code> is added for <code>science</code>. Your own
      <code>.mplstyle</code> files anywhere in the project are listed too.</p>
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
