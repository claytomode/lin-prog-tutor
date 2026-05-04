from __future__ import annotations

import numpy as np

from backend.geometry import (
    feasible_interval_1d,
    geometry_3d_vertices,
    order_polygon_ccw,
    vertices_2d_halfspaces,
)
from backend.mip_plot import discrete_feasible_points_2d
from backend.model import LinprogMatrices, build_matrices, point_dict
from backend.parser import ParseError, merge_request_variable_domains, parse_lp_source
from backend.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ConstraintPlot2D,
    FeasibleRegion1D,
    FeasibleRegion2D,
    ParsedProblemView,
)
from backend.solver import solve_dispatch
from backend.tableau import TableauOptions, build_tableau_if_supported
from backend.tableau_verify import verify_tableau_against_solver
from backend.tutor_graphical import build_3d_vertex_tutor, build_graphical_tutor


def _error_response(
    *,
    code: str,
    message: str,
    hint: str | None = None,
    context: dict[str, object] | None = None,
) -> AnalyzeResponse:
    return AnalyzeResponse(
        ok=False,
        error=message,
        error_code=code,
        error_hint=hint,
        error_context=context,
    )


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
        merge_request_variable_domains(parsed, body.variable_domains)
        mat = build_matrices(parsed)
    except ParseError as exc:
        return _error_response(
            code=exc.code,
            message=str(exc),
            hint=exc.hint,
            context=exc.context,
        )
    except ValueError as exc:
        msg = str(exc)
        if msg == "no variables":
            return _error_response(
                code="NO_VARIABLES",
                message=msg,
                hint="Use variable terms like `x`, `y`, or `z` in objective/constraints.",
            )
        return _error_response(code="MODEL_ERROR", message=f"model error: {exc}")
    except Exception as exc:  # noqa: BLE001
        return _error_response(code="MODEL_ERROR", message=f"model error: {exc}")

    inferred_problem_class = "milp" if parsed.is_mip else "lp"
    requested_problem_class = body.problem_class
    if requested_problem_class == "lp" and parsed.is_mip:
        return _error_response(
            code="PROBLEM_CLASS_MISMATCH",
            message="requested LP class but integer/binary variable domains were declared",
            hint="Set problem_class to `auto` or `milp`, or remove integer/binary domains.",
        )

    solve = solve_dispatch(mat, is_mip=parsed.is_mip)
    if solve.error_code is not None:
        return _error_response(
            code=solve.error_code,
            message=solve.message,
            hint=solve.error_hint,
            context={
                "problem_class": inferred_problem_class,
                "is_mip": parsed.is_mip,
                "mip_diagnostics": solve.diagnostics,
            },
        )

    problem = ParsedProblemView(
        sense=parsed.objective_sense,
        variables=mat.var_names,
        variable_domains=mat.var_domains,
        problem_class=inferred_problem_class,
        is_mip=parsed.is_mip,
        objective={v: float(c) for v, c in parsed.objective.items()},
        constraint_labels=plot_labels,
    )

    mip_diag = solve.diagnostics or {}
    resp = AnalyzeResponse(
        modeling_notes=list(parsed.modeling_notes),
        problem_class=inferred_problem_class,
        is_mip=parsed.is_mip,
        mip_diagnostics=solve.diagnostics,
        mip_gap=mip_diag.get("mip_gap"),
        mip_node_count=mip_diag.get("mip_node_count"),
        mip_time_limit_hit=mip_diag.get("mip_time_limit_hit"),
        problem=problem,
        solve_status=solve.status,
        optimal_value=solve.fun if solve.status == "optimal" else None,
        optimal_point=(
            point_dict(mat, solve.x, snap_domains=parsed.is_mip)
            if solve.status == "optimal" and solve.x is not None
            else None
        ),
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
        if parsed.is_mip:
            resp.mip_discrete_points_2d = discrete_feasible_points_2d(mat, A_all, b_all, verts)
            if resp.mip_discrete_points_2d:
                note = (
                    "Shaded region: LP relaxation; dots: feasible integer/binary points in this slice."
                )
                resp.geometry_note = (resp.geometry_note + "; " if resp.geometry_note else "") + note
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
    if n == 2 and A_all.size > 0 and not parsed.is_mip:
        verts_np = vertices_2d_halfspaces(A_all, b_all)
        if verts_np.shape[0] > 0:
            verts_np = order_polygon_ccw(verts_np)
        resp.tutor_steps = build_graphical_tutor(mat, solve, verts_np)
    elif (
        n == 3
        and A_all.size > 0
        and solve.status == "optimal"
        and solve.x is not None
        and not parsed.is_mip
    ):
        fr = resp.feasible_region
        v3: list[list[float]] = []
        if isinstance(fr, dict) and fr.get("kind") == "polyhedron_3d":
            v3 = fr.get("vertices") or []
        if v3:
            resp.tutor_steps = build_3d_vertex_tutor(mat, solve, np.asarray(v3, dtype=float))

    if solve.status == "optimal" and not parsed.is_mip:
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
    elif solve.status == "optimal" and parsed.is_mip:
        resp.tableau_status = "skipped"
        resp.tableau_message = (
            "Tableau walkthrough applies to continuous linear programs; "
            "mixed-integer models use branch-and-bound (or similar), not this primal simplex tableau."
        )
    else:
        resp.tableau_status = "skipped"

    return resp
