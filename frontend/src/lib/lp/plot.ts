import type { AnalyzeResponse } from "./types.js";
import { constraintHoverText, shortLegend } from "./format.js";
import {
  interval1dXRange,
  squareView,
} from "./feasible.js";

export function readCssVar(name: string, fallback: string): string {
  if (typeof document === "undefined") return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}

export function plotTheme() {
  return {
    feasibleFill: readCssVar("--plot-feasible-fill", "rgba(29, 75, 69, 0.14)"),
    feasibleLine: readCssVar("--plot-feasible-line", "#1d4b45"),
    constraint: readCssVar("--plot-constraint", "#8a8278"),
    objective: readCssVar("--plot-objective", "#9a3412"),
    optimum: readCssVar("--plot-optimum", "#6b1d3d"),
    vertexHi: readCssVar("--plot-vertex-hi", "#166534"),
    paper: readCssVar("--plot-paper", "#fffefb"),
    plotBg: readCssVar("--plot-bg", "#f3efe8"),
    ink: readCssVar("--plot-ink", "#1a1814"),
    grid: readCssVar("--plot-grid", "#d9d4cc"),
    zero: readCssVar("--plot-zero", "#b8b0a4"),
  };
}

export type PlotTheme = ReturnType<typeof plotTheme>;

function linspace(a: number, b: number, n: number): number[] {
  if (n <= 1) return [a];
  const o: number[] = [];
  for (let i = 0; i < n; i++) o.push(a + ((b - a) * i) / (n - 1));
  return o;
}

/** One translucent plane c·(x,y,z) = k over the bounding box of the polyhedron vertices. */
function isoprofitPlaneTrace(
  c: [number, number, number],
  k: number,
  xs: number[],
  ys: number[],
  zs: number[],
): object | null {
  const pad = (d: number[]) => {
    const lo = Math.min(...d);
    const hi = Math.max(...d);
    const s = Math.max(hi - lo, 1e-6) * 0.12;
    return [lo - s, hi + s] as [number, number];
  };
  const [xmin, xmax] = pad(xs);
  const [ymin, ymax] = pad(ys);
  const [zmin, zmax] = pad(zs);
  const [c0, c1, c2] = c;
  const nx = 22;
  const ny = 22;
  let x1: number[];
  let y1: number[];
  let z2: number[][];
  if (Math.abs(c2) >= Math.max(Math.abs(c0), Math.abs(c1), 1e-9)) {
    x1 = linspace(xmin, xmax, nx);
    y1 = linspace(ymin, ymax, ny);
    z2 = [];
    for (let i = 0; i < ny; i++) {
      const row: number[] = [];
      for (let j = 0; j < nx; j++) {
        row.push((k - c0 * x1[j]! - c1 * y1[i]!) / c2);
      }
      z2.push(row);
    }
  } else if (Math.abs(c1) >= Math.abs(c0)) {
    x1 = linspace(xmin, xmax, nx);
    const z1 = linspace(zmin, zmax, ny);
    z2 = [];
    y1 = z1;
    for (let i = 0; i < ny; i++) {
      const row: number[] = [];
      for (let j = 0; j < nx; j++) {
        row.push((k - c0 * x1[j]! - c2 * z1[i]!) / c1);
      }
      z2.push(row);
    }
  } else {
    const y1a = linspace(ymin, ymax, nx);
    const z1 = linspace(zmin, zmax, ny);
    x1 = y1a;
    y1 = z1;
    z2 = [];
    for (let i = 0; i < ny; i++) {
      const row: number[] = [];
      for (let j = 0; j < nx; j++) {
        row.push((k - c1 * y1a[j]! - c2 * z1[i]!) / c0);
      }
      z2.push(row);
    }
  }
  return {
    type: "surface",
    x: x1,
    y: y1,
    z: z2,
    opacity: 0.28,
    showscale: false,
    colorscale: [
      [0, "rgba(154, 52, 18, 0.35)"],
      [1, "rgba(154, 52, 18, 0.55)"],
    ],
    name: `cᵀx = ${Number.isInteger(k) ? String(k) : k.toFixed(4)}`,
    hovertemplate: "Isoprofit plane<extra></extra>",
    lighting: { ambient: 0.85 },
  };
}

