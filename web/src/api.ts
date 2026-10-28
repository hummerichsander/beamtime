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

export async function post<T = any>(method: string, params: Record<string, unknown> = {}): Promise<T> {
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

function load(e: Entry): Promise<void> {
  if (e.inflight) return e.inflight;
  e.stale = false;
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
      e.inflight = null;
      if (e.stale && e.listeners.size && !paused.value) void load(e);
    });
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
    const e = entryOf(call);
    const fn = () => force((n) => n + 1);
    e.listeners.add(fn);
    if (e.result !== rendered) fn();
    e.used = Date.now();
    if (e.stale) void load(e);
    watchChanged();
    return () => {
      e.listeners.delete(fn);
      watchChanged();
    };
  }, [key]);
  if (!call) return { status: "loading", data: null, error: null, refreshing: false };
  return entryOf(call).result as Result<T>;
}

export const paused = new Store<boolean>(false);
export const connection = new Store<"connecting" | "live" | "offline">("connecting");
// when the server last reported new data (or the stream opened): "updated 3 s ago".
export const updated = new Store<number>(Date.now());
const client = Math.random().toString(36).slice(2, 10);
let watchTimer: ReturnType<typeof setTimeout> | null = null;

function watchChanged(): void {
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

export function connect(): void {
  const source = new EventSource(`/api/subscribe?client=${client}`);
  let connected = false;
  source.addEventListener("hello", () => {
    connection.set("live");
    watchChanged();
    // after a reconnect, changes may have been missed: refetch what is on screen.
    if (connected) markStale([...entries.values()].filter((e) => e.listeners.size).map((e) => e.id));
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
