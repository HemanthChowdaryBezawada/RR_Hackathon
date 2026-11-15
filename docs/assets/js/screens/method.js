import { n, esc, notAvailableCard } from "../format.js";

export function renderMethod(container, state, data) {
  const meta = data?.meta;
  if (!meta) {
    container.innerHTML = notAvailableCard("Methodology Metadata");
    return;
  }

  const counts = meta.counts || {};
  const rules = meta.rules || {};
  const minHigh = rules.min_high_balls || {};

  container.innerHTML = `
    <div class="p-6 sm:p-8 max-w-[1600px] mx-auto w-full flex flex-col gap-6">
      
      <!-- Screen Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2 mb-1">
            <span class="text-[10px] font-bold text-[#9D174D] uppercase tracking-wider bg-[#FFF0F7] px-2 py-0.5 rounded-md border border-[#E6007E]/20">
              METHODOLOGY SPECIFICATION
            </span>
            <span class="text-xs text-slate-400 font-medium">• Hierarchical Statistical Architecture</span>
          </div>
          <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight" tabindex="-1">
            Methodology &amp; Mathematical Architecture
          </h1>
          <p class="text-xs sm:text-sm text-slate-500 mt-1 max-w-3xl leading-relaxed">
            From ball-by-ball match states to calibrated, uncertainty-aware player ratings.
          </p>
        </div>
      </div>

      <!-- The Analytical Pipeline Stepper -->
      <div class="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-card flex flex-col gap-5">
        <div class="flex items-center justify-between pb-3 border-b border-slate-100">
          <h2 class="text-sm font-bold text-slate-900">The Analytical Pipeline</h2>
          <span class="text-xs font-mono font-bold text-slate-500">${n(counts.usable_balls)} Tracked Deliveries</span>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-6 gap-3 text-xs">
          <!-- Stage 1 -->
          <div class="p-3 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-1">
            <span class="text-[10px] font-bold text-slate-400 uppercase">Stage 01</span>
            <span class="font-bold text-slate-900">State Tracking</span>
            <p class="text-[11px] text-slate-500 mt-1">Deliveries tagged with pre-ball alignment, match chase, and ball state.</p>
          </div>

          <!-- Stage 2 -->
          <div class="p-3 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-1">
            <span class="text-[10px] font-bold text-slate-400 uppercase">Stage 02</span>
            <span class="font-bold text-slate-900">WP Engine</span>
            <p class="text-[11px] text-slate-500 mt-1">Logistic gradient descent evaluating instantaneous win probability trajectory.</p>
          </div>

          <!-- Stage 3 -->
          <div class="p-3 rounded-xl bg-[#FFF0F7] border border-[#E6007E]/20 flex flex-col gap-1">
            <span class="text-[10px] font-bold text-[#E6007E] uppercase">Stage 03</span>
            <span class="font-bold text-slate-900">Pressure Index</span>
            <p class="text-[11px] text-slate-500 mt-1">Pre-ball valuation: 60% leverage, 25% closeness, 15% resource scarcity.</p>
          </div>

          <!-- Stage 4 -->
          <div class="p-3 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-1">
            <span class="text-[10px] font-bold text-slate-400 uppercase">Stage 04</span>
            <span class="font-bold text-slate-900">Net WPA Delta</span>
            <p class="text-[11px] text-slate-500 mt-1">Difference between observed outcome and expected contextual value.</p>
          </div>

          <!-- Stage 5 -->
          <div class="p-3 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-1">
            <span class="text-[10px] font-bold text-slate-400 uppercase">Stage 05</span>
            <span class="font-bold text-slate-900">Bayes Shrinkage</span>
            <p class="text-[11px] text-slate-500 mt-1">Hierarchical partial pooling regressing high-variance noisy samples to prior.</p>
          </div>

          <!-- Stage 6 -->
          <div class="p-3 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-1">
            <span class="text-[10px] font-bold text-slate-400 uppercase">Stage 06</span>
            <span class="font-bold text-slate-900">Credible Whiskers</span>
            <p class="text-[11px] text-slate-500 mt-1">Bootstrap resampling isolating 80% credible bounds and P(top 10) density.</p>
          </div>
        </div>
      </div>

      <!-- Eligibility & Ranking Rules Card -->
      <div class="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-card flex flex-col gap-4">
        <div class="flex items-center justify-between pb-3 border-b border-slate-100">
          <h2 class="text-sm font-bold text-slate-900">Player Eligibility &amp; Selection Cohort Rules</h2>
          <span class="text-xs font-mono font-bold text-[#E6007E]">One Ranking List</span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
          <div class="flex flex-col gap-3">
            <div class="flex items-center justify-between py-2 border-b border-slate-100">
              <span class="text-slate-600 font-medium">Minimum HIGH Balls (Batter):</span>
              <span class="font-mono font-bold text-slate-900">≥ ${minHigh.batter || 150} deliveries</span>
            </div>
            <div class="flex items-center justify-between py-2 border-b border-slate-100">
              <span class="text-slate-600 font-medium">Minimum HIGH Balls (Bowler):</span>
              <span class="font-mono font-bold text-slate-900">≥ ${minHigh.bowler || 120} deliveries</span>
            </div>
            <div class="flex items-center justify-between py-2 border-b border-slate-100">
              <span class="text-slate-600 font-medium">Temporal Activity Window:</span>
              <span class="font-mono font-bold text-slate-900">Active within ≤ ${rules.active_within_days || 365} days</span>
            </div>
          </div>

          <div class="flex flex-col gap-3">
            <div class="p-4 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-2">
              <span class="font-bold text-slate-800 text-xs">Jurisdiction &amp; Registry Policy:</span>
              <p class="text-slate-600 leading-relaxed text-xs">
                Rankings exclude Pakistan and Pakistan A players (not permitted in the IPL) and players with no match in the last 365 days. Bangladeshi players are included.
              </p>
              ${
                rules.included_note
                  ? `<p class="text-[11px] text-slate-500 border-t border-slate-200/60 pt-2 mt-1">${esc(rules.included_note)}</p>`
                  : ""
              }
            </div>
          </div>
        </div>
      </div>

      <!-- Formal Mathematical Formulation -->
      <div class="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-card flex flex-col gap-4">
        <h2 class="text-sm font-bold text-slate-900 pb-3 border-b border-slate-100">Mathematical Formulation &amp; Partial Pooling</h2>
        
        <div class="p-4 rounded-xl bg-slate-900 text-slate-100 font-mono text-xs leading-relaxed overflow-x-auto">
          <p class="text-slate-400">// Hierarchical Estimator Specification</p>
          <p class="mt-2 text-pink-400">θ_i ~ Normal(μ_pop, τ²)</p>
          <p>y_ij ~ Normal(θ_i, σ_ij²)</p>
          <p class="mt-2 text-slate-400">// Shrinkage Coefficient</p>
          <p>B_i = τ² / (τ² + σ_i² / n_i)</p>
          <p class="mt-1 text-teal-400">θ̂_i = B_i * ȳ_i + (1 - B_i) * μ_pop</p>
        </div>

        <p class="text-xs text-slate-600 leading-relaxed">
          Cricket performance under clutch scenarios exhibits high sampling variance due to sparse sample sizes. Unadjusted averages over-reward lucky emerging finishers and over-penalize small slumps. Hierarchical empirical Bayes shrinkage regularizes each player toward their capability prior, ensuring extreme ranks reflect persistent talent rather than noise.
        </p>
      </div>

    </div>
  `;
}