async function drawPlotPoly3d(
  Plotly: Awaited<typeof import("plotly.js-dist-min")>["default"],
  el: HTMLDivElement,
  payload: AnalyzeResponse,
  th: PlotTheme,
) {
  const fr = payload.feasible_region as { kind: string; vertices: number[][] };
  const verts = (fr.vertices ?? []).filter((p) => p.length === 3) as number[][];
  if (verts.length < 4) return;

  const prob = payload.problem;
  if (!prob || prob.variables.length !== 3) return;
  const [v0, v1, v2] = prob.variables;
  const xs = verts.map((p) => p[0]!);
  const ys = verts.map((p) => p[1]!);
  const zs = verts.map((p) => p[2]!);

  const traces: object[] = [];
  traces.push({
    type: "mesh3d",
    x: xs,
    y: ys,
    z: zs,
    alphahull: 0,
    opacity: 0.42,
    color: th.feasibleLine,
    flatshading: true,
    name: "Feasible polyhedron",
    hoverinfo: "skip",
  });

  const op = payload.optimal_point;
  if (op) {
    traces.push({
      type: "scatter3d",
      mode: "markers",
      x: [op[v0]],
      y: [op[v1]],
      z: [op[v2]],
      marker: {
        size: 11,
        color: th.optimum,
        line: { color: "#fffefb", width: 2 },
      },
      name: "Optimum",
      hovertemplate: `${v0}=%{x:.4f}<br>${v1}=%{y:.4f}<br>${v2}=%{z:.4f}<extra></extra>`,
    });
  }

  const ox = prob.objective[v0] ?? 0;
  const oy = prob.objective[v1] ?? 0;
  const oz = prob.objective[v2] ?? 0;
  const maximize = prob.sense === "maximize";
  const gx = maximize ? ox : -ox;
  const gy = maximize ? oy : -oy;
  const gz = maximize ? oz : -oz;
  const gn = Math.hypot(gx, gy, gz) || 1;
  const span = Math.max(
    Math.max(...xs) - Math.min(...xs),
    Math.max(...ys) - Math.min(...ys),
    Math.max(...zs) - Math.min(...zs),
    1e-6,
  );
  const glen = span * 0.38;
  const cx = xs.reduce((a, b) => a + b, 0) / xs.length;
  const cy = ys.reduce((a, b) => a + b, 0) / ys.length;
  const cz = zs.reduce((a, b) => a + b, 0) / zs.length;
  const ux = (gx / gn) * glen;
  const uy = (gy / gn) * glen;
  const uz = (gz / gn) * glen;
  traces.push({
    type: "scatter3d",
    mode: "lines",
    x: [cx, cx + ux],
    y: [cy, cy + uy],
    z: [cz, cz + uz],
    line: { width: 5, color: th.objective },
    name: maximize ? "∇f (ascent)" : "−∇f (descent)",
    hoverinfo: "name",
  });

  if (payload.optimal_value != null && Number.isFinite(payload.optimal_value)) {
    const cvec: [number, number, number] = [ox, oy, oz];
    const plane = isoprofitPlaneTrace(cvec, payload.optimal_value, xs, ys, zs);
    if (plane) traces.push(plane);
  }

  await Plotly.react(
    el,
    traces,
    {
      paper_bgcolor: th.paper,
      font: { family: "Instrument Sans, system-ui, sans-serif", color: th.ink, size: 11 },
      margin: { l: 0, r: 28, t: 8, b: 0 },
      scene: {
        xaxis: {
          title: { text: v0, font: { size: 11 } },
          backgroundcolor: th.plotBg,
          gridcolor: th.grid,
          showbackground: true,
        },
        yaxis: {
          title: { text: v1, font: { size: 11 } },
          backgroundcolor: th.plotBg,
          gridcolor: th.grid,
          showbackground: true,
        },
        zaxis: {
          title: { text: v2, font: { size: 11 } },
          backgroundcolor: th.plotBg,
          gridcolor: th.grid,
          showbackground: true,
        },
        bgcolor: th.paper,
        aspectmode: "data",
        camera: { eye: { x: 1.55, y: 1.35, z: 1.15 } },
      },
      showlegend: true,
      legend: {
        orientation: "v",
        x: 1.02,
        xref: "paper",
        xanchor: "left",
        y: 1,
        yref: "paper",
        yanchor: "top",
        font: { size: 10, family: "Instrument Sans, system-ui, sans-serif" },
        bgcolor: "rgba(255, 253, 248, 0.96)",
        bordercolor: th.grid,
        borderwidth: 1,
      },
      hovermode: "closest",
      dragmode: "orbit",
    },
    {
      responsive: true,
      displayModeBar: "hover",
      displaylogo: false,
      scrollZoom: true,
      toImageButtonOptions: { format: "png", scale: 2 },
    },
  );
}

