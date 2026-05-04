from __future__ import annotations

import numpy as np

from backend.geometry import (
    feasible_interval_1d,
    geometry_3d_vertices,
    order_polygon_ccw,
    vertices_2d_halfspaces,
)
from backend.model import LinprogMatrices, build_matrices, point_dict, solve_lp
from backend.parser import ParseError, parse_lp_source
from backend.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ConstraintPlot2D,
    FeasibleRegion1D,
    FeasibleRegion2D,
    ParsedProblemView,
)
from backend.tableau import TableauOptions, build_tableau_if_supported
from backend.tableau_verify import verify_tableau_against_solver
from backend.tutor_graphical import build_3d_vertex_tutor, build_graphical_tutor


def _constraints_for_plot(mat: LinprogMatrices, labels: list[str]) -> list[ConstraintPlot2D]:
    out: list[ConstraintPlot2D] = []
    if len(mat.var_names) != 2:
        return out
    if mat.A_ub is not None and mat.b_ub is not None:
        for i, row in enumerate(mat.A_ub):
            a, b = float(row[0]), float(row[1])
            rhs = float(mat.b_ub[i])
            label = labels[i] if i < len(labels) else f"row {i + 1}"
            out.append(ConstraintPlot2D(a=a, b=b, rhs=rhs, sense="<=", label=label))
    if mat.A_eq is not None and mat.b_eq is not None:
        for i, row in enumerate(mat.A_eq):
            a, b = float(row[0]), float(row[1])
            rhs = float(mat.b_eq[i])
            label = labels[len(out) + i] if len(out) + i < len(labels) else f"eq {i + 1}"
            out.append(ConstraintPlot2D(a=a, b=b, rhs=rhs, sense="=", label=label))
    return out


def _stack_inequalities(mat: LinprogMatrices) -> tuple[np.ndarray, np.ndarray]:
    rows: list[np.ndarray] = []
    rhs: list[float] = []
    if mat.A_ub is not None and mat.b_ub is not None:
        for i in range(mat.A_ub.shape[0]):
            rows.append(mat.A_ub[i])
            rhs.append(float(mat.b_ub[i]))
    if mat.A_eq is not None and mat.b_eq is not None:
        for i in range(mat.A_eq.shape[0]):
            rows.append(mat.A_eq[i])
            rhs.append(float(mat.b_eq[i]))
            rows.append(-mat.A_eq[i])
            rhs.append(-float(mat.b_eq[i]))
    n = len(mat.var_names)
    for j, (lo, hi) in enumerate(mat.bounds):
        e = np.zeros(n)
        e[j] = 1.0
        if lo is not None and lo > -1e100:
            rows.append(-e)
            rhs.append(-float(lo))
        if hi is not None and hi < 1e100:
            rows.append(e)
            rhs.append(float(hi))
    if not rows:
        return np.zeros((0, n)), np.zeros(0)
    return np.vstack(rows), np.array(rhs, dtype=float)


def analyze_source(request: AnalyzeRequest | str) -> AnalyzeResponse:
    if isinstance(request, str):
        body = AnalyzeRequest(source=request)
    else:
        body = request
    source = body.source
    try:
        parsed, plot_labels = parse_lp_source(source)
        mat = build_matrices(parsed)
    except ParseError as exc:
        return AnalyzeResponse(ok=False, error=str(exc))
    except Exception as exc:  # noqa: BLE001
        return AnalyzeResponse(ok=False, error=f"model error: {exc}")

    solve = solve_lp(mat)

    problem = ParsedProblemView(
        sense=parsed.objective_sense,
        variables=mat.var_names,
        objective={v: float(c) for v, c in parsed.objective.items()},
        constraint_labels=plot_labels,
    )

    resp = AnalyzeResponse(
        modeling_notes=list(parsed.modeling_notes),
        problem=problem,
        solve_status=solve.status,
        optimal_value=solve.fun if solve.status == "optimal" else None,
        optimal_point=point_dict(mat, solve.x) if solve.status == "optimal" and solve.x is not None else None,
        constraints_2d=_constraints_for_plot(mat, plot_labels),
    )

    A_all, b_all = _stack_inequalities(mat)
    n = len(mat.var_names)

    if n == 1 and A_all.size > 0:
        lo, hi = feasible_interval_1d(A_all, b_all)
        if lo is None and hi is None:
            resp.geometry_note = "Infeasible on the line."
        else:
            resp.feasible_region = FeasibleRegion1D(var=mat.var_names[0], lo=lo, hi=hi)
    elif n == 2 and A_all.size > 0:
        verts = vertices_2d_halfspaces(A_all, b_all)
        if verts.shape[0] > 0:
            verts = order_polygon_ccw(verts)
        resp.feasible_region = FeasibleRegion2D(vertices=[(float(p[0]), float(p[1])) for p in verts])
    elif n == 3 and A_all.size > 0 and solve.status == "optimal" and solve.x is not None:
        v3d, note = geometry_3d_vertices(A_all, b_all, solve.x)
        if v3d is not None:
            resp.feasible_region = {
                "kind": "polyhedron_3d",
                "vertices": v3d.tolist(),
            }
        if note:
            resp.geometry_note = (resp.geometry_note + "; " if resp.geometry_note else "") + note
    elif n > 3:
        resp.geometry_note = "Geometry sketch is limited to 3D; solver still runs in higher dimension."

    verts_np = np.zeros((0, 2))
    if n == 2 and A_all.size > 0:
        verts_np = vertices_2d_halfspaces(A_all, b_all)
        if verts_np.shape[0] > 0:
            verts_np = order_polygon_ccw(verts_np)
        resp.tutor_steps = build_graphical_tutor(mat, solve, verts_np)
    elif n == 3 and A_all.size > 0 and solve.status == "optimal" and solve.x is not None:
        fr = resp.feasible_region
        v3: list[list[float]] = []
        if isinstance(fr, dict) and fr.get("kind") == "polyhedron_3d":
            v3 = fr.get("vertices") or []
        if v3:
            resp.tutor_steps = build_3d_vertex_tutor(mat, solve, np.asarray(v3, dtype=float))

    if solve.status == "optimal":
        topts = TableauOptions(
            tableau_mode=body.tableau_mode,
            use_blands_rule=body.use_blands_rule,
            big_m_value=body.big_m_value,
        )
        tw, tstat = build_tableau_if_supported(mat, topts)
        if tw is not None and tstat == "ok":
            resp.tableau_walkthrough = tw
            resp.tableau_status = "ok"
            if solve.x is not None:
                try:
                    ok_v, msg_v = verify_tableau_against_solver(
                        mat,
                        tw,
                        np.asarray(solve.x, dtype=float),
                        resp.optimal_value,
                    )
                    resp.tableau_verified = ok_v
                    resp.tableau_verify_message = msg_v
                    if not ok_v and msg_v:
                        resp.modeling_notes = [*list(resp.modeling_notes), f"Tableau cross-check: {msg_v}"]
                except Exception as exc:  # noqa: BLE001
                    resp.tableau_verified = False
                    note = f"Tableau verification error: {exc}"
                    resp.tableau_verify_message = note
                    resp.modeling_notes = [*list(resp.modeling_notes), note]
        else:
            resp.tableau_status = "not_supported_yet"
            if tw is None and tstat:
                resp.tableau_message = tstat
    else:
        resp.tableau_status = "skipped"

    return resp
