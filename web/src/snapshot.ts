// A page exported as static HTML (`beamtime export --html`) answers every call from the snapshot
// taken when it was exported; nothing reaches a server, and nothing is written.

export type Frozen = { method: string; params: Record<string, unknown>; answer?: unknown; error?: string; code?: number };
export type Snapshot = { path: string; taken: number; points: number | "all"; version: string; calls: Frozen[] };

export const EXPORTED: boolean = typeof __EXPORT__ !== "undefined" && __EXPORT__;
export const snapshot: Snapshot | null = EXPORTED ? ((globalThis as any).__BT_SNAPSHOT__ ?? null) : null;

// the frontend's own files: served under /static, or next to an exported page.
export function staticUrl(path: string): string {
  return EXPORTED ? `static/${path}` : `/static/${path}`;
}

// a file a run logged (an image): from the server, or copied next to an exported page.
export function fileUrl(run: string, path: string): string {
  return EXPORTED ? `files/${run}/${path}` : `/api/file/${run}/${path}`;
}
