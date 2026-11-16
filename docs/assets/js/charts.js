const pink = "#E6007E";
const navy = "#0B1B3F";
const slate = "#8A94A6";
const grid = "#E6E9F0";

export function chart(el, option) {
  if (!el) return null;
  if (!window.echarts) {
    el.innerHTML = '<div class="p-6 text-center text-xs text-slate-400">Charts unavailable because the chart library did not load.</div>';
    return null;
  }
  try {
    const existing = window.echarts.getInstanceByDom(el);
    if (existing) existing.dispose();
    const c = window.echarts.init(el);
    c.setOption({ ...option, animation: false });
    window.addEventListener("resize", () => {
      try { c.resize(); } catch (_) {}
    });
    return c;
  } catch (err) {
    console.warn("Chart render failed:", err);
    return null;
  }
}

export function forest(el, rows) {
  if (!el || !rows || !rows.length) return null;
  const data = rows.slice(0, 25).reverse();
  el.setAttribute("role", "img");
  el.setAttribute("aria-label", "Top 25 forest plot showing point estimates and 80% interval (bootstrap)");
  
  return chart(el, {
    tooltip: {
      trigger: "item",
      formatter: (params) => {
        const p = data[params.data[0]];
        if (!p) return "";
        return `<strong>${p.name}</strong> (Rank ${p.rank})<br/>Rating: ${p.rating > 0 ? "+" : ""}${p.rating.toFixed(1)} runs/100b<br/>80% CI: [${p.lo80.toFixed(1)}, ${p.hi80.toFixed(1)}]<br/>P(top 10): ${(p.p_top10 * 100).toFixed(0)}%`;
      }
    },
    grid: { left: 110, right: 30, top: 15, bottom: 35 },
    xAxis: {
      type: "value",
      name: "Runs / 100b",
      nameLocation: "middle",
      nameGap: 22,
      splitLine: { lineStyle: { color: grid, type: "dashed" } },
      axisLabel: { fontSize: 10, color: slate }
    },
    yAxis: {
      type: "category",
      data: data.map(p => p.name),
      axisLabel: { fontSize: 10, color: navy, fontWeight: 500 }
    },
    series: [
      {
        type: "custom",
        renderItem: (params, api) => {
          const y = api.coord([0, api.value(0)])[1];
          const lo = api.coord([api.value(1), api.value(0)])[0];
          const hi = api.coord([api.value(2), api.value(0)])[0];
          const x = api.coord([api.value(3), api.value(0)])[0];
          const color = api.value(4);
          return {
            type: "group",
            children: [
              {
                type: "line",
                shape: { x1: lo, y1: y, x2: hi, y2: y },
                style: { stroke: color, lineWidth: 2 }
              },
              {
                type: "circle",
                shape: { cx: x, cy: y, r: 4 },
                style: { fill: color }
              }
            ]
          };
        },
        data: data.map((p, i) => [i, p.lo80, p.hi80, p.rating, p.rank <= 10 ? pink : slate])
      }
    ]
  });
}

export function calibration(el, rows, title) {
  if (!el || !rows || !rows.length) return null;
  return chart(el, {
    title: { text: title || "", left: 0, textStyle: { fontSize: 12, color: navy, fontWeight: 600 } },
    tooltip: { trigger: "axis" },
    grid: { left: 45, right: 20, top: 35, bottom: 35 },
    xAxis: {
      type: "value",
      name: "Predicted",
      min: 0,
      max: 1,
      splitLine: { lineStyle: { color: grid } },
      axisLabel: { fontSize: 10 }
    },
    yAxis: {
      type: "value",
      name: "Observed",
      min: 0,
      max: 1,
      splitLine: { lineStyle: { color: grid } },
      axisLabel: { fontSize: 10 }
    },
    series: [
      {
        type: "line",
        data: [[0, 0], [1, 1]],
        lineStyle: { color: slate, type: "dashed", width: 1 },
        symbol: "none",
        silent: true
      },
      {
        type: "line",
        data: rows.map(x => [x.pred, x.obs]),
        smooth: true,
        symbol: "circle",
        symbolSize: 6,
        lineStyle: { color: pink, width: 2 },
        itemStyle: { color: pink }
      }
    ]
  });
}

