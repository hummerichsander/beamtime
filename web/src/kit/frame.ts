// The frame side of a custom block: it receives the block's code and context from the page, runs
// the code on the kit, and reports its height, readiness, errors and layout back.

import { busy, deliver, setRemote } from "../api.ts";
import { theme } from "../bt/index.ts";
import { cssVariables, type Theme } from "../bt/theme.ts";
import { setAway } from "../router.ts";
import { makeKit } from "./index.ts";
import type { Init, ToFrame, ToPage } from "./protocol.ts";

const LIBS: Record<string, () => Promise<unknown>> = {
  d3: () => import("./d3.ts"),
  uplot: () => import("uplot").then((m) => m.default),
  katex: () => import("katex").then((m) => m.default),
};

let started = false;

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
  const root = document.documentElement;
  for (const [k, v] of Object.entries(cssVariables(t))) root.style.setProperty(k, v);
  root.dataset.mode = t.type;
  root.style.colorScheme = t.type;
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
  const view = { path: init.path, colors: new Map(init.colors), names: new Map(init.names), metrics: init.metrics };
  (window as any).bt = makeKit({ queries: init.queries, view, libs, warn: (message) => send({ type: "warn", message }) });
  const url = URL.createObjectURL(new Blob([init.code], { type: "text/javascript" }));
  const mod = await import(/* @vite-ignore */ url);
  URL.revokeObjectURL(url);
  if (typeof mod.default !== "function") throw new Error("the block's code must `export default function render(root)`");
  await mod.default(document.getElementById("root"));
  await settled();
  const root = document.getElementById("root")!;
  const drawn = root.querySelector("canvas, svg, img") !== null || (root.textContent ?? "").trim() !== "";
  send({ type: "ready", blank: !drawn, overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1 });
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
    case "result":
      deliver(msg.id, msg.result);
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
new ResizeObserver(() => send({ type: "height", height: Math.ceil(document.documentElement.scrollHeight) })).observe(document.body);
send({ type: "hello" });
