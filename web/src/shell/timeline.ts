// The timeline: runs as bars from start to end, colored by status, and notes as marks above them.
// Wheel zooms around the pointer, dragging pans, the buttons pick a range; clicks open what they hit.

import { html } from "htm/preact";
import { useEffect, useRef, useState } from "preact/hooks";

import { useCall } from "../api.ts";
import { rows } from "../blocks/common.ts";
import { useTheme } from "../bt/index.ts";
import { ago, duration } from "../bt/fmt.ts";
import { useChart } from "../bt/chart.ts";
import { plotChart, type PlotSpec } from "../bt/plot.ts";
import { timeLabel, timeTicks } from "../bt/shapes.ts";
import { alpha, chartStyle, type Theme } from "../bt/theme.ts";
import { groupUrl, navigate, runUrl, timelineUrl } from "../router.ts";
import type { TipRow } from "../bt/uplot.ts";
import * as calls from "./calls.ts";

const LANE = 20;
const NOTE_LANE = -1;
const RANGES = [
  ["day", 86400],
  ["week", 7 * 86400],
  ["month", 30 * 86400],
] as const;

type Bar = { id: string; name: string; group: string; status: string; start: number; end: number; lane: number };
type Mark = { id: string; type: string; group: string; description: string; t: number };

export function TimelinePage(props: { from: string }) {
  const tree = rows(useCall(calls.tree()).data).map((r) => r.path as string);
  const runs = useCall({
    method: "runs",
    params: { from: props.from, select: ["run.name", "run.status", "run.group", "run.created_at", "run.ended_at"], sort: ["run.created_at"], limit: 2000 },
    scope: props.from,
  });
  const notes = useCall({ method: "notes", params: { from: props.from, limit: 500, current: true }, scope: props.from });
  useEffect(() => {
    document.title = "Timeline · Beamtime";
  }, []);
  const now = Date.now() / 1000;
  const bars: Bar[] = rows(runs.data)
    .filter((r) => r["run.created_at"])
    .map((r, i) => ({
      id: r["run.id"],
      name: r["run.name"] ?? r["run.id"],
      group: r["run.group"],
      status: r["run.status"],
      start: Date.parse(r["run.created_at"]) / 1000,
      end: r["run.ended_at"] ? Date.parse(r["run.ended_at"]) / 1000 : now,
      lane: i,
    }));
  const marks: Mark[] = (notes.data?.entries ?? []).map((n: any) => ({
    id: n.id, type: n.type, group: n.group, description: n.description, t: versionTime(n.id),
  }));  // prettier-ignore
  return html`<div class="page timeline-page">
    <header class="header">
      <h1 class="title" tabindex="-1">Timeline</h1>
      <div class="timeline-filter">
        <label class="field inline"><span class="field-label">Group</span>
          <select value=${props.from} onChange=${(e: Event) => navigate(timelineUrl((e.target as HTMLSelectElement).value), { replace: true })}>
            ${tree.map((p) => html`<option value=${p}>${p === "." ? "everything" : p}</option>`)}
          </select></label>
        <span class="muted small">${bars.length} runs · ${marks.length} notes · wheel zooms, drag pans, click opens</span>
      </div>
    </header>
    ${runs.status === "error" ? html`<p class="notice error">${runs.error}</p>` : null}
    ${runs.data && notes.data ? html`<${Lanes} bars=${bars} marks=${marks} />` : html`<div class="skeleton late" style="block-size: 320px"></div>`}
  </div>`;
}

