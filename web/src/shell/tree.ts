// The group tree from one `groups` answer: nodes with counts, status and children.

export type TreeNode = {
  path: string;
  name: string;
  runs: number;
  running: number;
  failed: number;
  status: string | null;
  children: TreeNode[];
};

export function buildTree(rows: Record<string, any>[]): TreeNode {
  const nodes = new Map<string, TreeNode>();
  for (const r of rows) {
    nodes.set(r.path, {
      path: r.path,
      name: r.path === "." ? "local" : r.path.split("/").pop(),
      runs: r.runs ?? 0,
      running: r.running ?? 0,
      failed: (r.failed ?? 0) + (r.killed ?? 0) + (r.lost ?? 0),
      status: r.status ?? null,
      children: [],
    });
  }
  const root = nodes.get(".") ?? { path: ".", name: "local", runs: 0, running: 0, failed: 0, status: null, children: [] };
  for (const node of nodes.values()) {
    if (node.path === ".") continue;
    const i = node.path.lastIndexOf("/");
    const parent = nodes.get(i < 0 ? "." : node.path.slice(0, i)) ?? root;
    parent.children.push(node);
  }
  for (const node of nodes.values()) node.children.sort((a, b) => a.name.localeCompare(b.name));
  return root;
}

export function visible(root: TreeNode, open: Set<string>, filter: string): TreeNode[] {
  const out: TreeNode[] = [];
  const f = filter.toLowerCase();
  const walk = (n: TreeNode) => {
    const show = !f || n.path.toLowerCase().includes(f) || hasMatch(n, f);
    if (!show) return;
    out.push(n);
    if (f || open.has(n.path) || n.path === ".") n.children.forEach(walk);
  };
  walk(root);
  return out;
}

function hasMatch(n: TreeNode, f: string): boolean {
  return n.children.some((c) => c.path.toLowerCase().includes(f) || hasMatch(c, f));
}

export function siblings(root: TreeNode, path: string): TreeNode[] {
  const i = path.lastIndexOf("/");
  const parentPath = path === "." ? null : i < 0 ? "." : path.slice(0, i);
  if (parentPath === null) return [root];
  const find = (n: TreeNode): TreeNode | null =>
    n.path === parentPath ? n : n.children.map(find).find((x) => x) ?? null;
  return find(root)?.children ?? [];
}

export function depth(path: string): number {
  return path === "." ? 0 : path.split("/").length;
}
