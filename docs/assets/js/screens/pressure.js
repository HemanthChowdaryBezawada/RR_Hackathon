import { n, pct, esc, notAvailableCard } from "../format.js";
import { chart } from "../charts.js";

export function renderPressure(container, state, data) {
  const pressureData = data?.pressure;
  if (!pressureData) {
    container.innerHTML = notAvailableCard("Pressure Context Data");
    return;
  }

  const def = pressureData.definition || {};
  const highLow = pressureData.high_low || [];
  const heatmapData = pressureData.heatmap || {};
  const traces = pressureData.traces || [];

  // Local interactive state
  let selectedInnings = "innings2";
  let selectedMetric = "pi"; // 'pi' or 'high_share'
  let selectedTraceIdx = 0;

  function renderView() {
    const hasHeatmap = heatmapData && (heatmapData.innings1 || heatmapData.innings2);
    const hasHighLow = highLow && highLow.length > 0;
    const hasTraces = traces && traces.length > 0;

    const highRow = highLow.find(r => r.set === "HIGH") || {};
    const lowRow = highLow.find(r => r.set === "LOW") || {};

    container.innerHTML = `
      <div class="p-6 sm:p-8 max-w-[1600px] mx-auto w-full flex flex-col gap-6">
        
        <!-- Screen Header -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <span class="text-[10px] font-bold text-[#9D174D] uppercase tracking-wider bg-[#FFF0F7] px-2 py-0.5 rounded-md border border-[#E6007E]/20">
                CONTEXTUAL TAXONOMY
              </span>
              <span class="text-xs text-slate-400 font-medium">• Pre-Ball Valuation Engine</span>
            </div>
            <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight" tabindex="-1">
              Pressure Definition &amp; Context
            </h1>
            <p class="text-xs sm:text-sm text-slate-500 mt-1 max-w-3xl leading-relaxed">
              How is situational leverage quantified before each delivery? Isolating match state tension completely independent of player execution.
            </p>
          </div>
        </div>

        <!-- 1. Mathematical Formulation & Definition Card -->
        <div class="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-card flex flex-col gap-5">
          <div class="flex items-center justify-between pb-3 border-b border-slate-100">
            <h2 class="text-sm font-bold text-slate-900">Pre-Delivery Leverage Formulation</h2>
            <span class="px-2 py-0.5 rounded-md bg-teal-50 text-teal-700 text-[10px] font-bold border border-teal-200">
              Zero-Leakage Guarantee
            </span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="p-4 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-1">
              <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Weight: ${def.weights?.leverage_percentile != null ? (def.weights.leverage_percentile * 100).toFixed(0) : 60}%</div>
              <div class="text-sm font-bold text-slate-900">Leverage Gradient (LI)</div>
              <p class="text-xs text-slate-500 mt-1">Maximum theoretical win-probability swing potential from current state.</p>
            </div>
            <div class="p-4 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-1">
              <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Weight: ${def.weights?.closeness != null ? (def.weights.closeness * 100).toFixed(0) : 25}%</div>
              <div class="text-sm font-bold text-slate-900">Game Closeness</div>
              <p class="text-xs text-slate-500 mt-1">Proximity of current win probability to 50-50 parity.</p>
            </div>
            <div class="p-4 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-1">
              <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Weight: ${def.weights?.scarcity != null ? (def.weights.scarcity * 100).toFixed(0) : 15}%</div>
              <div class="text-sm font-bold text-slate-900">Resource Scarcity</div>
              <p class="text-xs text-slate-500 mt-1">Deliveries remaining weighted against wickets in hand and required run rate.</p>
            </div>
          </div>

          <div class="p-3.5 rounded-xl bg-[#FFF0F7] border border-[#E6007E]/20 text-xs text-slate-700 font-mono">
            <strong>Formula:</strong> ${esc(def.formula || "PI = 0.60*pct(LI) + 0.25*closeness + 0.15*scarcity")}
          </div>
        </div>

        <!-- 2. HIGH vs LOW Performance Divergence (from high_low) -->
        ${
          hasHighLow
            ? `
              <div class="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-card flex flex-col gap-5">
                <div class="flex items-center justify-between pb-3 border-b border-slate-100">
                  <h2 class="text-sm font-bold text-slate-900">High-Pressure vs Ordinary Situations</h2>
                  <span class="text-xs text-slate-400 font-medium">Empirical divergence across match pressure strata</span>
                </div>

                <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div class="p-4 rounded-xl bg-slate-50 border border-slate-100">
                    <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">WP Swing / Ball</span>
                    <div class="text-xl font-extrabold text-[#E6007E] font-mono mt-1">
                      ${highRow.mean_abs_dWP ? `${(highRow.mean_abs_dWP * 100).toFixed(2)}%` : "—"}
                    </div>
                    <span class="text-[11px] text-slate-500">Low: ${lowRow.mean_abs_dWP ? `${(lowRow.mean_abs_dWP * 100).toFixed(2)}%` : "—"}</span>
                  </div>

                  <div class="p-4 rounded-xl bg-slate-50 border border-slate-100">
                    <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Undecided Share</span>
                    <div class="text-xl font-extrabold text-slate-900 font-mono mt-1">
                      ${highRow.undecided_share ? pct(highRow.undecided_share) : "—"}
                    </div>
                    <span class="text-[11px] text-slate-500">Low: ${lowRow.undecided_share ? pct(lowRow.undecided_share) : "—"}</span>
                  </div>

                  <div class="p-4 rounded-xl bg-slate-50 border border-slate-100">
                    <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Wicket Hazard Rate</span>
                    <div class="text-xl font-extrabold text-slate-900 font-mono mt-1">
                      ${highRow.wicket_rate ? pct(highRow.wicket_rate, 1) : "—"}
                    </div>
                    <span class="text-[11px] text-slate-500">Low: ${lowRow.wicket_rate ? pct(lowRow.wicket_rate, 1) : "—"}</span>
                  </div>

                  <div class="p-4 rounded-xl bg-slate-50 border border-slate-100">
                    <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Dot Ball Share</span>
                    <div class="text-xl font-extrabold text-slate-900 font-mono mt-1">
                      ${highRow.dot_pct ? pct(highRow.dot_pct, 1) : "—"}
                    </div>
                    <span class="text-[11px] text-slate-500">Low: ${lowRow.dot_pct ? pct(lowRow.dot_pct, 1) : "—"}</span>
                  </div>
                </div>
              </div>
            `
            : notAvailableCard("High vs Low Pressure Comparison")
        }

        <!-- 3. Pressure Heatmap Card -->
        ${
          hasHeatmap
            ? `
              <div class="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-card flex flex-col gap-4">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                  <div>
                    <h2 class="text-sm font-bold text-slate-900">Pressure Index Heatmap</h2>
                    <span class="text-xs text-slate-400">Cross-tabulated across Overs (1–20) vs Wickets Lost (0–9)</span>
                  </div>
                  
                  <!-- Heatmap Controls -->
                  <div class="flex items-center gap-2 flex-wrap">
                    <!-- Innings toggle -->
                    <div class="flex items-center p-0.5 bg-slate-100 rounded-xl text-xs font-semibold">
                      <button id="btn-hm-inn1" class="px-3 py-1 rounded-lg transition-colors ${selectedInnings === "innings1" ? "bg-white text-slate-900 shadow-xs" : "text-slate-500 hover:text-slate-900"}">
                        Innings 1
                      </button>
                      <button id="btn-hm-inn2" class="px-3 py-1 rounded-lg transition-colors ${selectedInnings === "innings2" ? "bg-white text-slate-900 shadow-xs" : "text-slate-500 hover:text-slate-900"}">
                        Innings 2 (Chases)
                      </button>
                    </div>

                    <!-- Metric toggle -->
                    <div class="flex items-center p-0.5 bg-slate-100 rounded-xl text-xs font-semibold">
                      <button id="btn-hm-metric-pi" class="px-3 py-1 rounded-lg transition-colors ${selectedMetric === "pi" ? "bg-[#0B1B3F] text-white shadow-xs" : "text-slate-500 hover:text-slate-900"}">
                        Avg PI
                      </button>
                      <button id="btn-hm-metric-high" class="px-3 py-1 rounded-lg transition-colors ${selectedMetric === "high_share" ? "bg-[#0B1B3F] text-white shadow-xs" : "text-slate-500 hover:text-slate-900"}">
                        % HIGH Balls
                      </button>
                    </div>
                  </div>
                </div>

                <div id="pressure-heatmap-container" class="w-full h-[450px]">
                  <!-- Heatmap rendered via ECharts -->
                </div>
              </div>
            `
            : notAvailableCard("Pressure Heatmap")
        }

        <!-- 4. Ball-by-Ball Match Leverage Explorer (from traces) -->
        ${
          hasTraces
            ? `
              <div class="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-card flex flex-col gap-4">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                  <div>
                    <h2 class="text-sm font-bold text-slate-900">Ball-by-Ball Match Leverage Timeline</h2>
                    <span class="text-xs text-slate-400">Trace continuous win probability and leverage zones in real match scenarios</span>
                  </div>

                  <!-- Match Trace Selector -->
                  <div class="w-full sm:w-64">
                    <select id="select-match-trace" class="w-full text-xs font-medium rounded-xl border border-slate-200 bg-slate-50 py-1.5 px-3 text-slate-800 focus:outline-none focus:border-[#E6007E]">
                      ${traces.map((t, idx) => `
                        <option value="${idx}" ${selectedTraceIdx === idx ? "selected" : ""}>
                          ${esc(t.label || `Match #${t.match_id}`)}
                        </option>
                      `).join("")}
                    </select>
                  </div>
                </div>

                <div id="match-trace-chart-container" class="w-full h-[320px]">
                  <!-- Match Trace ECharts rendered here -->
                </div>

                <div class="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100">
                  <span class="flex items-center gap-1.5">
                    <span class="w-3 h-0.5 bg-[#0B1B3F]"></span> Chasing Win Probability
                  </span>
                  <span class="flex items-center gap-1.5">
                    <span class="w-2.5 h-2.5 bg-[#E6007E] rotate-45 transform"></span> Wicket Delivery
                  </span>
                </div>
              </div>
            `
            : notAvailableCard("Match Traces Explorer")
        }

      </div>
    `;

    // Initialize Heatmap
    if (hasHeatmap) {
      const hmEl = container.querySelector("#pressure-heatmap-container");
      const currentInningsData = heatmapData[selectedInnings] || {};
      const matrix = currentInningsData[selectedMetric] || [];
      if (hmEl && matrix.length > 0) {
        // Render 20x10 matrix
        const dataArr = [];
        matrix.forEach((row, y) => {
          row.forEach((val, x) => {
            if (val != null) dataArr.push([x, y, Number(val.toFixed(3))]);
          });
        });

        chart(hmEl, {
          tooltip: {
            position: "top",
            formatter: (p) => {
              const wkts = p.data[0];
              const over = p.data[1] + 1;
              const val = p.data[2];
              const nBalls = currentInningsData.n?.[p.data[1]]?.[wkts];
              return `Over ${over}, ${wkts} Wickets Lost<br/><strong>${selectedMetric === "pi" ? "Pressure Index" : "High Share"}:</strong> ${val}${nBalls ? `<br/>Balls: ${nBalls}` : ""}`;
            }
          },
          grid: { left: 60, right: 20, top: 20, bottom: 40 },
          xAxis: {
            type: "category",
            data: Array.from({ length: 10 }, (_, i) => `${i} wkts`),
            axisLabel: { fontSize: 10 }
          },
          yAxis: {
            type: "category",
            data: Array.from({ length: 20 }, (_, i) => `Over ${i + 1}`),
            axisLabel: { fontSize: 10 }
          },
          visualMap: {
            min: 0,
            max: selectedMetric === "pi" ? 1 : 0.8,
            calculable: true,
            orient: "horizontal",
            left: "center",
            bottom: 0,
            inRange: {
              color: ["#eff6ff", "#fce7f3", "#ec4899", "#9d174d"]
            },
            textStyle: { fontSize: 10 }
          },
          series: [
            {
              type: "heatmap",
              data: dataArr,
              label: { show: false }
            }
          ]
        });
      }
    }

    // Initialize Match Trace Chart
    if (hasTraces) {
      const traceEl = container.querySelector("#match-trace-chart-container");
      const currentTrace = traces[selectedTraceIdx];
      if (traceEl && currentTrace) {
        const balls = currentTrace.balls || [];
        const wp = currentTrace.wp || [];
        const wickets = currentTrace.wicket || [];
        const pi = currentTrace.pi || [];

        chart(traceEl, {
          tooltip: {
            trigger: "axis",
            formatter: (params) => {
              const idx = params[0]?.dataIndex;
              if (idx == null) return "";
              const ballName = balls[idx];
              const curWp = wp[idx];
              const isWkt = wickets[idx] === 1;
              const curPi = pi[idx];
              return `Ball ${ballName}<br/>Win Prob: <strong>${(curWp * 100).toFixed(1)}%</strong>${curPi ? `<br/>PI: ${curPi.toFixed(2)}` : ""}${isWkt ? `<br/><span style="color:#E6007E;font-weight:bold;">WICKET</span>` : ""}`;
            }
          },
          grid: { left: 45, right: 20, top: 25, bottom: 35 },
          xAxis: {
            type: "category",
            data: balls,
            axisLabel: { interval: 11, fontSize: 10 }
          },
          yAxis: {
            type: "value",
            name: "Win Prob",
            min: 0,
            max: 1,
            splitLine: { lineStyle: { color: "#E6E9F0" } },
            axisLabel: { fontSize: 10 }
          },
          series: [
            {
              type: "line",
              data: wp,
              lineStyle: { color: "#0B1B3F", width: 2.5 },
              symbol: (val, p) => wickets[p.dataIndex] === 1 ? "diamond" : "none",
              symbolSize: 8,
              itemStyle: { color: "#E6007E" }
            }
          ]
        });
      }
    }

    // Attach Listeners
    container.querySelector("#btn-hm-inn1")?.addEventListener("click", () => {
      selectedInnings = "innings1";
      renderView();
    });
    container.querySelector("#btn-hm-inn2")?.addEventListener("click", () => {
      selectedInnings = "innings2";
      renderView();
    });
    container.querySelector("#btn-hm-metric-pi")?.addEventListener("click", () => {
      selectedMetric = "pi";
      renderView();
    });
    container.querySelector("#btn-hm-metric-high")?.addEventListener("click", () => {
      selectedMetric = "high_share";
      renderView();
    });
    container.querySelector("#select-match-trace")?.addEventListener("change", (e) => {
      selectedTraceIdx = Number(e.target.value);
      renderView();
    });
  }

  renderView();
}
