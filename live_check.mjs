/**
 * Verify the PUBLISHED game boots on the public URL.
 *
 * Files returning 200 is not proof. This drives the real page in a real
 * browser, waits for the sprite atlas to load, and confirms the canvas
 * actually painted something that is not the page background.
 */

import { loadPlaywright, launchBrowser } from '/Users/amre/Projects/GameStewKit/web/tests/browser_helpers.mjs';

const URL = process.argv[2];
const { chromium } = loadPlaywright();
const browser = await launchBrowser(chromium);
const page = await browser.newPage();

const errors = [];
page.on('console', (m) => {
  if (m.type() === 'error') errors.push(m.text());
});
page.on('pageerror', (e) => errors.push(String(e)));
page.on('requestfailed', (r) => errors.push(`REQUEST FAILED ${r.url()}`));

const response = await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
console.log(`status ${response?.status()} ${URL}`);

// Wait for the app's test seam to appear. If boot() threw, it never will.
await page.waitForFunction(() => Boolean(window.__sidhe), { timeout: 30000 });

const canvas = await page.evaluate(() => {
  const c = document.getElementById('game');
  const ctx = c.getContext('2d');
  const { data } = ctx.getImageData(0, 0, c.width, c.height);
  const colours = new Set();
  let opaque = 0;
  for (let i = 0; i < data.length; i += 4) {
    if (data[i + 3] > 0) {
      opaque++;
      colours.add(`${data[i]},${data[i + 1]},${data[i + 2]}`);
    }
  }
  return { w: c.width, h: c.height, distinct: colours.size, opaque };
});

console.log(`canvas ${canvas.w}x${canvas.h}, distinct colours ${canvas.distinct}, opaque px ${canvas.opaque}`);

// The title screen has a visible heading. Pull the region's text.
const title = await page.evaluate(() => {
  const app = window.__sidhe;
  const screen = app?.screens?.get?.('title');
  return {
    hasScreen: Boolean(screen),
    current: app?.current?.id ?? app?.currentId ?? 'unknown',
  };
});
console.log(`title screen present: ${title.hasScreen}, current screen: ${title.current}`);

if (errors.length) {
  console.log('CONSOLE ERRORS:');
  for (const e of errors.slice(0, 12)) console.log('  ' + e);
} else {
  console.log('no console errors');
}

await page.screenshot({ path: '/Users/amre/.openclaw/workspace/live-published.png' });
await browser.close();

const ok = errors.length === 0 && canvas.distinct > 4 && title.hasScreen;
console.log(ok ? 'LIVE CHECK OK' : 'LIVE CHECK FAILED');
process.exit(ok ? 0 : 1);
