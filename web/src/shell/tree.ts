// The group tree from one `groups` answer: a root per source, nodes with counts, status and children.

import { isRoot, rootOf } from "../router.ts";

export type TreeNode = {
  path: string;
  name: string;
  runs: number;
  running: number;
  failed: number;
  status: string | null;
  children: TreeNode[];
  // a remote's root: whether it answers, and why not.
  state?: string;
  error?: string;
};

export type SourceState = { name: string; state: string; error?: string };

// one root per source: this machine first, then each remote, even one that can't answer now.
export function buildTree(rows: Record<string, any>[], sources: SourceState[] = []): TreeNode[] {
  const nodes = new Map<string, TreeNode>();
  const node = (path: string, r: Record<string, any> = {}): TreeNode => ({
    path,
    name: path === "." ? "local" : path.split("/").pop()!,
    runs: r.runs ?? 0,
    running: r.running ?? 0,
    failed: (r.failed ?? 0) + (r.killed ?? 0) + (r.lost ?? 0),
    status: r.status ?? null,
    children: [],
  });
  for (const r of rows) nodes.set(r.path, node(r.path, r));
  // an empty list means no remotes are configured: local is implicitly the only source.
  const local = sources.length === 0 || sources.some((s) => s.name === "local");
  if (local && !nodes.has(".")) nodes.set(".", node("."));
  for (const s of sources) {
    const path = s.name === "local" ? "." : s.name;
    if (!nodes.has(path)) nodes.set(path, node(path));
    Object.assign(nodes.get(path)!, { state: s.state, error: s.error });
  }
  for (const n of nodes.values()) {
    if (isRoot(n.path)) continue;
    const i = n.path.lastIndexOf("/");
    const up = i < 0 ? "." : n.path.slice(0, i);
    (nodes.get(up) ?? nodes.get(rootOf(n.path)) ?? nodes.get(".")!).children.push(n);
  }
  for (const n of nodes.values()) n.children.sort((a, b) => a.name.localeCompare(b.name));
  const remotes = [...nodes.values()].filter((n) => n.path !== "." && isRoot(n.path)).sort((a, b) => a.name.localeCompare(b.name));
  const root = nodes.get(".");
  return root ? [root, ...remotes] : remotes;
}

// hosts are open unless closed; everything below them, closed unless open. A filter opens all.
export function visible(roots: TreeNode[], open: Set<string>, filter: string, closed: Set<string> = new Set()): TreeNode[] {
  const out: TreeNode[] = [];
  const f = filter.toLowerCase();
  const walk = (n: TreeNode) => {
    const show = !f || n.path.toLowerCase().includes(f) || hasMatch(n, f);
    if (!show) return;
    out.push(n);
    if (f || (isRoot(n.path) ? !closed.has(n.path) : open.has(n.path))) n.children.forEach(walk);
  };
  roots.forEach(walk);
  return out;
}

function hasMatch(n: TreeNode, f: string): boolean {
  return n.children.some((c) => c.path.toLowerCase().includes(f) || hasMatch(c, f));
}

export function siblings(roots: TreeNode[], path: string): TreeNode[] {
  if (isRoot(path)) return roots;
  const i = path.lastIndexOf("/");
  const parentPath = i < 0 ? "." : path.slice(0, i);
  const find = (n: TreeNode): TreeNode | null =>
    n.path === parentPath ? n : n.children.map(find).find((x) => x) ?? null;
  return roots.map(find).find((x) => x)?.children ?? [];
}

// how far a path sits below its source's root.
export function depth(path: string): number {
  if (isRoot(path)) return 0;
  return path.split("/").length - (path.startsWith("@") ? 1 : 0);
}
