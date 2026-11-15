import { loadData, byId } from "./data.js";
import { renderRankings } from "./screens/rankings.js";
import { renderOverview } from "./screens/overview.js";
import { renderPlayer } from "./screens/player.js";
import { renderCompare } from "./screens/compare.js";
import { renderPressure } from "./screens/pressure.js";
import { renderValidation } from "./screens/validation.js";
import { renderMethod } from "./screens/method.js";
import { initials, esc } from "./format.js";

const routes = {
  overview: {
    category: "Performance Intelligence",
    title: "Overview",
    render: renderOverview
  },
  rankings: {
    breadcrumbHtml: `<span class="text-slate-600 font-medium">Analytics</span><span class="text-slate-400">/</span><span class="text-slate-600 font-medium">Empirical Bayes Model</span><span class="text-slate-400">/</span><span class="text-slate-900 font-bold">Player Rankings</span>`,
    title: "Player Rankings",
    render: renderRankings
  },
  player: {
    breadcrumbHtml: `<span class="text-slate-600 font-medium">Pressure Index</span><span class="text-slate-400">/</span><span class="text-[10px] font-bold text-[#9D174D] uppercase tracking-wider bg-[#FFF0F7] px-2 py-0.5 rounded-md border border-[#E6007E]/20">LEVERAGE ENGINE</span>`,
    title: "Player Deep Dive",
    render: renderPlayer
  },
  compare: {
    breadcrumbHtml: `<span class="text-slate-600 font-medium">Pressure Index</span><span class="text-slate-400">/</span><span class="text-[10px] font-bold text-[#9D174D] uppercase tracking-wider bg-[#FFF0F7] px-2 py-0.5 rounded-md border border-[#E6007E]/20">LEVERAGE ENGINE</span>`,
    title: "Compare Tools",
    render: renderCompare
  },
  pressure: {
    breadcrumbHtml: `<span class="text-slate-600 font-medium">RR Performance Lab</span><span class="text-slate-400">/</span><span class="text-slate-600 font-medium">Pressure Index</span><span class="text-slate-400">/</span><span class="text-slate-900 font-bold">Pressure Definition</span>`,
    title: "Pressure Definition",
    render: renderPressure
  },
  validation: {
    breadcrumbHtml: `<span class="text-slate-600 font-medium">RR Performance Lab</span><span class="text-slate-400">/</span><span class="text-slate-600 font-medium">Science & Rigor</span><span class="text-slate-400">/</span><span class="text-slate-900 font-bold">Model Validation & Robustness</span>`,
    title: "Model Validation & Robustness",
    render: renderValidation
  },
  method: {
    breadcrumbHtml: `<span class="text-slate-600 font-medium">RR Performance Lab</span><span class="text-slate-400">/</span><span class="text-slate-600 font-medium">Science & Rigor</span><span class="text-slate-400">/</span><span class="text-slate-900 font-bold">Methodology</span>`,
    title: "Methodology",
    render: renderMethod
  }
};

const viewContainer = document.querySelector("#view");
const breadcrumbContainer = document.querySelector("#header-breadcrumb-container");
const sidebarToggle = document.querySelector("#sidebar-toggle");
const headerSidebarToggle = document.querySelector("#header-sidebar-toggle");
const mobileMenuBtn = document.querySelector("#mobile-menu-btn");
const appElement = document.querySelector("#app");
const toast = document.querySelector("#toast");
const toastMessage = document.querySelector("#toast-message");

// Global search elements
const globalSearchInput = document.querySelector("#global-player-search");
const globalSearchResults = document.querySelector("#global-search-results");

// Header info popover elements
const headerInfoBtn = document.querySelector("#header-info-btn");
const headerInfoPopover = document.querySelector("#header-info-popover");
const closeInfoPopover = document.querySelector("#close-info-popover");

let data = null;
const state = {
  role: "batter"
};

