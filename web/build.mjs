// Bundle the frontend into the Python package: src/beamtime/serve/static.

import { build } from "esbuild";
import { copyFile, mkdir, rm } from "node:fs/promises";

const out = "../src/beamtime/serve/static";
await rm(out, { recursive: true, force: true });
await mkdir(out, { recursive: true });
await build({
  entryPoints: { app: "src/main.ts" },
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
});
await copyFile("src/index.html", `${out}/index.html`);
