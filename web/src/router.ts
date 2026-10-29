// Every state has a URL: the page, the group or run, and the run open in the drawer.

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
  | { page: "missing"; url: string };

const RUN_ID = /^\d{8}-\d{6}-[0-9a-z]{8}$/;

export function isRunId(s: string): boolean {
  return RUN_ID.test(s);
}

export function parse(pathname: string, search: string): Route {
  const q = new URLSearchParams(search);
  const parts = pathname.split("/").filter(Boolean).map(decodeURIComponent);
  if (parts[0] === "f" && parts.length >= 2) {
    return {
      page: "group",
      source: parts[1],
      path: parts.slice(2).join("/") || ".",
      run: q.get("run"),
      drawer: q.get("drawer") === "1" || q.has("run"),
      version: q.get("v"),
      draft: q.get("draft"),
      history: q.has("history"),
    };
  }
  if (parts[0] === "f") return parse("/f/local", search);
  if (parts[0] === "r" && parts[1]) return { page: "run", id: parts[1] };
  if (parts[0] === "settings") return { page: "settings", section: parts[1] ?? "appearance" };
  return { page: "missing", url: pathname };
}

export function groupUrl(
  path: string,
  opts: { run?: string | null; drawer?: boolean; version?: string | null; history?: boolean } = {},
): string {
  const tail = path === "." || path === "" ? "" : `/${path.split("/").map(encodeURIComponent).join("/")}`;
  const q = new URLSearchParams();
  if (opts.version) q.set("v", opts.version);
  if (opts.history) q.set("history", "");
  if (opts.run) q.set("run", opts.run);
  else if (opts.drawer) q.set("drawer", "1");
  const qs = q.toString().replace(/=(?=&|$)/g, "");
  return `/f/local${tail}${qs ? `?${qs}` : ""}`;
}

export function runUrl(id: string): string {
  return `/r/${id}`;
}

export function parent(path: string): string {
  const i = path.lastIndexOf("/");
  return i < 0 ? "." : path.slice(0, i);
}

export const route = new Store<Route>(
  typeof location === "undefined" ? { page: "missing", url: "" } : parse(location.pathname, location.search),
);

const scrolls = new Map<string, number>();
let scroller: () => HTMLElement | null = () => null;

export function setScroller(get: () => HTMLElement | null): void {
  scroller = get;
}

export function navigate(url: string, opts: { replace?: boolean } = {}): void {
  const el = scroller();
  if (el) scrolls.set(location.pathname + location.search, el.scrollTop);
  const swap = () => {
    if (opts.replace) history.replaceState(null, "", url);
    else history.pushState(null, "", url);
    route.set(parse(location.pathname, location.search));
    if (!opts.replace && el) el.scrollTop = 0;
  };
  // only page changes cross-fade; drawer and selection changes (replace) are instant.
  if (opts.replace || !document.startViewTransition || matchMedia("(prefers-reduced-motion: reduce)").matches) {
    swap();
    if (!opts.replace) requestAnimationFrame(focusPage);
    return;
  }
  // frames are paused while the transition updates the DOM, so wait for Preact's render (a
  // microtask) with a task, never with requestAnimationFrame, or the transition times out.
  const t = document.startViewTransition(async () => {
    swap();
    await new Promise((r) => setTimeout(r, 0));
  });
  void t.finished.then(focusPage);
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
