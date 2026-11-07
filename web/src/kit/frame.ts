// The frame side of a custom block: it receives the block's code and context from the page, runs
// the code on the kit, and reports its height, readiness, errors and layout back. What the sandbox
// can't do (save files, draw PDFs, open the page's dialog) it asks the page for; the hovered run
// and the chart settings are shared with the page both ways.

import { busy, deliver, setRemote } from "../api.ts";
import { setHost } from "../bt/host.ts";
import { hovered, pair, theme, type ViewContext } from "../bt/index.ts";
import { prefsOf, type ViewPrefs } from "../bt/prefs.ts";
import { colormaps, paint, type Theme } from "../bt/theme.ts";
import { setAway } from "../router.ts";
import { EXPORTED } from "../snapshot.ts";
import { Store } from "../state.ts";
import { installTips } from "../ui/tip.ts";
import { makeKit } from "./index.ts";
import type { Init, ToFrame, ToPage } from "./protocol.ts";
import { svgOf } from "./snapshot.ts";

const LIBS: Record<string, () => Promise<unknown>> = {
  d3: () => import("./d3.ts"),
  uplot: () => import("uplot").then((m) => m.default),
  katex: () => import("katex").then((m) => m.default),
};

let started = false;
// the page's run names, colors and metrics; updated when the page's change.
const view = new Store<ViewContext>({ path: ".", colors: new Map(), names: new Map(), metrics: {}, charted: new Map(), pins: [] });

function send(msg: ToPage): void {
  parent.postMessage(msg, "*");
}

// the message and the stack lines in the block's own code (a blob:), not the kit's internals.
function fail(e: unknown): void {
  const err = e instanceof Error ? e : new Error(String(e));
  const own = (err.stack ?? "").split("\n").filter((line) => line.includes("blob:"));
  send({ type: "error", message: [String(err), ...own].join("\n") });
}

// the page sends its theme once it has one; blocks draw only after that.
let themed: () => void;
const hasTheme = new Promise<void>((resolve) => (themed = resolve));

function applyTheme(t: Theme): void {
  paint(t);
  theme.set(t);
  themed();
}

async function start(init: Init): Promise<void> {
  if (init.theme) applyTheme(init.theme);
  await hasTheme;
  const libs: Record<string, unknown> = {};
  for (const name of init.libs) {
    const load = LIBS[name];
    if (!load) throw new Error(`no library '${name}'; the kit offers ${Object.keys(LIBS).join(", ")}`);
    libs[name] = await load();
  }
  view.set({ path: init.path, colors: new Map(init.colors), names: new Map(init.names), metrics: init.metrics, charted: new Map(), pins: [] });
  if (init.pair) pair.set(init.pair);
  // the page may have sent them already, while the libraries loaded.
  if (init.colormaps) colormaps.set(init.colormaps);
  name = init.id;
  share(init.path, init.prefs);
  (window as any).bt = makeKit({
    queries: init.queries,
    params: init.params,
    view,
    libs,
    warn: (message) => send({ type: "warn", message }),
    own: () => send({ type: "chrome", own: true }),
  });
  const render = await load(init.code);
  if (typeof render !== "function") throw new Error("the block's code must `export default function render(root)`");
  await render(document.getElementById("root"));
  await settled();
  const root = document.getElementById("root")!;
  const drawn = root.querySelector("canvas, svg, img") !== null || (root.textContent ?? "").trim() !== "";
  send({ type: "ready", blank: !drawn, overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1 });
}

// the block's default export. An exported page opens from disk, where browsers load no modules,
// so there the code runs as a function body with its default export assigned instead.
async function load(code: string): Promise<unknown> {
  if (EXPORTED) {
    const holder: { render?: unknown } = {};
    new Function("__bt", code.replace(/\bexport\s+default\s+/, "__bt.render = "))(holder);
    return holder.render;
  }
  const url = URL.createObjectURL(new Blob([code], { type: "text/javascript" }));
  try {
    return (await import(/* @vite-ignore */ url)).default;
  } finally {
    URL.revokeObjectURL(url);
  }
}

