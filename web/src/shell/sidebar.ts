// The sidebar: the folder tree with run counts and status dots, filterable and keyboard-driven.

import { html } from "htm/preact";
import { useRef, useState } from "preact/hooks";

import { prefetch, useCall } from "../api.ts";
import { Dot, rows } from "../blocks/common.ts";
import { folderUrl, navigate, route } from "../router.ts";
import { stored, store, useStore } from "../state.ts";
import * as calls from "./calls.ts";
import { buildTree, depth, visible, type TreeNode } from "./tree.ts";

export function Sidebar() {
  const r = useStore(route);
  const result = useCall(calls.tree());
  const [open, setOpen] = useState<Set<string>>(() => new Set(stored<string[]>("open", [])));
  const [filter, setFilter] = useState("");
  const list = useRef<HTMLDivElement>(null);
  const current = r.page === "folder" ? r.path : null;
  const root = buildTree(rows(result.data));
  const shown = visible(root, withAncestors(open, current), filter);

  const toggle = (path: string, value?: boolean) => {
    const next = new Set(open);
    if (value ?? !next.has(path)) next.add(path);
    else next.delete(path);
    store("open", [...next]);
    setOpen(next);
  };

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
        if (node && open.has(node.path)) toggle(node.path, false);
        else if (node) items[shown.findIndex((n) => n.path === parentOf(node.path))]?.focus();
        break;
      default:
        return;
    }
    e.preventDefault();
  };

  return html`<nav class="sidebar" aria-label="Folders">
    <input class="filter" type="search" placeholder="Filter folders" value=${filter}
      onInput=${(e: Event) => setFilter((e.target as HTMLInputElement).value)} />
    <div class="tree" ref=${list} onKeyDown=${onKey} role="tree">
      ${shown.map((n) => html`<${Item} key=${n.path} node=${n} current=${n.path === current}
        open=${open.has(n.path) || !!filter} onToggle=${() => toggle(n.path)} />`)}
    </div>
  </nav>`;
}

function Item(props: { node: TreeNode; current: boolean; open: boolean; onToggle: () => void }) {
  const n = props.node;
  const hover = () => {
    prefetch(calls.view(n.path));
    prefetch(calls.folder(n.path));
  };
  return html`<a class=${`tree-item${props.current ? " current" : ""}`} href=${folderUrl(n.path)}
      role="treeitem" aria-current=${props.current ? "page" : undefined}
      style=${`padding-left:${8 + depth(n.path) * 12}px`} onMouseEnter=${hover} onFocus=${hover}
      onClick=${(e: MouseEvent) => {
        if (e.metaKey || e.ctrlKey) return;
        e.preventDefault();
        navigate(folderUrl(n.path));
      }}>
    <span class="twisty" onClick=${(e: Event) => { e.preventDefault(); e.stopPropagation(); props.onToggle(); }}>
      ${n.children.length && n.path !== "." ? (props.open ? "▾" : "▸") : ""}</span>
    <span class="tree-name">${n.name}</span>
    ${n.running ? html`<${Dot} status="running" />` : null}
    ${n.failed ? html`<${Dot} status="failed" />` : null}
    <span class="count">${n.runs || ""}</span>
  </a>`;
}

function parentOf(path: string): string {
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
