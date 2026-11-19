// Zoom and pan of one element inside a box: a CSS transform `translate(x, y) scale(k)` with the
// origin in the box's corner, so the point under the pointer stays under it.

import { useEffect, useRef, useState } from "preact/hooks";

export type Pose = { k: number; x: number; y: number };
export const FIT: Pose = { k: 1, x: 0, y: 0 };
export const MAX = 32;

// keeps the zoomed element covering the box.
export function clamp(p: Pose, w: number, h: number): Pose {
  const k = Math.min(MAX, Math.max(1, p.k));
  return { k, x: Math.min(0, Math.max(w * (1 - k), p.x)), y: Math.min(0, Math.max(h * (1 - k), p.y)) };
}

// scales by `factor` around the point (px, py) of the box.
export function zoomAt(p: Pose, factor: number, px: number, py: number, w: number, h: number): Pose {
  const k = Math.min(MAX, Math.max(1, p.k * factor));
  const r = k / p.k;
  return clamp({ k, x: px - (px - p.x) * r, y: py - (py - p.y) * r }, w, h);
}

export function panBy(p: Pose, dx: number, dy: number, w: number, h: number): Pose {
  return clamp({ ...p, x: p.x + dx, y: p.y + dy }, w, h);
}

export function transform(p: Pose): string {
  return `translate(${p.x}px, ${p.y}px) scale(${p.k})`;
}

// the pose of a box and what moves it: wheel and pinch (ctrl + wheel) zoom around the pointer,
// a drag pans, double-click fits. The wheel is caught only inside the box.
export function useZoom() {
  const box = useRef<HTMLDivElement>(null);
  const [pose, setPose] = useState<Pose>(FIT);
  const size = () => {
    const r = box.current!.getBoundingClientRect();
    return { w: r.width, h: r.height, left: r.left, top: r.top };
  };
  const zoomBy = (factor: number, at?: { x: number; y: number }) => {
    const { w, h } = size();
    setPose((p) => zoomAt(p, factor, at?.x ?? w / 2, at?.y ?? h / 2, w, h));
  };
  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const wheel = (e: WheelEvent) => {
      e.preventDefault();
      const { left, top } = size();
      zoomBy(Math.exp(-e.deltaY * (e.ctrlKey ? 0.01 : 0.002)), { x: e.clientX - left, y: e.clientY - top });
    };
    el.addEventListener("wheel", wheel, { passive: false });
    return () => el.removeEventListener("wheel", wheel);
  }, []);
  const pointers = useRef(new Map<number, { x: number; y: number }>());
  const handlers = {
    onPointerDown: (e: PointerEvent) => {
      (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
      pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
    },
    onPointerMove: (e: PointerEvent) => {
      const before = pointers.current.get(e.pointerId);
      if (!before) return;
      const now = { x: e.clientX, y: e.clientY };
      const { w, h, left, top } = size();
      const others = [...pointers.current.entries()].filter(([id]) => id !== e.pointerId).map(([, p]) => p);
      pointers.current.set(e.pointerId, now);
      if (others.length) {
        const [o] = others;
        const was = Math.hypot(before.x - o.x, before.y - o.y);
        const is = Math.hypot(now.x - o.x, now.y - o.y);
        if (was > 0) zoomBy(is / was, { x: (now.x + o.x) / 2 - left, y: (now.y + o.y) / 2 - top });
      } else setPose((p) => panBy(p, now.x - before.x, now.y - before.y, w, h));
    },
    onPointerUp: (e: PointerEvent) => void pointers.current.delete(e.pointerId),
    onPointerCancel: (e: PointerEvent) => void pointers.current.delete(e.pointerId),
    onDblClick: () => setPose(FIT),
  };
  return { box, pose, handlers, zoomBy, fit: () => setPose(FIT) };
}
