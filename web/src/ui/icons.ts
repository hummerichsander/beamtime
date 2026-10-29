// The icons Beamtime uses, by name, so symbols and blocks can refer to them as data.

import type { FunctionComponent } from "preact";
import { html } from "htm/preact";
import {
  Activity, Bookmark, Check, ChevronDown, ChevronRight, Circle, CircleCheck, CircleDashed, CircleDot,
  CircleHelp, CircleMinus, CircleX, Clock, CloudOff, Copy, Download, Ellipsis, Eye, EyeOff, FileText,
  FolderTree, GitCommitHorizontal, GripVertical, History, Hourglass, Image, LayoutPanelTop, Keyboard, Lightbulb, Link, Maximize2, Minus,
  Lock, Monitor, Moon, PanelLeft, PanelRight, Pause, Pencil, Play, Plus, RotateCcw, Scale, Search, Server, Settings,
  Save, Signpost, SlidersHorizontal, Square, Sun, Target, Terminal, Trash2, TriangleAlert, X,
} from "lucide-preact";

import type { SymbolSpec } from "./symbols.ts";

const ICONS: Record<string, FunctionComponent<any>> = {
  activity: Activity, bookmark: Bookmark, check: Check, "chevron-down": ChevronDown,
  "chevron-right": ChevronRight, circle: Circle, "circle-check": CircleCheck, "circle-dashed": CircleDashed,
  "circle-dot": CircleDot, "circle-help": CircleHelp, "circle-minus": CircleMinus, "circle-x": CircleX,
  clock: Clock, "cloud-off": CloudOff, copy: Copy, download: Download, ellipsis: Ellipsis, eye: Eye,
  "eye-off": EyeOff, "file-text": FileText, "folder-tree": FolderTree, "git-commit": GitCommitHorizontal, grip: GripVertical,
  history: History, hourglass: Hourglass, image: Image, layout: LayoutPanelTop, keyboard: Keyboard, lightbulb: Lightbulb, link: Link, lock: Lock,
  maximize: Maximize2, minus: Minus, monitor: Monitor, moon: Moon, "panel-left": PanelLeft,
  "panel-right": PanelRight, pause: Pause, pencil: Pencil, play: Play, plus: Plus, reset: RotateCcw, scale: Scale,
  save: Save, search: Search, server: Server, settings: Settings, signpost: Signpost, sliders: SlidersHorizontal,
  square: Square, sun: Sun, target: Target, terminal: Terminal, trash: Trash2, "triangle-alert": TriangleAlert, x: X,
};

export function Icon(props: { name: string; size?: number; class?: string; label?: string }) {
  const Component = ICONS[props.name] ?? Circle;
  return html`<${Component} size=${props.size ?? 16} stroke-width=${1.75} class=${`icon ${props.class ?? ""}`}
    aria-hidden=${props.label ? undefined : "true"} aria-label=${props.label} role=${props.label ? "img" : undefined} />`;
}

// a state shown as icon in its tone; with `word`, the label follows the icon.
export function Sym(props: { spec: SymbolSpec; word?: boolean; size?: number }) {
  const s = props.spec;
  return html`<span class=${`sym tone-${s.tone}${s.pulse ? " pulse" : ""}`} data-tip=${props.word ? undefined : s.label}>
    <${Icon} name=${s.icon} size=${props.size ?? 15} label=${props.word ? undefined : s.label} />
    ${props.word ? html`<span class="sym-word">${s.label}</span>` : null}
  </span>`;
}
