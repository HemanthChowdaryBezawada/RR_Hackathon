import { spawn } from "child_process";
import lighthouse from "lighthouse";
import * as chromeLauncher from "chrome-launcher";

const server = spawn("python3", ["-m", "http.server", "-d", "docs", "8000"]);

await new Promise((resolve) => setTimeout(resolve, 1000));

const chrome = await chromeLauncher.launch({ chromeFlags: ["--headless"] });
const options = {
  logLevel: "error",
  output: "json",
  onlyCategories: ["performance", "accessibility", "best-practices"],
  port: chrome.port,
  formFactor: "desktop",
  screenEmulation: {
    mobile: false,
    width: 1350,
    height: 940,
    deviceScaleFactor: 1,
    disabled: false
  },
  throttling: {
    rttMs: 40,
    throughputKbps: 10240,
    cpuSlowdownMultiplier: 1,
    requestLatencyMs: 0,
    downloadThroughputKbps: 0,
    uploadThroughputKbps: 0
  }
};

async function audit(url, name) {
  const runnerResult = await lighthouse(url, options);
  const categories = runnerResult.lhr.categories;
  const perf = Math.round((categories.performance?.score || 0) * 100);
  const a11y = Math.round((categories.accessibility?.score || 0) * 100);
  const bp = Math.round((categories["best-practices"]?.score || 0) * 100);
  console.log(`Lighthouse ${name}: Performance: ${perf}, Accessibility: ${a11y}, Best Practices: ${bp}`);
  return { perf, a11y, bp };
}

try {
  await audit("http://127.0.0.1:8000/#/overview", "Overview");
  await audit("http://127.0.0.1:8000/#/rankings", "Rankings");
} finally {
  await chrome.kill();
  server.kill();
}
