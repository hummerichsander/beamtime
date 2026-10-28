// A tiny observable value with a Preact hook; enough state management for the shell.

import { useEffect, useState } from "preact/hooks";

export class Store<T> {
  value: T;
  listeners = new Set<(v: T) => void>();

  constructor(value: T) {
    this.value = value;
  }

  set(value: T): void {
    this.value = value;
    for (const fn of [...this.listeners]) fn(value);
  }

  subscribe(fn: (v: T) => void): () => void {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }
}

export function useStore<T>(store: Store<T>): T {
  const [, force] = useState(0);
  const value = store.value;
  useEffect(() => {
    const unsubscribe = store.subscribe(() => force((n) => n + 1));
    // a change between render and subscription would otherwise be missed.
    if (store.value !== value) force((n) => n + 1);
    return unsubscribe;
  }, [store]);
  return value;
}

export function stored<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(`beamtime.${key}`);
    return raw === null ? fallback : (JSON.parse(raw) as T);
  } catch {
    return fallback;
  }
}

export function store<T>(key: string, value: T): void {
  try {
    localStorage.setItem(`beamtime.${key}`, JSON.stringify(value));
  } catch {
    // private windows and blocked storage: the preference just isn't remembered.
  }
}