export function tournamentChart(el, rows, ceiling) {
  if (!el || !rows || !rows.length) return null;
  const sorted = [...rows].sort((a, b) => b.mean_pearson - a.mean_pearson);
  return chart(el, {
    tooltip: {
      trigger: "item",
      formatter: (params) => {
        const r = sorted[params.dataIndex];
        return `<strong>${r.estimator}</strong> (${r.role})<br/>Held-out Pearson: ${r.mean_pearson.toFixed(3)}<br/>95% CI: [${r.ci95_lo.toFixed(3)}, ${r.ci95_hi.toFixed(3)}]`;
      }
    },
    grid: { left: 160, right: 40, top: 20, bottom: 30 },
    xAxis: {
      type: "value",
      name: "Held-out Pearson r",
      splitLine: { lineStyle: { color: grid } },
      axisLabel: { fontSize: 10 }
    },
    yAxis: {
      type: "category",
      data: sorted.map(r => `${r.estimator} (${r.role})`),
      axisLabel: { fontSize: 10, color: navy }
    },
    series: [
      {
        type: "bar",
        data: sorted.map(r => r.mean_pearson),
        itemStyle: {
          color: (p) => p.dataIndex === 0 ? pink : "#64748B"
        }
      }
    ]
  });
}

export function heatmapChart(el, matrix, title) {
  if (!el || !matrix || !matrix.length) return null;
  const data = [];
  matrix.forEach((row, y) => {
    row.forEach((v, x) => {
      if (v != null) data.push([x, y, Number(v.toFixed(3))]);
    });
  });

  return chart(el, {
    title: { text: title || "", left: 0, textStyle: { fontSize: 12, color: navy, fontWeight: 600 } },
    tooltip: {
      position: "top",
      formatter: (p) => `Over ${p.data[1] + 1}, Wickets lost: ${p.data[0]}<br/>Value: <strong>${p.data[2]}</strong>`
    },
    grid: { left: 55, right: 25, top: 35, bottom: 45 },
    xAxis: {
      type: "category",
      data: Array.from({ length: 10 }, (_, i) => `${i} wkts`),
      axisLabel: { fontSize: 9 }
    },
    yAxis: {
      type: "category",
      data: Array.from({ length: 20 }, (_, i) => `Over ${i + 1}`),
      axisLabel: { fontSize: 9 }
    },
    visualMap: {
      min: 0,
      max: 1,
      calculable: true,
      orient: "horizontal",
      left: "center",
      bottom: 0,
      inRange: {
        color: ["#eff6ff", "#fce7f3", "#ec4899", "#9d174d"]
      },
      textStyle: { fontSize: 9 }
    },
    series: [
      {
        type: "heatmap",
        data,
        label: { show: false }
      }
    ]
  });
}

export function traceChart(el, trace) {
  if (!el || !trace || !trace.balls) return null;
  const balls = trace.balls;
  const xData = balls.map((b, i) => `${b.over || Math.floor(i / 6) + 1}.${b.over_ball || (i % 6) + 1}`);
  const wpData = balls.map(b => b.wp);

  return chart(el, {
    tooltip: {
      trigger: "axis",
      formatter: (params) => {
        const idx = params[0]?.dataIndex;
        const b = balls[idx];
        if (!b) return "";
        return `Ball: ${xData[idx]}<br/>WP: ${(b.wp * 100).toFixed(1)}%<br/>PI: ${b.pi ? b.pi.toFixed(2) : "—"}${b.is_wicket ? "<br/><strong style='color:#E6007E'>WICKET!</strong>" : ""}`;
      }
    },
    grid: { left: 45, right: 25, top: 25, bottom: 35 },
    xAxis: {
      type: "category",
      data: xData,
      axisLabel: { interval: 11, fontSize: 9 }
    },
    yAxis: {
      type: "value",
      name: "Win Prob",
      min: 0,
      max: 1,
      splitLine: { lineStyle: { color: grid } },
      axisLabel: { fontSize: 9 }
    },
    series: [
      {
        type: "line",
        data: wpData,
        lineStyle: { color: navy, width: 2 },
        symbol: (value, params) => {
          const b = balls[params.dataIndex];
          return b && b.is_wicket ? "diamond" : "none";
        },
        symbolSize: 8,
        itemStyle: { color: pink }
      }
    ]
  });
}
