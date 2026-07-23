#!/usr/bin/env node
// render_asset.mjs — deterministic HTML -> PNG for fixed-size social assets.
//
// Adapted from frontend-slides scripts/export-pdf.sh (MIT (c) 2025 Zara Zhang):
// same local-HTTP-server + networkidle + document.fonts.ready + per-element
// screenshot shape, re-cut for arbitrary fixed-size canvases instead of slides.
//
// Usage:
//   node render_asset.mjs <input.html> <output.png> \
//     [--selector .canvas] [--width 1080] [--height 1440] [--scale 2] [--wait 400]
//
// Behavior:
//   --selector given  -> screenshot each matching element. One match writes
//                        <output.png>; N matches write <output>-01.png ... -NN.png.
//   no --selector     -> screenshot the viewport at width x height.
//   --scale (default 2) = deviceScaleFactor, so a 1080x1440 canvas exports
//   2160x2880 physical pixels (platforms downsample; text stays crisp).
//
// Playwright resolution: plain import first, then $PLAYWRIGHT_DIR/node_modules.
// One-time bootstrap if neither works:
//   mkdir -p ~/.cache/pwenv && cd ~/.cache/pwenv \
//     && npm i playwright && npx playwright install chromium
//   PLAYWRIGHT_DIR=~/.cache/pwenv node render_asset.mjs ...

import { createServer } from 'http';
import { readFileSync } from 'fs';
import { dirname, join, extname, basename, resolve } from 'path';
import { pathToFileURL } from 'url';

async function loadChromium() {
  try { return (await import('playwright')).chromium; } catch {}
  const base = process.env.PLAYWRIGHT_DIR;
  if (base) {
    try {
      const url = pathToFileURL(
        join(resolve(base), 'node_modules', 'playwright', 'index.mjs')).href;
      return (await import(url)).chromium;
    } catch {}
  }
  console.error(
    'ERROR: playwright not importable.\n' +
    'Bootstrap once:  mkdir -p ~/.cache/pwenv && cd ~/.cache/pwenv' +
    ' && npm i playwright && npx playwright install chromium\n' +
    'Then run with:   PLAYWRIGHT_DIR=~/.cache/pwenv node render_asset.mjs ...');
  process.exit(2);
}

// ---- args ------------------------------------------------------------------
const argv = process.argv.slice(2);
const positional = [];
const opts = { width: 1080, height: 1440, scale: 2, wait: 400, selector: null };
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--selector') opts.selector = argv[++i];
  else if (a === '--width') opts.width = parseInt(argv[++i], 10);
  else if (a === '--height') opts.height = parseInt(argv[++i], 10);
  else if (a === '--scale') opts.scale = parseFloat(argv[++i]);
  else if (a === '--wait') opts.wait = parseInt(argv[++i], 10);
  else positional.push(a);
}
const [inputHtml, outputPng] = positional;
if (!inputHtml || !outputPng) {
  console.error('Usage: node render_asset.mjs <input.html> <output.png> ' +
    '[--selector .canvas] [--width W] [--height H] [--scale 2] [--wait ms]');
  process.exit(1);
}
const inputAbs = resolve(inputHtml);
const serveDir = dirname(inputAbs);
const htmlFile = basename(inputAbs);

// ---- static server (fonts/assets need HTTP, not file://) --------------------
const MIME = {
  '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
  '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.svg': 'image/svg+xml',
  '.webp': 'image/webp', '.woff': 'font/woff', '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
};
const server = createServer((req, res) => {
  try {
    const p = join(serveDir, decodeURIComponent(req.url) === '/'
      ? htmlFile : decodeURIComponent(req.url));
    res.writeHead(200, { 'Content-Type': MIME[extname(p).toLowerCase()] || 'application/octet-stream' });
    res.end(readFileSync(p));
  } catch { res.writeHead(404); res.end('Not found'); }
});
const port = await new Promise((r) => server.listen(0, () => r(server.address().port)));

// ---- render ------------------------------------------------------------------
const chromium = await loadChromium();
const browser = await chromium.launch();
try {
  const page = await browser.newPage({
    viewport: { width: opts.width, height: opts.height },
    deviceScaleFactor: opts.scale,
  });
  await page.goto(`http://localhost:${port}/`, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready); // CRITICAL: webfonts settle
  await page.waitForTimeout(opts.wait);

  if (opts.selector) {
    const els = await page.$$(opts.selector);
    if (els.length === 0) {
      console.error(`ERROR: no elements match selector "${opts.selector}"`);
      process.exit(1);
    }
    if (els.length === 1) {
      await els[0].screenshot({ path: outputPng });
      console.log(outputPng);
    } else {
      const stem = outputPng.replace(/\.png$/i, '');
      for (let i = 0; i < els.length; i++) {
        await els[i].scrollIntoViewIfNeeded();
        const p = `${stem}-${String(i + 1).padStart(2, '0')}.png`;
        await els[i].screenshot({ path: p });
        console.log(p);
      }
    }
  } else {
    await page.screenshot({ path: outputPng, fullPage: false });
    console.log(outputPng);
  }
} finally {
  await browser.close();
  server.close();
}
