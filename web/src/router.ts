// Every state has a URL: the page, the folder or run, and the run open in the drawer.

import { Store } from "./state.ts";

export type Route =
  | { page: "folder"; source: string; path: string; run: string | null; drawer: boolean }
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
      page: "folder",
      source: parts[1],
      path: parts.slice(2).join("/") || ".",
      run: q.get("run"),
      drawer: q.get("drawer") === "1" || q.has("run"),
    };
  }
  if (parts[0] === "f") return { page: "folder", source: "local", path: ".", run: null, drawer: false };
  if (parts[0] === "r" && parts[1]) return { page: "run", id: parts[1] };
  if (parts[0] === "settings") return { page: "settings", section: parts[1] ?? "appearance" };
  return { page: "missing", url: pathname };
}

export function folderUrl(path: string, opts: { run?: string | null; drawer?: boolean } = {}): string {
  const tail = path === "." || path === "" ? "" : `/${path.split("/").map(encodeURIComponent).join("/")}`;
  const q = new URLSearchParams();
  if (opts.run) q.set("run", opts.run);
  else if (opts.drawer) q.set("drawer", "1");
  const qs = q.toString();
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
  if (opts.replace) history.replaceState(null, "", url);
  else history.pushState(null, "", url);
  route.set(parse(location.pathname, location.search));
  if (!opts.replace && el) el.scrollTop = 0;
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
