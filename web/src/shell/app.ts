// The shell: top bar, sidebar, the page, the context drawer and the status bar.

import { html } from "htm/preact";
import { useEffect, useRef } from "preact/hooks";

import { fetchCall, paused } from "../api.ts";
import { rows } from "../blocks/common.ts";
import { groupUrl, navigate, rendering, route, setScroller } from "../router.ts";
import { useStore } from "../state.ts";
import { StatusBar, TopBar } from "./bars.ts";
import * as calls from "./calls.ts";
import { Drawer } from "./drawer.ts";
import { GroupPage, RunRedirect } from "./page.ts";
import { Settings } from "./settings.ts";
import { TimelinePage } from "./timeline.ts";
import { Palette } from "./palette.ts";
import { Sidebar } from "./sidebar.ts";
import { buildTree, siblings } from "./tree.ts";
import { help, palette, sidebar, SHORTCUTS, typing } from "./ui.ts";

export function App() {
  const r = useStore(route);
  const showSidebar = useStore(sidebar);
  const query = useStore(palette);
  const showHelp = useStore(help);
  const main = useRef<HTMLElement>(null);
  useEffect(() => setScroller(() => main.current), []);
  useEffect(() => {
    addEventListener("keydown", onKey);
    return () => removeEventListener("keydown", onKey);
  }, []);
  const drawer = r.page === "group" && r.drawer;
  let page;
  switch (r.page) {
    case "group":
      page = html`<${GroupPage} key=${`${r.path} ${r.version} ${r.draft} ${r.history}`} path=${r.path} version=${r.version}
        draft=${r.draft} history=${r.history} />`;
      break;
    case "run":
      page = html`<${RunRedirect} id=${r.id} />`;
      break;
    case "settings":
      page = html`<${Settings} />`;
      break;
    case "timeline":
      page = html`<${TimelinePage} key=${r.from} from=${r.from} />`;
      break;
    default:
      page = html`<div class="page"><p>No page at ${r.url}. <a href="/f/local">Go to the log dir.</a></p></div>`;
  }
  // the headless renderer gets the view alone.
  if (rendering) return html`<main class="main render-main" ref=${main}>${page}</main>`;
  return html`<div class=${`shell${showSidebar ? "" : " no-sidebar"}${drawer ? " with-drawer" : ""}`}>
    <${TopBar} />
    ${showSidebar ? html`<${Sidebar} />` : null}
    <main class="main" ref=${main}>${page}</main>
    ${drawer ? html`<${Drawer} path=${r.path} run=${r.run} />` : null}
    <${StatusBar} />
    ${query !== null ? html`<${Palette} query=${query} />` : null}
    ${showHelp ? html`<${Help} />` : null}
  </div>`;
}

function onKey(e: KeyboardEvent): void {
  const mod = e.metaKey || e.ctrlKey;
  if (mod && e.key.toLowerCase() === "k") {
    e.preventDefault();
    palette.set(palette.value === null ? "" : null);
    return;
  }
  if (mod && e.key.toLowerCase() === "b") {
    e.preventDefault();
    sidebar.set(!sidebar.value);
    return;
  }
  if (e.key === "Escape") {
    if (palette.value !== null || help.value) return;
    const r = route.value;
    if (r.page === "group" && r.run) return navigate(groupUrl(r.path, { drawer: true }), { replace: true });
    if (r.page === "group" && r.drawer) return navigate(groupUrl(r.path), { replace: true });
    return;
  }
  if (mod || e.altKey || typing(e) || palette.value !== null || help.value) return;
  const r = route.value;
  switch (e.key) {
    case "/":
      e.preventDefault();
      palette.set("");
      break;
    case "?":
      help.set(!help.value);
      break;
    case "p":
      paused.set(!paused.value);
      break;
    case "i":
      if (r.page === "group") navigate(groupUrl(r.path, { drawer: !r.drawer }), { replace: true });
      break;
    case "b":
      sidebar.set(!sidebar.value);
      break;
    case "[":
    case "]":
      if (r.page === "group") void sibling(r.path, e.key === "]" ? 1 : -1);
      break;
  }
}

async function sibling(path: string, step: number): Promise<void> {
  const answer = await fetchCall(calls.tree());
  const list = siblings(buildTree(rows(answer), answer?.meta?.sources ?? []), path);
  const i = list.findIndex((n) => n.path === path);
  const next = list[i + step];
  if (next) navigate(groupUrl(next.path));
}

function Help() {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = dialog.current!;
    d.showModal();
    const closed = () => help.set(false);
    d.addEventListener("close", closed);
    return () => d.removeEventListener("close", closed);
  }, []);
  return html`<dialog class="sheet" ref=${dialog} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${SHORTCUTS.map(([k, d]) => html`<tr><td><kbd>${k}</kbd></td><td>${d}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 14px"><button class="link" autofocus>Close</button></form>
    </div>
  </dialog>`;
}
