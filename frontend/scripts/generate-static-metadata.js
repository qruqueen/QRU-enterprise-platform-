#!/usr/bin/env node
/**
 * Browserless postbuild metadata generator for the public storefront.
 *
 * This app is a plain client-rendered CRA build with no server of its own, so a
 * crawler or link-preview bot that doesn't execute JavaScript only ever sees the
 * single static index.html regardless of route — Seo.js sets per-route
 * title/description/canonical/OG tags client-side via useEffect, which such
 * clients never run. Emergent's production static hosting DOES serve a nested
 * build/<route>/index.html for a request to /<route> before falling back to the
 * root SPA shell (confirmed with Emergent Support), so writing route-specific
 * files here closes that gap for real.
 *
 * This does NOT use a browser. An earlier version of this script used Playwright
 * to render each route and capture the resulting HTML, but Emergent's production
 * build runs on a minimal Alpine/musl Node image with no Chromium and no glibc,
 * which Playwright's bundled browser requires — it cannot run there. This version
 * only ever touches the <head> of the already-built build/index.html as text: it
 * clones that real, finished template (so the exact hashed JS/CSS/asset
 * references the CRA build produced are preserved byte-for-byte) and replaces
 * only the <title> and a well-defined block of <meta>/<link> tags. It never
 * renders or executes the React app, and never invents an asset filename.
 *
 * Runs as `npm run postbuild`. Never fails the build: if the public API is
 * unreachable, times out, errors, or returns something unexpected, it logs a
 * clear summary and leaves the static routes (/ and /catalog) as the only
 * output — the SPA itself is completely unaffected either way for real visitors,
 * since every generated file is still a normal entry point into the same app.
 *
 * Config resolution: `npm run build` (craco build) loads .env files itself via
 * dotenv to embed REACT_APP_* values into the client bundle — but that happens
 * entirely inside react-scripts/craco's own process. `postbuild` is a separate
 * child process of npm and only inherits whatever was already exported into the
 * actual shell/CI environment; it never sees values that a *different* process
 * merely parsed out of a .env file. If the build environment supplies these
 * values via a .env file rather than a true exported variable, process.env.*
 * is empty here even though the very same build correctly embedded them into
 * the JS bundle a moment earlier. readConfig() below closes that gap by
 * checking process.env first, then reading the exact same .env files CRA
 * itself would (same precedence order), and only that one named key from
 * each — nothing else in the file is read, logged, or written anywhere.
 */
const fs = require("fs");
const path = require("path");

const BUILD_DIR = path.join(__dirname, "..", "build");
const INDEX_HTML = path.join(BUILD_DIR, "index.html");
const FRONTEND_DIR = path.join(__dirname, "..");
const KNOWN_PRODUCTION_SITE_URL = "https://qru-online.com";

/** Parse KEY=value lines only; ignores comments/blank lines. Never returns or
 * logs anything but the single value the caller asked for. */
function readKeyFromEnvFile(filePath, key) {
  if (!fs.existsSync(filePath)) return null;
  let content;
  try {
    content = fs.readFileSync(filePath, "utf8");
  } catch {
    return null;
  }
  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const eq = line.indexOf("=");
    if (eq === -1) continue;
    if (line.slice(0, eq).trim() !== key) continue;
    let val = line.slice(eq + 1).trim();
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    return val || null;
  }
  return null;
}

/** process.env first (a true exported variable always wins, matching how CRA
 * itself resolves config), then the same .env files CRA loads for a production
 * build, in CRA's own precedence order, so this script only ever reaches a
 * DIFFERENT value than the client bundle embedded if the build environment
 * genuinely disagrees with itself. */
function readConfig(key) {
  if (process.env[key]) return process.env[key];
  const nodeEnv = process.env.NODE_ENV || "production";
  const candidates = [
    path.join(FRONTEND_DIR, `.env.${nodeEnv}.local`),
    path.join(FRONTEND_DIR, ".env.local"),
    path.join(FRONTEND_DIR, `.env.${nodeEnv}`),
    path.join(FRONTEND_DIR, ".env"),
  ];
  for (const file of candidates) {
    const val = readKeyFromEnvFile(file, key);
    if (val) return val;
  }
  return null;
}

const BACKEND_URL = readConfig("REACT_APP_BACKEND_URL");
// PUBLIC_SITE_URL from process.env or .env, else the known production origin —
// canonical/og:url must always be absolute and unambiguous, never silently
// fall back to a relative path.
const SITE_URL = (readConfig("PUBLIC_SITE_URL") || KNOWN_PRODUCTION_SITE_URL).replace(/\/+$/, "");
const FETCH_TIMEOUT_MS = 8000;
const MAX_ATTEMPTS = 2;
const DEFAULT_DESC =
  "QRU Press™ is a premium educational publishing house. Every title is carefully researched, thoughtfully written, and verified to the Treasure Standard™.";
// Must match backend/routers/public_site.py's _slugify() output exactly: lowercase
// alnum segments joined by single hyphens, no leading/trailing hyphen.
const SAFE_SLUG_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

function log(...a) {
  console.log("[static-metadata]", ...a);
}
function warn(...a) {
  console.warn("[static-metadata]", ...a);
}

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function absUrl(maybeRelative, origin) {
  if (!maybeRelative) return null;
  return /^https?:\/\//i.test(maybeRelative) ? maybeRelative : `${origin || ""}${maybeRelative}`;
}

function safeSlug(raw) {
  return typeof raw === "string" && SAFE_SLUG_RE.test(raw) ? raw : null;
}

/** Clone the real built index.html and inject route-specific metadata into <head>.
 * Only ever touches <title> and a clearly-delimited block this function owns —
 * never the <script>/<link rel="stylesheet"> tags the CRA build emitted. Strips
 * its own previously-injected block first, so this is safe to run more than once
 * against the same file without accumulating duplicate tags. */
