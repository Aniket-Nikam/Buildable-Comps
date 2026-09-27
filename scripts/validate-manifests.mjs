import { readFile } from "node:fs/promises";
import Ajv2020 from "ajv/dist/2020.js";
import { loadManifests } from "./lib/registry.mjs";

const schema = JSON.parse(
  await readFile("registry/component.schema.json", "utf8"),
);
const ajv = new Ajv2020({ allErrors: true, strict: false });
const validate = ajv.compile(schema);
const entries = await loadManifests();
let failed = false;

for (const { manifestPath, manifest } of entries) {
  if (!validate(manifest)) {
    failed = true;
    console.error(
      `${manifestPath}: ${ajv.errorsText(validate.errors, { separator: "\n" })}`,
    );
  }
}

if (failed) process.exitCode = 1;
else console.log(`Validated ${entries.length} component manifests.`);
