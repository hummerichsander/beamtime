// Compact, readable numbers, steps, durations and labels; full values go in tooltips.

export function value(v: unknown): string {
  if (v === null || v === undefined) return "–";
  if (typeof v === "boolean") return v ? "true" : "false";
  if (typeof v !== "number") return String(v);
  if (!Number.isFinite(v)) return Number.isNaN(v) ? "NaN" : v > 0 ? "∞" : "−∞";
  if (Number.isInteger(v) && Math.abs(v) < 1e4) return String(v);
  const a = Math.abs(v);
  if (a >= 1e4) return big(v);
  if (a !== 0 && a < 1e-3) return exp(v);
  return trim(v.toPrecision(4));
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

export function label(field: string): string {
  const m = /^metric\.(.+)\.(last|first|min|max|mean|count|ema_last|last_step)$/.exec(field);
  if (m) return `${m[1]} ${m[2].replace("_", " ")}`;
  for (const prefix of ["config.", "run.", "value.", "proposal."]) {
    if (field.startsWith(prefix)) return field.slice(prefix.length);
  }
  return field;
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
