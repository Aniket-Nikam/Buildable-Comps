import { analyzeDependencies, loadManifests } from "./lib/registry.mjs";

const entries = await loadManifests();
const ids = entries.map(({ manifest }) => manifest.id);
if (new Set(ids).size !== ids.length)
  throw new Error("Component ids must be unique.");

const { missing, cycles } = analyzeDependencies(entries);
for (const item of missing)
  console.error(`${item.component} requires missing ${item.dependency}`);
for (const cycle of cycles)
  console.error(`Dependency cycle: ${cycle.join(" -> ")}`);
if (missing.length || cycles.length) process.exitCode = 1;
else console.log(`Dependency graph is valid for ${entries.length} components.`);