export type DrawPlotOptions = {
  activeStep: number;
  skipPlot3d: boolean;
};

/** Remove Plotly traces from an element (e.g. before showing a non-Plotly empty state). */
export async function clearPlot(plotDiv: HTMLDivElement | null): Promise<void> {
  if (!plotDiv) return;
  const Plotly = (await import("plotly.js-dist-min")).default;
  const plotly = Plotly as typeof Plotly & { purge?: (el: HTMLElement) => void };
  plotly.purge?.(plotDiv);
}

export async function drawPlot(
  plotDiv: HTMLDivElement | null,
  payload: AnalyzeResponse,
  opts: DrawPlotOptions,
): Promise<void> {
  if (!plotDiv) return;
  const Plotly = (await import("plotly.js-dist-min")).default;
  const th = plotTheme();
  const traces: object[] = [];
  const fr = payload.feasible_region;
  const nVar = payload.problem?.variables.length ?? 0;
  const is3dPoly =
    fr != null &&
    typeof fr === "object" &&
    "kind" in fr &&
    (fr as { kind: string }).kind === "polyhedron_3d";
  if (is3dPoly && opts.skipPlot3d) {
    const plotly = Plotly as typeof Plotly & { purge?: (el: HTMLElement) => void };
    plotly.purge?.(plotDiv);
    return;
  }
  const rawVerts =
    fr && "vertices" in fr && Array.isArray((fr as { vertices: unknown }).vertices)
      ? ((fr as { vertices: number[][] }).vertices as number[][])
      : [];
  if (is3dPoly && rawVerts.length > 0 && rawVerts[0]?.length === 3) {
    await drawPlotPoly3d(Plotly, plotDiv, payload, th);
    return;
  }

  const is1dInterval =
    fr != null &&
    typeof fr === "object" &&
    "kind" in fr &&
    (fr as { kind: string }).kind === "interval_1d";
  if (is1dInterval) {
    const iv = fr as { kind: "interval_1d"; var: string; lo: number | null; hi: number | null };
    const op = payload.optimal_point;
    const optVal =
      op && typeof op[iv.var] === "number" && Number.isFinite(op[iv.var] as number)
        ? (op[iv.var] as number)
        : undefined;
    const [x0, x1] = interval1dXRange(iv.lo, iv.hi, optVal);
    const hasLo = iv.lo != null && Number.isFinite(iv.lo);
    const hasHi = iv.hi != null && Number.isFinite(iv.hi);
    const segX0 = hasLo ? Math.max(iv.lo!, x0) : x0;
    const segX1 = hasHi ? Math.min(iv.hi!, x1) : x1;
    const traces1d: object[] = [];
    const segW = segX1 - segX0;
    if (segW > 1e-10) {
      traces1d.push({
        type: "scatter",
        mode: "lines",
        x: [segX0, segX1],
        y: [0, 0],
        line: { color: th.feasibleLine, width: 10 },
        name: "Feasible interval",
        hovertemplate: `${iv.var}=%{x:.6g}<extra></extra>`,
      });
    } else if (hasLo && hasHi) {
      const px = (iv.lo! + iv.hi!) / 2;
      traces1d.push({
        type: "scatter",
        mode: "markers",
        marker: {
          size: 12,
          color: th.feasibleLine,
          line: { width: 1.5, color: "#fffefb" },
          symbol: "square",
        },
        name: "Feasible point",
        hovertemplate: `${iv.var}=%{x:.6g}<extra></extra>`,
        x: [px],
        y: [0],
      });
    }
    if (optVal != null && Number.isFinite(optVal) && optVal >= x0 - 1e-9 && optVal <= x1 + 1e-9) {
      traces1d.push({
        type: "scatter",
        mode: "markers",
        marker: {
          size: 11,
          color: th.optimum,
          line: { width: 1.5, color: "#fffefb" },
          symbol: "circle",
        },
        name: "Optimum",
        hovertemplate: `${iv.var}=%{x:.6g}<extra></extra>`,
        x: [optVal],
        y: [0],
      });
    }
    const yPad = 0.42;
    await Plotly.react(
      plotDiv,
      traces1d,
      {
        paper_bgcolor: th.paper,
        plot_bgcolor: th.plotBg,
        font: { family: "Instrument Sans, system-ui, sans-serif", color: th.ink, size: 11 },
        margin: { l: 52, r: 132, t: 16, b: 44 },
        xaxis: {
          title: { text: iv.var, font: { size: 11 }, standoff: 8 },
          range: [x0, x1],
          tickformat: ".4g",
          zeroline: true,
          zerolinewidth: 1,
          zerolinecolor: th.zero,
          gridcolor: th.grid,
          linecolor: th.grid,
          showspikes: false,
          ticks: "outside",
          ticklen: 4,
          minor: { showgrid: false },
        },
        yaxis: {
          visible: true,
          range: [-yPad, yPad],
          fixedrange: true,
          showticklabels: false,
          title: { text: "" },
          zeroline: true,
          zerolinewidth: 1,
          zerolinecolor: th.zero,
          showgrid: false,
          linecolor: th.grid,
        },
        hoverlabel: {
          bgcolor: th.paper,
          bordercolor: th.grid,
          font: { family: "Instrument Sans, system-ui, sans-serif", size: 11, color: th.ink },
        },
        showlegend: traces1d.length > 0,
        legend: {
          orientation: "v",
          x: 1.01,
          xref: "paper",
          xanchor: "left",
          y: 1,
          yref: "paper",
          yanchor: "top",
          font: { size: 10, family: "Instrument Sans, system-ui, sans-serif" },
          bgcolor: "rgba(255, 253, 248, 0.96)",
          bordercolor: th.grid,
          borderwidth: 1,
          tracegroupgap: 0,
          itemwidth: 34,
          itemsizing: "constant",
        },
        annotations: [],
        hovermode: "closest",
        dragmode: "pan",
      },
      {
        responsive: true,
        displayModeBar: "hover",
        displaylogo: false,
        scrollZoom: true,
        toImageButtonOptions: { format: "png", scale: 2 },
      },
    );
    return;
  }

  let verts2d: [number, number][] | undefined;
  if (fr && "vertices" in fr && Array.isArray(fr.vertices) && fr.vertices.length > 0) {
    const raw = fr.vertices as number[][];
    if (raw[0]?.length === 2) {
      verts2d = raw as [number, number][];
    }
  }

  let opt2d: { x: number; y: number } | undefined;
  if (payload.optimal_point && payload.problem && (nVar === 2 || nVar === 3)) {
    const [v0, v1] = payload.problem.variables;
    opt2d = {
      x: payload.optimal_point[v0] ?? 0,
      y: payload.optimal_point[v1] ?? 0,
    };
  }

  const { xrange, yrange } = squareView(verts2d, opt2d);
  const span = Math.max(xrange[1] - xrange[0], yrange[1] - yrange[0]);
  const lineSpan = span * 0.55 + 0.25;

  if (verts2d && verts2d.length >= 2) {
    const vx = verts2d.map((p) => p[0]);
    const vy = verts2d.map((p) => p[1]);
    if (vx[0] !== vx[vx.length - 1] || vy[0] !== vy[vy.length - 1]) {
      vx.push(vx[0]!);
      vy.push(vy[0]!);
    }
    const canFill = verts2d.length >= 3;
    traces.push({
      type: "scatter",
      mode: "lines",
      ...(canFill ? { fill: "toself" as const, fillcolor: th.feasibleFill } : {}),
      line: { color: th.feasibleLine, width: 2 },
      name: "Feasible set",
      hoverinfo: "skip",
      x: vx,
      y: vy,
    });
  }

  const xLab = payload.problem?.variables[0] ?? "x";
  const yLab = payload.problem?.variables[1] ?? "y";
  for (const c of payload.constraints_2d) {
    const xs: number[] = [];
    const ys: number[] = [];
    if (Math.abs(c.b) > 1e-12) {
      const mid = (xrange[0] + xrange[1]) / 2;
      for (let x = mid - lineSpan; x <= mid + lineSpan; x += 0.04) {
        xs.push(x);
        ys.push((c.rhs - c.a * x) / c.b);
      }
    } else if (Math.abs(c.a) > 1e-12) {
      const x0 = c.rhs / c.a;
      const mid = (yrange[0] + yrange[1]) / 2;
      for (let y = mid - lineSpan; y <= mid + lineSpan; y += 0.04) {
        xs.push(x0);
        ys.push(y);
      }
    }
    traces.push({
      type: "scatter",
      mode: "lines",
      line: { dash: "4 3", width: 1.15, color: th.constraint },
      name: shortLegend(c.label),
      hovertemplate: `${constraintHoverText(c, xLab, yLab)}<extra></extra>`,
      x: xs,
      y: ys,
    });
  }

  if (payload.optimal_point && payload.problem && (nVar === 2 || nVar === 3)) {
    const [v0, v1] = payload.problem.variables;
    const op = payload.optimal_point;
    const z3 = nVar === 3 ? payload.problem.variables[2] : null;
    const hoverText =
      z3 != null
        ? `${v0}=${Number(op[v0]).toFixed(4)}<br>${v1}=${Number(op[v1]).toFixed(4)}<br>${z3}=${Number(op[z3]).toFixed(4)}`
        : `${v0}=${Number(op[v0]).toFixed(4)}<br>${v1}=${Number(op[v1]).toFixed(4)}`;
    traces.push({
      type: "scatter",
      mode: "markers",
      marker: {
        size: 9,
        color: th.optimum,
        line: { width: 1.5, color: "#fffefb" },
        symbol: "circle",
      },
      name: "Optimum",
      text: [hoverText],
      hovertemplate: "%{text}<extra></extra>",
      x: [op[v0]],
      y: [op[v1]],
    });
  }

  const hi = payload.tutor_steps[opts.activeStep]?.highlight_vertex_index;
  if (hi != null && verts2d && verts2d[hi]) {
    const p = verts2d[hi];
    traces.push({
      type: "scatter",
      mode: "markers",
      marker: {
        size: 11,
        color: th.vertexHi,
        symbol: "diamond",
        line: { width: 1.25, color: "#fffefb" },
      },
      name: "Tutor vertex",
      showlegend: false,
      hoverinfo: "skip",
      x: [p[0]],
      y: [p[1]],
    });
  }

  const annotations: object[] = [];
  if (payload.problem && payload.problem.variables.length === 2) {
    const [v0, v1] = payload.problem.variables;
    const ox = payload.problem.objective[v0] ?? 0;
    const oy = payload.problem.objective[v1] ?? 0;
    const maximize = payload.problem.sense === "maximize";
    const dx = maximize ? ox : -ox;
    const dy = maximize ? oy : -oy;
    const norm = Math.hypot(dx, dy) || 1;
    const len = span * 0.36;
    const hx = (dx / norm) * len;
    const hy = (dy / norm) * len;
    const label = maximize ? "∇f" : "−∇f";
    annotations.push({
      x: hx,
      y: hy,
      ax: 0,
      ay: 0,
      xref: "x",
      yref: "y",
      axref: "x",
      ayref: "y",
      showarrow: true,
      arrowhead: 3,
      arrowsize: 1.35,
      arrowwidth: 2.25,
      arrowcolor: th.objective,
      text: "",
      opacity: 1,
    });
    annotations.push({
      x: hx,
      y: hy,
      xref: "x",
      yref: "y",
      text: label,
      showarrow: false,
      xanchor: "left",
      yanchor: "middle",
      xshift: 8,
      font: {
        size: 12,
        color: th.objective,
        family: "Instrument Sans, system-ui, sans-serif",
      },
      bgcolor: "rgba(255, 253, 248, 0.92)",
      bordercolor: "rgba(154, 52, 18, 0.28)",
      borderwidth: 1,
      borderpad: 3,
    });
  }

  await Plotly.react(
    plotDiv,
    traces,
    {
      paper_bgcolor: th.paper,
      plot_bgcolor: th.plotBg,
      font: { family: "Instrument Sans, system-ui, sans-serif", color: th.ink, size: 11 },
      margin: { l: 52, r: 132, t: 16, b: 44 },
      xaxis: {
        title: { text: payload.problem?.variables[0] ?? "x", font: { size: 11 }, standoff: 8 },
        range: xrange,
        constrain: "domain",
        tickformat: ".4g",
        zeroline: true,
        zerolinewidth: 1,
        zerolinecolor: th.zero,
        gridcolor: th.grid,
        linecolor: th.grid,
        showspikes: false,
        ticks: "outside",
        ticklen: 4,
        minor: { showgrid: false },
      },
      yaxis: {
        title: { text: payload.problem?.variables[1] ?? "y", font: { size: 11 }, standoff: 8 },
        range: yrange,
        scaleanchor: "x",
        scaleratio: 1,
        constrain: "domain",
        tickformat: ".4g",
        zeroline: true,
        zerolinewidth: 1,
        zerolinecolor: th.zero,
        gridcolor: th.grid,
        linecolor: th.grid,
        showspikes: false,
        ticks: "outside",
        ticklen: 4,
        minor: { showgrid: false },
      },
      hoverlabel: {
        bgcolor: th.paper,
        bordercolor: th.grid,
        font: { family: "Instrument Sans, system-ui, sans-serif", size: 11, color: th.ink },
      },
      showlegend: traces.length > 0,
      legend: {
        orientation: "v",
        x: 1.01,
        xref: "paper",
        xanchor: "left",
        y: 1,
        yref: "paper",
        yanchor: "top",
        font: { size: 10, family: "Instrument Sans, system-ui, sans-serif" },
        bgcolor: "rgba(255, 253, 248, 0.96)",
        bordercolor: th.grid,
        borderwidth: 1,
        tracegroupgap: 0,
        itemwidth: 34,
        itemsizing: "constant",
      },
      annotations,
      hovermode: "closest",
      dragmode: "pan",
    },
    {
      responsive: true,
      displayModeBar: "hover",
      displaylogo: false,
      scrollZoom: true,
      toImageButtonOptions: { format: "png", scale: 2 },
    },
  );
}
