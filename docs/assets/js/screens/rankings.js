import { n, pct, initials, esc, interval, chips, notAvailableCard } from "../format.js";
import { forest } from "../charts.js";

export function renderRankings(container, state, data) {
  if (!data || !data.meta) {
    container.innerHTML = notAvailableCard("Rankings Data");
    return;
  }

  const meta = data.meta;
  const currentRole = state.role || "batter";
  const allBatters = data.players_batters || [];
  const allBowlers = data.players_bowlers || [];
  const minHighFloor = meta.rules?.min_high_balls?.[currentRole] || (currentRole === "batter" ? 150 : 120);

  // Local filter & pagination state
  let searchQuery = "";
  let minBalls = minHighFloor;
  let activeOnly = true;
  let iplOnly = false;
  let selectedTeam = "all";
  let sortKey = "rank";
  let sortDir = "asc";
  let currentPage = 1;
  const pageSize = 15;

  // Extract unique IPL teams for the dropdown
  const playerPool = currentRole === "batter" ? allBatters : allBowlers;
  const allTeams = Array.from(
    new Set(
      playerPool.flatMap(p => p.ipl_teams || [])
    )
  ).sort();

  function getFilteredAndSortedPlayers() {
    const rawList = currentRole === "batter" ? allBatters : allBowlers;

    const filtered = rawList.filter(p => {
      // Name search: case-insensitive, trimmed, word match
      if (searchQuery) {
        const words = searchQuery.toLowerCase().trim().split(/\s+/);
        const pName = (p.name || "").toLowerCase();
        const matchesAll = words.every(w => pName.includes(w));
        if (!matchesAll) return false;
      }

      // Min HIGH balls
      if (p.n_high < minBalls) return false;

      // Active only
      if (activeOnly && p.active === false) return false;

      // IPL only
      if (iplOnly && !p.ipl_experience && (!p.ipl_teams || p.ipl_teams.length === 0)) return false;

      // Team filter
      if (selectedTeam !== "all") {
        if (!p.ipl_teams || !p.ipl_teams.includes(selectedTeam)) return false;
      }

      return true;
    });

    // Sorting
    filtered.sort((a, b) => {
      let valA = a[sortKey];
      let valB = b[sortKey];
      if (valA == null) valA = sortDir === "asc" ? Infinity : -Infinity;
      if (valB == null) valB = sortDir === "asc" ? Infinity : -Infinity;

      if (typeof valA === "string") {
        return sortDir === "asc"
          ? valA.localeCompare(valB)
          : valB.localeCompare(valA);
      }
      return sortDir === "asc" ? valA - valB : valB - valA;
    });

    return filtered;
  }

  function downloadFilteredCSV(players) {
    const headers = [
      "rank", "player_id", "name", "role", "rating", "lo80", "hi80",
      "p_top10", "n_high", "n_ipl_high", "n_t20i_high", "beta", "delta", "estimator"
    ];
    const rows = players.map(p => [
      p.rank,
      p.player_id,
      `"${(p.name || "").replace(/"/g, '""')}"`,
      p.role,
      p.rating?.toFixed(2),
      p.lo80?.toFixed(2),
      p.hi80?.toFixed(2),
      (p.p_top10 * 100).toFixed(0) + "%",
      p.n_high,
      p.n_ipl_high,
      p.n_t20i_high,
      p.beta?.toFixed(2),
      p.delta?.toFixed(2),
      p.estimator || ""
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `rankings_${currentRole}s_filtered.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  function renderView() {
    const filteredPlayers = getFilteredAndSortedPlayers();
    const totalCount = filteredPlayers.length;
    const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
    if (currentPage > totalPages) currentPage = totalPages;

    const startIdx = (currentPage - 1) * pageSize;
    const endIdx = Math.min(startIdx + pageSize, totalCount);
    const pagedPlayers = filteredPlayers.slice(startIdx, endIdx);

    const isBelowFloor = minBalls < minHighFloor;

    container.innerHTML = `
      <div class="p-6 sm:p-8 max-w-[1600px] mx-auto w-full flex flex-col gap-6">
        
        <!-- Header & Role Switcher -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <span class="text-[10px] font-bold text-[#9D174D] uppercase tracking-wider bg-[#FFF0F7] px-2 py-0.5 rounded-md border border-[#E6007E]/20">
                SEASON 2026 ENGINE
              </span>
              <span class="text-xs text-slate-400 font-medium">• 80% interval (bootstrap) Posterior Mean</span>
            </div>
            <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight" tabindex="-1">
              Player Rankings
            </h1>
            <p class="text-xs sm:text-sm text-slate-500 mt-1 max-w-3xl leading-relaxed">
              Empirical Bayes latent clutch score — calibrated runs delivered above contextual expectation per 100 high-leverage deliveries.
            </p>
          </div>

          <!-- Role Toggle Buttons -->
          <div class="flex items-center p-1 bg-slate-900 rounded-2xl shadow-sm self-start sm:self-auto">
            <button id="btn-role-batter" class="px-5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${currentRole === "batter" ? "bg-[#E6007E] text-white shadow-xs" : "text-slate-400 hover:text-white"}">
              <span>🏏 Batters</span>
              <span class="px-1.5 py-0.5 rounded-full text-[10px] ${currentRole === "batter" ? "bg-white/20 text-white" : "bg-slate-800 text-slate-400"}">${allBatters.length}</span>
            </button>
            <button id="btn-role-bowler" class="px-5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${currentRole === "bowler" ? "bg-[#E6007E] text-white shadow-xs" : "text-slate-400 hover:text-white"}">
              <span>🎯 Bowlers</span>
              <span class="px-1.5 py-0.5 rounded-full text-[10px] ${currentRole === "bowler" ? "bg-white/20 text-white" : "bg-slate-800 text-slate-400"}">${allBowlers.length}</span>
            </button>
          </div>
        </div>

        <!-- Filter Controls Toolbar -->
        <div class="bg-white rounded-2xl border border-[#E2E8F0] p-5 shadow-card flex flex-col gap-4">
          <div class="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
            
            <!-- Min HIGH balls slider -->
            <div class="md:col-span-4 flex flex-col gap-1.5">
              <div class="flex items-center justify-between text-xs font-semibold text-slate-700">
                <span class="flex items-center gap-1.5">
                  <span>Min HIGH Balls</span>
                  ${isBelowFloor ? `<span class="px-1.5 py-0.5 text-[9px] font-bold rounded-md bg-amber-100 text-amber-800 border border-amber-200">Below Floor (${minHighFloor})</span>` : ""}
                </span>
                <span class="font-mono text-slate-900 font-bold" id="val-min-balls">${minBalls} balls</span>
              </div>
              <input 
                id="slider-min-balls" 
                type="range" 
                min="0" 
                max="500" 
                step="10" 
                value="${minBalls}"
                class="w-full accent-[#E6007E] cursor-pointer"
                aria-label="Minimum high pressure balls slider"
              />
            </div>

            <!-- Active Only Toggle -->
            <div class="md:col-span-2 flex items-center gap-2">
              <label class="relative inline-flex items-center cursor-pointer select-none">
                <input type="checkbox" id="toggle-active-only" class="sr-only peer" ${activeOnly ? "checked" : ""}>
                <div class="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#0C9588]"></div>
                <span class="ml-2.5 text-xs font-semibold text-slate-700">Active (365d)</span>
              </label>
            </div>

            <!-- IPL Only Toggle -->
            <div class="md:col-span-2 flex items-center gap-2">
              <label class="relative inline-flex items-center cursor-pointer select-none">
                <input type="checkbox" id="toggle-ipl-only" class="sr-only peer" ${iplOnly ? "checked" : ""}>
                <div class="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#E6007E]"></div>
                <span class="ml-2.5 text-xs font-semibold text-slate-700">IPL caps only</span>
              </label>
            </div>

            <!-- Team Multi-Select / Dropdown -->
            <div class="md:col-span-2">
              <select id="select-team-filter" aria-label="Filter by franchise team" class="w-full text-xs font-medium rounded-xl border border-slate-200 bg-slate-50 py-2 px-3 text-slate-700 focus:bg-white focus:border-[#E6007E] focus:outline-none">
                <option value="all">All Teams</option>
                ${allTeams.map(t => `<option value="${esc(t)}" ${selectedTeam === t ? "selected" : ""}>${esc(t)}</option>`).join("")}
              </select>
            </div>

            <!-- Export CSV Button -->
            <div class="md:col-span-2 flex justify-end">
              <button id="btn-export-csv" class="w-full sm:w-auto px-4 py-2 rounded-xl border border-slate-200 bg-slate-50 hover:bg-white hover:border-slate-300 text-xs font-bold text-slate-700 transition-colors flex items-center justify-center gap-1.5 shadow-xs" title="Download filtered CSV">
                <span class="material-symbols-outlined text-[16px] text-slate-500">download</span>
                <span>Export CSV (${totalCount})</span>
              </button>
            </div>

          </div>

          <!-- Search Input Bar -->
          <div class="relative w-full">
            <span class="material-symbols-outlined absolute left-3 top-2.5 text-[18px] text-slate-400 pointer-events-none">search</span>
            <input 
              id="filter-player-search" 
              type="text" 
              placeholder="Search by player name or franchise..." 
              value="${esc(searchQuery)}"
              class="w-full pl-9 pr-4 py-2 text-xs rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-[#E6007E] focus:outline-none focus:ring-1 focus:ring-[#E6007E] text-slate-900 placeholder-slate-400 font-medium transition-all"
            />
          </div>
        </div>

        <!-- Main Content Grid: Table + Forest Plot -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          <!-- Rankings Table Column -->
          <div class="lg:col-span-8 bg-white rounded-2xl border border-[#E2E8F0] shadow-card overflow-hidden flex flex-col">
            <div class="overflow-x-auto">
              <table class="w-full text-left border-collapse" id="rankings-table">
                <thead>
                  <tr class="bg-slate-50/70 border-b border-slate-100 text-[10px] font-bold text-slate-400 uppercase tracking-wider select-none">
                    <th class="py-3 px-3 w-12 text-left cursor-pointer hover:text-slate-700" data-sort="rank" aria-sort="${sortKey === "rank" ? (sortDir === "asc" ? "ascending" : "descending") : "none"}">
                      <span class="flex items-center gap-1"># ${sortKey === "rank" ? (sortDir === "asc" ? "↓" : "↑") : ""}</span>
                    </th>
                    <th class="py-3 px-4 text-left cursor-pointer hover:text-slate-700" data-sort="name" aria-sort="${sortKey === "name" ? (sortDir === "asc" ? "ascending" : "descending") : "none"}">
                      <span class="flex items-center gap-1">Player ${sortKey === "name" ? (sortDir === "asc" ? "↓" : "↑") : ""}</span>
                    </th>
                    <th class="py-3 px-3 text-right cursor-pointer hover:text-slate-700" data-sort="rating" aria-sort="${sortKey === "rating" ? (sortDir === "asc" ? "ascending" : "descending") : "none"}">
                      <span class="flex items-center justify-end gap-1">Rating (80% CI) ${sortKey === "rating" ? (sortDir === "asc" ? "↓" : "↑") : ""}</span>
                    </th>
                    <th class="py-3 px-3 text-right cursor-pointer hover:text-slate-700" data-sort="p_top10" aria-sort="${sortKey === "p_top10" ? (sortDir === "asc" ? "ascending" : "descending") : "none"}">
                      <span class="flex items-center justify-end gap-1">P(Top 10) ${sortKey === "p_top10" ? (sortDir === "asc" ? "↓" : "↑") : ""}</span>
                    </th>
                    <th class="py-3 px-3 text-right cursor-pointer hover:text-slate-700" data-sort="n_high" aria-sort="${sortKey === "n_high" ? (sortDir === "asc" ? "ascending" : "descending") : "none"}">
                      <span class="flex items-center justify-end gap-1">HIGH Balls ${sortKey === "n_high" ? (sortDir === "asc" ? "↓" : "↑") : ""}</span>
                    </th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100" id="rankings-tbody">
                  ${
                    filteredPlayers.length === 0
                      ? `
                        <tr>
                          <td colspan="5" class="py-12 px-4 text-center">
                            <div class="flex flex-col items-center gap-2">
                              <span class="material-symbols-outlined text-[32px] text-slate-300">search_off</span>
                              <span class="text-xs font-bold text-slate-600">No players match the criteria</span>
                              <span class="text-[11px] text-slate-400">Try adjusting your search or relaxing the sample filters</span>
                            </div>
                          </td>
                        </tr>
                      `
                      : pagedPlayers.map((p, idx) => {
                          const isTop10 = p.rank <= 10;
                          const showCutoff = isTop10 && pagedPlayers[idx + 1] && pagedPlayers[idx + 1].rank > 10;
                          const rowBg = isTop10 ? "bg-[#FFF0F7]/40 hover:bg-[#FFF0F7]/70" : "hover:bg-slate-50/80";
                          const rankColor = isTop10 ? "bg-[#E6007E] text-white" : "bg-slate-100 text-slate-600";
                          const pTop10Pct = Math.round((p.p_top10 || 0) * 100);
                          const pillBg = p.p_top10 >= 0.7 ? "bg-[#FFF0F7] text-[#E6007E] border-[#E6007E]/30" : "bg-slate-50 text-slate-600 border-slate-200";

                          const rowHtml = `
                            <tr class="${rowBg} cursor-pointer transition-colors group" onclick="location.hash='#/player/${p.player_id}'" role="button" tabindex="0" onkeydown="if(event.key==='Enter')location.hash='#/player/${p.player_id}'">
                              <td class="py-3 px-3 text-left w-12">
                                <span class="w-6 h-6 rounded-lg ${rankColor} text-xs font-bold flex items-center justify-center font-mono shadow-xs">
                                  ${p.rank}
                                </span>
                              </td>
                              <td class="py-3 px-4 text-left">
                                <div class="flex items-center gap-2.5">
                                  <span class="w-8 h-8 rounded-full bg-slate-900 text-white text-[11px] font-bold flex items-center justify-center shrink-0">
                                    ${initials(p.name)}
                                  </span>
                                  <div class="flex flex-col min-w-0">
                                    <span class="text-xs font-bold text-slate-900 group-hover:text-[#E6007E] transition-colors truncate">
                                      ${esc(p.name)}
                                    </span>
                                    <div class="flex items-center gap-1 mt-0.5 truncate">
                                      ${chips(p)}
                                    </div>
                                  </div>
                                </div>
                              </td>
                              <td class="py-3 px-3 text-right">
                                <div class="flex flex-col items-end">
                                  <span class="font-mono text-xs font-bold text-slate-900">
                                    ${p.rating > 0 ? "+" : ""}${n(p.rating, 1)}
                                  </span>
                                  <span class="text-[10px] text-slate-400 font-mono">
                                    [${n(p.lo80, 1)}, ${n(p.hi80, 1)}]
                                  </span>
                                </div>
                              </td>
                              <td class="py-3 px-3 text-right">
                                <span class="px-2 py-0.5 rounded-md border text-[11px] font-bold font-mono ${pillBg}">
                                  ${pTop10Pct}%
                                </span>
                              </td>
                              <td class="py-3 px-3 text-right font-mono text-xs font-bold text-slate-700">
                                ${n(p.n_high)}
                              </td>
                            </tr>
                          `;

                          if (showCutoff) {
                            return (
                              rowHtml +
                              `
                                <tr>
                                  <td colspan="5" class="py-2 px-4 bg-gradient-to-r from-[#FFF0F7] to-white border-y border-[#E6007E]/20 text-center">
                                    <div class="flex items-center justify-center gap-2 text-[10px] font-bold uppercase tracking-wider text-[#E6007E]">
                                      <span class="material-symbols-outlined text-[14px]">flag</span>
                                      <span>Top 10 Cut-off (Posterior Frontier)</span>
                                    </div>
                                  </td>
                                </tr>
                              `
                            );
                          }
                          return rowHtml;
                        }).join("")
                  }
                </tbody>
              </table>
            </div>

            <!-- Pagination Footer -->
            <div class="p-4 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
              <div>
                Showing <span class="font-bold text-slate-700">${totalCount === 0 ? 0 : startIdx + 1}–${endIdx}</span> of <span class="font-bold text-slate-700">${totalCount}</span> qualified ${currentRole}s
              </div>
              <div class="flex items-center gap-1.5" id="pagination-controls">
                <button id="btn-page-prev" class="w-8 h-8 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 flex items-center justify-center font-bold text-slate-600 disabled:opacity-40 disabled:pointer-events-none transition-colors" ${currentPage <= 1 ? "disabled" : ""} aria-label="Previous Page">
                  ‹
                </button>
                ${Array.from({ length: totalPages }, (_, i) => i + 1)
                  .filter(p => p === 1 || p === totalPages || Math.abs(p - currentPage) <= 1)
                  .map((p, idx, arr) => {
                    const isEllipsisBefore = idx > 0 && p - arr[idx - 1] > 1;
                    return `
                      ${isEllipsisBefore ? `<span class="px-1 text-slate-400">…</span>` : ""}
                      <button class="btn-page-num w-8 h-8 rounded-lg border text-xs font-bold transition-colors ${p === currentPage ? "bg-[#0B1B3F] text-white border-[#0B1B3F]" : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"}" data-page="${p}">
                        ${p}
                      </button>
                    `;
                  }).join("")}
                <button id="btn-page-next" class="w-8 h-8 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 flex items-center justify-center font-bold text-slate-600 disabled:opacity-40 disabled:pointer-events-none transition-colors" ${currentPage >= totalPages ? "disabled" : ""} aria-label="Next Page">
                  ›
                </button>
              </div>
            </div>

          </div>

          <!-- Forest Plot Column -->
          <div class="lg:col-span-4 bg-white rounded-2xl border border-[#E2E8F0] p-5 shadow-card flex flex-col gap-3">
            <div class="flex items-center justify-between pb-3 border-b border-slate-100">
              <div class="flex flex-col">
                <span class="text-[10px] font-bold uppercase tracking-wider text-slate-500">Comparative Distribution</span>
                <h2 class="text-sm font-bold text-slate-900">Forest Plot (Top 25)</h2>
              </div>
              <span class="w-2 h-2 rounded-full bg-[#E6007E]"></span>
            </div>

            <div id="rankings-forest-container" role="region" aria-label="Top 25 forest plot showing point estimates and 80% interval (bootstrap)" class="w-full h-[580px]">
              <!-- ECharts forest plot rendered here -->
            </div>

            <div class="pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-600">
              <span class="flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-[#E6007E]"></span> Top 10 Tier
              </span>
              <span class="flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-slate-500"></span> Chasing Tier
              </span>
            </div>
          </div>

        </div>

      </div>
    `;

    // Initialize Forest Chart
    const forestEl = container.querySelector("#rankings-forest-container");
    if (forestEl) {
      forest(forestEl, filteredPlayers);
    }

    // Attach Event Listeners
    // 1. Role switcher
    container.querySelector("#btn-role-batter")?.addEventListener("click", () => {
      state.role = "batter";
      currentPage = 1;
      renderRankings(container, state, data);
    });
    container.querySelector("#btn-role-bowler")?.addEventListener("click", () => {
      state.role = "bowler";
      currentPage = 1;
      renderRankings(container, state, data);
    });

    // 2. Search input
    const searchInput = container.querySelector("#filter-player-search");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        searchQuery = e.target.value;
        currentPage = 1;
        renderView();
        // Restore focus and cursor to search input
        const newSearch = container.querySelector("#filter-player-search");
        if (newSearch) {
          newSearch.focus();
          newSearch.setSelectionRange(searchQuery.length, searchQuery.length);
        }
      });
    }

    // 3. Min balls slider
    const slider = container.querySelector("#slider-min-balls");
    if (slider) {
      slider.addEventListener("input", (e) => {
        minBalls = Number(e.target.value);
        container.querySelector("#val-min-balls").textContent = `${minBalls} balls`;
      });
      slider.addEventListener("change", (e) => {
        minBalls = Number(e.target.value);
        currentPage = 1;
        renderView();
      });
    }

    // 4. Active only toggle
    container.querySelector("#toggle-active-only")?.addEventListener("change", (e) => {
      activeOnly = e.target.checked;
      currentPage = 1;
      renderView();
    });

    // 5. IPL only toggle
    container.querySelector("#toggle-ipl-only")?.addEventListener("change", (e) => {
      iplOnly = e.target.checked;
      currentPage = 1;
      renderView();
    });

    // 6. Team filter dropdown
    container.querySelector("#select-team-filter")?.addEventListener("change", (e) => {
      selectedTeam = e.target.value;
      currentPage = 1;
      renderView();
    });

    // 7. Table headers sort
    container.querySelectorAll("#rankings-table th[data-sort]").forEach(th => {
      th.addEventListener("click", () => {
        const key = th.getAttribute("data-sort");
        if (sortKey === key) {
          sortDir = sortDir === "asc" ? "desc" : "asc";
        } else {
          sortKey = key;
          sortDir = key === "name" || key === "rank" ? "asc" : "desc";
        }
        currentPage = 1;
        renderView();
      });
    });

    // 8. Pagination buttons
    container.querySelector("#btn-page-prev")?.addEventListener("click", () => {
      if (currentPage > 1) {
        currentPage--;
        renderView();
      }
    });
    container.querySelector("#btn-page-next")?.addEventListener("click", () => {
      if (currentPage < totalPages) {
        currentPage++;
        renderView();
      }
    });
    container.querySelectorAll(".btn-page-num").forEach(btn => {
      btn.addEventListener("click", () => {
        currentPage = Number(btn.getAttribute("data-page"));
        renderView();
      });
    });

    // 9. Export CSV
    container.querySelector("#btn-export-csv")?.addEventListener("click", () => {
      downloadFilteredCSV(filteredPlayers);
    });
  }

  renderView();
}
