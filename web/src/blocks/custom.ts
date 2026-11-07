// `custom`: an agent-written block in a sandboxed frame. The page fetches its code and answers its
// calls over the bridge; a block that fails is replaced by an error panel, the rest of the view stays.

import { html } from "htm/preact";
import { useContext, useEffect, useRef, useState } from "preact/hooks";

import { busy, useCall, watch, type Call } from "../api.ts";
import { register } from "../bt/figures.ts";
import { expanded, host } from "../bt/host.ts";
import { theme as currentTheme, hovered, pair, useTheme, useVisible, ViewCtx, type Node } from "../bt/index.ts";
import { prefsOf } from "../bt/prefs.ts";
import { colormaps } from "../bt/theme.ts";
import { expandable, READS, ResizeGuard, savable, type ToFrame, type ToPage } from "../kit/protocol.ts";
import { IconButton } from "../ui/primitives.ts";
import { navigate, rendering } from "../router.ts";
import { EXPORTED, staticUrl } from "../snapshot.ts";
import { Notice, Panel } from "./common.ts";

const TIMEOUT = 15_000;

export function Custom({ node }: { node: Node }) {
  const view = useContext(ViewCtx);
  const theme = useTheme();
  const [box, visible] = useVisible();
  const ref = node.props.code;
  const code = useCall(visible && ref ? { method: "code", params: ref, scope: null } : null);
  // the element in state, so the bridge is set up once per frame; new code gets a new frame.
  const [frame, setFrame] = useState<HTMLIFrameElement | null>(null);
  const [height, setHeight] = useState(120);
  const [state, setState] = useState<{ error: string | null; warnings: string[]; blank?: boolean; overflow?: boolean }>({ error: null, warnings: [] });
  const fail = (message: string) => {
    if (rendering) console.error(`[block ${node.id}] ${message}`);
    setState((s) => ({ ...s, error: message }));
  };

  // the renderer waits for each frame's first render, an error or the time limit, once per frame.
  const firstDone = useRef<() => void>(() => {});
  useEffect(() => {
    if (!frame) return;
    let waiting = true;
    busy.n++;
    const done = () => {
      if (waiting) busy.n--;
      waiting = false;
    };
    firstDone.current = done;
    const timer = setTimeout(() => {
      if (waiting) fail(`no first render within ${TIMEOUT / 1000} s`);
      done();
    }, TIMEOUT);
    return () => {
      clearTimeout(timer);
      done();
    };
  }, [frame]);

  useEffect(() => {
    const win = frame?.contentWindow;
    if (!win || code.status !== "ready") return;
    const post = (msg: ToFrame) => win.postMessage(msg, "*");
    const subs = new Map<string, () => void>();
    const guard = new ResizeGuard();
    const onMessage = (e: MessageEvent<ToPage>) => {
      if (e.source !== win) return;
      const msg = e.data;
      switch (msg.type) {
        case "hello":
          post({ type: "init", init: {
            id: node.id, code: code.data.code, libs: node.props.libs ?? [], path: view.path, queries: (node.data ?? {}) as Record<string, Call>, params: node.props.params ?? {},
            theme: currentTheme.value, pair: pair.value, colormaps: colormaps.value, prefs: prefsOf(view.path).value, names: [...view.names], colors: [...view.colors], metrics: view.metrics,
          } });  // prettier-ignore
          break;
        case "sub":
          if (!READS.has(msg.call.method)) {
            post({ type: "result", id: msg.id, result: { status: "error", data: null, error: `${msg.call.method} is not available in a custom block`, refreshing: false } });
            break;
          }
          subs.get(msg.id)?.();
          subs.set(msg.id, watch(msg.call, (result) => post({ type: "result", id: msg.id, result })));
          break;
        case "unsub":
          subs.get(msg.id)?.();
          subs.delete(msg.id);
          break;
        case "navigate":
          if (msg.url.startsWith("/")) navigate(msg.url);
          break;
        case "height":
          if (guard.accept(performance.now())) setHeight(Math.max(40, msg.height));
          else warn("its height keeps changing, so it is fixed at its last height");
          break;
        case "ready":
          setState((s) => ({ ...s, blank: msg.blank, overflow: msg.overflow }));
          firstDone.current();
          break;
        case "warn":
          warn(msg.message);
          break;
        case "hover":
          hovered.set(msg.run);
          break;
        case "prefs":
          if (JSON.stringify(prefs.value) !== JSON.stringify(msg.prefs)) prefs.set(msg.prefs);
          break;
        case "download":
        case "snapshot":
          if (!msg.href) warn("it draws no SVG or canvas to download");
          else if (!savable(msg.href, msg.name)) warn(`a download of ${msg.name} was refused: only PNG, SVG and CSV files`);
          // a block can't flood the page with files: one a second.
          else if (performance.now() - lastSave > 1000) {
            lastSave = performance.now();
            host().download(msg.href, msg.name);
          }
          break;
        case "figure":
          host().figure(msg.spec, msg.name).catch((err: Error) => warn(`the PDF failed: ${err.message}`));
          break;
        case "expand":
          if (expandable(msg.node)) host().expand(msg.node, view);
          break;
        case "error":
          // stack lines name the block's file instead of the blob it was loaded from.
          fail(msg.message.replace(/blob:[^\s)]*?\/[\w-]+(?=:\d)/g, where));
          firstDone.current();
          break;
        default:
          break;
      }
    };
    const warn = (message: string) => {
      if (rendering) console.warn(`[block ${node.id}] ${message}`);
      setState((s) => (s.warnings.includes(message) ? s : { ...s, warnings: [...s.warnings, message] }));
    };
    // the first download always passes, however soon after the page loaded.
    let lastSave = -Infinity;
    const prefs = prefsOf(view.path);
    const unhover = hovered.subscribe((run) => post({ type: "hover", run }));
    const unprefs = prefs.subscribe((v) => post({ type: "prefs", prefs: v }));
    addEventListener("message", onMessage);
    post({ type: "ping" });
    return () => {
      unhover();
      unprefs();
      removeEventListener("message", onMessage);
      for (const unsub of subs.values()) unsub();
    };
  }, [code.status, code.data?.code, frame]);

  // the frame follows the page's run names, colors and metrics as they change.
  useEffect(() => {
    const msg: ToFrame = { type: "context", names: [...view.names], colors: [...view.colors], metrics: view.metrics };
    frame?.contentWindow?.postMessage(msg, "*");
  }, [view.names, view.colors, view.metrics, frame]);

  // the frame follows the page's theme.
  useEffect(() => {
    if (theme) frame?.contentWindow?.postMessage({ type: "theme", theme } satisfies ToFrame, "*");
  }, [theme]);

  const where = typeof ref === "object" ? ref.path ?? ref.block : String(ref ?? "");
  register(node.id, { png: () => frame?.contentWindow?.postMessage({ type: "snapshot" } satisfies ToFrame, "*") });
  const ready = visible && code.status === "ready" && !state.error;
  return html`<div ref=${box} class="custom-block">
    <div class="chart-head">
      <b class="chart-title">${node.props.title ?? ""}</b>
      ${ready
        ? html`<span class="chart-tools">
            <${IconButton} icon="download" label="Download what it draws (SVG or PNG)"
              onClick=${() => frame?.contentWindow?.postMessage({ type: "snapshot" } satisfies ToFrame, "*")} />
            ${node.props.expanded
              ? html`<${IconButton} icon="x" label="Close (Esc)" onClick=${() => expanded.set(null)} />`
              : html`<${IconButton} icon="maximize" label="Expand" onClick=${() => host().expand(node, view)} />`}
          </span>`
        : null}
    </div>
    <${Panel} caption=${node.props.expanded ? undefined : node.props.caption} result=${code}>
      ${state.error
        ? html`<div class="notice body error custom-error">
            <b>Custom block ${node.id} failed</b> <span class="muted">(${where})</span>
            <pre class="code">${state.error}</pre>
          </div>`
        : null}
      ${state.warnings.map((w) => html`<${Notice} kind="warning">${w}<//>`)}
      ${ready
        ? html`<div class="custom-frame" data-frame-blank=${state.blank ? "1" : undefined} data-frame-overflow=${state.overflow ? "1" : undefined}>
            <iframe key=${code.data.code} ref=${setFrame} sandbox="allow-scripts" ...${frameSource()} title=${node.props.title ?? `Custom block ${node.id}`}
              style=${`height:${height}px`} />
          </div>`
        : null}
    <//>
  </div>`;
}

// the frame's page: served, or for an exported page written inline with the kit's script and the
// styles, since a sandboxed frame of a page opened from disk may load no files.
function frameSource(): Record<string, string> {
  if (!EXPORTED) return { src: staticUrl("kit/frame.html") };
  const inline: { kit: string; css: string } = (globalThis as any).__BT_FRAME__ ?? { kit: "", css: "" };
  // no fonts: a sandboxed frame of a page opened from disk may load no files.
  const css = inline.css.replace(/<\/(style)/gi, "<\\/$1").replace(/@font-face\s*\{[^}]*\}/g, "");
  const kit = inline.kit.replace(/<\/(script)/gi, "<\\/$1");
  const srcdoc = `<!doctype html><html lang="en"><head><meta charset="utf-8"><style>${css}</style></head>`
    + `<body class="kit-frame body"><div id="root"></div><script>${kit}</script></body></html>`;
  return { srcdoc };
}
