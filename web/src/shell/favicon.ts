// The page's title and favicon: one consistent title everywhere, and a status dot plus a run
// count on the icon while something is live in the current scope, so a background tab stands out.

import { useEffect } from "preact/hooks";

import { useCall } from "../api.ts";
import { rows } from "../blocks/common.ts";
import { isRunId } from "../router.ts";
import { EXPORTED } from "../snapshot.ts";
import * as calls from "./calls.ts";

const PLAIN = "/static/favicon.svg";
let dotted: string | null = null;

// the plain mark with a small accent dot added, drawn once into a canvas and cached.
async function withDot(): Promise<string> {
  if (dotted) return dotted;
  const img = new Image();
  img.src = PLAIN;
  await img.decode();
  const size = 32;
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext("2d");
  if (!ctx) return PLAIN;
  const accent = getComputedStyle(document.documentElement).getPropertyValue("--accent").trim();
  if (!accent) return PLAIN;
  ctx.drawImage(img, 0, 0, size, size);
  ctx.beginPath();
  ctx.arc(size - 6, size - 6, 6, 0, Math.PI * 2);
  ctx.fillStyle = accent;
  ctx.fill();
  dotted = canvas.toDataURL("image/png");
  return dotted;
}

function setIcon(live: boolean): void {
  // an exported page's icon is a data URI baked in at export time; nothing is ever live in it,
  // and /static/favicon.svg doesn't resolve next to a page opened from disk.
  if (EXPORTED) return;
  const link = document.querySelector("link[rel=icon]");
  if (!(link instanceof HTMLLinkElement)) return;
  if (!live) {
    link.type = "image/svg+xml";
    link.href = PLAIN;
    return;
  }
  void withDot().then((href) => {
    link.type = "image/png";
    link.href = href;
  });
}

// sets the title and the icon's dot for any page; `running` is how many runs are live.
export function useTitle(label: string, running = 0): void {
  useEffect(() => {
    document.title = `${running ? `(${running}) ` : ""}${label} · Beamtime`;
    setIcon(running > 0);
  }, [label, running]);
}

// the title of a group or run page: its name, and how many runs are live (a run counts as
// one of its own); a remote or unreachable page still gets a title from its path alone.
export function usePageTitle(path: string): void {
  const runId = isRunId(path.split("/").pop() ?? "");
  const group = useCall(runId ? null : calls.group(path));
  const card = useCall(runId ? calls.card(path.split("/").pop() ?? "", path) : null);
  const label = runId
    ? card.data?.run.name ?? card.data?.run.id ?? path
    : path === "." ? "local" : path.split("/").pop() ?? path;
  const running = runId ? (card.data?.run.status === "running" ? 1 : 0) : (rows(group.data)[0]?.running ?? 0);
  useTitle(label, running);
}
