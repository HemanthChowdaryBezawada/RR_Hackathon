import { n, pct, initials, esc, interval, chips, notAvailableCard } from "../format.js";
import { byId, activePlayers } from "../data.js";

export function renderCompare(container, state, data) {
  if (!data || !data.meta) {
    container.innerHTML = notAvailableCard("Comparison Intelligence Data");
    return;
  }

  const allBatters = data.players_batters || [];
  const allBowlers = data.players_bowlers || [];
  const allPlayers = [...allBatters, ...allBowlers];

  // Parse player IDs from hash (?ids=id1,id2,id3)
  const hash = location.hash || "";
  const queryMatch = hash.match(/[?&]ids=([^&]+)/);
  let selectedIds = [];

  if (queryMatch) {
    selectedIds = queryMatch[1].split(",").map(s => s.trim()).filter(Boolean);
  }

  // If no IDs given or empty, default to top 3 batters
  if (selectedIds.length === 0 && allBatters.length >= 3) {
    selectedIds = [allBatters[0].player_id, allBatters[1].player_id, allBatters[2].player_id].map(String);
  }

  // Limit to max 3 players
  if (selectedIds.length > 3) {
    selectedIds = selectedIds.slice(0, 3);
  }

  const players = selectedIds.map(id => byId(data, id)).filter(Boolean);

  function updateUrl(newIds) {
    location.hash = `#/compare?ids=${newIds.join(",")}`;
  }

  container.innerHTML = `
    <div class="p-6 sm:p-8 max-w-[1600px] mx-auto w-full flex flex-col gap-6">
      
      <!-- Screen Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2 mb-1">
            <span class="text-[10px] font-bold text-[#9D174D] uppercase tracking-wider bg-[#FFF0F7] px-2 py-0.5 rounded-md border border-[#E6007E]/20">
              CROSS-PLAYER BENCHMARK
            </span>
            <span class="text-xs text-slate-400 font-medium">• Multi-Dimensional Clutch Evaluation</span>
          </div>
          <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight" tabindex="-1">
            Player Comparison
          </h1>
          <p class="text-xs sm:text-sm text-slate-500 mt-1 max-w-3xl leading-relaxed">
            Compare pressure performance, underlying ability decomposition, and credible intervals across qualified candidates.
          </p>
        </div>

        <!-- Add Player Search Input -->
        <div class="relative w-full sm:w-72">
          <div class="relative flex items-center">
            <span class="material-symbols-outlined absolute left-2.5 text-[17px] text-slate-400 pointer-events-none">person_add</span>
            <input 
              id="compare-search-input" 
              type="text" 
              placeholder="Add player (max 3)..." 
              class="w-full pl-8 pr-3 py-2 text-xs rounded-xl border border-slate-200 bg-white focus:border-[#E6007E] focus:outline-none focus:ring-1 focus:ring-[#E6007E] text-slate-800 placeholder-slate-400 font-medium transition-all shadow-xs"
              autocomplete="off"
            />
          </div>
          <!-- Typeahead Search Results Dropdown -->
          <div id="compare-search-results" class="hidden absolute right-0 left-0 mt-1 max-h-60 overflow-y-auto rounded-xl bg-white border border-[#E2E8F0] shadow-dropdown z-50 py-1 text-xs">
            <!-- Dynamically populated -->
          </div>
          <div id="compare-limit-warning" class="hidden mt-1 text-[11px] font-semibold text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-1.5 text-center">
            Comparison limit reached (max 3 players). Remove one to add another.
          </div>
        </div>
      </div>

      <!-- Comparison Cards Header Grid -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        ${
          players.length === 0
            ? `<div class="col-span-3 p-12 text-center text-slate-400 bg-white rounded-2xl border border-slate-200">No players selected for comparison. Use the search box above to add players.</div>`
            : players.map(p => `
                <div class="bg-white rounded-2xl border border-[#E2E8F0] p-5 shadow-card flex flex-col justify-between relative group">
                  <button class="btn-remove-player absolute top-4 right-4 w-7 h-7 rounded-lg bg-slate-50 hover:bg-red-50 text-slate-400 hover:text-red-600 transition-colors flex items-center justify-center text-xs font-bold" data-id="${p.player_id}" title="Remove from comparison">
                    ✕
                  </button>
                  <div>
                    <div class="flex items-center gap-3 mb-3">
                      <span class="w-10 h-10 rounded-xl bg-[#0B1B3F] text-white flex items-center justify-center font-bold text-xs font-mono shadow-xs">
                        ${initials(p.name)}
                      </span>
                      <div class="flex flex-col min-w-0 pr-6">
                        <div class="flex items-center gap-1.5 mb-0.5">
                          <span class="px-1.5 py-0.5 rounded text-[9px] font-bold ${p.rank <= 10 ? "bg-[#FFF0F7] text-[#E6007E]" : "bg-slate-100 text-slate-600"}">
                            #${p.rank}
                          </span>
                          <span class="text-[10px] text-slate-400 font-bold uppercase">${p.role}</span>
                        </div>
                        <a href="#/player/${p.player_id}" class="text-sm font-bold text-slate-900 hover:text-[#E6007E] transition-colors truncate">
                          ${esc(p.name)}
                        </a>
                      </div>
                    </div>
                    <div class="flex items-baseline gap-2 mt-2">
                      <span class="text-2xl font-extrabold text-slate-900 font-mono tracking-tight">
                        ${p.rating > 0 ? "+" : ""}${n(p.rating, 1)}
                      </span>
                      <span class="text-[11px] text-slate-500">runs / 100b</span>
                    </div>
                    <div class="text-[11px] text-slate-400 font-mono">
                      80% CI: [${n(p.lo80, 1)}, ${n(p.hi80, 1)}]
                    </div>
                  </div>

                  <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span class="text-slate-500">P(Top 10)</span>
                    <span class="font-bold font-mono text-[#E6007E]">${pct(p.p_top10)}</span>
                  </div>
                </div>
              `).join("")
        }
      </div>

      <!-- Credible Intervals Overlap Visualizer -->
      ${
        players.length > 0
          ? `
            <div class="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-card flex flex-col gap-4">
              <div class="flex items-center justify-between pb-3 border-b border-slate-100">
                <h2 class="text-sm font-bold text-slate-900">Latent Clutch Rating Posterior Uncertainty (80% Credible Intervals)</h2>
                <span class="text-xs text-slate-400 font-medium">Overlapping whiskers indicate statistical parity</span>
              </div>
              
              <div class="flex flex-col gap-3 py-2">
                ${players.map(p => `
                  <div class="grid grid-cols-12 items-center gap-4 text-xs">
                    <div class="col-span-3 sm:col-span-2 font-bold text-slate-800 truncate">
                      ${esc(p.name)}
                    </div>
                    <div class="col-span-6 sm:col-span-8 flex justify-center">
                      ${interval(p, -15, 55, p.rank <= 10)}
                    </div>
                    <div class="col-span-3 sm:col-span-2 text-right font-mono font-bold text-slate-900">
                      ${p.rating > 0 ? "+" : ""}${n(p.rating, 1)}
                    </div>
                  </div>
                `).join("")}
              </div>

              <div class="p-3 rounded-xl bg-slate-50 border border-slate-100 text-[11px] text-slate-500 leading-relaxed">
                <strong>Analytical Takeaway:</strong> Overlapping credible intervals indicate uncertainty in relative ordering. Rank differences should not automatically be interpreted as meaningful performance separation.
              </div>
            </div>
          `
          : ""
      }

      <!-- Detailed Side-by-Side Comparison Matrix -->
      ${
        players.length > 0
          ? `
            <div class="bg-white rounded-2xl border border-[#E2E8F0] shadow-card overflow-hidden">
              <div class="p-5 border-b border-slate-100">
                <h2 class="text-sm font-bold text-slate-900">Multi-Dimensional Metric Comparison</h2>
              </div>
              <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr class="bg-slate-50/70 border-b border-slate-100 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                      <th class="py-3 px-4 w-48">Metric Dimension</th>
                      ${players.map(p => `<th class="py-3 px-4 font-bold text-slate-900">${esc(p.name)}</th>`).join("")}
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-slate-100">
                    
                    <!-- 1. Latent Clutch Performance -->
                    <tr class="bg-slate-50/40 font-bold text-[11px] text-slate-700">
                      <td colspan="${players.length + 1}" class="py-2 px-4 uppercase tracking-wider">1. Clutch Performance</td>
                    </tr>
                    <tr>
                      <td class="py-3 px-4 text-slate-500">Clutch Rating (Runs / 100b)</td>
                      ${players.map(p => `<td class="py-3 px-4 font-mono font-bold text-slate-900">${p.rating > 0 ? "+" : ""}${n(p.rating, 1)}</td>`).join("")}
                    </tr>
                    <tr>
                      <td class="py-3 px-4 text-slate-500">P(Top 10) Probability</td>
                      ${players.map(p => `<td class="py-3 px-4 font-mono font-bold text-[#E6007E]">${pct(p.p_top10)}</td>`).join("")}
                    </tr>
                    <tr>
                      <td class="py-3 px-4 text-slate-500">80% Credible Range</td>
                      ${players.map(p => `<td class="py-3 px-4 font-mono text-slate-600">[${n(p.lo80, 1)}, ${n(p.hi80, 1)}]</td>`).join("")}
                    </tr>
                    <tr>
                      <td class="py-3 px-4 text-slate-500">HIGH-Pressure Balls</td>
                      ${players.map(p => `<td class="py-3 px-4 font-mono font-bold text-slate-700">${n(p.n_high)}</td>`).join("")}
                    </tr>

                    <!-- 2. Underlying Ability Decomposition -->
                    <tr class="bg-slate-50/40 font-bold text-[11px] text-slate-700">
                      <td colspan="${players.length + 1}" class="py-2 px-4 uppercase tracking-wider">2. Underlying Ability Decomposition</td>
                    </tr>
                    <tr>
                      <td class="py-3 px-4 text-slate-500">Baseline Usual Level (β)</td>
                      ${players.map(p => `<td class="py-3 px-4 font-mono font-bold text-slate-800">${p.beta != null ? `${p.beta > 0 ? "+" : ""}${n(p.beta, 1)}` : "—"}</td>`).join("")}
                    </tr>
                    <tr>
                      <td class="py-3 px-4 text-slate-500">Pressure Shift (δ)</td>
                      ${players.map(p => `<td class="py-3 px-4 font-mono font-bold text-[#E6007E]">${p.delta != null ? `${p.delta > 0 ? "+" : ""}${n(p.delta, 1)}` : "—"}</td>`).join("")}
                    </tr>

                    <!-- 3. Consistency & Exposure -->
                    <tr class="bg-slate-50/40 font-bold text-[11px] text-slate-700">
                      <td colspan="${players.length + 1}" class="py-2 px-4 uppercase tracking-wider">3. Consistency &amp; Sample</td>
                    </tr>
                    <tr>
                      <td class="py-3 px-4 text-slate-500">Positive Ball Contribution Rate</td>
                      ${players.map(p => `<td class="py-3 px-4 font-mono">${pct(p.p_pos)}</td>`).join("")}
                    </tr>
                    <tr>
                      <td class="py-3 px-4 text-slate-500">Disaster Dismissal Rate (&lt;10b)</td>
                      ${players.map(p => `<td class="py-3 px-4 font-mono">${pct(p.disaster_rate)}</td>`).join("")}
                    </tr>
                    <tr>
                      <td class="py-3 px-4 text-slate-500">IPL Sample Share</td>
                      ${players.map(p => `<td class="py-3 px-4 font-mono">${p.n_high > 0 ? `${Math.round(((p.n_ipl_high || 0) / p.n_high) * 100)}%` : "—"}</td>`).join("")}
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          `
          : ""
      }

    </div>
  `;

  // Attach Event Listeners
  // 1. Remove player buttons
  container.querySelectorAll(".btn-remove-player").forEach(btn => {
    btn.addEventListener("click", () => {
      const remId = btn.getAttribute("data-id");
      const nextIds = selectedIds.filter(id => id !== remId);
      updateUrl(nextIds);
    });
  });

  // 2. Add player search input & typeahead
  const searchInput = container.querySelector("#compare-search-input");
  const searchResults = container.querySelector("#compare-search-results");
  const limitWarning = container.querySelector("#compare-limit-warning");

  if (searchInput && searchResults) {
    searchInput.addEventListener("input", (e) => {
      const q = e.target.value.trim().toLowerCase();
      if (!q) {
        searchResults.classList.add("hidden");
        return;
      }

      const matches = allPlayers.filter(p => (p.name || "").toLowerCase().includes(q));
      if (!matches.length) {
        searchResults.innerHTML = `<div class="p-3 text-slate-400 text-center">No matching players</div>`;
        searchResults.classList.remove("hidden");
        return;
      }

      searchResults.innerHTML = matches.slice(0, 8).map(p => {
        const isSelected = selectedIds.includes(String(p.player_id));
        return `
          <div class="px-3 py-2 cursor-pointer hover:bg-slate-50 flex items-center justify-between border-b border-slate-50 last:border-b-0 ${isSelected ? "opacity-50 pointer-events-none" : ""}" data-id="${p.player_id}">
            <div class="flex items-center gap-2">
              <span class="w-6 h-6 rounded-md bg-slate-900 text-white text-[10px] font-bold flex items-center justify-center font-mono">
                ${initials(p.name)}
              </span>
              <div class="flex flex-col">
                <span class="font-bold text-slate-800">${esc(p.name)}</span>
                <span class="text-[10px] text-slate-400 uppercase">${p.role} • #${p.rank}</span>
              </div>
            </div>
            <span class="font-mono font-bold text-slate-700">${p.rating > 0 ? "+" : ""}${p.rating?.toFixed(1)}</span>
          </div>
        `;
      }).join("");

      searchResults.classList.remove("hidden");

      // Attach clicks to dropdown options
      searchResults.querySelectorAll("[data-id]").forEach(opt => {
        opt.addEventListener("click", () => {
          const addId = opt.getAttribute("data-id");
          if (selectedIds.length >= 3) {
            if (limitWarning) limitWarning.classList.remove("hidden");
            setTimeout(() => { if (limitWarning) limitWarning.classList.add("hidden"); }, 3000);
            return;
          }
          if (!selectedIds.includes(addId)) {
            const nextIds = [...selectedIds, addId];
            updateUrl(nextIds);
          }
          searchInput.value = "";
          searchResults.classList.add("hidden");
        });
      });
    });

    document.addEventListener("click", (e) => {
      if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
        searchResults.classList.add("hidden");
      }
    });
  }
}
