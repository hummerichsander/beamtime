// The calls the shell makes, in one place so pages and prefetching share cache entries.

import { type Call, fetchCall, prefetch } from "../api.ts";
import type { Node } from "../bt/index.ts";
import { prefsOf, type Pin } from "../bt/prefs.ts";
import { sourcedRun } from "../router.ts";

// the group tree covers every source; pages of this machine show only this machine.
export const tree = (): Call => ({ method: "groups", params: { from: ".", everywhere: true }, scope: "." });
// the viewer's pins go along only when set, so a remote that doesn't know them answers as before.
export const view = (path: string, version: string | null = null, draft: string | null = null, metrics: Pin[] | null = null): Call => ({
  method: "view",
  params: { path, ...(version ? { version } : {}), ...(draft ? { draft } : {}), ...(metrics ? { metrics } : {}) },
  scope: path,
});
export const summary = (path: string, metrics: Pin[] | null = null): Call => ({
  method: "summary",
  params: { path, ...(metrics ? { metrics } : {}) },
  scope: path,
});
export const group = (path: string): Call => ({ method: "groups", params: { from: path, depth: 0 }, scope: path });
export const check = (path: string): Call => ({ method: "check", params: { group: path }, scope: path });
export const proposal = (path: string): Call => ({ method: "proposal_show", params: { group: path }, scope: path });
export const card = (run: string, scope: string): Call => ({ method: "card", params: { run: sourcedRun(run, scope) }, scope });
export const output = (run: string, scope: string): Call => ({ method: "output", params: { run: sourcedRun(run, scope), tail: 30 }, scope });
export const diff = (run: string, scope: string): Call => ({ method: "run_diff", params: { run: sourcedRun(run, scope) }, scope });
export const runIds = (path: string): Call => ({
  method: "runs",
  params: { from: path, select: ["run.name", "run.status"], limit: 10000 },
  scope: path,
});
export const notes = (path: string): Call => ({ method: "notes", params: { from: path, limit: 20, full: true, current: true }, scope: path });
export const timeline = (path: string): Call => ({ method: "timeline", params: { from: path, limit: 30 }, scope: path });
export const status = (): Call => ({ method: "status", params: {}, scope: "." });
export const allRuns = (): Call => ({
  method: "runs",
  params: { from: ".", select: ["run.name", "run.path", "run.status", "run.ended_at"], sort: ["-run.created_at"], limit: 5000 },
  scope: ".",
});

// what a group page asks for, fetched while the pointer rests on a link to it: the page's own calls,
// then, once its view is in, its blocks' calls (charts size theirs to the page, so not those).
export function prefetchGroup(path: string): void {
  const main = prefsOf(path).value.main;
  for (const call of [view(path, null, null, main), group(path), runIds(path), summary(path, main)]) prefetch(call);
  fetchCall<{ view?: Node }>(view(path, null, null, main))
    .then((answer) => {
      for (const call of blockCalls(answer.view)) prefetch(call);
    })
    .catch(() => {});
}

function blockCalls(node: Node | undefined): Call[] {
  if (!node) return [];
  const own = SIZED.has(node.block) ? [] : Object.values(node.data ?? {});
  return [...own, ...(node.children ?? []).flatMap(blockCalls)];
}

// blocks whose calls depend on their width or run in a frame, so a prefetch would miss.
const SIZED = new Set(["line", "custom"]);
export const history = (path: string): Call => ({ method: "view_history", params: { group: path }, scope: path });
