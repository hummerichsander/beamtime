// A run's nested config as a tree for reading: single-child chains joined (a.b.c), what varies marked,
// and a filter that keeps the matching branches.

export type ConfigNode = {
  name: string;
  // the dotted key as the server writes it (config.<path>), so it matches `keys` and `summary`.
  path: string;
  value?: unknown;
  children: ConfigNode[];
  varies: boolean;
};

// leaves: scalars, arrays and empty objects; only non-empty objects branch.
const branches = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v) && Object.keys(v).length > 0;

export function configTree(config: Record<string, unknown>, varying: ReadonlySet<string> = new Set()): ConfigNode[] {
  const build = (obj: Record<string, unknown>, prefix: string): ConfigNode[] =>
    Object.entries(obj).map(([name, v]) => {
      const path = `${prefix}${name.includes(".") ? `["${name}"]` : prefix ? `.${name}` : name}`;
      if (!branches(v)) return { name, path, value: v, children: [], varies: varying.has(path) };
      const children = build(v, path);
      return { name, path, children, varies: children.some((c) => c.varies) };
    });
  return build(config, "").map(collapse);
}

// a node whose only child is a node of its own reads as one: a.b.c.
function collapse(node: ConfigNode): ConfigNode {
  let n = node;
  while (n.children.length === 1) {
    const [child] = n.children;
    n = { ...child, name: `${n.name}.${child.name}` };
  }
  return { ...n, children: n.children.map(collapse) };
}

export function leaves(nodes: ConfigNode[]): number {
  return nodes.reduce((n, x) => n + (x.children.length ? leaves(x.children) : 1), 0);
}

// the branches that hold a leaf whose key or value contains the text (any case), and, with `only`,
// varies between runs.
export function filterTree(nodes: ConfigNode[], text: string, only: boolean): ConfigNode[] {
  const q = text.trim().toLowerCase();
  const out: ConfigNode[] = [];
  for (const n of nodes) {
    if (n.children.length) {
      const children = filterTree(n.children, q, only);
      if (children.length) out.push({ ...n, children });
      continue;
    }
    const hit = !q || n.path.toLowerCase().includes(q) || JSON.stringify(n.value)?.toLowerCase().includes(q);
    if (hit && (!only || n.varies)) out.push(n);
  }
  return out;
}

// the config keys that differ between runs, from a `keys` answer ([key, runs, values] rows).
export function varyingKeys(keys: { config?: { rows: [string, number, unknown][] } } | null | undefined): string[] {
  return (keys?.config?.rows ?? []).filter(([, , v]) => !Array.isArray(v) || v.length > 1).map(([k]) => k.replace(/^config\./, ""));
}
