<script lang="ts">
  import { onMount, tick } from "svelte";

  type TableauMode = "auto" | "primal" | "dual" | "big_m";

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
    sense_for_tableau: "maximize" | "minimize";
    initial_narrative: string;
    steps: TableauStep[];
    outcome: string;
  };

  type AnalyzeResponse = {
    ok: boolean;
    error: string | null;
    modeling_notes: string[];
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
    tableau_verified: boolean | null;
    tableau_verify_message: string | null;
  };

  const defaultSource = `maximize 3 x + 2 y
subject to
x + y <= 4
x >= 0
y >= 0`;

  const PRESET_STORAGE_KEY = "lp-tutor-study-preset";
  type StudyPreset = "default" | "classroom" | "self-study";

  function presetFlags(p: StudyPreset): {
    compactTableau: boolean;
    skipPlot3d: boolean;
    hintsDefault: boolean;
  } {
    if (p === "classroom") {
      return { compactTableau: true, skipPlot3d: true, hintsDefault: false };
    }
    if (p === "self-study") {
      return { compactTableau: false, skipPlot3d: false, hintsDefault: true };
    }
    return { compactTableau: false, skipPlot3d: false, hintsDefault: true };
  }

  let source = $state(defaultSource);
  let loading = $state(false);
  let err = $state<string | null>(null);
  let data = $state<AnalyzeResponse | null>(null);
  let activeStep = $state(0);
  let tableauStep = $state(0);
  let plotDiv: HTMLDivElement | null = $state(null);
  let tableauMode = $state<TableauMode>("auto");
  let useBlandsRule = $state(false);
  let bigMText = $state("");
  let studyPreset = $state<StudyPreset>("default");
  let presetHydrated = $state(false);
  let solutionHeadingEl: HTMLHeadingElement | null = $state(null);

  const showHints = $derived(presetFlags(studyPreset).hintsDefault);
  const skipPlot3d = $derived(presetFlags(studyPreset).skipPlot3d);
  const compactTableau = $derived(presetFlags(studyPreset).compactTableau);

  onMount(() => {
    const raw = localStorage.getItem(PRESET_STORAGE_KEY);
    if (raw === "classroom" || raw === "self-study" || raw === "default") {
      studyPreset = raw;
    }
    presetHydrated = true;
  });

  $effect(() => {
    if (typeof localStorage === "undefined" || !presetHydrated) return;
    localStorage.setItem(PRESET_STORAGE_KEY, studyPreset);
  });

  function isPolyhedron3d(d: AnalyzeResponse | null): boolean {
    const fr = d?.feasible_region;
    return (
      fr != null &&
      typeof fr === "object" &&
      "kind" in fr &&
      (fr as { kind: string }).kind === "polyhedron_3d"
    );
  }

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

  function humanizeApiError(message: string): string {
    const low = message.toLowerCase();
    if (low.includes("could not read response")) return message;
    if (low.includes("empty problem"))
      return "The source is empty after comments. Add a maximize or minimize line and constraints.";
    if (low.includes("need a maximize") || low.includes("need a minimize"))
      return "Start with a line like `maximize 3 x + 2 y` or `minimize x + y`.";
    if (low.includes("subject to"))
      return 'After the objective, add a line `subject to` or `s.t.` (colon optional), then one constraint per line.';
    if (low.includes("missing comparator"))
      return "Each constraint needs a comparator: <=, >=, =, <, or > between the left and right sides.";
    if (low.includes("only linear expressions"))
      return "Only linear sums are allowed: use `2 x` or `−y`, not `*` or `/` between coefficient and variable.";
    if (low.includes("cannot parse term"))
      return "A term in a sum could not be parsed. Use forms like `3 x`, `x`, or `−0.5 y` with explicit +/− between terms.";
    if (low.includes("no variables")) return message;
    return message;
  }

  type Constraint2d = AnalyzeResponse["constraints_2d"][number];

  function fmtLin2d(v: number): string {
    if (!Number.isFinite(v)) return "?";
    const a = Math.abs(v);
    if (a < 1e-10) return "0";
    if (Number.isInteger(v)) return String(v);
    return v.toFixed(4).replace(/\.?0+$/, "");
  }

  /** Human-readable boundary line for 2D constraint hover. */
  function constraintHoverText(c: Constraint2d, x0: string, x1: string): string {
    let lhs = `${fmtLin2d(c.a)}·${x0} + ${fmtLin2d(c.b)}·${x1}`;
    lhs = lhs.replace(/\+ -/g, "− ").replace(/\+ \+/g, "+ ");
    const sym = c.sense === "<=" ? "≤" : c.sense === ">=" ? "≥" : "=";
    return `<b>${escapeHtml(c.label.replace(/\s+/g, " ").trim())}</b><br>${lhs} ${sym} ${fmtLin2d(c.rhs)}`;
  }

  function escapeHtml(s: string): string {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  /** Readable tableau coefficients; wide values use scientific notation so cells stay scannable. */
  function formatTableauCell(value: number): string {
    if (!Number.isFinite(value)) return "—";
    const ax = Math.abs(value);
    if (ax === 0) return "0";
    if (ax >= 1e4 || (ax > 0 && ax < 1e-3)) return value.toPrecision(4);
    if (ax >= 1000) return value.toFixed(1);
    if (Number.isInteger(value) && ax < 1e3) return String(value);
    return value.toFixed(2);
  }

  function formatRatio(value: number): string {
    if (!Number.isFinite(value)) return "—";
    const ax = Math.abs(value);
    if (ax === 0) return "0";
    if (ax >= 1e4 || (ax > 0 && ax < 1e-4)) return value.toPrecision(4);
    if (ax >= 100) return value.toFixed(2);
    return value.toFixed(4);
  }

  function isDualRatioNarrative(narrative: string): boolean {
    const t = narrative.toLowerCase();
    return t.includes("dual pivot") || t.includes("dual ratio test");
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
    if ((verts?.length ?? 0) === 0 && !opt) {
      return { xrange: [-0.25, 4.25], yrange: [-0.25, 4.25] };
    }
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

  function interval1dXRange(
    lo: number | null | undefined,
    hi: number | null | undefined,
    optVal: number | undefined,
  ): [number, number] {
    const hasLo = lo != null && Number.isFinite(lo);
    const hasHi = hi != null && Number.isFinite(hi);
    if (hasLo && hasHi) {
      const span = hi! - lo!;
      const pad = Math.max(span * 0.14, 0.12);
      return [lo! - pad, hi! + pad];
    }
    if (hasHi && !hasLo) {
      const anchor = optVal != null && Number.isFinite(optVal) ? optVal : hi! - 1;
      const pad = Math.max(0.25 * Math.abs(hi!), 0.5);
      return [Math.min(anchor - 2 * pad, hi! - 4 * pad), hi! + pad];
    }
    if (hasLo && !hasHi) {
      const anchor = optVal != null && Number.isFinite(optVal) ? optVal : lo! + 1;
      const pad = Math.max(0.25 * Math.abs(lo!), 0.5);
      return [lo! - pad, Math.max(anchor + 2 * pad, lo! + 4 * pad)];
    }
    const a = optVal != null && Number.isFinite(optVal) ? optVal : 0;
    return [a - 2, a + 2];
  }

  function plotObjectiveCaption(d: AnalyzeResponse | null): string | null {
    if (!d?.problem) return null;
    const vars = d.problem.variables;
    if (vars.length === 1) {
      const v = vars[0]!;
      const c = d.problem.objective[v] ?? 0;
      const fc = Number.isInteger(c) ? String(c) : String(Math.round(c * 1000) / 1000);
      return `Objective ${fc}·${v}. The feasible set is an interval on the axis; the optimum lies at an endpoint unless the objective is flat on that segment.`;
    }
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

  function parseBigM(): number | null {
    const t = bigMText.trim();
    if (t === "") return null;
    const n = Number(t);
    return Number.isFinite(n) ? n : null;
  }

  async function analyze() {
    loading = true;
    err = null;
    data = null;
    activeStep = 0;
    tableauStep = 0;
    try {
      const big_m_value = parseBigM();
      const res = await fetch("/api/lp/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source,
          tableau_mode: tableauMode,
          use_blands_rule: useBlandsRule,
          big_m_value,
        }),
      });
      let raw: unknown;
      try {
        raw = await res.json();
      } catch {
        err = `Could not read response (HTTP ${res.status} ${res.statusText}). Is the API running on port 8000?`;
        return;
      }
      if (!res.ok) {
        const j = raw as { error?: string; detail?: unknown };
        const d = j.detail;
        err = humanizeApiError(
          typeof j.error === "string"
            ? j.error
            : typeof d === "string"
              ? d
              : `Request failed (HTTP ${res.status})`,
        );
        return;
      }
      const parsed = raw as AnalyzeResponse;
      const json: AnalyzeResponse = {
        ...parsed,
        modeling_notes: parsed.modeling_notes ?? [],
        tableau_verified: parsed.tableau_verified ?? null,
        tableau_verify_message: parsed.tableau_verify_message ?? null,
      };
      if (!json.ok) {
        err = humanizeApiError(json.error ?? "Request failed");
        return;
      }
      data = json;
      await drawPlot(json);
      await tick();
      solutionHeadingEl?.focus();
    } catch (e) {
      err = humanizeApiError(e instanceof Error ? e.message : String(e));
    } finally {
      loading = false;
    }
  }

  function printWorksheet() {
    window.print();
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
    if (is3dPoly && skipPlot3d) {
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

  $effect(() => {
    if (data && plotDiv) {
      void drawPlot(data);
    }
  });
</script>

<div
  class="lp-page"
  data-hints={showHints ? "on" : "off"}
  aria-busy={loading ? true : undefined}
>
<div class="lp-screen">
<header class="hero">
  <p class="eyebrow">Interactive LP</p>
  <h1>Feasible set &amp; simplex</h1>
  <p class="lede">
    Write an objective (<code>maximize</code> or <code>minimize</code>), a <code>subject to</code> line, then one constraint per line (commas between terms are fine). <strong>Analyze</strong> to solve, see the feasible region, follow the graphical tutor when it applies, and step through a simplex tableau when your model supports it. <strong>Print worksheet</strong> gives a clean page for notes or class.
  </p>
</header>

<div class="grid">
  <section class="panel">
    <h2 class="panel-title">Model</h2>
    <label for="src">Source</label>
    <textarea id="src" bind:value={source} rows="14" spellcheck="false"></textarea>
    <details class="solver-details">
      <summary>Tableau &amp; solver options</summary>
      <div class="solver-details-body">
        <label for="tab-mode">Tableau mode</label>
        <select id="tab-mode" bind:value={tableauMode}>
          <option value="auto">Auto</option>
          <option value="primal">Primal (two-phase)</option>
          <option value="dual">Dual simplex</option>
          <option value="big_m">Big-M</option>
        </select>
        <label class="check-row">
          <input type="checkbox" bind:checked={useBlandsRule} />
          Use Bland&rsquo;s rule (tie-breaking)
        </label>
        {#if tableauMode === "big_m"}
          <label for="big-m">Big M (optional)</label>
          <input
            id="big-m"
            class="big-m-input"
            type="text"
            inputmode="decimal"
            bind:value={bigMText}
            placeholder="Default from model scale"
            autocomplete="off"
          />
        {/if}
      </div>
    </details>
    <div class="preset-row">
      <label for="preset">Session preset</label>
      <select id="preset" bind:value={studyPreset}>
        <option value="default">Default</option>
        <option value="classroom">Classroom</option>
        <option value="self-study">Self-study</option>
      </select>
      <span class="muted small preset-hint"
        >Classroom: compact tableau, skip 3D plot/tutor, fewer on-screen hints.</span
      >
    </div>
    <div class="row">
      <button
        type="button"
        class="btn-analyze"
        onclick={() => analyze()}
        disabled={loading}
        aria-busy={loading ? true : undefined}
      >
        <span class="btn-analyze-left" aria-hidden="true">
          {#if loading}
            <span class="spinner spinner--btn"></span>
          {:else}
            <span class="btn-analyze-slot"></span>
          {/if}
        </span>
        <span class="btn-analyze-label">Analyze</span>
        <span class="btn-analyze-right" aria-hidden="true"><span class="btn-analyze-slot"></span></span>
      </button>
      <button type="button" class="ghost" onclick={() => (source = defaultSource)}>Reset example</button>
      <button type="button" class="ghost" onclick={printWorksheet}>Print worksheet</button>
    </div>
    {#if err}
      <p class="error">{err}</p>
    {/if}
  </section>

  <section class="panel grow plot-panel" class:plot-panel-loading={loading}>
    <div class="plot-head">
      <h2 class="panel-title">
        {#if data?.feasible_region && typeof data.feasible_region === "object" && "kind" in data.feasible_region && (data.feasible_region as { kind: string }).kind === "polyhedron_3d"}
          Feasible polyhedron (3D)
        {:else if data?.feasible_region && typeof data.feasible_region === "object" && "kind" in data.feasible_region && (data.feasible_region as { kind: string }).kind === "interval_1d"}
          Feasible interval
        {:else}
          Feasible set
        {/if}
      </h2>
      {#if data}
        {@const cap = plotObjectiveCaption(data)}
        {#if cap && (!isPolyhedron3d(data) || !skipPlot3d)}
          <p class="plot-sub hint-on">{cap}</p>
        {/if}
      {:else}
        <p class="plot-sub plot-sub-skeleton" class:sk-shimmer={loading} aria-hidden="true">
          <span class="sk-line sk-line-wide"></span>
        </p>
      {/if}
    </div>
    <div class="plot-wrap">
      {#if !data}
        <div class="plot-skeleton" class:sk-shimmer={loading} aria-hidden="true">
          <div class="plot-skeleton-inner">
            <div class="plot-skeleton-feasible"></div>
            <div class="plot-skeleton-axis"></div>
          </div>
        </div>
      {/if}
      <div class="plot" bind:this={plotDiv}></div>
      {#if loading}
        <div class="plot-busy" role="status" aria-live="polite">
          <span class="spinner" aria-hidden="true"></span>
          <span>Analyzing model&hellip;</span>
        </div>
      {/if}
    </div>
    {#if data && isPolyhedron3d(data) && skipPlot3d}
      <p class="muted small plot-note plot-skip-note">3D feasible region hidden for this session preset.</p>
    {/if}
    {#if data?.geometry_note}
      <p class="muted small plot-note hint-on">{data.geometry_note}</p>
    {/if}
  </section>
</div>

<div class="lp-below-grid">
{#if data}
  <section class="panel solution">
    <h2 class="panel-title" tabindex="-1" bind:this={solutionHeadingEl}>Solution</h2>
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
    {#if data.tableau_status === "ok" && data.tableau_verified != null}
      <p
        class="small tableau-verify"
        class:tableau-verify-ok={data.tableau_verified}
        class:tableau-verify-bad={!data.tableau_verified}
      >
        {#if data.tableau_verified}
          Tableau cross-check: final basis feasible solution matches HiGHS optimal value and constraints
          (within tolerance).
        {:else}
          Tableau cross-check failed. {data.tableau_verify_message ?? ""}
        {/if}
      </p>
      {#if data.tableau_verified && data.tableau_verify_message}
        <p class="muted small tableau-verify-note">{data.tableau_verify_message}</p>
      {/if}
    {/if}
  </section>

  {#if data.modeling_notes.length > 0}
    <section class="panel modeling-notes">
      <h2 class="panel-title">Modeling notes</h2>
      <ul class="modeling-notes-list">
        {#each data.modeling_notes as note, i (i)}
          <li>{note}</li>
        {/each}
      </ul>
    </section>
  {/if}

  {#if !(isPolyhedron3d(data) && skipPlot3d)}
    <div class="grid grid-tutor-row">
      <section class="panel panel-tutor">
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
    </div>
  {/if}

  {#if data.tableau_walkthrough}
    {@const tw = data.tableau_walkthrough}
    {@const st = tw.steps[tableauStep]}
    <section class="panel tableau-panel tableau-panel-bottom" class:tableau-compact={compactTableau}>
      <div class="tableau-head">
        <h2 class="panel-title tableau-title">
          Tableau <span class="tag">{tw.outcome}</span>
          <span class="muted small tableau-sense">Tableau sense: {tw.sense_for_tableau}</span>
        </h2>
        <div class="tableau-step-bar">
          <button
            type="button"
            class="ghost tableau-step-btn"
            disabled={tableauStep <= 0}
            aria-label="Previous tableau step"
            onclick={() => (tableauStep = Math.max(0, tableauStep - 1))}>← Prev</button>
          <span class="tableau-step-label"
            >Step <strong>{tableauStep + 1}</strong> of <strong>{tw.steps.length}</strong></span
          >
          <button
            type="button"
            class="ghost tableau-step-btn"
            disabled={tableauStep >= tw.steps.length - 1}
            aria-label="Next tableau step"
            onclick={() => {
              tableauStep = Math.min(tw.steps.length - 1, tableauStep + 1);
            }}>Next →</button>
        </div>
      </div>
      <p class="muted small tableau-lede">{tw.initial_narrative}</p>
      {#if st}
        <p class="tableau-narrative">{st.narrative}</p>
      {/if}
      {#if st}
        <div class="table-wrap">
          <table class="tableau">
            <colgroup>
              <col class="tableau-col-basis" />
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
        {#if st?.ratios?.length}
          {@const ratioNums = st.ratios.filter((r) => r != null && Number.isFinite(r))}
          {#if ratioNums.length > 0}
            {@const dualRatios = isDualRatioNarrative(st.narrative)}
            {@const primalByRow = !dualRatios && st.ratios.length === st.basis_labels.length}
            {@const enteringName =
              st.entering_col != null &&
              st.entering_col >= 0 &&
              st.entering_col < st.column_labels.length &&
              st.column_labels[st.entering_col] !== "RHS"
                ? st.column_labels[st.entering_col]
                : null}
            <div class="tableau-ratios" role="region" aria-label="Ratio test values for this step">
              <p class="tableau-ratios-lede">
                {#if dualRatios}
                  Dual ratio test · one value per tableau column for this pivot
                {:else if enteringName}
                  Primal minimum ratio test · use the <strong>{enteringName}</strong> column with each
                  <strong>constraint</strong> row (ignore the bottom z-row here)
                {:else}
                  Primal minimum ratio test · one ratio per constraint row
                {/if}
              </p>
              {#if primalByRow}
                <ul class="tableau-ratios-list">
                  {#each st.ratios as r, i (i)}
                    <li>
                      <span class="tableau-ratios-k">Row {i + 1} ({st.basis_labels[i]}):</span>
                      <code class="tableau-ratios-v">{r == null || !Number.isFinite(r) ? "—" : formatRatio(r)}</code>
                    </li>
                  {/each}
                </ul>
                <p class="muted small tableau-ratios-hint hint-on">
                  For row <em>i</em> in the basis list above: divide that row&rsquo;s <strong>RHS</strong> by the number in
                  the <strong>{enteringName ?? "entering"}</strong> column on the same row. If that entry is
                  <strong>greater than 0</strong>, you get a ratio; if it is <strong>zero or negative</strong>, the
                  ratio is <strong>–</strong> (that row does not cap how far you can increase the entering variable).
                  The <strong>smallest</strong> positive ratio is the winner; its row is where the <strong>leaving</strong>
                  basic variable is chosen.
                </p>
              {:else}
                <ul class="tableau-ratios-list tableau-ratios-cols">
                  {#each st.ratios as r, j (j)}
                    {#if j < st.column_labels.length - 1 && st.column_labels[j] !== "RHS"}
                      <li>
                        <span class="tableau-ratios-k">{st.column_labels[j]}:</span>
                        <code class="tableau-ratios-v">{r == null || !Number.isFinite(r) ? "—" : formatRatio(r)}</code>
                      </li>
                    {/if}
                  {/each}
                </ul>
                <p class="muted small tableau-ratios-hint hint-on">
                  {#if dualRatios}
                    One entry per column header (not RHS). <strong>–</strong> means that column is not eligible for the
                    dual ratio rule on this pivot. The smallest finite eligible ratio picks the <strong>entering</strong>
                    variable.
                  {:else}
                    <strong>–</strong> marks columns that do not get a ratio on this step.
                  {/if}
                </p>
              {/if}
            </div>
          {/if}
        {/if}
        <p class="muted small tableau-basis hint-on">
          Each constraint row shows its basic variable in the first column; the bottom row is the z-row (objective,
          maximize slack form).
        </p>
      {/if}
    </section>
  {:else if data.tableau_message}
    <section class="panel tableau-panel tableau-panel-bottom">
      <h2 class="panel-title">Tableau</h2>
      <p class="muted">{data.tableau_message}</p>
    </section>
  {/if}
{:else}
  <div class="sk-placeholder-root" class:sk-shimmer={loading}>
    <section class="panel sk-panel solution-skeleton" aria-hidden="true">
      <div class="sk-title"></div>
      <div class="sk-stack">
        <div class="sk-line sk-line-wide"></div>
        <div class="sk-line sk-line-medium"></div>
        <div class="sk-line sk-line-narrow"></div>
      </div>
    </section>
    <section class="panel sk-panel tutor-skeleton" aria-hidden="true">
      <div class="sk-title sk-title-short"></div>
      <div class="sk-step-pill"></div>
      <div class="sk-step-pill sk-step-pill-delay"></div>
    </section>
    <section class="panel sk-panel tableau-skeleton" aria-hidden="true">
      <div class="sk-tableau-top">
        <div class="sk-title sk-title-medium"></div>
        <div class="sk-stepbar">
          <div class="sk-chip"></div>
          <div class="sk-chip sk-chip-wide"></div>
          <div class="sk-chip"></div>
        </div>
      </div>
      <div class="sk-line sk-line-wide sk-gap-top"></div>
      <div class="sk-table-rows">
        {#each [0, 1, 2, 3, 4, 5] as r (r)}
          <div class="sk-table-row" style="--sk-i: {r}"></div>
        {/each}
      </div>
    </section>
  </div>
{/if}
</div>

</div>

<aside class="lp-print-sheet" aria-label="Printable worksheet">
  <h2 class="print-sheet-title">Linear program (worksheet)</h2>
  <pre class="print-problem">{source}</pre>
  <div class="print-workspace">
    <p class="print-workspace-label">Workspace</p>
  </div>
</aside>
</div>

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
    .grid:not(.grid-tutor-row) {
      grid-template-columns: minmax(0, 1fr) minmax(0, 1.12fr);
      align-items: start;
    }
  }
  .grid-tutor-row {
    margin-top: 0.25rem;
    grid-template-columns: minmax(0, 1fr);
  }
  .panel-tutor {
    min-height: 0;
    width: 100%;
    max-width: none;
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
  .tableau-verify {
    margin: 0.65rem 0 0;
    font-weight: 600;
    line-height: 1.45;
  }
  .tableau-verify-ok {
    color: var(--color-text-muted);
  }
  .tableau-verify-bad {
    color: var(--color-danger);
  }
  .tableau-verify-note {
    margin: 0.35rem 0 0;
    max-width: 48rem;
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
  .btn-analyze {
    display: inline-grid;
    grid-template-columns: 1.15rem auto 1.15rem;
    align-items: center;
    justify-items: center;
    column-gap: 0.35rem;
  }
  .btn-analyze-left,
  .btn-analyze-right {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 1.15rem;
    height: 1.15rem;
  }
  .btn-analyze-left {
    grid-column: 1;
  }
  .btn-analyze-label {
    grid-column: 2;
  }
  .btn-analyze-right {
    grid-column: 3;
  }
  .btn-analyze-slot {
    display: block;
    width: 1.05rem;
    height: 1.05rem;
    flex-shrink: 0;
  }
  .spinner.spinner--btn {
    width: 1.05rem;
    height: 1.05rem;
    border-width: 2px;
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
    -webkit-tap-highlight-color: transparent;
    touch-action: manipulation;
  }
  button:focus {
    outline: none;
  }
  button:focus-visible {
    outline: 2px solid var(--color-accent);
    outline-offset: 2px;
  }
  button:hover:not(:disabled) {
    background: var(--color-accent-hover);
  }
  button:active:not(:disabled) {
    transform: none;
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
  button.ghost:active:not(:disabled) {
    background: var(--color-bg-deep);
    border-color: var(--color-text-faint);
  }
  .plot {
    position: relative;
    z-index: 1;
    width: 100%;
    min-height: 380px;
    border-radius: var(--radius-sm);
    border: 1px solid var(--color-border);
    overflow: hidden;
    background: var(--plot-paper);
    touch-action: pan-x pan-y pinch-zoom;
    overscroll-behavior: contain;
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
  ol.steps li button:active:not(:disabled) {
    border-color: var(--color-border-strong);
    background: color-mix(in srgb, var(--color-surface-raised) 70%, var(--color-bg));
    box-shadow: none;
  }
  ol.steps li button.sel:active:not(:disabled) {
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
    overflow-x: auto;
    overflow-y: visible;
    -webkit-overflow-scrolling: touch;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    background: var(--color-surface);
    margin-top: 0.85rem;
  }
  table.tableau {
    border-collapse: collapse;
    table-layout: auto;
    width: max-content;
    min-width: 100%;
    max-width: none;
    font-size: 0.95rem;
    font-family: var(--font-mono);
    font-variant-numeric: tabular-nums lining-nums;
  }
  col.tableau-col-basis {
    width: auto;
    min-width: 4.5rem;
  }
  table.tableau th,
  table.tableau td {
    border-bottom: 1px solid var(--color-border);
    padding: 0.5rem 0.65rem;
    vertical-align: middle;
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
    white-space: nowrap;
    min-width: 3.25rem;
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

  .tableau-panel-bottom {
    margin-top: 1rem;
  }
  .tableau-head {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    justify-content: space-between;
    gap: 0.75rem 1.25rem;
    margin-bottom: 0.35rem;
  }
  .tableau-title {
    margin: 0;
    flex: 1 1 12rem;
  }
  .tableau-step-bar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.65rem 1rem;
    padding: 0.45rem 0.65rem;
    border-radius: var(--radius-sm);
    background: var(--color-bg-deep);
    border: 1px solid var(--color-border);
  }
  .tableau-step-btn {
    padding: 0.55rem 1.15rem !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    min-width: 6.5rem;
  }
  .tableau-step-label {
    font-size: 0.95rem;
    color: var(--color-text);
    min-width: 8.5rem;
    text-align: center;
  }
  .tableau-lede {
    margin: 0.5rem 0 0;
    line-height: 1.45;
    max-width: 60rem;
  }
  .tableau-narrative {
    margin: 0.65rem 0 0;
    line-height: 1.5;
    font-size: 0.95rem;
    max-width: 60rem;
  }
  .tableau-ratios {
    margin: 0.5rem 0 0;
    padding: 0.55rem 0.7rem;
    border-radius: var(--radius-sm);
    border: 1px solid var(--color-border);
    background: color-mix(in srgb, var(--color-bg-deep) 65%, var(--color-surface-raised));
    max-width: 52rem;
  }
  .tableau-ratios-lede {
    margin: 0 0 0.4rem;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--color-text-muted);
  }
  .tableau-ratios-list {
    margin: 0;
    padding: 0;
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 0.28rem 1rem;
    font-size: 0.86rem;
  }
  @media (min-width: 640px) {
    .tableau-ratios-list.tableau-ratios-cols {
      flex-flow: row wrap;
    }
  }
  .tableau-ratios-list li {
    display: flex;
    align-items: baseline;
    gap: 0.35rem;
    min-width: 0;
  }
  .tableau-ratios-k {
    color: var(--color-text-muted);
    font-weight: 500;
    flex: 0 0 auto;
  }
  .tableau-ratios-v {
    font-family: var(--font-mono);
    font-variant-numeric: tabular-nums;
    font-size: 0.84rem;
  }
  .tableau-ratios-hint {
    margin: 0.45rem 0 0;
    line-height: 1.45;
  }
  .tableau-basis {
    margin: 0.65rem 0 0;
  }

  .lp-page[data-hints="off"] .hint-on {
    display: none !important;
  }

  .solver-details {
    margin-top: 0.75rem;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    padding: 0.35rem 0.65rem;
    background: var(--color-surface);
  }
  .solver-details summary {
    cursor: pointer;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--color-text-muted);
    user-select: none;
  }
  .solver-details-body {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
    margin-top: 0.65rem;
    padding-top: 0.55rem;
    border-top: 1px solid var(--color-border);
  }
  .solver-details-body select,
  .big-m-input {
    font-family: var(--font-sans);
    font-size: 0.88rem;
    padding: 0.35rem 0.45rem;
    border-radius: var(--radius-sm);
    border: 1px solid var(--color-border-strong);
    background: var(--color-surface-raised);
    color: var(--color-text);
    max-width: 16rem;
  }
  .check-row {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    font-size: 0.86rem;
    color: var(--color-text);
    font-weight: 500;
  }
  .preset-row {
    margin-top: 0.75rem;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }
  .preset-hint {
    max-width: 36rem;
  }

  .plot-wrap {
    position: relative;
    min-height: 380px;
    overscroll-behavior: contain;
  }
  .plot-panel-loading .plot {
    opacity: 0.35;
    pointer-events: none;
  }
  .plot-busy {
    position: absolute;
    inset: 0;
    z-index: 2;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.65rem;
    background: color-mix(in srgb, var(--color-surface-raised) 88%, transparent);
    font-size: 0.92rem;
    font-weight: 600;
    color: var(--color-text-muted);
  }
  .spinner {
    width: 1.65rem;
    height: 1.65rem;
    border: 2px solid var(--color-border-strong);
    border-top-color: var(--color-accent);
    border-radius: 50%;
    animation: lp-spin 0.75s linear infinite;
  }
  @keyframes lp-spin {
    to {
      transform: rotate(360deg);
    }
  }

  .modeling-notes-list {
    margin: 0;
    padding-left: 1.15rem;
    color: var(--color-text);
    font-size: 0.92rem;
    line-height: 1.55;
  }
  .modeling-notes-list li {
    margin: 0.25rem 0;
  }

  .tableau-sense {
    font-weight: 500;
  }

  .tableau-compact table.tableau {
    font-size: 0.82rem;
  }
  .tableau-compact table.tableau th,
  .tableau-compact table.tableau td {
    padding: 0.38rem 0.45rem;
  }
  .tableau-compact .tableau-step-btn {
    padding: 0.45rem 0.85rem !important;
    font-size: 0.88rem !important;
    min-width: 5.5rem;
  }
  .tableau-compact .tableau-step-label {
    font-size: 0.88rem;
  }

  .lp-below-grid {
    display: flex;
    flex-direction: column;
    gap: 1.1rem;
    margin-top: 1.1rem;
  }

  .plot-sub-skeleton {
    margin: 0;
    min-height: 1.35rem;
    display: flex;
    align-items: center;
  }

  .plot-skeleton {
    position: absolute;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    border-radius: var(--radius-sm);
    background: color-mix(in srgb, var(--color-surface) 92%, var(--color-bg-deep));
  }
  .plot-skeleton-inner {
    position: absolute;
    inset: 10% 9% 12% 11%;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    gap: 0.45rem;
    border: 1px dashed color-mix(in srgb, var(--color-border) 75%, transparent);
    border-radius: 6px;
    padding: 0.5rem 0.55rem;
  }
  .plot-skeleton-feasible {
    flex: 1;
    min-height: 42%;
    border-radius: 5px;
    background: color-mix(in srgb, var(--color-border) 35%, var(--color-surface));
    opacity: 0.52;
    animation: none;
  }
  .plot-skeleton-axis {
    height: 0.55rem;
    border-radius: 4px;
    width: 72%;
    align-self: flex-end;
    background: color-mix(in srgb, var(--color-border) 55%, var(--color-bg-deep));
    opacity: 0.55;
    animation: none;
  }
  .plot-skeleton.sk-shimmer .plot-skeleton-feasible {
    animation: sk-pulse 1.35s ease-in-out infinite;
  }
  .plot-skeleton.sk-shimmer .plot-skeleton-axis {
    animation: sk-pulse 1.35s ease-in-out 0.15s infinite;
  }

  .sk-placeholder-root {
    display: flex;
    flex-direction: column;
    gap: 1.1rem;
  }

  @keyframes sk-pulse {
    0%,
    100% {
      opacity: 0.42;
    }
    50% {
      opacity: 0.78;
    }
  }

  .sk-panel {
    min-height: 0;
  }
  .solution-skeleton {
    min-height: 7.5rem;
  }
  .tutor-skeleton {
    min-height: 9.5rem;
  }
  .tutor-skeleton .sk-step-pill {
    max-width: none;
  }
  .tableau-skeleton {
    min-height: 18rem;
  }
  .sk-title {
    height: 1.05rem;
    width: 6.5rem;
    border-radius: 5px;
    background: color-mix(in srgb, var(--color-border) 50%, var(--color-bg-deep));
    opacity: 0.54;
    animation: none;
  }
  .sk-title-short {
    width: 5rem;
  }
  .sk-title-medium {
    width: 9rem;
  }
  .sk-stack {
    margin-top: 0.85rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .sk-line {
    height: 0.68rem;
    border-radius: 4px;
    background: color-mix(in srgb, var(--color-border) 45%, var(--color-bg-deep));
    opacity: 0.52;
    animation: none;
  }
  .sk-line-wide {
    width: min(100%, 22rem);
  }
  .sk-line-medium {
    width: min(100%, 15rem);
  }
  .sk-line-narrow {
    width: min(100%, 9rem);
  }
  .plot-sub-skeleton .sk-line {
    opacity: 0.5;
    animation: none;
  }
  .plot-sub-skeleton.sk-shimmer .sk-line {
    animation: sk-pulse 1.35s ease-in-out infinite;
  }
  .sk-gap-top {
    margin-top: 0.75rem;
  }
  .sk-step-pill {
    margin-top: 0.65rem;
    height: 2.65rem;
    max-width: 30rem;
    width: 100%;
    border-radius: var(--radius-sm);
    border: 1px solid var(--color-border);
    background: color-mix(in srgb, var(--color-surface) 70%, var(--color-bg-deep));
    opacity: 0.5;
    animation: none;
  }
  .sk-step-pill-delay {
    opacity: 0.48;
  }
  .sk-tableau-top {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    justify-content: space-between;
    gap: 0.75rem 1rem;
    margin-bottom: 0.35rem;
  }
  .sk-stepbar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0.55rem;
    border-radius: var(--radius-sm);
    border: 1px solid var(--color-border);
    background: var(--color-bg-deep);
  }
  .sk-chip {
    height: 1.85rem;
    width: 5.5rem;
    border-radius: var(--radius-sm);
    background: color-mix(in srgb, var(--color-border) 40%, var(--color-surface-raised));
    opacity: 0.52;
    animation: none;
  }
  .sk-chip-wide {
    width: 8.5rem;
  }
  .sk-table-rows {
    margin-top: 0.65rem;
    display: flex;
    flex-direction: column;
    gap: 0.38rem;
  }
  .sk-table-row {
    height: 0.95rem;
    width: 100%;
    border-radius: 4px;
    background: color-mix(in srgb, var(--color-border) 38%, var(--color-bg-deep));
    opacity: 0.5;
    animation: none;
  }

  .sk-placeholder-root.sk-shimmer .sk-title,
  .sk-placeholder-root.sk-shimmer .sk-line,
  .sk-placeholder-root.sk-shimmer .sk-step-pill,
  .sk-placeholder-root.sk-shimmer .sk-chip,
  .sk-placeholder-root.sk-shimmer .sk-table-row {
    animation: sk-pulse 1.35s ease-in-out infinite;
  }
  .sk-placeholder-root.sk-shimmer .sk-line-medium {
    animation-delay: 0.08s;
  }
  .sk-placeholder-root.sk-shimmer .sk-line-narrow {
    animation-delay: 0.16s;
  }
  .sk-placeholder-root.sk-shimmer .sk-step-pill {
    animation-delay: 0.05s;
  }
  .sk-placeholder-root.sk-shimmer .sk-step-pill-delay {
    animation-delay: 0.12s;
  }
  .sk-placeholder-root.sk-shimmer .sk-chip-wide {
    animation-delay: 0.1s;
  }
  .sk-placeholder-root.sk-shimmer .sk-table-row {
    animation-delay: calc(0.04s * var(--sk-i, 0));
  }

  @media (prefers-reduced-motion: reduce) {
    .plot-skeleton.sk-shimmer .plot-skeleton-feasible,
    .plot-skeleton.sk-shimmer .plot-skeleton-axis,
    .plot-sub-skeleton.sk-shimmer .sk-line,
    .sk-placeholder-root.sk-shimmer .sk-title,
    .sk-placeholder-root.sk-shimmer .sk-line,
    .sk-placeholder-root.sk-shimmer .sk-step-pill,
    .sk-placeholder-root.sk-shimmer .sk-chip,
    .sk-placeholder-root.sk-shimmer .sk-table-row {
      animation: none !important;
      opacity: 0.52;
    }
  }
</style>
