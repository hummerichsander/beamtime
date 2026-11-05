import assert from "node:assert/strict";
import { test } from "node:test";

import { configTree, filterTree, leaves, varyingKeys } from "../src/bt/configtree.ts";

const config = {
  arm: "large",
  seed: 1,
  hparams: { egnn: { vector_channels: 32 } },
  hydrantic: { seed: 1, trainer: { max_epochs: 5, root: "/scratch/run" }, "a.b": [1, 2, 3] },
};

test("single-child chains read as one name", () => {
  const tree = configTree(config);
  assert.deepEqual(tree.map((n) => n.name), ["arm", "seed", "hparams.egnn.vector_channels", "hydrantic"]);
  const hydrantic = tree[3];
  assert.deepEqual(hydrantic.children.map((n) => n.name), ["seed", "trainer", "a.b"]);
  assert.equal(hydrantic.children[2].path, 'hydrantic["a.b"]');
  assert.equal(leaves(tree), 7);
});

test("what varies is marked up the branches", () => {
  const tree = configTree(config, new Set(["hparams.egnn.vector_channels", "hydrantic.seed"]));
  assert.deepEqual(tree.map((n) => n.varies), [false, false, true, true]);
  assert.deepEqual(filterTree(tree, "", true).map((n) => n.name), ["hparams.egnn.vector_channels", "hydrantic"]);
  assert.deepEqual(filterTree(tree, "", true)[1].children.map((n) => n.name), ["seed"]);
});

test("the filter matches keys and values, in any case", () => {
  const tree = configTree(config);
  assert.deepEqual(filterTree(tree, "MAX_EPOCHS", false)[0].children.map((n) => n.name), ["trainer"]);
  assert.deepEqual(filterTree(tree, "large", false).map((n) => n.name), ["arm"]);
  assert.deepEqual(filterTree(tree, "nothing", false), []);
});

test("varying keys come from a keys answer, also for long sweeps", () => {
  const keys = {
    config: {
      rows: [
        ["config.lr", 12, { min: 1e-5, max: 2e-2, distinct: 12 }],
        ["config.seed", 3, [0, 1, 2]],
        ["config.model", 3, ["resnet18"]],
      ] as [string, number, unknown][],
    },
  };
  assert.deepEqual(varyingKeys(keys), ["lr", "seed"]);
  assert.deepEqual(varyingKeys(null), []);
});
