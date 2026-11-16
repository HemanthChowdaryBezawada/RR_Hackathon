import { test, expect } from "@playwright/test";
import fs from "fs";
import path from "path";

const meta = JSON.parse(fs.readFileSync(path.resolve("docs/data/meta.json"), "utf8"));
const batters = JSON.parse(fs.readFileSync(path.resolve("docs/data/players_batters.json"), "utf8"));
const bowlers = JSON.parse(fs.readFileSync(path.resolve("docs/data/players_bowlers.json"), "utf8"));

const FAKE_VALUES = ["0.864", "0.141", "182,410", "182410", "r = 0.78", "tau = 4.18", "PI: 0.88"];
const ALL_ROUTES = [
  "#/overview",
  "#/rankings",
  `#/player/${batters[0].player_id}`,
  `#/player/${bowlers[0].player_id}`,
  `#/compare?ids=${batters[0].player_id},${batters[1].player_id},${batters[2].player_id}`,
  "#/pressure",
  "#/validation",
  "#/method"
];

test.describe("SupeRR Dashboard E2E Tests", () => {
  test("1. No console errors on any route", async ({ page }) => {
    const consoleErrors = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text());
      }
    });

    for (const route of ALL_ROUTES) {
      await page.goto(`/${route}`);
      await page.waitForLoadState("networkidle");
      await page.waitForTimeout(100);
    }

    expect(consoleErrors).toEqual([]);
  });

  test("2. Overview shows counts equal to meta.counts and top 10 names equal first 10 JSON names", async ({ page }) => {
    await page.goto("/#/overview");
    await page.waitForLoadState("networkidle");

    const bodyText = await page.textContent("body");
    // Verify matches count from meta
    expect(bodyText).toContain(String(meta.counts.usable_matches));

    // Verify first 10 batter names appear
    for (let i = 0; i < 10; i++) {
      expect(bodyText).toContain(batters[i].name);
    }
    // Verify first 10 bowler names appear
    for (let i = 0; i < 10; i++) {
      expect(bodyText).toContain(bowlers[i].name);
    }
  });

  test("3. Player deep dive: first player in each list shows name & rating; invalid id shows Player not found", async ({ page }) => {
    // First batter
    const b0 = batters[0];
    await page.goto(`/#/player/${b0.player_id}`);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("h1")).toContainText(b0.name);
    await expect(page.locator("body")).toContainText(b0.rating.toFixed(1));

    // First bowler
    const w0 = bowlers[0];
    await page.goto(`/#/player/${w0.player_id}`);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("h1")).toContainText(w0.name);
    await expect(page.locator("body")).toContainText(w0.rating.toFixed(1));

    // Invalid ID
    await page.goto("/#/player/99999999");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("h1")).toContainText("Player not found");
  });

  test("4. Rankings: search filter, sorting and CSV export", async ({ page }) => {
    await page.goto("/#/rankings");
    await page.waitForLoadState("networkidle");

    // Typing zzzz yields zero rows and empty state
    const searchInput = page.locator("#filter-player-search");
    await searchInput.fill("zzzz");
    await expect(page.locator("text=No players match the criteria")).toBeVisible();

    // Typing first word of a real name yields at least one row
    const firstWord = batters[0].name.split(" ")[0];
    await searchInput.fill(firstWord);
    await expect(page.locator("#rankings-tbody tr")).not.toHaveCount(0);
    await expect(page.locator("#rankings-tbody")).toContainText(batters[0].name);

    // Clear search
    await searchInput.fill("");

    // Sorting by rating ascending reverses the order
    // Default is sorted by rank ascending (highest rating first)
    const ratingHeader = page.locator("th[data-sort='rating']");
    await ratingHeader.click(); // desc
    await ratingHeader.click(); // asc (lowest rating first)
    
    // In ascending rating sort, the lowest rating appears in the first row
    const firstRowText = await page.locator("#rankings-tbody tr").first().textContent();
    // Lowest rated qualified batter is near bottom of batters list
    const lowestBatter = batters[batters.length - 1];
    expect(firstRowText).toContain(lowestBatter.name);

    // Reset sort back to rank asc
    await page.locator("th[data-sort='rank']").click();

    // CSV export test: trigger download and verify row count
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.click("#btn-export-csv")
    ]);
    const downloadPath = await download.path();
    const csvContent = fs.readFileSync(downloadPath, "utf8");
    const csvLines = csvContent.trim().split("\n");
    // Header line + 1 line per filtered player
    expect(csvLines.length).toBe(batters.length + 1);
  });

  test("5. Compare: shows three names; adding fourth is blocked", async ({ page }) => {
    const p1 = batters[0];
    const p2 = batters[1];
    const p3 = batters[2];
    const p4 = batters[3];

    await page.goto(`/#/compare?ids=${p1.player_id},${p2.player_id},${p3.player_id}`);
    await page.waitForLoadState("networkidle");

    const bodyText = await page.textContent("body");
    expect(bodyText).toContain(p1.name);
    expect(bodyText).toContain(p2.name);
    expect(bodyText).toContain(p3.name);

    // Try to add fourth player
    const searchInput = page.locator("#compare-search-input");
    await searchInput.fill(p4.name);
    await page.waitForSelector("#compare-search-results");

    // Click candidate
    await page.locator(`#compare-search-results [data-id='${p4.player_id}']`).click();

    // Verify limit warning appears
    await expect(page.locator("#compare-limit-warning")).toBeVisible();

    // Verify URL still only has 3 players
    expect(page.url()).not.toContain(String(p4.player_id));
  });

  test("6. No element or text containing Alternate, Primary list or a list switch", async ({ page }) => {
    for (const route of ALL_ROUTES) {
      await page.goto(`/${route}`);
      await page.waitForLoadState("networkidle");

      const bodyText = await page.textContent("body");
      expect(bodyText).not.toMatch(/Alternate list/i);
      expect(bodyText).not.toMatch(/Primary list/i);

      // Check header dropdown switch does not exist
      await expect(page.locator("#btn-list-dropdown")).toHaveCount(0);
      await expect(page.locator("#list-dropdown-menu")).toHaveCount(0);
    }
  });

  test("7. Deleting pressure.json makes Pressure page show Not available without crashing", async ({ page }) => {
    // We can simulate missing pressure.json by routing pressure.json to 404
    await page.route("**/data/pressure.json", (route) => route.abort());

    await page.goto("/#/pressure");
    await page.waitForLoadState("networkidle");

    // Should not crash, and should show Not available in this build
    await expect(page.locator("body")).toContainText("Not available in this build");
  });

  test("8. No text on any page matches fabricated values in check_dashboard.py", async ({ page }) => {
    test.setTimeout(60000);
    for (const route of ALL_ROUTES) {
      await page.goto(`/${route}`);
      await page.waitForLoadState("networkidle");

      const text = await page.textContent("body");
      for (const val of FAKE_VALUES) {
        expect(text).not.toContain(val);
      }
    }
  });
});
