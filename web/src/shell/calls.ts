// The calls the shell makes, in one place so pages and prefetching share cache entries.

import { type Call, prefetch } from "../api.ts";

export const tree = (): Call => ({ method: "groups", params: { from: "." }, scope: "." });
export const view = (path: string): Call => ({ method: "view", params: { path }, scope: path });
export const summary = (path: string): Call => ({ method: "summary", params: { path }, scope: path });
export const group = (path: string): Call => ({ method: "groups", params: { from: path, depth: 0 }, scope: path });
export const check = (path: string): Call => ({ method: "check", params: { group: path }, scope: path });
export const proposal = (path: string): Call => ({ method: "proposal_show", params: { group: path }, scope: path });
export const card = (run: string, scope: string): Call => ({ method: "card", params: { run }, scope });
export const output = (run: string, scope: string): Call => ({ method: "output", params: { run, tail: 30 }, scope });
export const runIds = (path: string): Call => ({
  method: "runs",
  params: { from: path, select: ["run.status"], limit: 10000 },
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

// what a group page asks for first, fetched while the pointer rests on a link to it.
export function prefetchGroup(path: string): void {
  for (const call of [view(path), group(path), runIds(path), summary(path)]) prefetch(call);
}