function withMetadata(template, { title, description, routePath, image }) {
  let html = template;
  if (title) html = html.replace(/<title>[\s\S]*?<\/title>/, `<title>${esc(title)}</title>`);

  html = html.replace(/<meta name="description"[^>]*>\s*/i, "");
  html = html.replace(/<!-- static-metadata:start -->[\s\S]*?<!-- static-metadata:end -->\n?/, "");

  const desc = description || DEFAULT_DESC;
  const canonical = SITE_URL ? absUrl(routePath, SITE_URL) : routePath;
  const ogImage = image ? absUrl(image, BACKEND_URL) : null;

  const tags = [`<meta name="description" content="${esc(desc)}">`];
  if (canonical) tags.push(`<link rel="canonical" href="${esc(canonical)}">`);
  tags.push(`<meta property="og:site_name" content="QRU Press™">`);
  tags.push(`<meta property="og:type" content="website">`);
  if (title) tags.push(`<meta property="og:title" content="${esc(title)}">`);
  tags.push(`<meta property="og:description" content="${esc(desc)}">`);
  if (canonical) tags.push(`<meta property="og:url" content="${esc(canonical)}">`);
  if (ogImage) tags.push(`<meta property="og:image" content="${esc(ogImage)}">`);
  tags.push(`<meta name="twitter:card" content="${ogImage ? "summary_large_image" : "summary"}">`);
  if (title) tags.push(`<meta name="twitter:title" content="${esc(title)}">`);
  tags.push(`<meta name="twitter:description" content="${esc(desc)}">`);
  if (ogImage) tags.push(`<meta name="twitter:image" content="${esc(ogImage)}">`);

  const block = `<!-- static-metadata:start -->\n    ${tags.join("\n    ")}\n    <!-- static-metadata:end -->\n`;
  return html.replace("</head>", `${block}  </head>`);
}

/** Resolve where a route's generated file goes, refusing anything that would
 * land outside build/ — the caller is responsible for only passing already
 * slug-validated paths, but this is a second, independent guard. */
function outputPathFor(routePath) {
  const rel = routePath === "/" ? "index.html" : path.join(routePath.replace(/^\//, ""), "index.html");
  const resolved = path.resolve(BUILD_DIR, rel);
  const buildRoot = path.resolve(BUILD_DIR) + path.sep;
  return resolved.startsWith(buildRoot) ? resolved : null;
}

function writeRoute(template, routePath, meta) {
  const outPath = outputPathFor(routePath);
  if (!outPath) {
    warn(`Refusing to write outside build/ for route "${routePath}".`);
    return false;
  }
  try {
    fs.mkdirSync(path.dirname(outPath), { recursive: true });
    fs.writeFileSync(outPath, withMetadata(template, { ...meta, routePath }));
    return true;
  } catch (e) {
    warn(`Failed writing ${routePath}: ${e.message}`);
    return false;
  }
}

async function fetchJsonWithRetry(url) {
  let lastErr;
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(FETCH_TIMEOUT_MS) });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      lastErr = e;
      if (attempt < MAX_ATTEMPTS) warn(`Book discovery attempt ${attempt}/${MAX_ATTEMPTS} failed (${e.message}), retrying...`);
    }
  }
  throw lastErr;
}

async function discoverBooks() {
  if (!BACKEND_URL) {
    warn("REACT_APP_BACKEND_URL is not set — skipping book discovery.");
    return { books: [], apiAvailable: false };
  }
  try {
    const data = await fetchJsonWithRetry(`${BACKEND_URL}/api/public/books`);
    if (!data || !Array.isArray(data.books)) throw new Error("unexpected response shape (books is not an array)");
    return { books: data.books, apiAvailable: true };
  } catch (e) {
    warn(`Book discovery failed after ${MAX_ATTEMPTS} attempt(s): ${e.message}`);
    return { books: [], apiAvailable: false };
  }
}

async function main() {
  if (!fs.existsSync(INDEX_HTML)) {
    warn(`No build/index.html found at ${INDEX_HTML} — run "npm run build" first. Skipping.`);
    return;
  }
  const template = fs.readFileSync(INDEX_HTML, "utf8");

  const staticOk =
    writeRoute(template, "/", {
      title: "QRU Press™ — Books that make hard ideas easy",
      description: DEFAULT_DESC,
    }) &&
    writeRoute(template, "/catalog", {
      title: "Explore All · QRU Press™",
      description: "Browse every authorized title and product from QRU Press™ — each one manufactured and verified to the Treasure Standard™.",
    });

  const { books, apiAvailable } = await discoverBooks();
  let written = 0;
  let failures = 0;
  for (const b of books) {
    const slug = safeSlug(b && b.slug);
    if (!slug) {
      failures++;
      warn(`Skipping a book with an unsafe or missing slug: ${JSON.stringify(b && b.slug)}`);
      continue;
    }
    const title = b.title ? `${b.title}${b.author ? ` — ${b.author}` : ""} · QRU Press™` : null;
    const ok = writeRoute(template, `/book/${slug}`, {
      title,
      description: b.excerpt || null,
      image: b.thumb_url || b.cover_url || null,
    });
    if (ok) written++;
    else failures++;
  }

  const summaryLines = [
    "Prerender summary:",
    `  Static routes: ${staticOk ? 2 : 0}`,
    `  Book routes: ${written}`,
  ];
  summaryLines.push(apiAvailable ? `  Failures: ${failures}` : `  Book API unavailable: yes`);
  log("\n" + summaryLines.join("\n"));
}

main().catch((e) => {
  warn(`Static metadata generation failed unexpectedly (${e.message}) — build output is unaffected.`);
});
