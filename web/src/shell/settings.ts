// The settings page: the project's theme, mode, colormaps and figure styles, written to its beamtime.yaml.

import { html } from "htm/preact";
import { useState } from "preact/hooks";

import { Notice } from "../blocks/common.ts";
import { applyTheme, mode, pair, useTheme } from "../bt/index.ts";
import { saveSetting } from "../bt/writes.ts";
import { useStore } from "../state.ts";
import { Icon } from "../ui/icons.ts";
import { MultiSelect } from "../ui/multiselect.ts";
import { Section } from "../ui/primitives.ts";
import { useTitle } from "./favicon.ts";
import { meta, SHORTCUTS } from "./ui.ts";

type Mode = "system" | "light" | "dark";
type Key = "theme" | "theme_mode" | "colormap" | "colormap_diverging" | "figure_style";

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

let latest = 0;

// a setting changes beamtime.yaml, then the page follows the project's new meta.
export async function change(key: Key, value: unknown): Promise<void> {
  const mine = ++latest;
  if (key === "theme_mode") {
    // the mode applies at once; the file follows.
    mode.set(value as Mode);
    applyTheme();
  }
  const m = await saveSetting(key, value);
  // an answer to an earlier click can't undo a later one.
  if (mine === latest) applyMeta(m);
}

export function Settings() {
  const m = useStore(mode);
  const theme = useTheme();
  const info = useStore(meta);
  const [error, setError] = useState<string | null>(null);
  useTitle("Settings");
  const set = (key: Key, value: unknown) => {
    setError(null);
    change(key, value).catch((e: Error) => setError(e.message));
  };
  const s = info?.settings ?? {};
  const choice = (key: Key, label: string, options: string[]) => html`
    <label class="field-label small" for=${`setting-${key}`}>${label}</label>
    <span class="input body">
      <select id=${`setting-${key}`} value=${s[key]} onChange=${(e: Event) => set(key, (e.target as HTMLSelectElement).value)}>
        ${options.map((o) => html`<option value=${o}>${o}</option>`)}
      </select>
    </span>`;
  return html`<div class="page settings"><div class="sections">
    <${Section} label="settings">
      <h1 class="page-title title" tabindex="-1">Settings</h1>
      <p class="muted small">Changes are written to <code>${s.file ?? "beamtime.yaml"}</code>, the project's settings.</p>
      ${error ? html`<${Notice} kind="error">${error}<//>` : null}
    <//>
    <${Section} label="appearance">
      <div class="settings-rows">
        <span class="field-label small">Mode</span>
        <div class="segmented" role="radiogroup" aria-label="Theme mode">
          ${MODES.map(([k, icon, label]) => html`<button type="button" role="radio" aria-checked=${m === k} onClick=${() => set("theme_mode", k)}>
            <${Icon} name=${icon} size=${15} />${label}</button>`)}
        </div>
        ${choice("theme", "Theme", info?.themes ?? [])}
        ${choice("colormap", "Colormap", info?.colormaps?.sequential ?? [])}
        ${choice("colormap_diverging", "Diverging colormap", info?.colormaps?.diverging ?? [])}
      </div>
      <p class="muted small">Shown: <b>${theme?.name ?? "–"}</b>. Your own theme files recolor this layout: they go in <code>themes/</code> next to
        beamtime.yaml. Colormaps color numeric groups and heatmaps.</p>
      ${(info?.theme?.problems ?? []).map((p: string) => html`<${Notice} kind="warning">${p}<//>`)}
    <//>
    <${Section} label="figures">
      <div class="settings-rows">
        <span class="field-label small">Style sheets</span>
        ${(info?.figure_styles ?? []).length
          ? html`<${MultiSelect} options=${info.figure_styles} value=${s.figure_style ?? []} label="Style sheets"
              placeholder="Add a style" onChange=${(v: string[]) => set("figure_style", v)} />`
          : html`<span class="muted small"><code>${JSON.stringify(s.figure_style ?? [])}</code>; choosing others needs the figures
              extra: <code>uv add matplotlib scienceplots</code></span>`}
      </div>
      <p class="muted small">PDF downloads are drawn with <code>plt.style.use(${JSON.stringify(s.figure_style ?? [])})</code>, in this order
        (later sheets override earlier ones). Without LaTeX, <code>no-latex</code> is added for <code>science</code>. Your own
        <code>.mplstyle</code> files anywhere in the project are listed too.</p>
    <//>
    <${Section} label="keyboard">
      <table class="kv">${SHORTCUTS.map(([k, d]) => html`<tr><td><kbd class="small">${k}</kbd></td><td>${d}</td></tr>`)}</table>
    <//>
    <${Section} label="about">
      <table class="kv">
        <tr><td class="muted">version</td><td>${info?.version}</td></tr>
        <tr><td class="muted">root</td><td><code class="code">${info?.root}</code></td></tr>
        <tr><td class="muted">log dir</td><td><code class="code">${info?.logdir}</code></td></tr>
      </table>
    <//>
  </div></div>`;
}
