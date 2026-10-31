// Every state has a URL: the page, the group or run, and the run open in the drawer.

import { EXPORTED, snapshot } from "./snapshot.ts";
import { Store } from "./state.ts";

export type Route =
  | {
      page: "group";
      source: string;
      path: string;
      run: string | null;
      drawer: boolean;
      // a saved view version, a draft (for the renderer), the version history.
      version: string | null;
      draft: string | null;
      history: boolean;
    }
  | { page: "run"; id: string }
  | { page: "settings"; section: string }
  | { page: "timeline"; from: string }
  | { page: "missing"; url: string };

const RUN_ID = /^\d{8}-\d{6}-[0-9a-z]{8}$/;

export function isRunId(s: string): boolean {
  return RUN_ID.test(s);
}

export function parse(pathname: string, search: string): Route {
  const q = new URLSearchParams(search);
  const parts = pathname.split("/").filter(Boolean).map(decodeURIComponent);
  if (parts[0] === "f" && parts.length >= 2) {
    // a remote's groups keep their source in the path: /f/@box/scaling is "@box/scaling".
    const rest = parts.slice(2).join("/");
    return {
      page: "group",
      source: parts[1],
      path: parts[1] === "local" ? rest || "." : [parts[1], ...parts.slice(2)].join("/"),
      run: q.get("run"),
      drawer: q.get("drawer") === "1" || q.has("run"),
      version: q.get("v"),
      draft: q.get("draft"),
      history: q.has("history"),
    };
  }
  if (parts[0] === "f") return parse("/f/local", search);
  // a run on a remote: /r/@box/<id>, so a copy of the same run here doesn't answer for it.
  if (parts[0] === "r" && parts[1]) return { page: "run", id: parts.slice(1).join("/") };
  if (parts[0] === "settings") return { page: "settings", section: parts[1] ?? "appearance" };
  if (parts[0] === "timeline") return { page: "timeline", from: q.get("from") ?? "." };
  return { page: "missing", url: pathname };
}

export function groupUrl(
  path: string,
  opts: { run?: string | null; drawer?: boolean; version?: string | null; history?: boolean } = {},
): string {
  const [source, ...rest] = path.startsWith("@") ? path.split("/") : ["local", ...(path === "." || path === "" ? [] : path.split("/"))];
  const tail = rest.length ? `/${rest.map(encodeURIComponent).join("/")}` : "";
  const q = new URLSearchParams();
  if (opts.version) q.set("v", opts.version);
  if (opts.history) q.set("history", "");
  if (opts.run) q.set("run", opts.run);
  else if (opts.drawer) q.set("drawer", "1");
  const qs = q.toString().replace(/=(?=&|$)/g, "");
  return `/f/${source}${tail}${qs ? `?${qs}` : ""}`;
}

export function timelineUrl(from = "."): string {
  return from === "." ? "/timeline" : `/timeline?from=${encodeURIComponent(from)}`;
}

// a run's link; on a remote's page, runs are that remote's.
export function runUrl(id: string, from?: string): string {
  const r = route.value;
  return `/r/${sourcedRun(id, from ?? (r.page === "group" ? r.path : "."))}`;
}

// a run id with the source of the page it is shown on: "@box/<id>" on @box's pages.
export function sourcedRun(id: string, scope: string): string {
  const root = rootOf(scope);
  return id.startsWith("@") || root === "." ? id : `${root}/${id}`;
}

// the root of a path's source: "." for this machine, "@box" for the remote box.
export function rootOf(path: string): string {
  return path.startsWith("@") ? path.split("/")[0] : ".";
}

export function isRoot(path: string): boolean {
  return path === "." || (path.startsWith("@") && !path.includes("/"));
}

export function parent(path: string): string {
  const i = path.lastIndexOf("/");
  return i < 0 ? "." : path.slice(0, i);
}

export const route = new Store<Route>(
  typeof location === "undefined"
    ? { page: "missing", url: "" }
    : snapshot
      ? parse(groupUrl(snapshot.path), "")
      : parse(location.pathname, location.search),
);

const scrolls = new Map<string, number>();
let scroller: () => HTMLElement | null = () => null;

export function setScroller(get: () => HTMLElement | null): void {
  scroller = get;
}

// inside a custom block's frame, navigation happens in the page.
let away: ((url: string) => void) | null = null;

export function setAway(fn: (url: string) => void): void {
  away = fn;
}

export function navigate(url: string, opts: { replace?: boolean } = {}): void {
  if (away) return away(url);
  // an exported page is one page; other pages aren't part of it.
  if (EXPORTED) return;
  const el = scroller();
  if (el) scrolls.set(location.pathname + location.search, el.scrollTop);
  if (opts.replace) history.replaceState(null, "", url);
  else history.pushState(null, "", url);
  route.set(parse(location.pathname, location.search));
  if (opts.replace) return;
  if (el) el.scrollTop = 0;
  requestAnimationFrame(focusPage);
}

// after a page change, focus goes to the new heading, unless it stayed somewhere still on screen
// (the group tree), so keyboard users keep their place.
function focusPage(): void {
  const active = document.activeElement;
  const main = scroller();
  const lost = !active || active === document.body || !active.isConnected || (main?.contains(active) ?? false);
  if (lost) document.querySelector<HTMLElement>(".page h1")?.focus({ preventScroll: true });
}

export function restoreScroll(): void {
  const el = scroller();
  const top = scrolls.get(location.pathname + location.search);
  if (el && top !== undefined) el.scrollTop = top;
}

export function listen(): void {
  addEventListener("popstate", () => {
    route.set(parse(location.pathname, location.search));
    requestAnimationFrame(() => requestAnimationFrame(restoreScroll));
  });
  // plain links inside the app navigate without a reload; modified clicks open new tabs.
  addEventListener("click", (e) => {
    const a = (e.target as Element | null)?.closest?.("a");
    if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const href = a.getAttribute("href");
    if (!href || !href.startsWith("/") || href.startsWith("/api/") || a.target) return;
    e.preventDefault();
    navigate(href);
  });
}

// the headless renderer opens pages with ?render=1: the view alone, no live updates.
export const rendering = typeof location !== "undefined" && new URLSearchParams(location.search).get("render") === "1";
// an export records a page with ?record=1: every block mounted and loaded, folded or not.
export const recording = rendering && new URLSearchParams(location.search).get("record") === "1";
// figures for an export are taken with ?figures=1: each block's downloads, captured by id.
export const figures = rendering && new URLSearchParams(location.search).get("figures") === "1";