// no call or chart build pending for a few checks in a row.
async function settled(): Promise<void> {
  let quiet = 0;
  while (quiet < 3) {
    await new Promise((r) => setTimeout(r, 50));
    quiet = busy.n === 0 ? quiet + 1 : 0;
  }
}

setRemote({
  subscribe: (id, call) => send({ type: "sub", id, call }),
  unsubscribe: (id) => send({ type: "unsub", id }),
});
setAway((url) => send({ type: "navigate", url }));

addEventListener("message", (e: MessageEvent<ToFrame>) => {
  if (e.source !== parent) return;
  const msg = e.data;
  switch (msg.type) {
    // the page asks again when it starts listening, in case the first hello came too early.
    case "ping":
      if (!started) send({ type: "hello" });
      break;
    case "init":
      if (started) break;
      started = true;
      start(msg.init).catch(fail);
      break;
    case "theme":
      applyTheme(msg.theme);
      break;
    case "colormaps":
      colormaps.set(msg.colormaps);
      break;
    case "context":
      view.set({ ...view.value, names: new Map(msg.names), colors: new Map(msg.colors), metrics: msg.metrics });
      break;
    case "result":
      deliver(msg.id, msg.result);
      break;
    case "hover":
      quiet(() => hovered.set(msg.run));
      break;
    case "prefs":
      if (shared && JSON.stringify(shared.value) !== JSON.stringify(msg.prefs)) quiet(() => shared!.set(msg.prefs));
      break;
    case "snapshot":
      send({ type: "snapshot", ...snapshot() });
      break;
    default:
      break;
  }
});
addEventListener("error", (e) => {
  // the browser's note that a resize was handled a frame later; harmless, not the block's error.
  if (/ResizeObserver loop/.test(e.message)) return;
  fail(e.error ?? e.message);
});
addEventListener("unhandledrejection", (e) => fail(e.reason));
// links open in the page, never inside the frame.
document.addEventListener("click", (e) => {
  const a = (e.target as Element | null)?.closest?.("a[href]");
  const href = a?.getAttribute("href");
  if (!href || !href.startsWith("/")) return;
  e.preventDefault();
  send({ type: "navigate", url: href });
});
// the height the page gives the frame; open popovers (top layer) count too, or they'd be cut off.
function height(): number {
  const open = [...document.querySelectorAll<HTMLElement>("[popover]")].filter((e) => e.matches(":popover-open"));
  return Math.ceil(Math.max(document.documentElement.scrollHeight, ...open.map((e) => e.getBoundingClientRect().bottom + 8)));
}

// a change that came from the page isn't sent back to it.
let fromPage = false;
function quiet(change: () => void): void {
  fromPage = true;
  try {
    change();
  } finally {
    fromPage = false;
  }
}

let name = "block";
let shared: Store<ViewPrefs> | null = null;

// the page's chart settings for the view: in at the start and on change, the frame's own out.
function share(path: string, prefs: ViewPrefs): void {
  shared = prefsOf(path);
  quiet(() => shared!.set({ ...shared!.value, ...prefs }));
  shared.subscribe((v) => !fromPage && send({ type: "prefs", prefs: v }));
}

// what the block draws as a file: its SVG with the theme's colors written in, else its canvas.
function snapshot(): { href: string | null; name: string } {
  const root = document.getElementById("root")!;
  const svg = svgOf(root);
  if (svg) return { href: svg, name: `${name}.svg` };
  const canvas = root.querySelector("canvas");
  return { href: canvas ? canvas.toDataURL("image/png") : null, name: `${name}.png` };
}

setHost({
  download: (href, file) => send({ type: "download", href, name: file }),
  figure: async (spec, file) => send({ type: "figure", spec, name: file }),
  expand: (node) => send({ type: "expand", node }),
});
hovered.subscribe((run) => !fromPage && send({ type: "hover", run }));
installTips();
const report = () => send({ type: "height", height: height() });
new ResizeObserver(report).observe(document.body);
document.addEventListener("toggle", () => requestAnimationFrame(report), true);
send({ type: "hello" });
