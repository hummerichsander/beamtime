import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { effective, metricsOf, normalizeSeries, seriesCall } from "../src/bt/chart-settings.ts";
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
