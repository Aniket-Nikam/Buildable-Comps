import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

export async function findManifestPaths(root = "components") {
  const results = [];
  async function walk(directory) {
    for (const entry of await readdir(directory, { withFileTypes: true })) {
      const fullPath = path.join(directory, entry.name);
      if (entry.isDirectory()) await walk(fullPath);
      if (entry.isFile() && entry.name === "component.json")
        results.push(fullPath);
    }
  }
  await walk(root);
  return results.sort();
}

export async function loadManifests(root = "components") {
  const paths = await findManifestPaths(root);
  return Promise.all(
    paths.map(async (manifestPath) => ({
      manifestPath: manifestPath.replaceAll("\\", "/"),
      manifest: JSON.parse(await readFile(manifestPath, "utf8")),
    })),
  );
}

export function analyzeDependencies(entries) {
  const ids = new Set(entries.map(({ manifest }) => manifest.id));
  const missing = [];
  const graph = new Map();
  for (const { manifest } of entries) {
    graph.set(manifest.id, manifest.requires);
    for (const dependency of manifest.requires) {
      if (!ids.has(dependency))
        missing.push({ component: manifest.id, dependency });
    }
  }

  const cycles = [];
  const visiting = new Set();
  const visited = new Set();
  function visit(id, trail) {
    if (visiting.has(id)) {
      const cycleStart = trail.indexOf(id);
      cycles.push([...trail.slice(cycleStart), id]);
      return;
    }
    if (visited.has(id)) return;
    visiting.add(id);
    for (const dependency of graph.get(id) ?? [])
      visit(dependency, [...trail, id]);
    visiting.delete(id);
    visited.add(id);
  }
  for (const id of graph.keys()) visit(id, []);
  return { missing, cycles };
}
