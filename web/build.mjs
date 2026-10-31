// Bundle the frontend into the Python package: src/beamtime/serve/static.

import { build } from "esbuild";
import { copyFile, mkdir, readFile, rm } from "node:fs/promises";

const out = "../src/beamtime/serve/static";
await rm(out, { recursive: true, force: true });
await mkdir(out, { recursive: true });
await build({
  entryPoints: { app: "src/main.ts", kit: "src/kit/frame.ts" },
  bundle: true,
  splitting: true,
  format: "esm",
  minify: true,
  target: "es2022",
  outdir: out,
  entryNames: "[name]",
  chunkNames: "chunks/[name]-[hash]",
  legalComments: "none",
  logLevel: "warning",
  define: { __EXPORT__: "false" },
});
// pages exported as static HTML open from disk, where browsers load no ES modules: the page and the
// custom-block kit as classic scripts, libraries included (beamtime export --html).
await build({
  entryPoints: { main: "src/main.ts", kit: "src/kit/frame.ts" },
  bundle: true,
  format: "iife",
  minify: true,
  target: "es2022",
  outdir: `${out}/export`,
  legalComments: "none",
  logLevel: "warning",
  define: { __EXPORT__: "true" },
});
// KaTeX's stylesheet, loaded by the Markdown renderer when a text has math; woff2 fonts only.
const woff2Only = {
  name: "woff2-only",
  setup(b) {
    b.onLoad({ filter: /katex\.min\.css$/ }, async (args) => ({
      contents: (await readFile(args.path, "utf8")).replace(/,url\([^)]*\.(woff|ttf)\) format\("(woff|truetype)"\)/g, ""),
      loader: "css",
    }));
  },
};
await build({
  entryPoints: { katex: "node_modules/katex/dist/katex.min.css" },
  bundle: true,
  minify: true,
  outdir: out,
  assetNames: "fonts/[name]-[hash]",
  loader: { ".woff2": "file" },
  plugins: [woff2Only],
  logLevel: "warning",
});
await copyFile("src/index.html", `${out}/index.html`);
await mkdir(`${out}/kit`, { recursive: true });
await copyFile("src/kit/frame.html", `${out}/kit/frame.html`);
