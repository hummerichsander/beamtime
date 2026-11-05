// Compact, readable numbers, steps, durations and labels; full values go in tooltips.

export function value(v: unknown): string {
  if (v === null || v === undefined) return "–";
  if (typeof v === "boolean") return v ? "true" : "false";
  if (Array.isArray(v)) return v.length <= 5 ? `[${v.map(value).join(", ")}]` : `[${v.length} items]`;
  if (typeof v === "object") {
    const n = Object.keys(v).length;
    return n ? `{${n} ${n === 1 ? "key" : "keys"}}` : "{}";
  }
  if (typeof v !== "number") return String(v);
  if (!Number.isFinite(v)) return Number.isNaN(v) ? "NaN" : v > 0 ? "∞" : "−∞";
  if (Number.isInteger(v) && Math.abs(v) < 1e4) return String(v);
  const a = Math.abs(v);
  if (a >= 1e4) return big(v);
  if (a !== 0 && a < 1e-3) return exp(v);
  return trim(v.toPrecision(4));
}

// the whole value for a tooltip: nested values as indented JSON, nothing cut.
export function full(v: unknown): string {
  if (v === null || v === undefined) return "–";
  if (typeof v !== "object") return String(v);
  return JSON.stringify(v, (_, x) => (typeof x === "number" && !Number.isFinite(x) ? String(x) : x), 2);
}

// sort order for table cells: numbers as numbers, the rest as text, missing values last.
export function compare(a: unknown, b: unknown): number {
  if (a === b) return 0;
  if (a === null || a === undefined) return 1;
  if (b === null || b === undefined) return -1;
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b));
}

// a version or note id (20261028-215111-36js) as an ISO time.
export function versionTime(v: string | null | undefined): string | null {
  if (!v) return null;
  return `${v.slice(0, 4)}-${v.slice(4, 6)}-${v.slice(6, 8)}T${v.slice(9, 11)}:${v.slice(11, 13)}:${v.slice(13, 15)}Z`;
}

export function step(n: number | null | undefined): string {
  if (n === null || n === undefined) return "–";
  return Math.abs(n) >= 1e4 ? big(n) : String(n);
}

export function duration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || !Number.isFinite(seconds)) return "–";
  const s = Math.round(seconds);
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m ${s % 60}s`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
  return `${Math.floor(s / 86400)}d ${Math.floor((s % 86400) / 3600)}h`;
}

export function ago(iso: string | null | undefined, now: number = Date.now()): string {
  if (!iso) return "–";
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return iso;
  const s = (now - t) / 1000;
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`;
  if (s < 7 * 86400) return `${Math.floor(s / 86400)} d ago`;
  return iso.slice(0, 10);
}

const NAMES: Record<string, string> = {
  "run.name": "run",
  "run.created_at": "started",
  "run.ended_at": "ended",
  "run.group": "group",
};

export function label(field: string): string {
  if (NAMES[field]) return NAMES[field];
  const m = /^metric\.(.+)\.(last|first|min|max|mean|count|ema_last|last_step)$/.exec(field);
  // "last" is what a run table means by a metric; other statistics are named.
  if (m) return m[2] === "last" ? m[1] : `${m[1]} ${m[2].replace("_", " ")}`;
  for (const prefix of ["config.", "run.", "value.", "proposal."]) {
    if (field.startsWith(prefix)) return field.slice(prefix.length);
  }
  return field;
}

// a dotted config key as its segments; a key with a dot in it is written ["a.b"].
export function segments(key: string): string[] {
  return key.match(/\["[^"]*"\]|[^.[\]]+/g)?.map((x) => (x.startsWith("[") ? x.slice(2, -2) : x)) ?? [key];
}

// column labels: a config key shows its shortest suffix that no other column shares
// (beads.edge_frame, not config.model.beads.edge_frame); other fields read as `label` says.
export function shortLabels(fields: string[]): Map<string, string> {
  const out = new Map<string, string>();
  const parts = fields.filter((f) => f.startsWith("config.")).map((f) => [f, segments(f.slice(7))] as const);
  for (const [field, own] of parts) {
    let n = 1;
    const shared = (k: number) => parts.some(([f, o]) => f !== field && o.slice(-k).join(".") === own.slice(-k).join("."));
    while (n < own.length && shared(n)) n++;
    out.set(field, own.slice(-n).join("."));
  }
  for (const f of fields) if (!out.has(f)) out.set(f, label(f));
  return out;
}

function big(v: number): string {
  const a = Math.abs(v);
  const [d, unit] = a >= 1e9 ? [1e9, "G"] : a >= 1e6 ? [1e6, "M"] : [1e3, "k"];
  return `${trim((v / d).toPrecision(3))}${unit}`;
}

function exp(v: number): string {
  const [mant, e] = v.toExponential(1).split("e");
  return `${trim(mant)}e${Number(e)}`;
}

function trim(s: string): string {
  return s.includes(".") && !s.includes("e") ? s.replace(/\.?0+$/, "") : s;
}

const LOWER_IS_BETTER = ["loss", "err", "ppl", "perplexity", "nll", "mse", "mae", "wer", "cer"];

// a guess from the metric's name, matching the server's default view (views/defaults.py).
export function lowerIsBetter(field: string): boolean {
  const m = /^metric\.(.+)\.[a-z_]+$/.exec(field);
  const leaf = (m ? m[1] : field).split("/").pop()!.toLowerCase();
  return LOWER_IS_BETTER.some((w) => leaf.includes(w));
}
