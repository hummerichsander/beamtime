// Regenerate src/styles/tokens.css from src/beamtime/views/tokens.json: `npm run tokens`. With
// --check, fail instead of writing when the file is stale (`npm test` runs this).

import { readFile, writeFile } from "node:fs/promises";

const SOURCE = new URL("../../src/beamtime/views/tokens.json", import.meta.url);
const OUT = new URL("../src/styles/tokens.css", import.meta.url);

export function css(t) {
  const note = (usage) => (usage ? ` /* ${usage} */` : "");
  const colors = t.color.tokens;
  const colorLines = (id, notes) => colors.map((c) => `  --${c.name}: ${c.value[id]};${notes ? note(c.usage) : ""}`);
  const length = (family) => t[family].tokens.map((x) => `  --${x.name}: ${x.value};${note(x.usage)}`);
  const styles = t.type.groups.flatMap((g) => g.styles.map((s) => ({ ...s, family: s.family || g.family })));
  const shorthand = (s) => `${s.fontStyle === "italic" ? "italic " : ""}${s.fontWeight} ${s.fontSize}/${s.lineHeight} var(--font-${s.family})`;
  const classes = styles.flatMap((s) => [
    `.${s.name} {`,
    `  font-family: var(--font-${s.family});`,
    `  font-size: ${s.fontSize};`,
    `  line-height: ${s.lineHeight};`,
    `  font-weight: ${s.fontWeight};`,
    `  letter-spacing: ${s.letterSpacing};`,
    ...(s.fontStyle === "italic" ? ["  font-style: italic;"] : []),
    "}",
  ]);
  const faces = t.type.fonts.flatMap((f) => [
    "@font-face {",
    `  font-family: "${f.family}";`,
    `  src: url("${f.file}") format("woff2");`,
    `  font-weight: ${f.weight};`,
    `  font-style: ${f.style};`,
    "  font-display: swap;",
    "}",
  ]);
  return [
    "/* Beamtime: generated from src/beamtime/views/tokens.json by web/scripts/tokens.mjs. Do not edit by hand. */",
    ':root, [data-theme="light"] {',
    ...colorLines("light", true),
    "}",
    '[data-theme="dark"] {',
    ...colorLines("dark", false),
    "}",
    // before the page's script sets data-theme, the system's preference decides, so nothing flashes.
    "@media (prefers-color-scheme: dark) {",
    "  :root:not([data-theme]) {",
    ...colorLines("dark", false).map((l) => `  ${l}`),
    "    color-scheme: dark;",
    "  }",
    "}",
    ":root {",
    ...["spacing", "radius", "layout", "dash", "stroke"].flatMap(length),
    ...Object.entries(t.type.families).map(([k, v]) => `  --font-${k}: ${v};`),
    ...styles.map((s) => `  --text-${s.name}: ${shorthand(s)};${note(s.usage)}`),
    "}",
    ...classes,
    ...faces,
    "",
  ].join("\n");
}

const wanted = css(JSON.parse(await readFile(SOURCE, "utf8")));
if (process.argv.includes("--check")) {
  if ((await readFile(OUT, "utf8")) !== wanted) {
    console.error("src/styles/tokens.css is stale: run npm run tokens");
    process.exit(1);
  }
} else {
  await writeFile(OUT, wanted);
}
