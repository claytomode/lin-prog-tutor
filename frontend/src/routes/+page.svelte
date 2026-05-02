<script lang="ts">
  type TutorStep = {
    id: string;
    title: string;
    detail: string;
    highlight_vertex_index: number | null;
  };

  type Feasible2D = {
    kind: "polygon_2d";
    vertices: [number, number][];
    clipped_to_box?: boolean;
  };

  type TableauStep = {
    index: number;
    tableau: number[][];
    column_labels: string[];
    basis_labels: string[];
    entering_col: number | null;
    leaving_row: number | null;
    ratios: (number | null)[] | null;
    narrative: string;
  };

  type TableauWalkthrough = {
    sense_for_tableau: "maximize";
    initial_narrative: string;
    steps: TableauStep[];
    outcome: string;
  };

  type AnalyzeResponse = {
    ok: boolean;
    error: string | null;
    problem: {
      sense: "maximize" | "minimize";
      variables: string[];
      objective: Record<string, number>;
      constraint_labels: string[];
    } | null;
    solve_status: string | null;
    optimal_value: number | null;
    optimal_point: Record<string, number> | null;
    constraints_2d: {
      a: number;
      b: number;
      rhs: number;
      sense: string;
      label: string;
    }[];
    feasible_region: Feasible2D | Record<string, unknown> | null;
    geometry_note: string | null;
    tutor_steps: TutorStep[];
    tableau_walkthrough: TableauWalkthrough | null;
    tableau_status: string;
    tableau_message: string | null;
  };

  const defaultSource = `maximize 3 x + 2 y
subject to
x + y <= 4
x >= 0
y >= 0`;

  let source = $state(defaultSource);
  let loading = $state(false);
  let err = $state<string | null>(null);
  let data = $state<AnalyzeResponse | null>(null);
  let activeStep = $state(0);
  let tableauStep = $state(0);
  let plotDiv: HTMLDivElement | null = $state(null);

  function readCssVar(name: string, fallback: string): string {
    if (typeof document === "undefined") return fallback;
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  }

  function plotTheme() {
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

  function shortLegend(s: string, max = 22): string {
    const t = s.replace(/\s+/g, " ").trim();
    return t.length <= max ? t : `${t.slice(0, max - 1)}…`;
  }

  /** Stable-width display for tableau coefficients (pairs with tabular-nums CSS). */
  function formatTableauCell(value: number): string {
    if (!Number.isFinite(value)) return "—";
    return value.toFixed(2);
  }

  function tableauRowLabel(
    rowIndex: number,
    numRows: number,
    basisLabels: string[],
  ): string {
    if (rowIndex < numRows - 1) return basisLabels[rowIndex] ?? "";
    return "z";
  }

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
    th: ReturnType<typeof plotTheme>,
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

  function squareView(
    verts: [number, number][] | undefined,
    opt: { x: number; y: number } | undefined,
  ): { xrange: [number, number]; yrange: [number, number] } {
    let minx = Infinity;
    let maxx = -Infinity;
    let miny = Infinity;
    let maxy = -Infinity;
    const use = (x: number, y: number) => {
      minx = Math.min(minx, x);
      maxx = Math.max(maxx, x);
      miny = Math.min(miny, y);
      maxy = Math.max(maxy, y);
    };
    for (const p of verts ?? []) use(p[0], p[1]);
    if (opt) use(opt.x, opt.y);
    use(0, 0);
    if (!Number.isFinite(minx)) {
      return { xrange: [-0.25, 4.25], yrange: [-0.25, 4.25] };
    }
    const cx = (minx + maxx) / 2;
    const cy = (miny + maxy) / 2;
    const span = Math.max(maxx - minx, maxy - miny, 1e-6);
    const pad = span * 0.14 + 0.12;
    const half = span / 2 + pad;
    return {
      xrange: [cx - half, cx + half],
      yrange: [cy - half, cy + half],
    };
  }

  function plotObjectiveCaption(d: AnalyzeResponse | null): string | null {
    if (!d?.problem) return null;
    const vars = d.problem.variables;
    if (vars.length === 2) {
      const [v0, v1] = vars;
      const c0 = d.problem.objective[v0] ?? 0;
      const c1 = d.problem.objective[v1] ?? 0;
      const f0 = Number.isInteger(c0) ? String(c0) : String(Math.round(c0 * 1000) / 1000);
      const f1 = Number.isInteger(c1) ? String(c1) : String(Math.round(c1 * 1000) / 1000);
      const lin = `${f0}·${v0} + ${f1}·${v1}`;
      if (d.problem.sense === "minimize") {
        return `Linear objective ${lin}. Arrow shows −∇f = (−${f0}, −${f1}) — steepest descent in the plane.`;
      }
      return `Linear objective ${lin}. Arrow shows ∇f = (${f0}, ${f1}) — steepest ascent in the plane.`;
    }
    if (vars.length === 3) {
      const max = d.problem.sense === "maximize";
      return max
        ? "3D polyhedron (drag to rotate). Isoprofit planes cᵀx = k are parallel and orthogonal to ∇f; sliding a plane along ∇f raises k until it last touches the feasible set. One plane at f* and a ∇f segment are drawn—not the whole family of planes you would sketch by hand."
        : "3D polyhedron (drag to rotate). For minimization, lower k by moving the isoprofit plane along −∇f until it last touches the feasible set. One plane at f* and a −∇f segment are drawn—not the full stack of planes.";
    }
    return null;
  }

  async function analyze() {
    loading = true;
    err = null;
    data = null;
    activeStep = 0;
    tableauStep = 0;
    try {
      const res = await fetch("/api/lp/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source }),
      });
      const json = (await res.json()) as AnalyzeResponse;
      if (!json.ok) {
        err = json.error ?? "Request failed";
        return;
      }
      data = json;
      await drawPlot(json);
    } catch (e) {
      err = e instanceof Error ? e.message : String(e);
    } finally {
      loading = false;
    }
  }

  async function drawPlot(payload: AnalyzeResponse) {
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
    const rawVerts =
      fr && "vertices" in fr && Array.isArray((fr as { vertices: unknown }).vertices)
        ? ((fr as { vertices: number[][] }).vertices as number[][])
        : [];
    if (is3dPoly && rawVerts.length > 0 && rawVerts[0]?.length === 3) {
      await drawPlotPoly3d(Plotly, plotDiv, payload, th);
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
        hoverinfo: "name",
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

    const hi = payload.tutor_steps[activeStep]?.highlight_vertex_index;
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
          title: { text: payload.problem?.variables[0] ?? "x", font: { size: 11 } },
          range: xrange,
          constrain: "domain",
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
          title: { text: payload.problem?.variables[1] ?? "y", font: { size: 11 } },
          range: yrange,
          scaleanchor: "x",
          scaleratio: 1,
          constrain: "domain",
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

  $effect(() => {
    if (data && plotDiv) {
      void drawPlot(data);
    }
  });
</script>

<header class="hero">
  <p class="eyebrow">Interactive LP</p>
  <h1>Feasible set &amp; simplex</h1>
  <p class="lede">
    Describe a linear program in the box. We parse it, call SciPy’s HiGHS-based solver, sketch the feasible region (polygon in 2D, rotatable polyhedron in 3D),
    narrate the graphical corner idea, and—when the model is in standard slack form—show a primal simplex tableau you can step through.
  </p>
</header>

<div class="grid">
  <section class="panel">
    <h2 class="panel-title">Model</h2>
    <label for="src">Source</label>
    <textarea id="src" bind:value={source} rows="14" spellcheck="false"></textarea>
    <div class="row">
      <button type="button" onclick={() => analyze()} disabled={loading}>
        {loading ? "Running…" : "Analyze"}
      </button>
      <button type="button" class="ghost" onclick={() => (source = defaultSource)}>Reset example</button>
    </div>
    {#if err}
      <p class="error">{err}</p>
    {/if}
  </section>

  <section class="panel grow plot-panel">
    <div class="plot-head">
      <h2 class="panel-title">
        {#if data?.feasible_region && typeof data.feasible_region === "object" && "kind" in data.feasible_region && (data.feasible_region as { kind: string }).kind === "polyhedron_3d"}
          Feasible polyhedron (3D)
        {:else}
          Feasible set
        {/if}
      </h2>
      {#if data}
        {@const cap = plotObjectiveCaption(data)}
        {#if cap}
          <p class="plot-sub">{cap}</p>
        {/if}
      {/if}
    </div>
    <div class="plot" bind:this={plotDiv}></div>
    {#if data?.geometry_note}
      <p class="muted small plot-note">{data.geometry_note}</p>
    {/if}
  </section>
</div>

{#if data}
  <section class="panel solution">
    <h2 class="panel-title">Solution</h2>
    <p>
      Status: <code>{data.solve_status}</code>
      {#if data.optimal_value != null}
        &nbsp;·&nbsp; Objective: <code>{data.optimal_value.toFixed(6)}</code>
      {/if}
    </p>
    {#if data.optimal_point}
      <p class="small">
        Point:
        {#each Object.entries(data.optimal_point) as [k, v] (k)}
          <code>{k} = {v.toFixed(6)}</code>
          &nbsp;
        {/each}
      </p>
    {/if}
  </section>

  <div class="grid">
    <section class="panel">
      <h2 class="panel-title">Graphical tutor</h2>
      <ol class="steps">
        {#each data.tutor_steps as step, i (step.id)}
          <li>
            <button
              type="button"
              class:sel={i === activeStep}
              onclick={() => {
                activeStep = i;
                if (data) void drawPlot(data);
              }}
            >
              <strong>{step.title}</strong>
              <span class="detail">{step.detail}</span>
            </button>
          </li>
        {/each}
      </ol>
    </section>

    {#if data.tableau_walkthrough}
      {@const tw = data.tableau_walkthrough}
      {@const st = tw.steps[tableauStep]}
      <section class="panel grow tableau-panel">
        <h2 class="panel-title">Tableau <span class="tag">{tw.outcome}</span></h2>
        <div class="tableau-split">
          <div class="tableau-copy">
            <p class="muted small tableau-lede">{tw.initial_narrative}</p>
            <div class="row tableau-nav">
              <button
                type="button"
                class="ghost"
                disabled={tableauStep <= 0}
                onclick={() => (tableauStep = Math.max(0, tableauStep - 1))}>Prev</button>
              <button
                type="button"
                class="ghost"
                disabled={tableauStep >= tw.steps.length - 1}
                onclick={() => {
                  tableauStep = Math.min(tw.steps.length - 1, tableauStep + 1);
                }}>Next</button>
              <span class="muted small">Step {tableauStep + 1} / {tw.steps.length}</span>
            </div>
            {#if st}
              <p class="small tableau-narrative">{st.narrative}</p>
            {/if}
          </div>
          <div class="tableau-main">
            {#if st}
              <div class="table-wrap">
                <table class="tableau">
                  <colgroup>
                    <col class="tableau-col-basis" />
                    {#each st.column_labels as _}
                      <col class="tableau-col-num" />
                    {/each}
                  </colgroup>
                  <thead>
                    <tr>
                      <th scope="col" class="tableau-corner">Basis</th>
                      {#each st.column_labels as lab}
                        <th scope="col" class="tableau-num-head">{lab}</th>
                      {/each}
                    </tr>
                  </thead>
                  <tbody>
                    {#each st.tableau as row, rowIdx}
                      <tr>
                        <th scope="row" class="tableau-row-label"
                          >{tableauRowLabel(rowIdx, st.tableau.length, st.basis_labels)}</th>
                        {#each row as cell}
                          <td class="tableau-num">{formatTableauCell(cell)}</td>
                        {/each}
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
              <p class="muted small tableau-basis">
                Each constraint row shows its basic variable in the first column; the bottom row is the z-row
                (objective, maximize slack form).
              </p>
            {/if}
          </div>
        </div>
      </section>
    {:else if data.tableau_message}
      <section class="panel grow">
        <h2 class="panel-title">Tableau</h2>
        <p class="muted">{data.tableau_message}</p>
      </section>
    {/if}
  </div>
{/if}

<style>
  .hero {
    margin-bottom: 1.75rem;
    max-width: 52rem;
  }
  .eyebrow {
    margin: 0 0 0.35rem;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--color-text-muted);
  }
  h1 {
    font-family: var(--font-serif);
    font-weight: 600;
    font-size: clamp(1.85rem, 3.6vw, 2.35rem);
    line-height: 1.12;
    letter-spacing: -0.02em;
    margin: 0 0 0.65rem;
    color: var(--color-text);
  }
  .lede {
    margin: 0;
    font-size: 1.02rem;
    line-height: 1.6;
    color: var(--color-text-muted);
    max-width: 48rem;
  }
  .panel-title {
    font-family: var(--font-serif);
    font-size: 1.15rem;
    font-weight: 600;
    margin: 0 0 0.85rem;
    color: var(--color-text);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }
  .tag {
    font-family: var(--font-sans);
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    padding: 0.2rem 0.45rem;
    border-radius: 999px;
    border: 1px solid var(--color-border-strong);
    color: var(--color-text-muted);
    background: var(--color-bg-deep);
  }
  .muted {
    color: var(--color-text-muted);
  }
  .small {
    font-size: 0.875rem;
    line-height: 1.5;
  }
  .error {
    margin: 0.75rem 0 0;
    padding: 0.65rem 0.75rem;
    border-radius: var(--radius-sm);
    background: var(--color-danger-bg);
    color: var(--color-danger);
    border: 1px solid #f0c4c4;
    font-size: 0.9rem;
  }
  .grid {
    display: grid;
    gap: 1.1rem;
    margin-top: 0.25rem;
  }
  @media (min-width: 900px) {
    .grid {
      grid-template-columns: minmax(0, 1fr) minmax(0, 1.12fr);
      align-items: start;
    }
  }
  .grow {
    min-height: 380px;
  }
  .panel {
    background: var(--color-surface-raised);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    padding: 1.1rem 1.15rem 1.2rem;
    box-shadow: var(--shadow);
  }
  .plot-panel {
    background: var(--color-surface);
  }
  .plot-head {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    margin-bottom: 0.65rem;
  }
  .plot-head .panel-title {
    margin: 0;
  }
  .plot-sub {
    margin: 0;
    max-width: 42rem;
    font-size: 0.88rem;
    line-height: 1.45;
    color: var(--color-text-muted);
  }
  .plot-note {
    margin: 0.55rem 0 0;
  }
  .solution :global(p) {
    margin: 0.35rem 0 0;
  }
  label {
    display: block;
    margin: 0 0 0.4rem;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--color-text-muted);
  }
  textarea {
    width: 100%;
    box-sizing: border-box;
    font-family: var(--font-mono);
    font-size: 0.84rem;
    line-height: 1.5;
    background: var(--color-surface);
    color: var(--color-text);
    border: 1px solid var(--color-border-strong);
    border-radius: var(--radius-sm);
    padding: 0.75rem 0.85rem;
    resize: vertical;
    box-shadow: var(--shadow-inset);
  }
  textarea:focus {
    outline: 2px solid color-mix(in srgb, var(--color-accent) 45%, transparent);
    outline-offset: 1px;
    border-color: var(--color-accent);
  }
  .row {
    display: flex;
    gap: 0.55rem;
    align-items: center;
    margin-top: 0.85rem;
    flex-wrap: wrap;
  }
  button {
    font-family: var(--font-sans);
    background: var(--color-accent);
    color: #fdfcfa;
    border: 1px solid color-mix(in srgb, var(--color-accent) 88%, #000);
    border-radius: var(--radius-sm);
    padding: 0.55rem 1.05rem;
    font-weight: 600;
    font-size: 0.92rem;
    letter-spacing: -0.01em;
    cursor: pointer;
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.12) inset;
  }
  button:hover:not(:disabled) {
    background: var(--color-accent-hover);
  }
  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  button.ghost {
    background: transparent;
    color: var(--color-text);
    border: 1px solid var(--color-border-strong);
    box-shadow: none;
  }
  button.ghost:hover:not(:disabled) {
    background: var(--color-bg-deep);
    border-color: var(--color-text-faint);
  }
  .plot {
    width: 100%;
    min-height: 380px;
    border-radius: var(--radius-sm);
    border: 1px solid var(--color-border);
    overflow: hidden;
    background: var(--plot-paper);
  }
  ol.steps {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
  }
  ol.steps li button {
    width: 100%;
    text-align: left;
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    color: var(--color-text);
    font-weight: 500;
    box-shadow: none;
    padding: 0.65rem 0.75rem;
  }
  ol.steps li button:hover {
    border-color: var(--color-border-strong);
    background: color-mix(in srgb, var(--color-surface-raised) 70%, var(--color-bg));
  }
  ol.steps li button.sel {
    border-color: var(--color-accent);
    box-shadow: 0 0 0 1px var(--color-accent) inset;
    background: color-mix(in srgb, var(--color-surface-raised) 55%, var(--color-bg));
  }
  .detail {
    display: block;
    font-weight: 450;
    color: var(--color-text-muted);
    margin-top: 0.25rem;
    font-size: 0.84rem;
    line-height: 1.45;
  }
  .table-wrap {
    overflow: auto;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    background: var(--color-surface);
  }
  table.tableau {
    border-collapse: collapse;
    table-layout: fixed;
    width: 100%;
    min-width: max(100%, 22rem);
    font-size: 0.78rem;
    font-family: var(--font-mono);
    font-variant-numeric: tabular-nums lining-nums;
  }
  col.tableau-col-basis {
    width: 3.25rem;
  }
  col.tableau-col-num {
    width: 3.35rem;
  }
  table.tableau th,
  table.tableau td {
    border-bottom: 1px solid var(--color-border);
    padding: 0.35rem 0.4rem;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  table.tableau .tableau-corner,
  table.tableau .tableau-row-label {
    text-align: left;
    font-weight: 600;
    color: var(--color-text-muted);
    white-space: nowrap;
  }
  table.tableau tbody .tableau-row-label {
    font-weight: 600;
    color: var(--color-text);
    background: var(--color-bg-deep);
    border-right: 1px solid var(--color-border-strong);
  }
  table.tableau .tableau-num-head,
  table.tableau .tableau-num {
    text-align: right;
  }
  table.tableau tbody tr:nth-child(even) .tableau-num {
    background: color-mix(in srgb, var(--color-bg) 55%, transparent);
  }
  table.tableau thead th {
    background: var(--color-bg-deep);
    color: var(--color-text);
    font-weight: 600;
    border-bottom-color: var(--color-border-strong);
  }
  table.tableau thead .tableau-corner {
    border-right: 1px solid var(--color-border-strong);
  }

  /* Tableau: text wraps in the left column so the matrix stays visually anchored */
  .tableau-panel .panel-title {
    margin-bottom: 0.65rem;
  }
  .tableau-split {
    display: grid;
    gap: 1rem 1.35rem;
    align-items: start;
  }
  @media (min-width: 720px) {
    .tableau-split {
      grid-template-columns: minmax(0, min(38%, 22rem)) minmax(0, 1fr);
    }
  }
  .tableau-copy {
    min-width: 0;
  }
  .tableau-lede {
    margin: 0;
    line-height: 1.45;
  }
  .tableau-nav {
    margin-top: 0.5rem;
  }
  .tableau-narrative {
    margin: 0.75rem 0 0;
    line-height: 1.45;
  }
  .tableau-main {
    min-width: 0;
  }
  .tableau-basis {
    margin: 0.55rem 0 0;
  }
</style>
