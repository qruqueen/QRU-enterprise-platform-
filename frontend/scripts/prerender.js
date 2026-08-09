#!/usr/bin/env node
/**
 * Build-time prerender for the public storefront.
 *
 * This app is a plain client-rendered CRA build with no server of its own — the
 * production build directory is served as static files. That means a crawler or
 * social link-preview bot that does not execute JavaScript only ever sees the
 * single static index.html, regardless of which route was requested (see Seo.js,
 * which sets per-route title/meta/OG/canonical tags client-side via useEffect).
 *
 * This script closes that gap without a framework or hosting migration: after
 * `npm run build`, it serves the built app locally, visits each known public
 * route in a real (headless) browser, lets the app's own React/Seo.js logic run
 * exactly as it does for a real visitor, and writes the resulting HTML to
 * build/<route>/index.html. Most static hosts (including the pattern this app
 * already uses) resolve a request for /book/some-slug to that exact file before
 * falling back to the SPA's index.html — so a non-JS crawler hitting that URL
 * gets fully-formed, route-specific HTML in the initial response.
 *
 * Runs as `npm run postbuild` (see package.json). Never fails the build: if the
 * public API isn't reachable at build time (e.g. a preview build with no backend
 * configured), it logs a warning and exits 0, and the normal SPA build output is
 * left untouched.
 */
const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");
const http = require("http");

const BUILD_DIR = path.join(__dirname, "..", "build");
const PORT = process.env.PRERENDER_PORT || 4183;
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const CHROMIUM_PATH = process.env.PRERENDER_CHROMIUM_PATH || undefined;

function log(...args) {
  console.log("[prerender]", ...args);
}
function warn(...args) {
  console.warn("[prerender]", ...args);
}

async function fetchJson(url) {
  const res = await fetch(url, { signal: AbortSignal.timeout(15000) });
  if (!res.ok) throw new Error(`${url} -> HTTP ${res.status}`);
  return res.json();
}

/** Site-wide fallback routes that always exist, independent of catalog data. */
const STATIC_ROUTES = ["/", "/catalog"];

async function collectRoutes() {
  if (!BACKEND_URL) {
    warn("REACT_APP_BACKEND_URL is not set — prerendering static routes only (/, /catalog).");
    return STATIC_ROUTES;
  }
  try {
    const data = await fetchJson(`${BACKEND_URL}/api/public/books`);
    const bookRoutes = (data.books || [])
      .filter((b) => b.slug)
      .map((b) => `/book/${b.slug}`);
    log(`Discovered ${bookRoutes.length} published book route(s) from the public API.`);
    return [...STATIC_ROUTES, ...bookRoutes];
  } catch (e) {
    warn(`Could not reach the public API (${e.message}) — prerendering static routes only.`);
    return STATIC_ROUTES;
  }
}

const MIME = {
  ".html": "text/html", ".js": "application/javascript", ".css": "text/css",
  ".json": "application/json", ".png": "image/png", ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg", ".svg": "image/svg+xml", ".ico": "image/x-icon",
  ".woff": "font/woff", ".woff2": "font/woff2", ".map": "application/json",
  ".txt": "text/plain", ".webmanifest": "application/manifest+json",
};

/** Minimal static server matching standard SPA-hosting behavior: serve the exact
 * file if one exists at this path, otherwise fall back to the root index.html so
 * client-side routing still works for any route not yet prerendered. */
function startStaticServer() {
  const server = http.createServer((req, res) => {
    const urlPath = decodeURIComponent(req.url.split("?")[0]);
    let filePath = path.join(BUILD_DIR, urlPath);
    if (!filePath.startsWith(BUILD_DIR)) filePath = BUILD_DIR; // guard traversal
    const candidates = [filePath, path.join(filePath, "index.html")];
    const found = candidates.find((p) => fs.existsSync(p) && fs.statSync(p).isFile());
    const servePath = found || path.join(BUILD_DIR, "index.html");
    const ext = path.extname(servePath);
    res.writeHead(200, { "Content-Type": MIME[ext] || "application/octet-stream" });
    fs.createReadStream(servePath).pipe(res);
  });
  return new Promise((resolve, reject) => {
    server.on("error", reject);
    server.listen(PORT, () => resolve(server));
  });
}

async function prerenderRoute(browser, route) {
  const page = await browser.newPage();
  const url = `http://127.0.0.1:${PORT}${route}`;
  await page.goto(url, { waitUntil: "networkidle", timeout: 30000 });
  // Give the app's own data-fetch -> Seo.js effect chain a moment to settle beyond
  // "network idle" (React state updates that follow the last response).
  await page.waitForTimeout(150);
  const html = await page.content();
  const outPath =
    route === "/"
      ? path.join(BUILD_DIR, "index.html")
      : path.join(BUILD_DIR, route.replace(/^\//, ""), "index.html");
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, html);
  const title = /<title>(.*?)<\/title>/s.exec(html)?.[1] ?? "(no title found)";
  log(`${route} -> ${path.relative(BUILD_DIR, outPath)}  title="${title}"`);
  await page.close();
}

async function main() {
  if (!fs.existsSync(BUILD_DIR)) {
    warn(`No build/ directory found at ${BUILD_DIR} — run "npm run build" first. Skipping.`);
    return;
  }

  const routes = await collectRoutes();
  let server, browser;
  try {
    server = await startStaticServer();
    browser = await chromium.launch({ executablePath: CHROMIUM_PATH });
    for (const route of routes) {
      try {
        await prerenderRoute(browser, route);
      } catch (e) {
        warn(`Failed to prerender ${route}: ${e.message} — leaving the default build output for this route.`);
      }
    }
  } catch (e) {
    warn(`Prerendering could not run (${e.message}). The build is unaffected; the SPA will still work normally for JS-executing visitors.`);
  } finally {
    if (browser) await browser.close();
    if (server) server.close();
  }
}

if (require.main === module) {
  main();
}

module.exports = { startStaticServer };