export function showToast(msg) {
  if (!toast || !toastMessage) return;
  toastMessage.textContent = msg;
  toast.classList.remove("translate-y-20", "opacity-0", "pointer-events-none");
  setTimeout(() => {
    toast.classList.add("translate-y-20", "opacity-0", "pointer-events-none");
  }, 3000);
}

function updateSidebarActive(activeRoute) {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach((item) => {
    const route = item.getAttribute("data-route");
    const icon = item.querySelector(".material-symbols-outlined");
    const dot = item.querySelector(".active-dot");

    if (route === activeRoute) {
      item.setAttribute("aria-current", "page");
      item.className =
        "nav-item flex items-center gap-3 px-3 py-2 rounded-xl bg-slate-900 text-white font-semibold text-[13px] shadow-sm transition-all";
      if (icon) icon.className = "material-symbols-outlined text-[19px] text-[#E6007E]";
      if (!dot) {
        const newDot = document.createElement("span");
        newDot.className = "active-dot ml-auto w-1.5 h-1.5 rounded-full bg-[#E6007E]";
        item.appendChild(newDot);
      }
    } else {
      item.removeAttribute("aria-current");
      item.className =
        "nav-item flex items-center gap-3 px-3 py-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-50 font-medium text-[13px] transition-colors";
      if (icon) icon.className = "material-symbols-outlined text-[19px] text-slate-400";
      if (dot) dot.remove();
    }
  });
}

function parseHash() {
  const raw = location.hash.slice(2) || "overview";
  const [path, query] = raw.split("?");
  const params = new URLSearchParams(query || "");

  if (params.get("role")) {
    state.role = params.get("role");
  }

  // Handle path with parameters, e.g. player/6281
  const segments = path.split("/").filter(Boolean);
  const routeBase = segments[0] || "overview";

  return {
    routeBase,
    segments,
    query: params
  };
}

async function render() {
  const { routeBase, segments } = parseHash();

  // Check for unknown routes
  if (routeBase !== "player" && !routes[routeBase]) {
    document.title = "Page not found — SupeRR Intelligence Engine";
    if (breadcrumbContainer) {
      breadcrumbContainer.innerHTML = `<span class="text-slate-900 font-bold">Page Not Found</span>`;
    }
    viewContainer.innerHTML = `
      <div class="p-12 max-w-lg mx-auto text-center flex flex-col items-center gap-4">
        <div class="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400">
          <span class="material-symbols-outlined text-[32px]">error</span>
        </div>
        <div>
          <h1 class="text-xl font-bold text-slate-900" tabindex="-1">Page not found</h1>
          <p class="text-xs text-slate-500 mt-1">The requested intelligence screen does not exist.</p>
        </div>
        <a href="#/rankings" class="px-5 py-2.5 rounded-xl bg-[#0B1B3F] text-white text-xs font-bold hover:bg-slate-800 transition-colors shadow-sm">
          Return to Rankings
        </a>
      </div>
    `;
    updateSidebarActive("");
    return;
  }

  const currentRoute = routes[routeBase];

  // Update header breadcrumbs
  if (breadcrumbContainer) {
    if (currentRoute.breadcrumbHtml) {
      breadcrumbContainer.innerHTML = currentRoute.breadcrumbHtml;
    } else {
      breadcrumbContainer.innerHTML = `
        <span class="text-slate-600 font-medium hidden sm:inline">${currentRoute.category}</span>
        <span class="text-slate-400 hidden sm:inline">/</span>
        <span class="text-slate-900 font-bold truncate">${currentRoute.title}</span>
      `;
    }
  }

  // Update document title
  document.title = `${currentRoute.title} — SupeRR Intelligence Engine`;

  // Update sidebar active styling
  updateSidebarActive(routeBase);

  // Scroll to top
  window.scrollTo({ top: 0, behavior: "instant" });

  // Render route content
  try {
    currentRoute.render(viewContainer, state, data);
    // Focus the page heading for accessibility
    setTimeout(() => {
      const heading = viewContainer.querySelector("h1");
      if (heading) heading.focus();
    }, 50);
  } catch (err) {
    console.error("Error rendering route:", err);
    viewContainer.innerHTML = `<div class="p-8 text-center text-red-500 font-semibold">Error rendering screen: ${err.message}</div>`;
  }
}

