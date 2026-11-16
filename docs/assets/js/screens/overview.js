import { n, pct, initials, esc, interval, chips, notAvailableCard } from "../format.js";

export function renderOverview(container, state, data) {
  if (!data || !data.meta) {
    container.innerHTML = notAvailableCard("Overview Data");
    return;
  }

  const meta = data.meta;
  const counts = meta.counts || {};
  const batters = data.players_batters || [];
  const bowlers = data.players_bowlers || [];
  const wpReport = data.validation?.wp_report || [];
  
  // Find Innings-2 'all' row AUC
  const inn2All = wpReport.find(r => r.innings === 2 && r.group === "all");
  const inn2Auc = inn2All && inn2All.auc != null ? inn2All.auc.toFixed(3) : null;

  // Compute "What to know" strips
  function computeSummaryStrip(list, role) {
    const top10 = list.slice(0, 10);
    const firmRanks = top10.filter(p => p.p_top10 >= 0.8).map(p => `#${p.rank}`);
    const firstTie = top10.find(p => p.p_top10 < 0.5);
    const overlap = top10.reduce((s, p) => s + (p.p_top10 || 0), 0).toFixed(1);

    const firmText = firmRanks.length > 0
      ? `Ranks ${firmRanks.join(", ")} demonstrate firm credibility (P(top 10) ≥ 80%).`
      : `High parity at top tier (no rank exceeds 80% P(top 10)).`;
    
    const tieText = firstTie
      ? `Ranks #${firstTie.rank}–#10 mark statistical ties (P(top 10) < 50%), where individual rank order is subject to sample variance.`
      : `Top tier displays consistent separation.`;

    const overlapText = `Expected top-10 overlap across independent tournament resamples is ${overlap} / 10.`;

    return { firmText, tieText, overlapText, overlap };
  }

  const batSummary = computeSummaryStrip(batters, "batter");
  const bowSummary = computeSummaryStrip(bowlers, "bowler");

  const minHighBatter = meta.rules?.min_high_balls?.batter || 150;
  const minHighBowler = meta.rules?.min_high_balls?.bowler || 120;

  function renderTop10List(list, roleName, minHigh) {
    const top10 = list.slice(0, 10);
    return top10.map(p => {
      const isBelowMin = p.n_high < minHigh;
      const rankColor = p.rank <= 3 ? "bg-[#E6007E] text-white" : "bg-slate-100 text-slate-700";
      const pTop10Pct = Math.round((p.p_top10 || 0) * 100);
      const pillBg = p.p_top10 >= 0.7 ? "bg-[#FFF0F7] text-[#E6007E] border-[#E6007E]/30" : "bg-slate-50 text-slate-600 border-slate-200";

      return `
        <tr class="hover:bg-slate-50/80 cursor-pointer border-b border-slate-100 last:border-b-0 transition-colors group" onclick="location.hash='#/player/${p.player_id}'" role="button" tabindex="0" onkeydown="if(event.key==='Enter')location.hash='#/player/${p.player_id}'">
          <td class="py-3 px-3 text-left w-12">
            <span class="w-6 h-6 rounded-lg ${rankColor} text-xs font-bold flex items-center justify-center font-mono shadow-xs">
              ${p.rank}
            </span>
          </td>
          <td class="py-3 px-3 text-left">
            <div class="flex items-center gap-2.5">
              <span class="w-8 h-8 rounded-full bg-slate-900 text-white text-[11px] font-bold flex items-center justify-center shrink-0">
                ${initials(p.name)}
              </span>
              <div class="flex flex-col min-w-0">
                <span class="text-xs font-bold text-slate-900 group-hover:text-[#E6007E] transition-colors truncate flex items-center gap-1.5">
                  ${esc(p.name)}
                  ${isBelowMin ? `<span class="w-2 h-2 rounded-full bg-amber-500" title="High balls below role floor (${p.n_high}/${minHigh})"></span>` : ""}
                </span>
                <div class="flex items-center gap-1 mt-0.5 truncate">
                  ${chips(p)}
                </div>
              </div>
            </div>
          </td>
          <td class="py-3 px-3 text-right font-mono text-xs font-bold text-slate-900">
            ${p.rating > 0 ? "+" : ""}${n(p.rating, 1)}
          </td>
          <td class="py-3 px-3 text-center hidden sm:table-cell">
            <div class="flex justify-center">
              ${interval(p, -10, 50, true)}
            </div>
          </td>
          <td class="py-3 px-3 text-right">
            <span class="px-2 py-0.5 rounded-md border text-[11px] font-bold font-mono ${pillBg}">
              ${pTop10Pct}%
            </span>
          </td>
        </tr>
      `;
    }).join("");
  }

  container.innerHTML = `
    <div class="p-6 sm:p-8 max-w-[1600px] mx-auto w-full flex flex-col gap-6">
      
      <!-- Screen Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2 mb-1">
            <span class="text-[10px] font-bold text-[#9D174D] uppercase tracking-wider bg-[#FFF0F7] px-2 py-0.5 rounded-md border border-[#E6007E]/20">
              EXECUTIVE INTELLIGENCE
            </span>
            <span class="text-xs text-slate-400 font-medium">• Empirical Bayes Latent Index</span>
          </div>
          <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight" tabindex="-1">
            Performance Overview
          </h1>
          <p class="text-xs sm:text-sm text-slate-500 mt-1 max-w-3xl leading-relaxed">
            Calibrated situational impact delivered above contextual match expectation per 100 high-pressure deliveries.
          </p>
        </div>
      </div>

      <!-- KPI Summary Tiles -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <!-- Matches Analyzed -->
        <div class="bg-white rounded-2xl border border-[#E2E8F0] p-5 shadow-card flex flex-col justify-between">
          <div class="flex items-center justify-between text-slate-400 mb-2">
            <span class="text-xs font-bold uppercase tracking-wider">Usable Matches</span>
            <span class="material-symbols-outlined text-[20px] text-slate-400">sports_cricket</span>
          </div>
          <div class="text-2xl sm:text-3xl font-extrabold text-slate-900 font-mono tracking-tight">
            ${n(counts.usable_matches)}
          </div>
          <div class="text-[11px] text-slate-500 mt-2 font-medium">
            <span class="font-bold text-slate-700">${n(counts.ipl_matches)}</span> IPL • <span class="font-bold text-slate-700">${n(counts.t20i_and_other_matches)}</span> T20I/Other
          </div>
        </div>

        <!-- Usable Balls -->
        <div class="bg-white rounded-2xl border border-[#E2E8F0] p-5 shadow-card flex flex-col justify-between">
          <div class="flex items-center justify-between text-slate-400 mb-2">
            <span class="text-xs font-bold uppercase tracking-wider">Usable Balls</span>
            <span class="material-symbols-outlined text-[20px] text-slate-400">adjust</span>
          </div>
          <div class="text-2xl sm:text-3xl font-extrabold text-slate-900 font-mono tracking-tight">
            ${n(counts.usable_balls)}
          </div>
          <div class="text-[11px] text-slate-500 mt-2 font-medium">
            Continuous ball-by-ball leverage tracking
          </div>
        </div>

        <!-- Eligible Cohort -->
        <div class="bg-white rounded-2xl border border-[#E2E8F0] p-5 shadow-card flex flex-col justify-between">
          <div class="flex items-center justify-between text-slate-400 mb-2">
            <span class="text-xs font-bold uppercase tracking-wider">Eligible Players</span>
            <span class="material-symbols-outlined text-[20px] text-slate-400">group</span>
          </div>
          <div class="text-2xl sm:text-3xl font-extrabold text-slate-900 font-mono tracking-tight">
            ${n((counts.eligible_batters || 0) + (counts.eligible_bowlers || 0))}
          </div>
          <div class="text-[11px] text-slate-500 mt-2 font-medium">
            <span class="font-bold text-[#E6007E]">${counts.eligible_batters}</span> Batters • <span class="font-bold text-slate-700">${counts.eligible_bowlers}</span> Bowlers
          </div>
        </div>

        <!-- WP Model Calibration -->
        <div class="bg-white rounded-2xl border border-[#E2E8F0] p-5 shadow-card flex flex-col justify-between">
          <div class="flex items-center justify-between text-slate-400 mb-2">
            <span class="text-xs font-bold uppercase tracking-wider">Chase Model AUC</span>
            <span class="material-symbols-outlined text-[20px] text-[#0C9588]">verified</span>
          </div>
          <div class="text-2xl sm:text-3xl font-extrabold text-slate-900 font-mono tracking-tight">
            ${inn2Auc ? inn2Auc : "—"}
          </div>
          <div class="text-[11px] text-slate-500 mt-2 font-medium">
            ${inn2Auc ? "Innings-2 hold-out discrimination" : "Validation report card hidden"}
          </div>
        </div>
      </div>

      <!-- What to Know Strategic Intelligence Strip -->
      <div class="bg-white rounded-2xl border border-[#E2E8F0] p-5 shadow-card flex flex-col gap-3">
        <div class="flex items-center gap-2 text-xs font-bold text-slate-900 uppercase tracking-wider">
          <span class="material-symbols-outlined text-[18px] text-[#E6007E]">lightbulb</span>
          Strategic Interpretation &amp; Uncertainty Boundaries
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-600 leading-relaxed">
          <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-1.5">
            <span class="font-bold text-slate-900 text-xs flex items-center justify-between">
              <span>Batting Cohort Dynamics</span>
              <span class="font-mono text-[11px] text-[#E6007E]">${batSummary.overlap}/10 Overlap</span>
            </span>
            <p>${batSummary.firmText} ${batSummary.tieText}</p>
            <p class="text-[11px] text-slate-400 mt-0.5">${batSummary.overlapText}</p>
          </div>
          <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-1.5">
            <span class="font-bold text-slate-900 text-xs flex items-center justify-between">
              <span>Bowling Cohort Dynamics</span>
              <span class="font-mono text-[11px] text-[#E6007E]">${bowSummary.overlap}/10 Overlap</span>
            </span>
            <p>${bowSummary.firmText} ${bowSummary.tieText}</p>
            <p class="text-[11px] text-slate-400 mt-0.5">${bowSummary.overlapText}</p>
          </div>
        </div>
      </div>

      <!-- Top 10 Batters & Bowlers Leaderboard Cards -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        <!-- Top 10 Batters -->
        <div class="bg-white rounded-2xl border border-[#E2E8F0] shadow-card overflow-hidden flex flex-col">
          <div class="p-5 border-b border-slate-100 flex items-center justify-between">
            <div class="flex items-center gap-2.5">
              <span class="w-7 h-7 rounded-lg bg-[#FFF0F7] text-[#E6007E] flex items-center justify-center font-bold text-xs">
                🏏
              </span>
              <div>
                <h2 class="text-sm font-bold text-slate-900">Top 10 Batters under Pressure</h2>
                <span class="text-[11px] text-slate-400">Latent Clutch Rating (Runs / 100 HIGH balls)</span>
              </div>
            </div>
            <a href="#/rankings?role=batter" class="text-xs font-bold text-[#E6007E] hover:underline flex items-center gap-1">
              View All ${batters.length} →
            </a>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-slate-50/70 border-b border-slate-100 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  <th class="py-2.5 px-3 w-12 text-left">#</th>
                  <th class="py-2.5 px-3 text-left">Player</th>
                  <th class="py-2.5 px-3 text-right">Rating</th>
                  <th class="py-2.5 px-3 text-center hidden sm:table-cell">80% Interval (Bootstrap)</th>
                  <th class="py-2.5 px-3 text-right">P(Top 10)</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                ${renderTop10List(batters, "batter", minHighBatter)}
              </tbody>
            </table>
          </div>
        </div>

        <!-- Top 10 Bowlers -->
        <div class="bg-white rounded-2xl border border-[#E2E8F0] shadow-card overflow-hidden flex flex-col">
          <div class="p-5 border-b border-slate-100 flex items-center justify-between">
            <div class="flex items-center gap-2.5">
              <span class="w-7 h-7 rounded-lg bg-slate-100 text-slate-800 flex items-center justify-center font-bold text-xs">
                🎯
              </span>
              <div>
                <h2 class="text-sm font-bold text-slate-900">Top 10 Bowlers under Pressure</h2>
                <span class="text-[11px] text-slate-400">Latent Clutch Rating (Runs saved / 100 HIGH balls)</span>
              </div>
            </div>
            <a href="#/rankings?role=bowler" class="text-xs font-bold text-[#E6007E] hover:underline flex items-center gap-1">
              View All ${bowlers.length} →
            </a>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-slate-50/70 border-b border-slate-100 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  <th class="py-2.5 px-3 w-12 text-left">#</th>
                  <th class="py-2.5 px-3 text-left">Player</th>
                  <th class="py-2.5 px-3 text-right">Rating</th>
                  <th class="py-2.5 px-3 text-center hidden sm:table-cell">80% Interval (Bootstrap)</th>
                  <th class="py-2.5 px-3 text-right">P(Top 10)</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                ${renderTop10List(bowlers, "bowler", minHighBowler)}
              </tbody>
            </table>
          </div>
        </div>

      </div>

    </div>
  `;
}
