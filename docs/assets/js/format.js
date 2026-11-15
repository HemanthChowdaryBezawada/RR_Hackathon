export const n = (v, d = 0) =>
  v == null || Number.isNaN(Number(v))
    ? "—"
    : Number(v).toLocaleString(undefined, {
        minimumFractionDigits: d,
        maximumFractionDigits: d
      });

export const pct = (v, d = 0) =>
  v == null || Number.isNaN(Number(v))
    ? "—"
    : `${(Number(v) * 100).toFixed(d)}%`;

export const date = (v) =>
  v
    ? new Date(v).toLocaleDateString(undefined, {
        day: "2-digit",
        month: "short",
        year: "numeric"
      })
    : "—";

export const initials = (s) =>
  String(s || "?")
    .split(/\s+/)
    .slice(0, 2)
    .map((x) => x[0])
    .join("")
    .toUpperCase();

export const esc = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
      }[c])
  );

export function notAvailableCard(title = "") {
  return `
    <div class="rounded-2xl border border-dashed border-slate-200 bg-slate-50/50 p-8 text-center">
      ${title ? `<div class="text-xs font-bold text-slate-700 mb-1">${esc(title)}</div>` : ""}
      <div class="text-xs text-slate-400 font-medium">Not available in this build</div>
    </div>
  `;
}

export function interval(p, min = -15, max = 55, isPink = false) {
  if (!p || p.lo80 == null || p.hi80 == null || p.rating == null) return "—";
  const pos = (x) => Math.max(1, Math.min(99, ((x - min) / (max - min)) * 100));
  const a = pos(p.lo80);
  const b = pos(p.hi80);
  const center = pos(p.rating);
  const width = Math.max(2, b - a);
  const color = isPink || (p.rank && p.rank <= 10) ? "#E6007E" : "#64748B";

  return `
    <div class="relative w-28 sm:w-36 h-4 flex items-center select-none" role="img" aria-label="Rating ${n(p.rating, 1)}, 80% CI: ${n(p.lo80, 1)} to ${n(p.hi80, 1)}">
      <!-- Baseline zero indicator -->
      <div class="absolute h-3 w-px bg-slate-200" style="left: ${pos(0)}%;"></div>
      <!-- Credible Range Bar -->
      <div class="absolute h-1.5 rounded-full opacity-30" style="left: ${a}%; width: ${width}%; background-color: ${color};"></div>
      <!-- Left Whisker -->
      <div class="absolute h-2.5 w-0.5 rounded-full" style="left: ${a}%; background-color: ${color};"></div>
      <!-- Right Whisker -->
      <div class="absolute h-2.5 w-0.5 rounded-full" style="left: ${b}%; background-color: ${color};"></div>
      <!-- Point Estimate -->
      <div class="absolute w-2.5 h-2.5 rounded-full shadow-xs transform -translate-x-1/2" style="left: ${center}%; background-color: ${color};"></div>
    </div>
  `;
}

export function chips(p) {
  if (!p) return "";
  const list = [
    ...(p.ipl_teams || []).slice(0, 1),
    ...(p.national_teams || []).slice(0, 1)
  ];
  return list
    .map(
      (x) =>
        `<span class="px-1.5 py-0.5 text-[10px] font-semibold bg-slate-100 text-slate-600 rounded-md tracking-tight">${esc(x)}</span>`
    )
    .join(" ");
}
