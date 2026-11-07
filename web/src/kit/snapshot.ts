// What a drawing in the frame leaves as a file: its SVG with the theme's colors written in, or
// its canvas, as PNG.

import type { Background } from "../bt/export.ts";

// the SVG inside `el` as a data URL, or null when it draws none.
export function svgOf(el: Element): string | null {
  const svg = el.querySelector("svg");
  if (!svg) return null;
  const copy = svg.cloneNode(true) as SVGSVGElement;
  const from = [svg, ...svg.querySelectorAll("*")];
  const to = [copy, ...copy.querySelectorAll("*")];
  from.forEach((node, i) => {
    const style = getComputedStyle(node);
    for (const prop of ["fill", "stroke", "font-family", "font-size"]) to[i].setAttribute(prop, style.getPropertyValue(prop));
  });
  const { width, height } = svg.getBoundingClientRect();
  copy.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  copy.setAttribute("width", String(width));
  copy.setAttribute("height", String(height));
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(new XMLSerializer().serializeToString(copy))}`;
}

// the canvas or SVG inside `el` as a PNG data URL at twice its size, or null when it draws neither.
export async function pngOf(el: Element, background: Background = "transparent"): Promise<string | null> {
  const canvas = el.querySelector("canvas");
  const svg = canvas ? null : svgOf(el);
  if (!canvas && !svg) return null;
  const source: CanvasImageSource = canvas ?? (await image(svg!));
  const box = canvas ? canvas.getBoundingClientRect() : el.querySelector("svg")!.getBoundingClientRect();
  const out = document.createElement("canvas");
  out.width = Math.max(1, Math.round(box.width * 2));
  out.height = Math.max(1, Math.round(box.height * 2));
  const ctx = out.getContext("2d")!;
  if (background === "white") {
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, out.width, out.height);
  }
  ctx.drawImage(source, 0, 0, out.width, out.height);
  return out.toDataURL("image/png");
}

function image(href: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("the SVG could not be turned into a PNG"));
    img.src = href;
  });
}
