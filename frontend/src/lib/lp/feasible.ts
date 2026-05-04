import type { AnalyzeResponse } from "./types.js";

export function isPolyhedron3d(d: AnalyzeResponse | null): boolean {
  const fr = d?.feasible_region;
  return (
    fr != null &&
    typeof fr === "object" &&
    "kind" in fr &&
    (fr as { kind: string }).kind === "polyhedron_3d"
  );
}

/** True when the analyze response includes geometry the 2D Plotly panel can draw. */
export function hasFeasibleSetSketch(
  d: AnalyzeResponse | null,
  skipPlot3d: boolean,
): boolean {
  if (!d?.problem) return false;
  const n = d.problem.variables.length;
  if (n === 1) {
    const fr = d.feasible_region;
    return (
      fr != null &&
      typeof fr === "object" &&
      "kind" in fr &&
      (fr as { kind: string }).kind === "interval_1d"
    );
  }
  if (n === 2) return true;
  if (n === 3) {
    if (skipPlot3d) return false;
    const fr = d.feasible_region;
    if (
      fr != null &&
      typeof fr === "object" &&
      "kind" in fr &&
      (fr as { kind: string }).kind === "polyhedron_3d"
    ) {
      const verts = "vertices" in fr ? (fr as { vertices: unknown }).vertices : [];
      return Array.isArray(verts) && verts.length >= 4;
    }
    return false;
  }
  return false;
}

export function squareView(
  verts: [number, number][] | undefined,
  opt: { x: number; y: number } | undefined,
  extraPoints?: [number, number][],
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
  for (const p of extraPoints ?? []) use(p[0], p[1]);
  if (opt) use(opt.x, opt.y);
  if ((verts?.length ?? 0) === 0 && !opt && (extraPoints?.length ?? 0) === 0) {
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

export function interval1dXRange(
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

export function plotObjectiveCaption(d: AnalyzeResponse | null): string | null {
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
    const dots = (d.mip_discrete_points_2d?.length ?? 0) > 0;
    if (d.is_mip && dots) {
      return `Shaded region: LP relaxation; open circles: feasible integer/binary (${v0}, ${v1}). Arrow: objective direction in that relaxation (∇f or −∇f), not the integer hull. The MILP optimum is one of the circles here—you cannot rely on “solve the LP and round” in general.`;
    }
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
