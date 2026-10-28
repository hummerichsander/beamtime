// The top bar and the status bar.

import { html } from "htm/preact";

import { connection, paused, useCall } from "../api.ts";
import { mode, setMode } from "../bt/index.ts";
import { route } from "../router.ts";
import { useStore } from "../state.ts";
import * as calls from "./calls.ts";
import { meta, palette, sidebar } from "./ui.ts";

const NEXT = { system: "light", light: "dark", dark: "system" } as const;
const ICON = { system: "◐", light: "☀", dark: "☾" } as const;

export function TopBar() {
  const info = useStore(meta);
  const m = useStore(mode);
  return html`<header class="topbar">
    <button class="icon" title="Sidebar (⌘B)" onClick=${() => sidebar.set(!sidebar.value)}>☰</button>
    <a class="project" href="/f/local">${info?.project ?? "Beamtime"}</a>
    <button class="search" onClick=${() => palette.set(true)}>
      <span>Search groups, runs, commands</span><kbd>⌘K</kbd>
    </button>
    <span class="source" title="Sources; remotes come with M7"><span class="dot finished"></span> local</span>
    <button class="icon" title=${`Theme: ${m} (click for ${NEXT[m]})`} onClick=${() => setMode(NEXT[m])}>${ICON[m]}</button>
    <a class="icon" href="/settings/appearance" title="Settings">⚙</a>
  </header>`;
}

export function StatusBar() {
  const conn = useStore(connection);
  const isPaused = useStore(paused);
  const r = useStore(route);
  const status = useCall(calls.status()).data;
  const daemon = status?.daemon;
  const live = conn === "live" && daemon;
  return html`<footer class="statusbar">
    <span title=${daemon ? `pid ${daemon.pid}, version ${daemon.version}` : ""}>
      <span class=${`dot ${live ? "finished" : conn === "connecting" ? "killed" : "failed"}`}></span>
      ${conn === "live" ? (daemon ? "live" : "connected, daemon not running") : conn === "connecting" ? "connecting…" : "offline"}
    </span>
    ${daemon ? null : html`<span class="muted">${status?.meta?.freshness?.text ?? ""}</span>`}
    <span class="spacer"></span>
    ${r.page === "group" && r.run ? html`<span>1 run selected</span>` : null}
    <button class="link" title="Pause live updates (p)" onClick=${() => paused.set(!isPaused)}>
      ${isPaused ? "▶ resume" : "❚❚ pause"}</button>
  </footer>`;
}
