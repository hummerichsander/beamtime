// Rendered Markdown, with the renderer loaded on first use and an optional "more" for long texts.

import { html } from "htm/preact";
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";

let renderer: Promise<typeof import("../bt/md.ts")> | null = null;

export function Markdown(props: { text: string; clamp?: number; class?: string }) {
  const el = useRef<HTMLDivElement>(null);
  const [out, setOut] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [long, setLong] = useState(false);
  useEffect(() => {
    let live = true;
    renderer ??= import("../bt/md.ts");
    void renderer
      .then((m) => m.render(props.text ?? ""))
      .then((rendered) => live && setOut(rendered));
    return () => {
      live = false;
    };
  }, [props.text]);
  useLayoutEffect(() => {
    const node = el.current;
    if (!node || !props.clamp) return;
    const check = () => setLong(node.scrollHeight > node.clientHeight + 2);
    const ro = new ResizeObserver(check);
    ro.observe(node);
    return () => ro.disconnect();
  }, [props.clamp, out]);
  const clamped = props.clamp && !open;
  const cls = `md${clamped ? " clamped" : ""}`;
  const style = clamped ? `--clamp:${props.clamp}` : "";
  // the renderer escapes raw HTML and keeps only safe link targets (bt/md.ts).
  return html`<div class=${`md-wrap ${props.class ?? ""}`}>
    ${out === null
      ? html`<div class=${cls} ref=${el} style=${style}>
          ${(props.text ?? "").split(/\n{2,}/).map((p) => html`<p>${p}</p>`)}
        </div>`
      : html`<div class=${cls} ref=${el} style=${style} dangerouslySetInnerHTML=${{ __html: out }}></div>`}
    ${props.clamp && (long || open)
      ? html`<button type="button" class="link small more" onClick=${() => setOpen(!open)}>${open ? "less" : "more"}</button>`
      : null}
  </div>`;
}
