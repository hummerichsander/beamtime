// The API client: one cache entry per call, refetched when the server names it stale.

import { useEffect, useState } from "preact/hooks";

import { Store } from "./state.ts";

export type Call = { method: string; params: Record<string, unknown>; scope: string };
export type Result<T = any> = {
  status: "loading" | "ready" | "error";
  data: T | null;
  error: string | null;
  refreshing: boolean;
};

export class ApiError extends Error {
  code: number;

  constructor(message: string, code: number) {
    super(message);
    this.code = code;
  }
}

// inside a custom block's frame there is no network: the page answers calls over the bridge,
// and nothing is written from there.
type Remote = { subscribe(id: string, call: Call): void; unsubscribe(id: string): void };
let remote: Remote | null = null;

export function setRemote(r: Remote): void {
  remote = r;
}

// an answer the page sent for a call this frame subscribed to.
export function deliver(id: string, result: Result): void {
  for (const e of entries.values()) {
    if (e.id !== id) continue;
    update(e, result);
    if (result.status !== "loading") e.settle?.();
  }
}

export async function post<T = any>(method: string, params: Record<string, unknown> = {}): Promise<T> {
  if (remote) throw new ApiError(`${method} is not available in a custom block`, 2);
  const r = await fetch(`/api/${method}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(params),
    credentials: "same-origin",
  });
  const body = await r.json().catch(() => ({ error: `HTTP ${r.status}`, code: r.status }));
  if (!r.ok) throw new ApiError(body.error ?? `HTTP ${r.status}`, body.code ?? r.status);
  return body as T;
}

type Entry = {
  call: Call;
  id: string;
  result: Result;
  listeners: Set<() => void>;
  stale: boolean;
  inflight: Promise<void> | null;
  used: number;
  settle?: () => void;
};

const entries = new Map<string, Entry>();
let counter = 0;

export function keyOf(call: Call): string {
  return `${call.method} ${JSON.stringify(call.params)}`;
}

function entryOf(call: Call): Entry {
  const key = keyOf(call);
  let e = entries.get(key);
  if (!e) {
    e = {
      call,
      id: `q${++counter}`,
      result: { status: "loading", data: null, error: null, refreshing: false },
      listeners: new Set(),
      stale: true,
      inflight: null,
      used: Date.now(),
    };
    entries.set(key, e);
  }
  return e;
}

// calls and chart builds in flight; the headless renderer waits until there are none.
export const busy = { n: 0 };

function load(e: Entry): Promise<void> {
  if (e.inflight) return e.inflight;
  if (remote) return subscribeRemote(e, remote);
  e.stale = false;
  busy.n++;
  if (e.result.status === "ready") update(e, { ...e.result, refreshing: true });
  e.inflight = post(e.call.method, e.call.params)
    .then((data) => update(e, { status: "ready", data, error: null, refreshing: false }))
    .catch((err: Error) =>
      update(e, {
        // a failed refetch keeps the last answer and shows the error next to it.
        status: e.result.data === null ? "error" : "ready",
        data: e.result.data,
        error: err.message,
        refreshing: false,
      }),
    )
    .finally(() => {
      busy.n--;
      e.inflight = null;
      if (e.stale && e.listeners.size && !paused.value) void load(e);
    });
  return e.inflight;
}

function subscribeRemote(e: Entry, r: Remote): Promise<void> {
  e.stale = false;
  busy.n++;
  e.inflight = new Promise<void>((resolve) => {
    e.settle = () => {
      e.settle = undefined;
      e.inflight = null;
      busy.n--;
      resolve();
    };
  });
  r.subscribe(e.id, e.call);
  return e.inflight;
}

function update(e: Entry, result: Result): void {
  e.result = result;
  for (const fn of [...e.listeners]) fn();
}

export function fetchCall<T = any>(call: Call): Promise<T> {
  const e = entryOf(call);
  if (e.result.status === "ready" && !e.stale) return Promise.resolve(e.result.data as T);
  return load(e).then(() => {
    if (e.result.error && e.result.data === null) throw new Error(e.result.error);
    return e.result.data as T;
  });
}

export function prefetch(call: Call): void {
  const e = entryOf(call);
  e.used = Date.now();
  if (e.stale) void load(e);
}

export function useCall<T = any>(call: Call | null): Result<T> {
  const key = call ? keyOf(call) : "";
  const [, force] = useState(0);
  const rendered = call ? entryOf(call).result : null;
  useEffect(() => {
    if (!call) return;
    const fn = () => force((n) => n + 1);
    if (entryOf(call).result !== rendered) fn();
    return watch(call, fn);
  }, [key]);
  if (!call) return { status: "loading", data: null, error: null, refreshing: false };
  return entryOf(call).result as Result<T>;
}

// calls fn on every new answer to a call, fetching it while watched; returns the unwatch.
export function watch(call: Call, fn: (result: Result) => void): () => void {
  const e = entryOf(call);
  const listener = () => fn(e.result);
  e.listeners.add(listener);
  e.used = Date.now();
  if (e.stale) void load(e);
  watchChanged();
  return () => {
    e.listeners.delete(listener);
    if (remote && !e.listeners.size) {
      remote.unsubscribe(e.id);
      e.stale = true;
      e.settle?.();
    }
    watchChanged();
  };
}

export const paused = new Store<boolean>(false);
export const connection = new Store<"connecting" | "live" | "offline">("connecting");
// when the server last reported new data (or the stream opened): "updated 3 s ago".
export const updated = new Store<number>(Date.now());
const client = Math.random().toString(36).slice(2, 10);
let watchTimer: ReturnType<typeof setTimeout> | null = null;

function watchChanged(): void {
  if (remote) return;
  if (watchTimer) clearTimeout(watchTimer);
  watchTimer = setTimeout(() => {
    watchTimer = null;
    const watched: Record<string, string> = {};
    for (const e of entries.values()) if (e.listeners.size) watched[e.id] = e.call.scope;
    post("watch", { client, watched }).catch(() => {});
    evict();
  }, 50);
}

// unwatched answers stay for back and forward navigation, a few minutes at most.
function evict(): void {
  const old = Date.now() - 5 * 60_000;
  for (const [key, e] of entries) if (!e.listeners.size && e.used < old) entries.delete(key);
}

function markStale(ids: string[]): void {
  const set = new Set(ids);
  for (const e of entries.values()) {
    if (!set.has(e.id)) continue;
    e.stale = true;
    if (e.listeners.size && !paused.value) void load(e);
  }
}

export function connect(onReconnect?: () => void): void {
  const source = new EventSource(`/api/subscribe?client=${client}`);
  let connected = false;
  source.addEventListener("hello", () => {
    connection.set("live");
    watchChanged();
    // after a reconnect, changes may have been missed: refetch what is on screen.
    if (connected) {
      markStale([...entries.values()].filter((e) => e.listeners.size).map((e) => e.id));
      onReconnect?.();
    }
    connected = true;
  });
  source.addEventListener("stale", (ev) => {
    updated.set(Date.now());
    markStale(JSON.parse((ev as MessageEvent).data));
  });
  source.onerror = () => connection.set(source.readyState === EventSource.CLOSED ? "offline" : "connecting");
  paused.subscribe((p) => {
    if (!p) for (const e of entries.values()) if (e.stale && e.listeners.size) void load(e);
  });
}

// after a write, the answers it changes are fetched again (the live stream confirms later).
export function invalidate(match: (call: Call) => boolean): void {
  markStale([...entries.values()].filter((e) => match(e.call)).map((e) => e.id));
}
