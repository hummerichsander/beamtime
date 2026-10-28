// The command palette (⌘K): groups, runs by name or id, and commands.

import { html } from "htm/preact";
import { useEffect, useRef, useState } from "preact/hooks";

import { paused, useCall } from "../api.ts";
import { rows } from "../blocks/common.ts";
import { setMode } from "../bt/index.ts";
import { groupUrl, navigate, route } from "../router.ts";
import * as calls from "./calls.ts";
import { help, palette, sidebar } from "./ui.ts";

type Item = { kind: string; label: string; detail: string; run: () => void };

export function score(query: string, text: string): number {
  const q = query.toLowerCase();
  const t = text.toLowerCase();
  if (!q) return 1;
  const at = t.indexOf(q);
  if (at >= 0) return 100 - Math.min(at, 50) - t.length / 100;
  let i = 0;
  let gaps = 0;
  for (const ch of t) {
    if (ch === q[i]) i++;
    else if (i > 0) gaps++;
    if (i === q.length) return 40 - Math.min(gaps, 39);
  }
  return 0;
}

export function Palette() {
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  const groups = rows(useCall(calls.tree()).data);
  const runs = rows(useCall(calls.allRuns()).data);
  useEffect(() => input.current?.focus(), []);

  const close = () => palette.set(false);
  const go = (url: string) => () => {
    close();
    navigate(url);
  };
  const r = route.value;
  const here = r.page === "group" ? r.path : ".";
  const commands: Item[] = [
    { kind: "command", label: "Theme: light", detail: "", run: () => setMode("light") },
    { kind: "command", label: "Theme: dark", detail: "", run: () => setMode("dark") },
    { kind: "command", label: "Theme: follow the system", detail: "", run: () => setMode("system") },
    { kind: "command", label: "Copy link", detail: "this page", run: () => void navigator.clipboard?.writeText(location.href) },
    { kind: "command", label: "Toggle context drawer", detail: "i", run: go(groupUrl(here, { drawer: !(r.page === "group" && r.drawer) })) },
    { kind: "command", label: "Toggle sidebar", detail: "⌘B", run: () => sidebar.set(!sidebar.value) },
    { kind: "command", label: paused.value ? "Resume live updates" : "Pause live updates", detail: "p", run: () => paused.set(!paused.value) },
    { kind: "command", label: "Keyboard shortcuts", detail: "?", run: () => help.set(true) },
    { kind: "command", label: "Settings", detail: "", run: go("/settings/appearance") },
  ];
  const items: Item[] = [
    ...groups.map((f) => ({ kind: "group", label: f.path === "." ? "local" : f.path, detail: `${f.runs} runs`, run: go(groupUrl(f.path)) })),
    ...runs.map((x) => ({ kind: "run", label: x["run.name"] ?? x["run.id"], detail: `${x["run.path"]}`, run: go(groupUrl(x["run.path"])) })),
    ...commands,
  ];
  const ranked = items
    .map((it) => ({ it, s: Math.max(score(query, it.label), score(query, it.detail) * 0.8) }))
    .filter((x) => x.s > 0)
    .sort((a, b) => b.s - a.s)
    .slice(0, 50)
    .map((x) => x.it);
  const pick = (it: Item | undefined) => {
    if (!it) return;
    close();
    it.run();
  };
  const onKey = (e: KeyboardEvent) => {
    if (e.key === "ArrowDown") setActive(Math.min(ranked.length - 1, active + 1));
    else if (e.key === "ArrowUp") setActive(Math.max(0, active - 1));
    else if (e.key === "Enter") pick(ranked[active]);
    else if (e.key === "Escape") close();
    else return;
    e.preventDefault();
  };
  return html`<div class="overlay" onClick=${close}>
    <div class="palette" role="dialog" aria-label="Search" onClick=${(e: Event) => e.stopPropagation()}>
      <input ref=${input} value=${query} placeholder="Groups, runs by name or id, commands"
        onInput=${(e: Event) => { setQuery((e.target as HTMLInputElement).value); setActive(0); }} onKeyDown=${onKey} />
      <ul role="listbox">
        ${ranked.map((it, i) => html`<li role="option" aria-selected=${i === active} class=${i === active ? "active" : ""}
            onMouseMove=${() => setActive(i)} onClick=${() => pick(it)}>
          <span class="kind">${it.kind}</span><span class="label">${it.label}</span><span class="muted small">${it.detail}</span>
        </li>`)}
      </ul>
    </div>
  </div>`;
}

