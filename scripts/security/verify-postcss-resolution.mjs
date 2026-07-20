import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const REQUIRED_VERSION = "8.5.20";
const FIRST_PATCHED_VERSION = "8.5.10";
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");

function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function versionAtLeast(actual, minimum) {
  const left = actual.split(".").map(Number);
  const right = minimum.split(".").map(Number);
  for (const index of [0, 1, 2]) {
    if (left[index] > right[index]) {
      return true;
    }
    if (left[index] < right[index]) {
      return false;
    }
  }
  return true;
}

const rootPackage = readJson(resolve(root, "package.json"));
const webPackage = readJson(resolve(root, "apps", "web", "package.json"));
const lock = readJson(resolve(root, "package-lock.json"));
const packages = lock.packages ?? {};

assert(
  rootPackage.overrides?.postcss === REQUIRED_VERSION,
  `Root override must pin postcss ${REQUIRED_VERSION}.`,
);
assert(
  webPackage.devDependencies?.postcss === REQUIRED_VERSION,
  `Web workspace must pin postcss ${REQUIRED_VERSION}.`,
);

const postcssEntries = Object.entries(packages).filter(([path]) =>
  path === "node_modules/postcss" || path.endsWith("/node_modules/postcss"),
);
assert(postcssEntries.length > 0, "No PostCSS package is recorded in package-lock.json.");
for (const [path, metadata] of postcssEntries) {
  assert(
    versionAtLeast(metadata.version, FIRST_PATCHED_VERSION),
    `Vulnerable PostCSS ${metadata.version} remains at ${path}.`,
  );
}
assert(
  packages["node_modules/postcss"]?.version === REQUIRED_VERSION,
  `Lockfile must resolve root PostCSS to ${REQUIRED_VERSION}.`,
);
assert(
  !packages["node_modules/next/node_modules/postcss"],
  "Next.js still has a nested PostCSS copy; the security override is ineffective.",
);

const nextPostcssPin = packages["node_modules/next"]?.dependencies?.postcss;
assert(
  nextPostcssPin === "8.4.31",
  "Next.js changed its PostCSS pin; reassess and remove the temporary override.",
);

const installedPostcss = resolve(root, "node_modules", "postcss", "package.json");
if (existsSync(installedPostcss)) {
  assert(
    readJson(installedPostcss).version === REQUIRED_VERSION,
    `Installed PostCSS must be ${REQUIRED_VERSION}.`,
  );
  assert(
    !existsSync(resolve(root, "node_modules", "next", "node_modules", "postcss", "package.json")),
    "A nested PostCSS copy exists in the installed Next.js tree.",
  );
}

console.log(
  JSON.stringify({
    status: "PASS",
    advisory: "GHSA-qx2v-qp2m-jg93",
    resolved_version: REQUIRED_VERSION,
    nested_vulnerable_copy: false,
  }),
);
