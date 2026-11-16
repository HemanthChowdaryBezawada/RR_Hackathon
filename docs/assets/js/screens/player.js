import { n, pct, date, initials, esc, interval, chips, notAvailableCard } from "../format.js";
import { byId, activePlayers } from "../data.js";

export function renderPlayer(container, state, data) {
  if (!data || !data.meta) {
    container.innerHTML = notAvailableCard("Player Intelligence Data");
    return;
  }

  // Parse player ID from URL hash (#/player/:id or query id)
  const hash = location.hash || "";
  let playerId = null;
  const match = hash.match(/#\/player\/([^?]+)/);
  if (match) {
    playerId = match[1];
  } else {
    const qMatch = hash.match(/[?&]id=([^&]+)/);
    if (qMatch) playerId = qMatch[1];
  }

  // Default to rank 1 batter if no ID is specified
  let player = null;
  if (!playerId) {
    player = (data.players_batters || [])[0];
  } else {
    player = byId(data, playerId);
  }

  if (!player) {
    container.innerHTML = `
      <div class="p-12 max-w-lg mx-auto text-center flex flex-col items-center gap-4">
        <div class="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400">
          <span class="material-symbols-outlined text-[32px]">person_off</span>
        </div>
        <div>
          <h1 class="text-xl font-bold text-slate-900" tabindex="-1">Player not found</h1>
          <p class="text-xs text-slate-500 mt-1">The requested player profile does not exist in the qualified cohort.</p>
        </div>
        <a href="#/rankings" class="px-5 py-2.5 rounded-xl bg-[#0B1B3F] text-white text-xs font-bold hover:bg-slate-800 transition-colors shadow-sm">
          Return to Rankings
        </a>
      </div>
    `;
    return;
  }

  const role = player.role || "batter";
  const pool = activePlayers(data, role);
  const minHighFloor = data.meta.rules?.min_high_balls?.[role] || (role === "batter" ? 150 : 120);
  const isBelowFloor = player.n_high < minHighFloor;

  // Calculate pool medians for consistency & risk on the fly
  function median(arr) {
    const valid = arr.filter(v => v != null && !Number.isNaN(v)).sort((a, b) => a - b);
    if (!valid.length) return 0;
    const mid = Math.floor(valid.length / 2);
    return valid.length % 2 !== 0 ? valid[mid] : (valid[mid - 1] + valid[mid]) / 2;
  }

  const medianPos = median(pool.map(p => p.p_pos));
  const medianDisaster = median(pool.map(p => p.disaster_rate));

  // Find 3 nearest similar players by rating in same role
  const otherPlayers = pool.filter(p => p.player_id !== player.player_id);
  otherPlayers.sort((a, b) => Math.abs(a.rating - player.rating) - Math.abs(b.rating - player.rating));
  const similarPlayers = otherPlayers.slice(0, 3);

  // Pressure shift caption evaluation
  let deltaCaption = "";
  if (player.delta_lo80 != null && player.delta_hi80 != null) {
    if (player.delta_lo80 > 0) {
      deltaCaption = `Elevated clutch elevation (+${player.delta.toFixed(1)} runs/100b). The 80% interval (bootstrap) is strictly above zero, indicating positive performance elevation under pressure.`;
    } else if (player.delta_hi80 < 0) {
      deltaCaption = `Clutch suppression (${player.delta.toFixed(1)} runs/100b). The 80% interval (bootstrap) is strictly below zero, indicating pressure attenuation relative to standard situations.`;
    } else {
      deltaCaption = `Neutral pressure shift (${player.delta > 0 ? "+" : ""}${player.delta.toFixed(1)} runs/100b). The 80% interval (bootstrap) spans zero, indicating performance is primarily governed by baseline ability rather than clutch volatility.`;
    }
  }

  // Sample volume calculation
  const iplBalls = player.n_ipl_high || 0;
  const t20iBalls = player.n_t20i_high || 0;
  const totalHigh = player.n_high || (iplBalls + t20iBalls);
  const iplPct = totalHigh > 0 ? Math.round((iplBalls / totalHigh) * 100) : 0;
  const t20iPct = totalHigh > 0 ? 100 - iplPct : 0;

  // HIGH vs LOW Dumbbell check
  const hasHighLow = player.metric_high != null && player.metric_low != null;

  container.innerHTML = `
    <div class="p-6 sm:p-8 max-w-[1600px] mx-auto w-full flex flex-col gap-6">
      
      <!-- Player Profile Top Hero Card -->
      <div class="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-card flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div class="flex items-center gap-4">
          <div class="w-16 h-16 rounded-2xl bg-[#0B1B3F] text-white flex items-center justify-center text-xl font-bold font-mono shadow-sm shrink-0">
            ${initials(player.name)}
          </div>
          <div class="flex flex-col">
            <div class="flex items-center gap-2 flex-wrap mb-1">
              <span class="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ${player.rank <= 10 ? "bg-[#FFF0F7] text-[#E6007E] border border-[#E6007E]/20" : "bg-slate-100 text-slate-700"}">
                Rank #${player.rank} of ${pool.length} ${role}s
              </span>
              <span class="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ${player.active ? "bg-teal-50 text-teal-700 border border-teal-200" : "bg-slate-100 text-slate-500"}">
                ${player.active ? "Active Last 365d" : "Inactive"}
              </span>
              <span class="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-600">
                ${role.toUpperCase()}
              </span>
            </div>
            <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight" tabindex="-1">
              ${esc(player.name)}
            </h1>
            <div class="flex items-center gap-1.5 mt-1 text-xs text-slate-500 flex-wrap">
              ${chips(player)}
            </div>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <a href="#/compare?ids=${player.player_id}" class="px-4 py-2 rounded-xl border border-slate-200 bg-slate-50 hover:bg-white text-xs font-bold text-slate-700 transition-colors flex items-center gap-1.5 shadow-xs">
            <span class="material-symbols-outlined text-[16px]">compare</span>
            <span>Compare Player</span>
          </a>
          <a href="#/rankings?role=${role}" class="px-4 py-2 rounded-xl bg-[#0B1B3F] hover:bg-slate-800 text-white text-xs font-bold transition-colors shadow-xs flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[16px]">arrow_back</span>
            <span>Back to Rankings</span>
          </a>
        </div>
      </div>

      <!-- Core Metrics Triad: Rating, P(Top 10), Sample Volume -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        <!-- 1. Published Clutch Rating -->
        <div class="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-card flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
              <span class="text-slate-700 font-extrabold">Published Rating</span>
              <span class="px-2 py-0.5 rounded-md bg-[#FFF0F7] text-[#E6007E] text-[10px] font-bold">
                ${player.pctile ? `Top ${(100 - player.pctile).toFixed(1)}%` : "Top Tier"}
              </span>
            </div>
            <div class="flex items-baseline gap-2">
              <span class="text-3xl sm:text-4xl font-extrabold text-slate-900 font-mono tracking-tight">
                ${player.rating > 0 ? "+" : ""}${n(player.rating, 1)}
              </span>
              <span class="text-xs text-slate-500 font-medium">runs / 100b</span>
            </div>
            <div class="text-xs text-slate-500 font-mono mt-1">
              80% interval (bootstrap): [${n(player.lo80, 1)}, ${n(player.hi80, 1)}]
            </div>
          </div>
          
          <div class="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span class="font-mono text-slate-600 font-semibold">${player.estimator || (role === "batter" ? "E3_EB_general" : "E5_ridge_rho3")}</span>
            <span class="font-bold text-slate-700">WPA: ${n(player.wpa, 2)} pts/100b</span>
          </div>
        </div>

        <!-- 2. P(Top 10) Probability -->
        <div class="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-card flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
              <span>Top 10 Probability</span>
              <span class="px-2 py-0.5 rounded-md text-[10px] font-bold ${player.p_top10 >= 0.7 ? "bg-[#FFF0F7] text-[#E6007E]" : "bg-slate-100 text-slate-600"}">
                ${player.p_top10 >= 0.7 ? "High Confidence" : "Chasing Zone"}
              </span>
            </div>
            <div class="flex items-baseline gap-2">
              <span class="text-3xl sm:text-4xl font-extrabold text-slate-900 font-mono tracking-tight">
                ${pct(player.p_top10)}
              </span>
              <span class="text-xs text-slate-500 font-medium">posterior density</span>
            </div>
            <!-- Progress bar -->
            <div class="w-full bg-slate-100 rounded-full h-2 mt-3 overflow-hidden">
              <div class="bg-[#E6007E] h-2 rounded-full transition-all" style="width: ${Math.round((player.p_top10 || 0) * 100)}%;"></div>
            </div>
          </div>

          <div class="mt-6 pt-4 border-t border-slate-100 text-[11px] text-slate-500">
            Probability of player ranking in Top 10 under empirical shrinkage
          </div>
        </div>

        <!-- 3. Sample Volume & Exposure -->
        <div class="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-card flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
              <span>Sample Exposure</span>
              <span class="px-2 py-0.5 rounded-md text-[10px] font-bold ${isBelowFloor ? "bg-amber-100 text-amber-800" : "bg-teal-50 text-teal-700"}">
                ${isBelowFloor ? "Low Sample" : "Robust Sample"}
              </span>
            </div>
            <div class="flex items-baseline gap-2 flex-wrap">
              <span class="text-3xl sm:text-4xl font-extrabold text-slate-900 font-mono tracking-tight">
                ${n(player.n_high)}
              </span>
              <span class="text-xs text-slate-500 font-medium">HIGH balls</span>
              ${player.n_balls_total != null ? `
                <span class="text-xs text-slate-400 font-medium">/ <strong class="text-slate-700">${n(player.n_balls_total)}</strong> total balls</span>
              ` : ""}
            </div>

            <!-- Stacked bar for IPL vs T20I -->
            <div class="w-full bg-slate-100 rounded-full h-2 mt-3 flex overflow-hidden">
              <div class="bg-[#0B1B3F] h-2" style="width: ${iplPct}%;" title="IPL: ${iplBalls}"></div>
              <div class="bg-[#0C9588] h-2" style="width: ${t20iPct}%;" title="T20I: ${t20iBalls}"></div>
            </div>
          </div>

          <div class="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span>IPL: <strong class="text-slate-800">${iplBalls}</strong> (${iplPct}%)</span>
            <span>T20I: <strong class="text-slate-800">${t20iBalls}</strong> (${t20iPct}%)</span>
          </div>
        </div>

      </div>

      <!-- Ridge cross-check (context only) -->
      <div class="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-card flex flex-col gap-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-slate-400 text-[18px]">verified</span>
            <h2 class="text-sm font-bold text-slate-900">Ridge cross-check (context only)</h2>
            <span class="px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 text-[10px] font-bold">Opposition & Leverage Regularized</span>
          </div>
          <span class="text-xs text-slate-400">Additive specification: Rating = Usual Level (β) + Pressure Shift (δ)</span>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-1">
            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Ridge Rating</span>
            <span class="text-lg font-mono font-extrabold text-slate-900">${player.rating_ridge != null ? (player.rating_ridge > 0 ? "+" : "") + n(player.rating_ridge, 1) : (player.rating != null ? (player.rating > 0 ? "+" : "") + n(player.rating, 1) : "—")}</span>
            <span class="text-[10px] text-slate-500">runs / 100b</span>
          </div>

          <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-1">
            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Ridge Rank</span>
            <span class="text-lg font-mono font-extrabold text-slate-900">${player.rank_ridge != null ? "#" + player.rank_ridge : "#" + player.rank}</span>
            <span class="text-[10px] text-slate-500">among ${pool.length} ${role}s</span>
          </div>

          <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-1">
            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Usual Level (β)</span>
            <span class="text-lg font-mono font-extrabold text-slate-900">${(player.beta_ridge != null ? player.beta_ridge : player.beta) != null ? ((player.beta_ridge != null ? player.beta_ridge : player.beta) > 0 ? "+" : "") + n(player.beta_ridge != null ? player.beta_ridge : player.beta, 1) : "—"}</span>
            <span class="text-[10px] text-slate-500">baseline capability</span>
          </div>

          <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-1">
            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Pressure Shift (δ)</span>
            <span class="text-lg font-mono font-extrabold ${(player.delta_ridge != null ? player.delta_ridge : player.delta) > 0 ? "text-[#E6007E]" : "text-slate-700"}">${(player.delta_ridge != null ? player.delta_ridge : player.delta) != null ? ((player.delta_ridge != null ? player.delta_ridge : player.delta) > 0 ? "+" : "") + n(player.delta_ridge != null ? player.delta_ridge : player.delta, 1) : "—"}</span>
            <span class="text-[10px] text-slate-500">clutch differential</span>
          </div>
        </div>
      </div>

      <!-- Usual Level vs Pressure Shift Decomposition -->
      <div class="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-card flex flex-col gap-5">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-100">
          <div>
            <h2 class="text-sm font-bold text-slate-900">Usual Level vs. Pressure-Specific Shift</h2>
            <span class="text-xs text-slate-500">Bayesian decomposition isolating general talent baseline (β) vs crunch-moment deviation (δ)</span>
          </div>
          <div class="flex items-center gap-4 text-xs font-semibold text-slate-500">
            <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-[#0B1B3F]"></span> Baseline (β)</span>
            <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-[#E6007E]"></span> Pressure Shift (δ)</span>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Baseline / Usual Level -->
          <div class="p-4 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-2">
            <div class="flex items-center justify-between text-xs">
              <span class="font-bold text-slate-700">Baseline / Usual Level (β)</span>
              <span class="font-mono font-bold text-slate-900">${player.beta != null ? `${player.beta > 0 ? "+" : ""}${player.beta.toFixed(1)} runs/100b` : "—"}</span>
            </div>
            <div class="text-[11px] text-slate-400 font-mono">
              80% CI: [${player.beta_lo80 != null ? player.beta_lo80.toFixed(1) : "—"}, ${player.beta_hi80 != null ? player.beta_hi80.toFixed(1) : "—"}]
            </div>
            <div class="mt-2 flex justify-center">
              ${interval({ rating: player.beta, lo80: player.beta_lo80, hi80: player.beta_hi80 }, -15, 55, false)}
            </div>
          </div>

          <!-- Pressure Shift -->
          <div class="p-4 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-2">
            <div class="flex items-center justify-between text-xs">
              <span class="font-bold text-slate-700">Pressure Shift (δ)</span>
              <span class="font-mono font-bold text-[#E6007E]">${player.delta != null ? `${player.delta > 0 ? "+" : ""}${player.delta.toFixed(1)} runs/100b` : "—"}</span>
            </div>
            <div class="text-[11px] text-slate-400 font-mono">
              80% CI: [${player.delta_lo80 != null ? player.delta_lo80.toFixed(1) : "—"}, ${player.delta_hi80 != null ? player.delta_hi80.toFixed(1) : "—"}]
            </div>
            <div class="mt-2 flex justify-center">
              ${interval({ rating: player.delta, lo80: player.delta_lo80, hi80: player.delta_hi80 }, -25, 25, true)}
            </div>
          </div>
        </div>

        <div class="p-3.5 rounded-xl bg-[#FFF0F7] border border-[#E6007E]/20 text-xs text-slate-700 leading-relaxed">
          <strong>Analytical Interpretation:</strong> ${deltaCaption}
        </div>
      </div>

      <!-- High vs Low Performance Dumbbell (if available) -->
      ${
        hasHighLow
          ? `
            <div class="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-card flex flex-col gap-4">
              <div class="flex items-center justify-between pb-3 border-b border-slate-100">
                <h2 class="text-sm font-bold text-slate-900">Ordinary vs High-Pressure Performance</h2>
                <div class="flex items-center gap-3 text-xs text-slate-500">
                  <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-slate-400"></span> Low Pressure (${player.low_n || 0} balls)</span>
                  <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-[#E6007E]"></span> High Pressure (${player.high_n || 0} balls)</span>
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="p-4 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-2">
                  <div class="flex items-center justify-between text-xs">
                    <span class="font-bold text-slate-700">${player.metric_label || "Scoring Rate"}</span>
                    <span class="font-mono text-xs font-bold text-[#E6007E]">
                      Shift: ${(player.metric_high - player.metric_low) > 0 ? "+" : ""}${(player.metric_high - player.metric_low).toFixed(1)}
                    </span>
                  </div>
                  <div class="flex items-center justify-between text-xs font-mono text-slate-600 mt-2">
                    <span>Low: ${player.metric_low?.toFixed(1)}</span>
                    <span>High: ${player.metric_high?.toFixed(1)}</span>
                  </div>
                </div>

                <div class="p-4 rounded-xl bg-slate-50 border border-slate-100 flex flex-col gap-2">
                  <div class="flex items-center justify-between text-xs">
                    <span class="font-bold text-slate-700">Strike Rate Elevation</span>
                    <span class="font-mono text-xs font-bold text-[#E6007E]">
                      ${player.strike_rate_high && player.strike_rate_low ? `${(player.strike_rate_high - player.strike_rate_low) > 0 ? "+" : ""}${(player.strike_rate_high - player.strike_rate_low).toFixed(1)} SR` : "—"}
                    </span>
                  </div>
                  <div class="flex items-center justify-between text-xs font-mono text-slate-600 mt-2">
                    <span>Low: ${player.strike_rate_low ? player.strike_rate_low.toFixed(1) : "—"}</span>
                    <span>High: ${player.strike_rate_high ? player.strike_rate_high.toFixed(1) : "—"}</span>
                  </div>
                </div>
              </div>
            </div>
          `
          : ""
      }

      <!-- Consistency, Risk & Availability -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        <!-- Consistency & Risk -->
        <div class="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-card flex flex-col justify-between">
          <div>
            <h2 class="text-sm font-bold text-slate-900 pb-3 border-b border-slate-100">Consistency &amp; Volatility</h2>
            
            <div class="flex flex-col gap-4 mt-4">
              <div>
                <div class="flex items-center justify-between text-xs mb-1">
                  <span class="font-bold text-slate-700">Positive Ball Contribution Rate</span>
                  <span class="font-mono font-bold text-slate-900">${pct(player.p_pos)}</span>
                </div>
                <div class="text-[11px] text-slate-400">Pool Median: ${pct(medianPos)}</div>
                <div class="w-full bg-slate-100 rounded-full h-1.5 mt-2">
                  <div class="bg-[#0C9588] h-1.5 rounded-full" style="width: ${Math.round((player.p_pos || 0) * 100)}%;"></div>
                </div>
              </div>

              <div>
                <div class="flex items-center justify-between text-xs mb-1">
                  <span class="font-bold text-slate-700">Disaster Dismissal Rate (&lt;10b)</span>
                  <span class="font-mono font-bold text-slate-900">${pct(player.disaster_rate)}</span>
                </div>
                <div class="text-[11px] text-slate-400">Pool Median: ${pct(medianDisaster)}</div>
                <div class="w-full bg-slate-100 rounded-full h-1.5 mt-2">
                  <div class="bg-[#ba1a1a] h-1.5 rounded-full" style="width: ${Math.round((player.disaster_rate || 0) * 100)}%;"></div>
                </div>
              </div>
            </div>
          </div>

          <div class="mt-6 pt-4 border-t border-slate-100 text-[11px] text-slate-400">
            Assesses catastrophic failure rate in leverage situations
          </div>
        </div>

        <!-- Availability & Similar Profiles -->
        <div class="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-card flex flex-col justify-between">
          <div>
            <h2 class="text-sm font-bold text-slate-900 pb-3 border-b border-slate-100">Availability &amp; Cohort Peers</h2>
            
            <div class="flex items-center justify-between py-3 border-b border-slate-100 text-xs">
              <span class="text-slate-500">Last Tracked Match</span>
              <span class="font-mono font-bold text-slate-800">${date(player.last_match_date)} (${player.days_since} days ago)</span>
            </div>

            <div class="mt-4 flex flex-col gap-2">
              <span class="text-xs font-bold text-slate-700 uppercase tracking-wider text-[10px]">Nearest Similar Profiles (by Rating)</span>
              <div class="flex flex-col gap-1.5">
                ${similarPlayers.map(sp => `
                  <a href="#/player/${sp.player_id}" class="p-2 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-100 transition-colors flex items-center justify-between text-xs group">
                    <span class="font-bold text-slate-800 group-hover:text-[#E6007E] transition-colors">${esc(sp.name)}</span>
                    <span class="font-mono text-slate-600">${sp.rating > 0 ? "+" : ""}${sp.rating.toFixed(1)} runs/100b</span>
                  </a>
                `).join("")}
              </div>
            </div>
          </div>

          <div class="mt-6 pt-4 border-t border-slate-100 text-[11px] text-slate-400">
            Selected using nearest-neighbor Euclidean distance over latent clutch score
          </div>
        </div>

      </div>

    </div>
  `;
}
