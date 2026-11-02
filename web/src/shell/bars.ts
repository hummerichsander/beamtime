// The top bar and the status bar.

import { html } from "htm/preact";
import { useEffect, useState } from "preact/hooks";

import { connection, paused, updated, useCall } from "../api.ts";
import { rows } from "../blocks/common.ts";
import { mode } from "../bt/index.ts";
import { ago } from "../bt/fmt.ts";
import { groupUrl, route, timelineUrl } from "../router.ts";
import { useStore } from "../state.ts";
import { Icon } from "../ui/icons.ts";
import { IconButton } from "../ui/primitives.ts";
import { change } from "./settings.ts";
import * as calls from "./calls.ts";
import { lastVisit, meta, palette, sidebar } from "./ui.ts";

const NEXT = { system: "light", light: "dark", dark: "system" } as const;
const MODE_ICON = { system: "monitor", light: "sun", dark: "moon" } as const;

export function TopBar() {
  const info = useStore(meta);
  const m = useStore(mode);
  const side = useStore(sidebar);
  return html`<header class="topbar">
    <${IconButton} icon="panel-left" label=${side ? "Hide the sidebar (⌘B)" : "Show the sidebar (⌘B)"}
      pressed=${side} onClick=${() => sidebar.set(!side)} />
    <a class="project heading" href="/f/local">${info?.project ?? "Beamtime"}</a>
    <button type="button" class="search input body" onClick=${() => palette.set("")} aria-label="Search (⌘K)">
      <${Icon} name="search" size=${15} /><span class="search-label small">Search groups, runs, commands</span><kbd class="small">⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${Sources} />
      <${IconButton} icon=${MODE_ICON[m]} label=${`Theme: ${m === "system" ? "follows the system" : m} (switch to ${NEXT[m]})`}
        onClick=${() => void change("theme_mode", NEXT[m])} />
      <a class="icon-button" href=${timelineUrl(route.value.page === "group" ? route.value.path : ".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${Icon} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${Icon} name="settings" size=${16} /></a>
    </div>
  </header>`;
}

// this machine and each remote, with whether it answers; the tree's answer keeps it current.
function Sources() {
  const sources: { name: string; state: string; error?: string }[] = useCall(calls.tree()).data?.meta?.sources ?? [];
  const remotes = sources.filter((s) => s.name !== "local");
  if (!remotes.length) {
    return html`<span class="source small" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${Icon} name="server" size=${15} /> local</span>`;
  }
  return html`${[{ name: "local", state: "connected" }, ...remotes].map((s) => html`<a class=${`source small ${s.state}`}
      href=${groupUrl(s.name === "local" ? "." : s.name)}
      data-tip=${s.state === "connected" ? `${s.name}: connected` : `${s.name}: unreachable. ${s.error ?? ""}`}>
      <${Icon} name=${s.state === "connected" ? "server" : "cloud-off"} size=${15} /> ${s.name}</a>`)}`;
}

function useNow(everyMs: number): number {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), everyMs);
    return () => clearInterval(t);
  }, [everyMs]);
  return now;
}

function endedAt(v: unknown): number {
  if (typeof v === "number") return v * 1000;
  return typeof v === "string" ? Date.parse(v) : NaN;
}

export function StatusBar() {
  const conn = useStore(connection);
  const isPaused = useStore(paused);
  const last = useStore(updated);
  const r = useStore(route);
  const now = useNow(5000);
  const status = useCall(calls.status()).data;
  const runs = rows(useCall(calls.allRuns()).data);
  const info = useStore(meta);
  const daemon = status?.daemon;
  const running = status?.runs?.running ?? 0;
  const failed = runs.filter((x) => x["run.status"] === "failed" && endedAt(x["run.ended_at"]) > lastVisit).length;
  const fresh = status?.meta?.freshness;
  const [dot, text, tip] = isPaused
    ? ["paused", "paused", "Live updates are paused (p)"]
    : conn === "live" && daemon
      ? ["", `live · updated ${ago(new Date(last).toISOString(), now)}`, `beamtime serve, pid ${daemon.pid}`]
      : conn === "live"
        ? ["wait", "connected; the indexer is not running", "Start it with: beamtime serve"]
        : conn === "connecting"
          ? ["wait", "connecting…", "Reconnecting to beamtime serve"]
          : ["off", "offline", "The server is not reachable"];
  return html`<footer class="statusbar small">
    <span class="status-item" data-tip=${tip}><span class=${`live-dot ${dot}`}></span>${text}</span>
    ${running
      ? html`<button type="button" class="status-item" data-tip="List the running runs" onClick=${() => palette.set("running")}>
          <${Icon} name="circle-dot" size=${14} class="tone-accent" />${running} running</button>`
      : null}
    ${failed
      ? html`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${() => palette.set("failed")}>
          <${Icon} name="circle-x" size=${14} />${failed} failed since your last visit</button>`
      : null}
    ${fresh?.behind
      ? html`<span class="status-item warn-text" data-tip=${fresh.text}><${Icon} name="hourglass" size=${14} />${fresh.behind} runs behind</span>`
      : null}
    ${fresh?.damaged?.length
      ? html`<span class="status-item warn-text" data-tip=${fresh.damaged.join("\n")}><${Icon} name="triangle-alert" size=${14} />${fresh.damaged.length} unreadable</span>`
      : null}
    <span class="spacer"></span>
    ${r.page === "group" && r.run ? html`<span class="status-item"><${Icon} name="activity" size=${14} />1 run selected</span>` : null}
    <${IconButton} icon=${isPaused ? "play" : "pause"} label=${isPaused ? "Resume live updates (p)" : "Pause live updates (p)"}
      pressed=${isPaused} onClick=${() => paused.set(!isPaused)} />
    ${info?.outdated
      ? html`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`
      : null}
    <span class="status-item">${info?.version ? `beamtime ${info.version}` : ""}</span>
  </footer>`;
}
