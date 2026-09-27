import { writeFile } from "node:fs/promises";
import { format } from "prettier";
import { loadManifests } from "./lib/registry.mjs";

const entries = await loadManifests();
const registry = {
  schemaVersion: 1,
  components: entries.map(({ manifestPath, manifest }) => ({
    ...manifest,
    manifestPath,
  })),
};
const output = await format(JSON.stringify(registry), { parser: "json" });
await writeFile("registry/components.json", output);
console.log(`Registry contains ${entries.length} components.`);