function Lanes(props: { bars: Bar[]; marks: Mark[] }) {
  const theme = useTheme();
  const el = useRef<HTMLDivElement>(null);
  const times = [...props.bars.flatMap((b) => [b.start, b.end]), ...props.marks.map((m) => m.t)];
  const full: [number, number] = times.length ? pad(Math.min(...times), Math.max(...times)) : pad(Date.now() / 1000 - 86400, Date.now() / 1000);
  const [range, setRange] = useState<[number, number]>(full);
  const lanes = props.bars.length;
  const height = Math.min(900, Math.max(160, (lanes + 1.5) * LANE + 40));

  const spec = (t: Theme): PlotSpec => {
    const ticks = timeTicks(range[0], range[1]);
    const status = (s: string) => String(t.colors[s] ?? t.colors.muted);
    const noteColor = (type: string) => String(t.colors[type === "verdict" ? "good" : type === "decision" ? "accent" : type === "question" ? "warn" : "muted"]);
    return {
      style: chartStyle(t),
      height,
      x: { range, log: false, format: (v) => timeLabel(v, ticks.step), splits: ticks.at },
      y: {
        range: [NOTE_LANE - 0.8, lanes + 0.5],
        log: false,
        reverse: true,
        size: 150,
        splits: lanes <= 40 ? [NOTE_LANE, ...props.bars.map((b) => b.lane)] : [NOTE_LANE],
        format: (v) => (v === NOTE_LANE ? "notes" : short(props.bars[Math.round(v)]?.name ?? "")),
      },
      draw: ({ ctx, x, y, px, focused }) => {
        const h = LANE * 0.62 * px;
        for (const b of props.bars) {
          const x0 = x(b.start);
          const w = Math.max(3 * px, x(b.end) - x0);
          ctx.fillStyle = focused !== null && focused !== b.id ? alpha(status(b.status), 0.35) : status(b.status);
          ctx.beginPath();
          ctx.roundRect(x0, y(b.lane) - h / 2, w, h, 3 * px);
          ctx.fill();
        }
        for (const m of props.marks) {
          const cx = x(m.t);
          const cy = y(NOTE_LANE);
          const r = (focused === m.id ? 6 : 4.5) * px;
          ctx.fillStyle = noteColor(m.type);
          ctx.beginPath();
          ctx.moveTo(cx, cy - r);
          ctx.lineTo(cx + r, cy);
          ctx.lineTo(cx, cy + r);
          ctx.lineTo(cx - r, cy);
          ctx.closePath();
          ctx.fill();
        }
      },
      hit: (left, top, x, y) => {
        if (Math.abs(top - y(NOTE_LANE)) < LANE / 2) {
          const m = nearest(props.marks, (mk) => Math.abs(x(mk.t) - left), 8);
          return m ? { key: m.id, rows: noteRows(m) } : null;
        }
        const lane = Math.round((top - y(0)) / (y(1) - y(0)));
        const b = props.bars.find((bb) => bb.lane === lane && x(bb.start) - 3 <= left && left <= Math.max(x(bb.end), x(bb.start) + 3) + 3);
        return b ? { key: b.id, rows: barRows(b) } : null;
      },
      onClick: (key) => {
        const m = props.marks.find((mk) => mk.id === key);
        if (m) navigate(groupUrl(m.group, { drawer: true }));
        else navigate(runUrl(key));
      },
    };
  };

  const plot = useChart(el, plotChart, theme ? spec(theme) : null, [range, props.bars, props.marks], theme);

  // wheel zooms around the pointer; dragging pans.
  const onWheel = (e: WheelEvent) => {
    if (!plot.current) return;
    e.preventDefault();
    const at = plot.current.xAt(e.clientX);
    const f = Math.exp(e.deltaY * 0.0015);
    setRange(([a, b]) => clamp([at - (at - a) * f, at + (b - at) * f], full));
  };
  const drag = useRef<{ x: number; range: [number, number] } | null>(null);
  const onDown = (e: PointerEvent) => (drag.current = { x: e.clientX, range });
  const onMove = (e: PointerEvent) => {
    if (!drag.current || !plot.current || !(e.buttons & 1)) return;
    const dx = (e.clientX - drag.current.x) * plot.current.xPerPixel();
    const [a, b] = drag.current.range;
    if (Math.abs(e.clientX - drag.current.x) > 3) setRange(clamp([a - dx, b - dx], full));
  };
  const last = Math.max(...times, Date.now() / 1000);
  return html`<div class="timeline-chart">
    <div class="segmented small" role="radiogroup" aria-label="Range">
      ${RANGES.map(([name, s]) => html`<button type="button" role="radio" aria-checked=${Math.abs(range[1] - range[0] - s) < 1}
          onClick=${() => setRange(clamp([last - s, last + s * 0.02], [Math.min(full[0], last - s), full[1]]))}>last ${name}</button>`)}
      <button type="button" role="radio" aria-checked=${range[0] === full[0] && range[1] === full[1]} onClick=${() => setRange(full)}>all</button>
    </div>
    <div class="chart" ref=${el} style=${`min-block-size:${height}px`}
      onWheel=${onWheel} onPointerDown=${onDown} onPointerMove=${onMove} onPointerUp=${() => (drag.current = null)}></div>
    <p class="muted small">${legend(theme)}</p>
  </div>`;
}

function barRows(b: Bar): TipRow[] {
  return [
    { label: b.name, value: "", color: null, strong: true },
    { label: "group", value: b.group, color: null },
    { label: "status", value: b.status, color: null },
    { label: "started", value: ago(new Date(b.start * 1000).toISOString()), color: null },
    { label: "duration", value: duration(b.end - b.start), color: null },
  ];
}

function noteRows(m: Mark): TipRow[] {
  return [
    { label: m.description.slice(0, 80), value: "", color: null, strong: true },
    { label: m.type, value: m.group, color: null },
    { label: "written", value: ago(new Date(m.t * 1000).toISOString()), color: null },
  ];
}

function legend(theme: Theme | null): string {
  return theme ? "bars: runs by status · diamonds: notes (green verdicts, blue decisions, amber questions)" : "";
}

function nearest<T>(items: T[], distance: (item: T) => number, max: number): T | null {
  let best: T | null = null;
  let d = max;
  for (const it of items) {
    const di = distance(it);
    if (di < d) [best, d] = [it, di];
  }
  return best;
}

function pad(a: number, b: number): [number, number] {
  const d = Math.max(60, (b - a) * 0.03);
  return [a - d, b + d];
}

// a range stays within the data's span and never shorter than a minute.
function clamp([a, b]: [number, number], full: [number, number]): [number, number] {
  const span = Math.min(full[1] - full[0], Math.max(60, b - a));
  const lo = Math.max(full[0], Math.min(a, full[1] - span));
  return [lo, lo + span];
}

function short(name: string): string {
  return name.length > 22 ? `${name.slice(0, 21)}…` : name;
}

// a note's id (20261028-215111-36js) as seconds.
function versionTime(id: string): number {
  const iso = `${id.slice(0, 4)}-${id.slice(4, 6)}-${id.slice(6, 8)}T${id.slice(9, 11)}:${id.slice(11, 13)}:${id.slice(13, 15)}Z`;
  return Date.parse(iso) / 1000;
}
