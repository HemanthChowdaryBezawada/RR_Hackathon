import { test, expect } from "@playwright/test";

const widths = [1440, 1024, 768, 390];
const routes = ["#/overview", "#/rankings", "#/player/5553", "#/pressure"];

test.describe("Responsive Visual & Overflow Pass", () => {
  for (const w of widths) {
    test(`Width ${w}px layout check`, async ({ page }) => {
      await page.setViewportSize({ width: w, height: 900 });

      for (const route of routes) {
        await page.goto(`/${route}`);
        await page.waitForLoadState("networkidle");

        const overflowInfo = await page.evaluate(() => {
          const docW = document.documentElement.clientWidth;
          const scrollW = document.documentElement.scrollWidth;
          const bad = [];
          if (scrollW > docW) {
            document.querySelectorAll("*").forEach(el => {
              const r = el.getBoundingClientRect();
              if (r.right > docW + 1) {
                bad.push(`${el.tagName}#${el.id}.${el.className.slice(0, 30)} (right: ${Math.round(r.right)})`);
              }
            });
          }
          return { isOver: scrollW > docW, docW, scrollW, bad: bad.slice(0, 4) };
        });

        if (overflowInfo.isOver) {
          console.log(`Overflow on ${route} at ${w}px:`, overflowInfo);
        }
        expect(overflowInfo.isOver).toBe(false);
      }
    });
  }
});
