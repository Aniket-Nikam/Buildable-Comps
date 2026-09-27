import assert from "node:assert/strict";
import test from "node:test";
import { analyzeDependencies } from "./lib/registry.mjs";

const entry = (id, requires = []) => ({ manifest: { id, requires } });

test("reports missing dependencies", () => {
  const result = analyzeDependencies([entry("core.one", ["core.missing"])]);
  assert.deepEqual(result.missing, [
    { component: "core.one", dependency: "core.missing" },
  ]);
});

test("reports circular dependencies", () => {
  const result = analyzeDependencies([
    entry("core.one", ["core.two"]),
    entry("core.two", ["core.one"]),
  ]);
  assert.deepEqual(result.cycles, [["core.one", "core.two", "core.one"]]);
});
