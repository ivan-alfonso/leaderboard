#!/usr/bin/env node
/**
 * Translation validation script.
 * Compares all language files against the English reference to detect missing
 * or unexpected keys and reports coverage per language.
 *
 * Usage: node scripts/validate-i18n.js
 *   or:  npm run validate:i18n
 */

const fs = require("fs");
const path = require("path");

const LOCALES_DIR = path.join(__dirname, "..", "src", "i18n", "locales");
const REFERENCE_LANG = "en";
const NAMESPACES = ["common", "leaderboard"];

let hasErrors = false;

/**
 * Recursively collect all dot-separated key paths from an object.
 */
function collectKeys(obj, prefix = "") {
  const keys = [];
  for (const [k, v] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${k}` : k;
    if (v !== null && typeof v === "object" && !Array.isArray(v)) {
      keys.push(...collectKeys(v, fullKey));
    } else {
      keys.push(fullKey);
    }
  }
  return keys;
}

/**
 * Load and parse a JSON file, returning null on error.
 */
function loadJSON(filePath) {
  try {
    const content = fs.readFileSync(filePath, "utf-8");
    return JSON.parse(content);
  } catch (err) {
    console.error(`  ✗ JSON parse error in ${filePath}: ${err.message}`);
    hasErrors = true;
    return null;
  }
}

const languages = fs
  .readdirSync(LOCALES_DIR)
  .filter((d) => fs.statSync(path.join(LOCALES_DIR, d)).isDirectory());

console.log("=".repeat(60));
console.log("  Translation Validation Report");
console.log("=".repeat(60));
console.log(`  Languages found: ${languages.join(", ")}`);
console.log();

// Load reference (English) keys per namespace
const referenceKeys = {};
for (const ns of NAMESPACES) {
  const refPath = path.join(LOCALES_DIR, REFERENCE_LANG, `${ns}.json`);
  const refData = loadJSON(refPath);
  if (!refData) {
    console.error(`ERROR: Could not load reference file: ${refPath}`);
    process.exit(1);
  }
  referenceKeys[ns] = collectKeys(refData);
}

const totalReferenceKeys = NAMESPACES.reduce(
  (sum, ns) => sum + referenceKeys[ns].length,
  0
);
console.log(`  Reference (${REFERENCE_LANG}) keys: ${totalReferenceKeys} total`);
for (const ns of NAMESPACES) {
  console.log(`    ${ns}: ${referenceKeys[ns].length} keys`);
}
console.log();

// Validate each language
const summary = [];
for (const lang of languages) {
  if (lang === REFERENCE_LANG) continue;

  console.log(`Language: ${lang.toUpperCase()}`);
  console.log("-".repeat(40));

  let langTotal = 0;
  let langPresent = 0;
  let langMissing = 0;
  let langExtra = 0;

  for (const ns of NAMESPACES) {
    const filePath = path.join(LOCALES_DIR, lang, `${ns}.json`);
    const data = loadJSON(filePath);

    if (!data) {
      console.log(`  [${ns}] ✗ File missing or invalid: ${filePath}`);
      langMissing += referenceKeys[ns].length;
      langTotal += referenceKeys[ns].length;
      hasErrors = true;
      continue;
    }

    const langKeys = collectKeys(data);
    const refKeys = referenceKeys[ns];

    const missing = refKeys.filter((k) => !langKeys.includes(k));
    const extra = langKeys.filter((k) => !refKeys.includes(k));
    const present = refKeys.filter((k) => langKeys.includes(k));

    langTotal += refKeys.length;
    langPresent += present.length;
    langMissing += missing.length;
    langExtra += extra.length;

    const coverage = ((present.length / refKeys.length) * 100).toFixed(1);
    console.log(`  [${ns}] ${coverage}% coverage (${present.length}/${refKeys.length} keys)`);

    if (missing.length > 0) {
      hasErrors = true;
      console.log(`    Missing keys (${missing.length}):`);
      missing.forEach((k) => console.log(`      - ${k}`));
    }
    if (extra.length > 0) {
      console.log(`    Extra keys not in reference (${extra.length}):`);
      extra.forEach((k) => console.log(`      + ${k}`));
    }
  }

  const overallCoverage = ((langPresent / langTotal) * 100).toFixed(1);
  summary.push({ lang, coverage: overallCoverage, missing: langMissing, extra: langExtra });
  console.log(`  Overall: ${overallCoverage}% (${langPresent}/${langTotal} keys)`);
  if (langMissing > 0) console.log(`  ⚠  ${langMissing} missing key(s)`);
  if (langExtra > 0) console.log(`  ℹ  ${langExtra} extra key(s)`);
  console.log();
}

console.log("=".repeat(60));
console.log("  Summary");
console.log("=".repeat(60));
console.log(
  `  ${"Lang".padEnd(6)} ${"Coverage".padEnd(10)} ${"Missing".padEnd(10)} Extra`
);
console.log("  " + "-".repeat(38));
for (const { lang, coverage, missing, extra } of summary) {
  const status = missing > 0 ? "⚠" : "✓";
  console.log(
    `  ${status} ${lang.padEnd(5)} ${(coverage + "%").padEnd(10)} ${String(missing).padEnd(10)} ${extra}`
  );
}
console.log();

if (hasErrors) {
  console.log("✗ Validation FAILED — missing or invalid translations detected.");
  process.exit(1);
} else {
  console.log("✓ Validation PASSED — all languages are complete.");
  process.exit(0);
}
