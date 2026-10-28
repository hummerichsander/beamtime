// The command palette (⌘K), a modal dialog: groups, runs by name, id or status, and commands.

import { html } from "htm/preact";
import { useEffect, useRef, useState } from "preact/hooks";

import { paused, useCall } from "../api.ts";
import { rows } from "../blocks/common.ts";
import { setMode } from "../bt/index.ts";
import { groupUrl, navigate, route } from "../router.ts";
import { Icon, Sym } from "../ui/icons.ts";
import { symbolFor, type SymbolSpec } from "../ui/symbols.ts";
import * as calls from "./calls.ts";
import { help, palette, sidebar } from "./ui.ts";

type Item = { section: string; label: string; detail: string; sym: SymbolSpec; run: () => void };

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

export function Palette(props: { query: string }) {
  const [query, setQuery] = useState(props.query);
  const [active, setActive] = useState(0);
  const dialog = useRef<HTMLDialogElement>(null);
  const groups = rows(useCall(calls.tree()).data);
  const runs = rows(useCall(calls.allRuns()).data);

  useEffect(() => {
    const d = dialog.current!;
    d.showModal();
    const closed = () => palette.set(null);
    d.addEventListener("close", closed);
    // light dismiss where <dialog closedby> is missing (Safari): press and release outside.
    let outside = false;
    const off = (e: PointerEvent) => {
      const r = d.getBoundingClientRect();
      return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
    };
    const down = (e: PointerEvent) => (outside = off(e));
    const up = (e: PointerEvent) => outside && off(e) && d.close();
    if (!("closedBy" in HTMLDialogElement.prototype)) {
      d.addEventListener("pointerdown", down);
      d.addEventListener("pointerup", up);
    }
    return () => {
      d.removeEventListener("close", closed);
      d.removeEventListener("pointerdown", down);
      d.removeEventListener("pointerup", up);
    };
  }, []);

  const close = () => dialog.current?.close();
  const go = (url: string) => () => navigate(url);
  const r = route.value;
  const here = r.page === "group" ? r.path : ".";
  const command = (label: string, detail: string, icon: string, run: () => void): Item => ({
    section: "Commands", label, detail, sym: { icon, tone: "muted", label }, run,
  });
  const items: Item[] = [
    ...groups.map((g) => ({
      section: "Groups",
      label: g.path === "." ? "local" : g.path,
      detail: `${g.runs} runs${g.proposal ? ` · ${g.proposal}` : ""}`,
      sym: symbolFor("research", g.status),
      run: go(groupUrl(g.path)),
    })),
    ...runs.map((x) => ({
      section: "Runs",
      label: x["run.name"] ?? x["run.id"],
      detail: `${x["run.status"]} · ${x["run.path"]}`,
      sym: symbolFor("run", x["run.status"]),
      run: go(groupUrl(x["run.path"])),
    })),
    command("Theme: light", "", "sun", () => setMode("light")),
    command("Theme: dark", "", "moon", () => setMode("dark")),
    command("Theme: follow the system", "", "monitor", () => setMode("system")),
    command("Copy link to this page", "", "link", () => void navigator.clipboard?.writeText(location.href)),
    command("Show notes and timeline", "i", "file-text", go(groupUrl(here, { drawer: true }))),
    command("Show or hide the sidebar", "⌘B", "panel-left", () => sidebar.set(!sidebar.value)),
    command(paused.value ? "Resume live updates" : "Pause live updates", "p", paused.value ? "play" : "pause", () => paused.set(!paused.value)),
    command("Keyboard shortcuts", "?", "keyboard", () => help.set(true)),
    command("Settings", "", "settings", go("/settings/appearance")),
  ];
  const ranked = items
    .map((it) => ({ it, s: Math.max(score(query, it.label), score(query, it.detail) * 0.5) }))
    .filter((x) => x.s > 0)
    .sort((a, b) => b.s - a.s || order(a.it.section) - order(b.it.section))
    .slice(0, 60)
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
    else return;
    e.preventDefault();
  };
  let section = "";
  return html`<dialog class="sheet" ref=${dialog} aria-label="Search" closedby="any">
    <div class="palette-input"><${Icon} name="search" size=${18} />
      <input autofocus value=${query} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${ranked[active] ? `pal-${active}` : undefined}
        onInput=${(e: Event) => { setQuery((e.target as HTMLInputElement).value); setActive(0); }} onKeyDown=${onKey} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${ranked.map((it, i) => {
        const head = it.section !== section && !query ? (section = it.section) : null;
        return html`${head ? html`<li class="section" role="presentation">${head}</li>` : null}
          <li id=${`pal-${i}`} class="item" role="option" aria-selected=${i === active}
              onMouseMove=${() => setActive(i)} onClick=${() => pick(it)}>
            <${Sym} spec=${it.sym} /><span class="label">${it.label}</span><span class="detail">${it.detail}</span>
          </li>`;
      })}
    </ul>
  </dialog>`;
}

function order(section: string): number {
  return ["Groups", "Runs", "Commands"].indexOf(section);
}
