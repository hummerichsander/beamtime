// The sidebar: the group tree with run counts and status marks, filterable and keyboard-driven.

import { html } from "htm/preact";
import { useEffect, useRef, useState } from "preact/hooks";

import { useCall } from "../api.ts";
import { rows } from "../blocks/common.ts";
import { groupUrl, isRoot, navigate, rootOf, route } from "../router.ts";
import { stored, store, useStore } from "../state.ts";
import { Icon, Sym } from "../ui/icons.ts";
import { symbolFor } from "../ui/symbols.ts";
import * as calls from "./calls.ts";
import { buildTree, depth, visible, type TreeNode } from "./tree.ts";

export function Sidebar() {
  const r = useStore(route);
  const result = useCall(calls.tree());
  const [open, setOpen] = useState<Set<string>>(() => new Set(stored<string[]>("open", [])));
  // hosts start open, so the ones a viewer closed are what is kept.
  const [closed, setClosed] = useState<Set<string>>(() => new Set(stored<string[]>("closed-hosts", [])));
  const [filter, setFilter] = useState("");
  const list = useRef<HTMLDivElement>(null);
  const current = r.page === "group" ? r.path : null;
  const roots = buildTree(rows(result.data), result.data?.meta?.sources ?? []);
  const shown = visible(roots, withAncestors(open, current), filter, closed);
  const isOpen = (path: string) => (isRoot(path) ? !closed.has(path) : open.has(path));

  const toggle = (path: string, value?: boolean) => {
    const wanted = value ?? !isOpen(path);
    if (isRoot(path)) {
      const next = new Set(closed);
      if (wanted) next.delete(path);
      else next.add(path);
      store("closed-hosts", [...next]);
      setClosed(next);
      return;
    }
    const next = new Set(open);
    if (wanted) next.add(path);
    else next.delete(path);
    store("open", [...next]);
    setOpen(next);
  };

  // going to a group on a closed host shows it; closing the host while there, or reloading, doesn't.
  const was = useRef(current);
  useEffect(() => {
    if (current !== was.current && current && !isRoot(current) && closed.has(rootOf(current))) toggle(rootOf(current), true);
    was.current = current;
  }, [current]);

  const onKey = (e: KeyboardEvent) => {
    const items = [...(list.current?.querySelectorAll<HTMLAnchorElement>("a.tree-item") ?? [])];
    const i = items.indexOf(document.activeElement as HTMLAnchorElement);
    const node = shown[i];
    switch (e.key) {
      case "ArrowDown":
        items[Math.min(items.length - 1, i + 1)]?.focus();
        break;
      case "ArrowUp":
        items[Math.max(0, i - 1)]?.focus();
        break;
      case "ArrowRight":
        if (node?.children.length) toggle(node.path, true);
        break;
      case "ArrowLeft":
        if (node?.children.length && isOpen(node.path)) toggle(node.path, false);
        else if (node) items[shown.findIndex((n) => n.path === parentOf(node.path))]?.focus();
        break;
      default:
        return;
    }
    e.preventDefault();
  };

  return html`<nav class="sidebar" aria-label="Groups">
    <label class="filter input body"><${Icon} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${filter} aria-label="Filter groups"
        onInput=${(e: Event) => setFilter((e.target as HTMLInputElement).value)} />
    </label>
    <div class="tree" ref=${list} onKeyDown=${onKey} role="tree">
      ${shown.map((n) => html`<${Item} key=${n.path} node=${n} current=${n.path === current}
        open=${isOpen(n.path) || !!filter} onToggle=${() => toggle(n.path)} />`)}
    </div>
  </nav>`;
}

function Item(props: { node: TreeNode; current: boolean; open: boolean; onToggle: () => void }) {
  const n = props.node;
  const hover = () => calls.prefetchGroup(n.path);
  const expandable = n.children.length > 0;
  const unreachable = n.state === "unreachable";
  return html`<a class=${`tree-item${props.current ? " current" : ""}${isRoot(n.path) ? " source-root" : ""}`} href=${groupUrl(n.path)}
      role="treeitem" aria-current=${props.current ? "page" : undefined} aria-expanded=${expandable ? props.open : undefined}
      style=${`padding-inline-start:${8 + depth(n.path) * 14}px`} onMouseEnter=${hover} onFocus=${hover}
      onClick=${(e: MouseEvent) => {
        if (e.metaKey || e.ctrlKey) return;
        e.preventDefault();
        navigate(groupUrl(n.path));
      }}>
    <span class="twisty" onClick=${(e: Event) => { e.preventDefault(); e.stopPropagation(); props.onToggle(); }}>
      ${expandable ? html`<${Icon} name=${props.open ? "chevron-down" : "chevron-right"} size=${14} />` : null}</span>
    ${isRoot(n.path)
      ? html`<${Sym} size=${14} spec=${{
          icon: unreachable ? "cloud-off" : "server",
          tone: "muted",
          label: unreachable ? `Unreachable: ${n.error ?? "no answer"}` : n.path === "." ? "This machine" : `Remote host ${n.name}`,
        }} />`
      : null}
    <span class="tree-name">${n.name}</span>
    <span class="tree-marks">
      ${n.running ? html`<${Sym} spec=${symbolFor("run", "running")} size=${14} />` : null}
      ${n.failed ? html`<${Sym} spec=${{ ...symbolFor("run", "failed"), label: `${n.failed} failed, killed or lost` }} size=${14} />` : null}
    </span>
    <span class="count small">${n.runs || ""}</span>
  </a>`;
}

function parentOf(path: string): string {
  if (isRoot(path)) return path;
  const i = path.lastIndexOf("/");
  return i < 0 ? "." : path.slice(0, i);
}

function withAncestors(open: Set<string>, path: string | null): Set<string> {
  if (!path || path === ".") return open;
  const out = new Set(open);
  const parts = path.split("/");
  for (let i = 1; i < parts.length; i++) out.add(parts.slice(0, i).join("/"));
  return out;
}
