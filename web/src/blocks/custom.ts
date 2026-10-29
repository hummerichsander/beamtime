// `custom`: an agent-written block in a sandboxed frame. The page fetches its code and answers its
// calls over the bridge; a block that fails is replaced by an error panel, the rest of the view stays.

import { html } from "htm/preact";
import { useContext, useEffect, useState } from "preact/hooks";

import { busy, useCall, watch, type Call } from "../api.ts";
import { theme as currentTheme, useTheme, useVisible, ViewCtx, type Node } from "../bt/index.ts";
import { READS, ResizeGuard, type ToFrame, type ToPage } from "../kit/protocol.ts";
import { navigate, rendering } from "../router.ts";
import { Notice, Panel } from "./common.ts";

const TIMEOUT = 15_000;

export function Custom({ node }: { node: Node }) {
  const view = useContext(ViewCtx);
  const theme = useTheme();
  const [box, visible] = useVisible();
  const ref = node.props.code;
  const code = useCall(visible && ref ? { method: "code", params: ref, scope: view.path } : null);
  // the element in state, so the bridge is set up once per frame; new code gets a new frame.
  const [frame, setFrame] = useState<HTMLIFrameElement | null>(null);
  const [height, setHeight] = useState(120);
  const [state, setState] = useState<{ error: string | null; warnings: string[]; blank?: boolean; overflow?: boolean }>({ error: null, warnings: [] });
  const fail = (message: string) => {
    if (rendering) console.error(`[block ${node.id}] ${message}`);
    setState((s) => ({ ...s, error: message }));
  };

  useEffect(() => {
    const win = frame?.contentWindow;
    if (!win || code.status !== "ready") return;
    const post = (msg: ToFrame) => win.postMessage(msg, "*");
    const subs = new Map<string, () => void>();
    const guard = new ResizeGuard();
    // the renderer waits for the frame's first render, an error or the time limit.
    let waiting = true;
    busy.n++;
    const done = () => {
      if (waiting) busy.n--;
      waiting = false;
    };
    const timer = setTimeout(() => {
      if (waiting) fail(`no first render within ${TIMEOUT / 1000} s`);
      done();
    }, TIMEOUT);
    const onMessage = (e: MessageEvent<ToPage>) => {
      if (e.source !== win) return;
      const msg = e.data;
      switch (msg.type) {
        case "hello":
          post({ type: "init", init: {
            id: node.id, code: code.data.code, libs: node.props.libs ?? [], path: view.path, queries: (node.data ?? {}) as Record<string, Call>,
            theme: currentTheme.value, names: [...view.names], colors: [...view.colors], metrics: view.metrics,
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
          done();
          break;
        case "warn":
          warn(msg.message);
          break;
        case "error":
          fail(msg.message);
          done();
          break;
        default:
          break;
      }
    };
    const warn = (message: string) => {
      if (rendering) console.warn(`[block ${node.id}] ${message}`);
      setState((s) => (s.warnings.includes(message) ? s : { ...s, warnings: [...s.warnings, message] }));
    };
    addEventListener("message", onMessage);
    post({ type: "ping" });
    return () => {
      removeEventListener("message", onMessage);
      clearTimeout(timer);
      for (const unsub of subs.values()) unsub();
      done();
    };
  }, [code.status, code.data, frame]);

  // the frame follows the page's theme.
  useEffect(() => {
    if (theme) frame?.contentWindow?.postMessage({ type: "theme", theme } satisfies ToFrame, "*");
  }, [theme]);

  const where = typeof ref === "object" ? ref.path ?? ref.block : String(ref ?? "");
  return html`<div ref=${box}>
    <${Panel} title=${node.props.title} caption=${node.props.caption} result=${code}>
      ${state.error
        ? html`<div class="notice error custom-error">
            <b>Custom block ${node.id} failed</b> <span class="muted">(${where})</span>
            <pre>${state.error}</pre>
          </div>`
        : null}
      ${state.warnings.map((w) => html`<${Notice} kind="warning">${w}<//>`)}
      ${visible && code.status === "ready" && !state.error
        ? html`<div class="custom-frame" data-frame-blank=${state.blank ? "1" : undefined} data-frame-overflow=${state.overflow ? "1" : undefined}>
            <iframe key=${code.data.code} ref=${setFrame} src="/static/kit/frame.html" sandbox="allow-scripts" title=${node.props.title ?? `Custom block ${node.id}`}
              style=${`height:${height}px`} />
          </div>`
        : null}
    <//>
  </div>`;
}
