import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { colorOptions, effective, metricsOf, normalizeSeries, seriesCall } from "../src/bt/chart-settings.ts";
import type { Node } from "../src/bt/index.ts";
import { prefsOf } from "../src/bt/prefs.ts";

type Case = {
  name: string;
  settings: Record<string, unknown>;
  node: Node;
  effective: Record<string, unknown>;
  series_params: Record<string, unknown>;
  frozen_key: Record<string, unknown>;
};

const cases: Case[] = JSON.parse(readFileSync(new URL("./fixtures/chart-settings.json", import.meta.url), "utf8"));

// what crosses the wire has no undefined values.
const wire = (v: unknown): unknown => JSON.parse(JSON.stringify(v));

for (const c of cases) {
  test(`the node of "${c.name}" gives its settings, series call and frozen key`, () => {
    const prefs = prefsOf(`fixture.${c.name}`).value;
    const eff = effective(c.node, prefs);
    assert.deepEqual(wire(eff), c.effective);

    const call = seriesCall(c.node, eff, { zoom: null, width: 600 });
    assert.deepEqual(wire(call.params), c.series_params);
    assert.equal(call.method, "series");

    assert.deepEqual(wire(normalizeSeries(call.params)), c.frozen_key);
  });

  test(`the settings of "${c.name}" are what its node gives back`, () => {
    const eff = effective(c.node, prefsOf(`fixture.${c.name}`).value) as Record<string, unknown>;
    for (const [key, value] of Object.entries(c.settings)) {
      if (key === "y") assert.deepEqual(metricsOf(c.node), value);
      else if (key === "steps" && (value as unknown[]).every((v) => v === null)) assert.equal(eff.steps, null);
      else assert.deepEqual(eff[key], value, key);
    }
  });
}

const plain: Node = {
  block: "line",
  id: "p",
  props: { y: "val/loss" },
  data: { main: { method: "series", params: { from: "g", y: ["val/loss"] }, scope: "g" } },
} as unknown as Node;

test("mean over seeds averages over the group's seed key", () => {
  const eff = { ...effective(plain, prefsOf("fixture.plain").value), by: "seeds" } as ReturnType<typeof effective>;
  assert.equal(seriesCall(plain, eff, { zoom: null, width: 600, seed: "config.trainer.seed" }).params.seeds, "config.trainer.seed");
  assert.equal(seriesCall(plain, eff, { zoom: null, width: 600 }).params.seeds, "config.seed");
});

test("a node's own seeds win over the group's seed key", () => {
  const own = { ...plain, data: { main: { ...plain.data!.main, params: { ...plain.data!.main.params, seeds: "config.rng_seed" } } } } as Node;
  const eff = effective(own, prefsOf("fixture.own").value);
  assert.equal(seriesCall(own, eff, { zoom: null, width: 600, seed: "config.trainer.seed" }).params.seeds, "config.rng_seed");
});

const RUN: [string, string][] = [["run.status", "status"], ["run.tags", "tags"], ["run.name", "name"], ["run.group", "folder"]];

test("color by offers a seed-only group the seed and the run fields", () => {
  const options = colorOptions({ config: { varying: ["config.seed"], aliases: {}, dropped: {} } });
  assert.deepEqual(options, [["Config", [["config.seed", "seed"]]], ["Run", RUN]]);
});

test("color by lists aliases and dropped keys with their reason", () => {
  const options = colorOptions({
    config: {
      varying: ["config.arch", "config.seed"],
      aliases: { "config.x.arch": "config.arch" },
      dropped: { "config.model": "config.arch" },
    },
  });
  assert.deepEqual(options[2], [
    "Same split",
    [["config.x.arch", "x.arch · same split as arch"], ["config.model", "model · set by arch"]],
  ]);
});

test("color by copes with an answer without dropped keys, or none yet", () => {
  assert.deepEqual(colorOptions({ config: { varying: ["config.lr"], aliases: { "config.a": "config.lr" } } }).map(([g]) => g), ["Config", "Run", "Same split"]);
  assert.deepEqual(colorOptions(undefined), [["Run", RUN]]);
});
