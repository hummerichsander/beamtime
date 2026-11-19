// The page's title and favicon: one consistent title everywhere, and the gathered mark on the
// icon while something is live in the current scope, so a background tab stands out.

import { useEffect } from "preact/hooks";

import { useCall } from "../api.ts";
import { rows } from "../blocks/common.ts";
import { isRunId } from "../router.ts";
import { EXPORTED } from "../snapshot.ts";
import * as calls from "./calls.ts";

const PLAIN = "/static/favicon.svg";
const LIVE = "/static/favicon-live.svg";

function setIcon(live: boolean): void {
  // an exported page's icon is a data URI baked in at export time; nothing is ever live in it,
  // and /static/favicon.svg doesn't resolve next to a page opened from disk.
  if (EXPORTED) return;
  const link = document.querySelector("link[rel=icon]");
  if (!(link instanceof HTMLLinkElement)) return;
  const href = live ? LIVE : PLAIN;
  if (link.getAttribute("href") === href) return;
  link.type = "image/svg+xml";
  link.href = href;
}

// sets the title and the live icon for any page; `running` is how many runs are live.
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
