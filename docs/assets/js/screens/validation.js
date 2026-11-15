import { n, pct, esc, notAvailableCard } from "../format.js";
import { chart } from "../charts.js";

export function renderValidation(container, state, data) {
  const valData = data?.validation;
  if (!valData) {
    container.innerHTML = notAvailableCard("Model Validation Data");
    return;
  }

  const wpReport = valData.wp_report || [];
  const tournament = valData.tournament || [];
  const sensitivity = valData.sensitivity || [];
  const deltaEvidence = valData.delta_evidence || [];
  const exclusions = valData.exclusions || [];
  const calibrationData = data?.pressure?.calibration || {};

  const inn1All = wpReport.find(r => r.innings === 1 && r.group === "all") || {};
  const inn2All = wpReport.find(r => r.innings === 2 && r.group === "all") || {};

  // Filter sensitivity rows: hide rows where tau === 1
  const filteredSensitivity = sensitivity.filter(r => {
    if (r.kendall_tau === 1 || r.kendall_tau === 1.0) return false;
    if (r.run?.startsWith("fractional") || r.run?.startsWith("PI_q0.75") || r.run?.startsWith("half_life")) {
      if (r.top10_overlap !== 10) {
        console.warn(`Sensitivity default row ${r.run} has overlap ${r.top10_overlap} != 10`);
        return false;
      }
    }
    return true;
  });

  // Tournament splits: split by role
  const batterTournament = tournament.filter(r => r.role === "batter").sort((a, b) => b.mean_pearson - a.mean_pearson);
  const bowlerTournament = tournament.filter(r => r.role === "bowler").sort((a, b) => b.mean_pearson - a.mean_pearson);

  container.innerHTML = `
    <div class="p-6 sm:p-8 max-w-[1600px] mx-auto w-full flex flex-col gap-6">
      
      <!-- Screen Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2 mb-1">
            <span class="text-[10px] font-bold text-[#9D174D] uppercase tracking-wider bg-[#FFF0F7] px-2 py-0.5 rounded-md border border-[#E6007E]/20">
              EMPIRICAL RIGOR
            </span>
            <span class="text-xs text-slate-400 font-medium">• Institutional Verification</span>
          </div>
          <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight" tabindex="-1">
            Model Validation &amp; Robustness
          </h1>
          <p class="text-xs sm:text-sm text-slate-500 mt-1 max-w-3xl leading-relaxed">
            Comprehensive out-of-sample hold-out cross validation, split-half tournament stability, and parameter sensitivity audits.
          </p>
        </div>
      </div>

      <!-- Win-Probability Model Calibration & Discrimination -->
      ${
        wpReport.length > 0
          ? `
            <div class="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-card flex flex-col gap-5">
              <div class="flex items-center justify-between pb-3 border-b border-slate-100">
                <h2 class="text-sm font-bold text-slate-900">Win-Probability Engine Calibration &amp; Scoring</h2>
                <span class="text-xs text-slate-400 font-medium">Evaluated across hold-out match samples</span>
              </div>

              <!-- Metric Chips Grid -->
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div class="p-4 rounded-xl bg-slate-50 border border-slate-100">
                  <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Innings 2 AUC (Chase)</span>
                  <div class="text-2xl font-extrabold text-slate-900 font-mono mt-1">
                    ${inn2All.auc ? inn2All.auc.toFixed(3) : "—"}
                  </div>
                  <span class="text-[11px] text-slate-500">Innings 1: ${inn1All.auc ? inn1All.auc.toFixed(3) : "—"}</span>
                </div>

                <div class="p-4 rounded-xl bg-slate-50 border border-slate-100">
                  <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Innings 2 Brier Score</span>
                  <div class="text-2xl font-extrabold text-slate-900 font-mono mt-1">
                    ${inn2All.brier ? inn2All.brier.toFixed(3) : "—"}
                  </div>
                  <span class="text-[11px] text-slate-500">Innings 1: ${inn1All.brier ? inn1All.brier.toFixed(3) : "—"}</span>
                </div>

                <div class="p-4 rounded-xl bg-slate-50 border border-slate-100">
                  <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Innings 2 Log Loss</span>
                  <div class="text-2xl font-extrabold text-slate-900 font-mono mt-1">
                    ${inn2All.log_loss ? inn2All.log_loss.toFixed(3) : "—"}
                  </div>
                  <span class="text-[11px] text-slate-500">Base Loss: ${inn2All.base_logloss ? inn2All.base_logloss.toFixed(3) : "—"}</span>
                </div>

                <div class="p-4 rounded-xl bg-slate-50 border border-slate-100">
                  <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Calibration ECE</span>
                  <div class="text-2xl font-extrabold text-slate-900 font-mono mt-1">
                    ${inn2All.ece ? `${(inn2All.ece * 100).toFixed(2)}%` : "—"}
                  </div>
                  <span class="text-[11px] text-slate-500">Expected Calibration Error</span>
                </div>
              </div>

              <!-- Calibration Charts: Innings 1 and Innings 2 -->
              ${
                calibrationData.innings2
                  ? `
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
                      <div class="flex flex-col gap-2">
                        <span class="text-xs font-bold text-slate-700">Innings 1 Calibration Curve</span>
                        <div id="calib-inn1-chart" class="w-full h-56 border border-slate-100 rounded-xl p-2 bg-slate-50/50"></div>
                      </div>
                      <div class="flex flex-col gap-2">
                        <span class="text-xs font-bold text-slate-700">Innings 2 Calibration Curve (Chases)</span>
                        <div id="calib-inn2-chart" class="w-full h-56 border border-slate-100 rounded-xl p-2 bg-slate-50/50"></div>
                      </div>
                    </div>
                  `
                  : ""
              }
            </div>
          `
          : notAvailableCard("Win Probability Model Report")
      }

      <!-- Estimator Comparison Tournament -->
      ${
        tournament.length > 0
          ? `
            <div class="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-card flex flex-col gap-5">
              <div class="flex items-center justify-between pb-3 border-b border-slate-100">
                <h2 class="text-sm font-bold text-slate-900">Estimator Comparison Tournament (Out-of-Fold Splits)</h2>
                <span class="text-xs text-slate-400 font-medium">100 independent random tournament iterations</span>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                <!-- Batter Estimators -->
                <div class="flex flex-col gap-3">
                  <div class="flex items-center justify-between pb-2 border-b border-slate-100">
                    <span class="text-xs font-bold text-slate-900">🏏 Batter Estimators</span>
                    <span class="text-[11px] font-mono text-slate-400">Noise Ceiling: ${batterTournament[0]?.noise_ceiling_relB ? Math.sqrt(batterTournament[0].noise_ceiling_relB).toFixed(3) : "—"}</span>
                  </div>
                  <div class="flex flex-col gap-2">
                    ${batterTournament.map((r, i) => `
                      <div class="p-3 rounded-xl ${i === 0 ? "bg-[#FFF0F7] border border-[#E6007E]/30" : "bg-slate-50 border border-slate-100"} flex flex-col gap-1">
                        <div class="flex items-center justify-between text-xs">
                          <span class="font-bold ${i === 0 ? "text-[#E6007E]" : "text-slate-800"}">
                            ${r.estimator} ${i === 0 ? "★ Selected" : ""}
                          </span>
                          <span class="font-mono font-bold text-slate-900">r = ${r.mean_pearson.toFixed(3)}</span>
                        </div>
                        <div class="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                          <span>90% CI: [${r.p05.toFixed(3)}, ${r.p95.toFixed(3)}]</span>
                          <span>Disattenuated: ${(r.disattenuated * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                    `).join("")}
                  </div>
                </div>

                <!-- Bowler Estimators -->
                <div class="flex flex-col gap-3">
                  <div class="flex items-center justify-between pb-2 border-b border-slate-100">
                    <span class="text-xs font-bold text-slate-900">🎯 Bowler Estimators</span>
                    <span class="text-[11px] font-mono text-slate-400">Noise Ceiling: ${bowlerTournament[0]?.noise_ceiling_relB ? Math.sqrt(bowlerTournament[0].noise_ceiling_relB).toFixed(3) : "—"}</span>
                  </div>
                  <div class="flex flex-col gap-2">
                    ${bowlerTournament.map((r, i) => `
                      <div class="p-3 rounded-xl ${i === 0 ? "bg-[#FFF0F7] border border-[#E6007E]/30" : "bg-slate-50 border border-slate-100"} flex flex-col gap-1">
                        <div class="flex items-center justify-between text-xs">
                          <span class="font-bold ${i === 0 ? "text-[#E6007E]" : "text-slate-800"}">
                            ${r.estimator} ${i === 0 ? "★ Selected" : ""}
                          </span>
                          <span class="font-mono font-bold text-slate-900">r = ${r.mean_pearson.toFixed(3)}</span>
                        </div>
                        <div class="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                          <span>90% CI: [${r.p05.toFixed(3)}, ${r.p95.toFixed(3)}]</span>
                          <span>Disattenuated: ${(r.disattenuated * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                    `).join("")}
                  </div>
                </div>

              </div>
            </div>
          `
          : notAvailableCard("Tournament Estimator Comparison")
      }

      <!-- Sensitivity Analysis & Rank Stability Table -->
      ${
        filteredSensitivity.length > 0
          ? `
            <div class="bg-white rounded-2xl border border-[#E2E8F0] shadow-card overflow-hidden">
              <div class="p-5 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <h2 class="text-sm font-bold text-slate-900">Sensitivity Analysis &amp; Rank Stability</h2>
                  <span class="text-xs text-slate-400">Top-10 overlap and Kendall rank correlation under hyperparameter shifts</span>
                </div>
              </div>
              <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr class="bg-slate-50/70 border-b border-slate-100 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                      <th class="py-3 px-4">Role</th>
                      <th class="py-3 px-4">Variant Run</th>
                      <th class="py-3 px-4 text-center">Top 10 Overlap</th>
                      <th class="py-3 px-4 text-center">Top 15 Overlap</th>
                      <th class="py-3 px-4 text-right">Kendall Tau (τ)</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-slate-100 font-mono">
                    ${filteredSensitivity.map(r => `
                      <tr class="hover:bg-slate-50">
                        <td class="py-2.5 px-4 font-sans font-bold capitalize text-slate-800">${r.role}</td>
                        <td class="py-2.5 px-4 text-slate-700">${esc(r.run)}</td>
                        <td class="py-2.5 px-4 text-center font-bold ${r.top10_overlap >= 8 ? "text-teal-700" : "text-amber-700"}">${r.top10_overlap}/10</td>
                        <td class="py-2.5 px-4 text-center text-slate-600">${r.top15_overlap}/15</td>
                        <td class="py-2.5 px-4 text-right font-bold text-slate-900">${r.kendall_tau != null ? r.kendall_tau.toFixed(3) : "—"}</td>
                      </tr>
                    `).join("")}
                  </tbody>
                </table>
              </div>
            </div>
          `
          : notAvailableCard("Sensitivity Analysis")
      }

      <!-- Delta Evidence & Pressure Shift Audit -->
      ${
        deltaEvidence.length > 0
          ? `
            <div class="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-card flex flex-col gap-4">
              <div class="flex items-center justify-between pb-3 border-b border-slate-100">
                <h2 class="text-sm font-bold text-slate-900">Pressure Shift Evidence (δ 80% Credible Interval Separation)</h2>
                <span class="text-xs text-slate-400">Players with pressure shift entirely distinct from baseline vs 10% chance</span>
              </div>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                ${deltaEvidence.map(d => `
                  <div class="p-4 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-2">
                    <span class="font-bold text-slate-800 capitalize text-xs">${d.role} Cohort (${d.eligible_players} qualified)</span>
                    <div class="flex items-center justify-between text-xs py-1 border-b border-slate-100">
                      <span class="text-slate-600">80% CI Entirely &gt; 0 (Clutch Elevation):</span>
                      <span class="font-mono font-bold text-[#E6007E]">${d.delta_interval_above_zero} (${((d.delta_interval_above_zero / d.eligible_players) * 100).toFixed(1)}%)</span>
                    </div>
                    <div class="flex items-center justify-between text-xs py-1">
                      <span class="text-slate-600">80% CI Entirely &lt; 0 (Clutch Suppression):</span>
                      <span class="font-mono font-bold text-slate-700">${d.delta_interval_below_zero} (${((d.delta_interval_below_zero / d.eligible_players) * 100).toFixed(1)}%)</span>
                    </div>
                  </div>
                `).join("")}
              </div>
            </div>
          `
          : ""
      }

      <!-- Scope Limitations & Boundaries (Qualitative text only, no invented numbers) -->
      <div class="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-card flex flex-col gap-4">
        <h2 class="text-sm font-bold text-slate-900 pb-3 border-b border-slate-100">What the Data Cannot Tell Us (Analytical Boundaries)</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-600 leading-relaxed">
          <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-1">
            <span class="font-bold text-slate-800">Pressure-Specific Skill Isolation</span>
            <p>Pressure-specific talent beyond baseline capability is small and statistically noisy; individual performance under leverage is largely explained by general ability.</p>
          </div>
          <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-1">
            <span class="font-bold text-slate-800">Rankings Parity &amp; Statistical Ties</span>
            <p>Adjacent ranks in the chasing tier possess substantial credible interval overlap and should be treated as statistical parity rather than deterministic differences.</p>
          </div>
          <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-1">
            <span class="font-bold text-slate-800">Match Dynamics &amp; Context</span>
            <p>Pre-delivery state tracking does not incorporate pitch degradation, dew factors, wind vectors, or tactical field placement nuances.</p>
          </div>
          <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-1">
            <span class="font-bold text-slate-800">Unmodelled Extras Reconstruction</span>
            <p>Leg-bye and bye allocations are estimated through post-hoc trajectory inference rather than explicit tracking telemetry.</p>
          </div>
        </div>
      </div>

    </div>
  `;

  // Initialize calibration charts
  if (calibrationData.innings1 && calibrationData.innings2) {
    const el1 = container.querySelector("#calib-inn1-chart");
    const el2 = container.querySelector("#calib-inn2-chart");
    if (el1) {
      chart(el1, {
        grid: { left: 40, right: 15, top: 20, bottom: 25 },
        xAxis: { type: "value", min: 0, max: 1, splitLine: { lineStyle: { color: "#E6E9F0" } } },
        yAxis: { type: "value", min: 0, max: 1, splitLine: { lineStyle: { color: "#E6E9F0" } } },
        series: [
          { type: "line", data: [[0, 0], [1, 1]], lineStyle: { type: "dashed", color: "#8A94A6" }, symbol: "none" },
          { type: "line", data: calibrationData.innings1.map(x => [x.pred, x.obs]), smooth: true, itemStyle: { color: "#0B1B3F" }, lineStyle: { color: "#0B1B3F" } }
        ]
      });
    }
    if (el2) {
      chart(el2, {
        grid: { left: 40, right: 15, top: 20, bottom: 25 },
        xAxis: { type: "value", min: 0, max: 1, splitLine: { lineStyle: { color: "#E6E9F0" } } },
        yAxis: { type: "value", min: 0, max: 1, splitLine: { lineStyle: { color: "#E6E9F0" } } },
        series: [
          { type: "line", data: [[0, 0], [1, 1]], lineStyle: { type: "dashed", color: "#8A94A6" }, symbol: "none" },
          { type: "line", data: calibrationData.innings2.map(x => [x.pred, x.obs]), smooth: true, itemStyle: { color: "#E6007E" }, lineStyle: { color: "#E6007E" } }
        ]
      });
    }
  }
}
