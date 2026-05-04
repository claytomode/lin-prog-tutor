/**
 * Capture README assets (model panel, 2D plot, 3D plot, tableau) against a running dev stack.
 *
 *   1. Stop stray processes on ports 8000 / 5173 if you want a clean API + UI.
 *   2. Terminal 1: from repo root — `bun run dev` (or API + Vite separately).
 *   3. Terminal 2: `bun run readme:screenshots:install` once, then `bun run readme:screenshots`.
 *
 * Env: README_SCREENSHOT_BASE_URL (default http://localhost:5173)
 */
import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");
const outDir = path.join(root, "docs", "readme");

/** Match Vite’s “Local:” URL so the dev server host matches (127.0.0.1 vs localhost can matter for some setups). */
const baseURL =
  process.env.README_SCREENSHOT_BASE_URL ?? "http://localhost:5173";
const apiURL = process.env.README_SCREENSHOT_API_URL ?? "http://127.0.0.1:8000";

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const LP_2D = `maximize 3 x + 2 y
subject to
x + y <= 4
x >= 0
y >= 0`;

const LP_3D = `maximize 3 x + 2 y + z
subject to
x + y + z <= 6
2 x + y <= 8
x <= 4`;

async function checkApi() {
  try {
    const r = await fetch(`${apiURL}/health`, { signal: AbortSignal.timeout(3000) });
    if (!r.ok) console.warn(`[readme:screenshots] GET ${apiURL}/health returned ${r.status} — analyze may fail.`);
  } catch {
    console.warn(
      `[readme:screenshots] Could not reach ${apiURL}/health — start the backend (port 8000) so Analyze works.`,
    );
  }
}

async function analyze(page, sourceText) {
  await page.locator("#src").fill(sourceText);
  await sleep(200);
  await page.locator("button.btn-analyze").click();
  await page.getByRole("heading", { name: "Solution" }).waitFor({ state: "visible", timeout: 90_000 });
  await page.waitForLoadState("networkidle", { timeout: 30_000 }).catch(() => {});
  await sleep(800);
}

async function waitPlotly(page) {
  // First draw dynamically imports plotly.js-dist-min; cold start can be slow.
  await page.waitForFunction(
    () =>
      !!document.querySelector(".plot svg") ||
      !!document.querySelector(".plot .js-plotly-plot") ||
      !!document.querySelector(".plot .plotly"),
    { timeout: 120_000 },
  );
  await sleep(1800);
}

async function main() {
  await mkdir(outDir, { recursive: true });
  await checkApi();

  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: 1320, height: 900 },
    deviceScaleFactor: 1,
  });

  try {
    await page.goto(baseURL, { waitUntil: "domcontentloaded", timeout: 60_000 });
    await page.locator("#preset").selectOption("default");
    await sleep(600);

    const modelPanel = page.locator("section.panel").filter({ has: page.locator("#src") });
    await modelPanel.screenshot({ path: path.join(outDir, "readme-model.png") });

    await analyze(page, LP_2D);
    await waitPlotly(page);
    await page.locator(".plot-wrap").screenshot({ path: path.join(outDir, "readme-plot-2d.png") });

    await analyze(page, LP_3D);
    await page.getByRole("heading", { name: "Feasible polyhedron (3D)" }).waitFor({ state: "visible", timeout: 30_000 });
    await waitPlotly(page);
    await page.locator(".plot-wrap").screenshot({ path: path.join(outDir, "readme-plot-3d.png") });

    const nextTableau = page.getByRole("button", { name: "Next tableau step" });
    for (let i = 0; i < 2; i++) {
      if (await nextTableau.isEnabled().catch(() => false)) {
        await nextTableau.click();
        await sleep(350);
      }
    }

    const tableauPanel = page.locator("section.panel.tableau-panel").filter({ has: page.locator("table.tableau") });
    await tableauPanel.first().scrollIntoViewIfNeeded();
    await sleep(500);
    await tableauPanel.first().screenshot({ path: path.join(outDir, "readme-tableau.png") });

    console.log(`Wrote PNGs under ${path.relative(root, outDir)}:`);
    console.log("  readme-model.png, readme-plot-2d.png, readme-plot-3d.png, readme-tableau.png");
  } finally {
    await browser.close();
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
