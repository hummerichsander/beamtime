import assert from "node:assert/strict";
import { test } from "node:test";

import { commitUrl } from "../src/shell/lifecycle.ts";

test("a GitHub or GitLab remote, over ssh or https, links to the commit", () => {
  const github = { host: "GitHub", url: "https://github.com/acme/egnn/commit/9e41c2a" };
  assert.deepEqual(commitUrl("git@github.com:acme/egnn.git", "9e41c2a"), github);
  assert.deepEqual(commitUrl("https://github.com/acme/egnn.git", "9e41c2a"), github);
  assert.deepEqual(commitUrl("ssh://git@github.com:22/acme/egnn", "9e41c2a"), github);
  assert.deepEqual(commitUrl("https://user:token@github.com/acme/egnn", "9e41c2a"), github);
  assert.deepEqual(commitUrl("git@gitlab.com:lab/group/egnn.git", "9e41c2a"), {
    host: "GitLab",
    url: "https://gitlab.com/lab/group/egnn/-/commit/9e41c2a",
  });
  assert.equal(commitUrl("git@gitlab.example.org:lab/egnn.git", "abc")?.url, "https://gitlab.example.org/lab/egnn/-/commit/abc");
});

test("any other remote, a path or nothing has no link", () => {
  assert.equal(commitUrl("git@git.uni-heidelberg.de:thphys/egnn.git", "9e41c2a"), null);
  assert.equal(commitUrl("/srv/git/egnn.git", "9e41c2a"), null);
  assert.equal(commitUrl("", "9e41c2a"), null);
  assert.equal(commitUrl(null, "9e41c2a"), null);
});