// Sidebar toggle handler
function toggleSidebar() {
  appElement?.classList.toggle("sidebar-collapsed");
}

if (sidebarToggle) {
  sidebarToggle.onclick = toggleSidebar;
}

if (headerSidebarToggle) {
  headerSidebarToggle.onclick = toggleSidebar;
}

// Mobile menu toggle
if (mobileMenuBtn) {
  mobileMenuBtn.onclick = () => {
    appElement?.classList.toggle("sidebar-open");
  };
}

// Global Search logic
if (globalSearchInput && globalSearchResults) {
  globalSearchInput.addEventListener("input", (e) => {
    const q = e.target.value.trim().toLowerCase();
    if (!q || !data) {
      globalSearchResults.classList.add("hidden");
      return;
    }

    const all = [...(data.players_batters || []), ...(data.players_bowlers || [])];
    const matches = all.filter((p) => (p.name || "").toLowerCase().includes(q));

    if (!matches.length) {
      globalSearchResults.innerHTML = `<div class="p-3 text-slate-400 text-center">No qualified player matches</div>`;
      globalSearchResults.classList.remove("hidden");
      return;
    }

    globalSearchResults.innerHTML = matches.slice(0, 6).map((p) => `
      <div class="px-3 py-2 cursor-pointer hover:bg-slate-50 flex items-center justify-between border-b border-slate-50 last:border-b-0" data-id="${p.player_id}">
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
    `).join("");

    globalSearchResults.classList.remove("hidden");

    globalSearchResults.querySelectorAll("[data-id]").forEach((item) => {
      item.addEventListener("click", () => {
        const id = item.getAttribute("data-id");
        location.hash = `#/player/${id}`;
        globalSearchInput.value = "";
        globalSearchResults.classList.add("hidden");
      });
    });
  });

  document.addEventListener("click", (e) => {
    if (!globalSearchInput.contains(e.target) && !globalSearchResults.contains(e.target)) {
      globalSearchResults.classList.add("hidden");
    }
  });
}

// Info popover handlers
if (headerInfoBtn && headerInfoPopover) {
  headerInfoBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    headerInfoPopover.classList.toggle("hidden");
  });

  closeInfoPopover?.addEventListener("click", () => {
    headerInfoPopover.classList.add("hidden");
  });

  document.addEventListener("click", (e) => {
    if (!headerInfoPopover.contains(e.target) && !headerInfoBtn.contains(e.target)) {
      headerInfoPopover.classList.add("hidden");
    }
  });
}

// Global Search keyboard shortcut (Cmd+K / Ctrl+K)
window.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
    e.preventDefault();
    if (globalSearchInput) globalSearchInput.focus();
  }
});

window.addEventListener("hashchange", render);

// Initial bootstrap
(async function init() {
  try {
    data = await loadData();
    if (data?.meta?.generated_at) {
      const footerMeta = document.querySelector("#footer-data-meta");
      if (footerMeta) {
        footerMeta.textContent = `Data source: IPL 2022–2026 + T20Is ball-by-ball database • Data as of ${data.meta.generated_at} • Rankings exclude Pakistan and Pakistan A players (not permitted in the IPL) and players with no match in the last 365 days. Bangladeshi players are included. • Prepared for SupeRR Selector Season 2 - Round 1`;
      }
    }
  } catch (e) {
    console.warn("Could not load dataset from data/*.json:", e);
  }

  if (!location.hash || location.hash === "#" || location.hash === "#/") {
    location.hash = "#/overview";
  } else {
    render();
  }
})();
