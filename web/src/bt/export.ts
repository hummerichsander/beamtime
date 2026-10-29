// Figures leave the UI in the light theme, whatever the viewer uses: PNG on a transparent or a
// white background, drawn offscreen, and PDF drawn by the server with matplotlib.

import { pair } from "./index.ts";
import type { Theme } from "./theme.ts";

export type Background = "transparent" | "white";

// the light theme, which every exported figure uses.
export function light(): Theme | null {
  return pair.value?.light ?? null;
}

// a color of one theme's categorical palette as the same slot of another's.
export function recolor(color: string, from: Theme, to: Theme): string {
  const i = from.data.categorical.indexOf(color);
  return i < 0 ? color : to.data.categorical[i % to.data.categorical.length];
}

// draws a chart offscreen at the given width, takes its PNG and removes it again.
export async function offscreen(
  width: number,
  draw: (el: HTMLElement) => Promise<{ png(background: string | null): string; destroy(): void }>,
  background: Background,
): Promise<string> {
  const el = document.createElement("div");
  el.style.cssText = `position:fixed;left:-10000px;top:0;width:${Math.max(320, width)}px`;
  document.body.append(el);
  try {
    const chart = await draw(el);
    // wait a frame, so the canvas has been painted.
    await new Promise((r) => requestAnimationFrame(r));
    const href = chart.png(background === "white" ? "#ffffff" : null);
    chart.destroy();
    return href;
  } finally {
    el.remove();
  }
}

export function save(href: string, name: string): void {
  const a = document.createElement("a");
  a.href = href;
  a.download = name;
  a.click();
}

export function fileName(title: string, ext: string): string {
  return `${title.replace(/[^\w.-]+/g, "_").replace(/^_+|_+$/g, "") || "chart"}.${ext}`;
}

// the server draws the figure with matplotlib (vector PDF); the figures extra provides it.
export async function pdf(spec: Record<string, unknown>, name: string): Promise<void> {
  const r = await fetch("/api/figure", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(spec),
    credentials: "same-origin",
  });
  if (!r.ok) {
    const body = await r.json().catch(() => ({ error: `HTTP ${r.status}` }));
    throw new Error(body.error ?? `HTTP ${r.status}`);
  }
  const url = URL.createObjectURL(await r.blob());
  save(url, name);
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
}
