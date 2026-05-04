"""Solver abstraction: continuous LP (HiGHS) vs mixed-integer (HiGHS MILP via scipy.optimize.milp)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp

from backend.lp.model import LinprogMatrices


@dataclass
class SolveResult:
    status: str
    fun: float | None
    x: np.ndarray | None
    message: str
    raw: Any = None
    error_code: str | None = None
    error_hint: str | None = None
    diagnostics: dict[str, Any] | None = None


def _bounds_from_mat(mat: LinprogMatrices) -> Bounds:
    lb: list[float] = []
    ub: list[float] = []
    for lo, hi in mat.bounds:
        lb.append(-np.inf if lo is None else float(lo))
        ub.append(np.inf if hi is None else float(hi))
    return Bounds(np.asarray(lb, dtype=float), np.asarray(ub, dtype=float))


def _linear_constraints_from_mat(mat: LinprogMatrices) -> LinearConstraint | tuple[LinearConstraint, ...] | None:
    parts: list[LinearConstraint] = []
    if mat.A_ub is not None and mat.b_ub is not None and mat.A_ub.size > 0:
        m = mat.A_ub.shape[0]
        parts.append(LinearConstraint(mat.A_ub, -np.inf * np.ones(m, dtype=float), mat.b_ub))
    if mat.A_eq is not None and mat.b_eq is not None and mat.A_eq.size > 0:
        parts.append(LinearConstraint(mat.A_eq, mat.b_eq, mat.b_eq))
    if not parts:
        return None
    if len(parts) == 1:
        return parts[0]
    return tuple(parts)


def _integrality_from_mat(mat: LinprogMatrices) -> np.ndarray:
    """SciPy: 0 continuous, 1 integer, 2 binary."""
    out = np.zeros(len(mat.var_names), dtype=np.int32)
    for i, v in enumerate(mat.var_names):
        d = mat.var_domains[v]
        if d == "binary":
            out[i] = 2
        elif d == "integer":
            out[i] = 1
        else:
            out[i] = 0
    return out


def _milp_status(res: Any) -> str:
    if getattr(res, "success", False) and res.x is not None and np.all(np.isfinite(res.x)):
        return "optimal"
    st = int(getattr(res, "status", -1))
    if st == 2:
        return "infeasible"
    if st == 3:
        return "unbounded"
    # HiGHS may report 4 for infeasible or unbounded — treat as unbounded for tutor UX when likely
    if st == 4 and res.x is None:
        msg = str(getattr(res, "message", "")).lower()
        if "unbounded" in msg and "infeasible" not in msg:
            return "unbounded"
        if "infeasible" in msg:
            return "infeasible"
        return "not_attempted"
    return "not_attempted"


def solve_lp(mat: LinprogMatrices) -> SolveResult:
    res = linprog(
        c=mat.c,
        A_ub=mat.A_ub,
        b_ub=mat.b_ub,
        A_eq=mat.A_eq,
        b_eq=mat.b_eq,
        bounds=mat.bounds,
        method="highs",
    )
    status_map = {0: "optimal", 1: "not_attempted", 2: "infeasible", 3: "unbounded"}
    st = status_map.get(int(res.status), "not_attempted")
    x = res.x if res.success and res.x is not None else None
    fun = float(res.fun) if res.fun is not None and np.isfinite(res.fun) else None
    if mat.original_maximize and fun is not None:
        fun = -fun
    return SolveResult(status=st, fun=fun, x=x, message=str(res.message), raw=res)


def solve_mip(mat: LinprogMatrices) -> SolveResult:
    bounds = _bounds_from_mat(mat)
    constraints = _linear_constraints_from_mat(mat)
    integrality = _integrality_from_mat(mat)
    try:
        res = milp(
            c=mat.c,
            integrality=integrality,
            bounds=bounds,
            constraints=constraints,
        )
    except Exception as exc:  # noqa: BLE001
        return SolveResult(
            status="not_attempted",
            fun=None,
            x=None,
            message=f"MIP solver error: {exc}",
            error_code="MIP_SOLVER_ERROR",
            error_hint="The mixed-integer solver failed unexpectedly. Try simplifying the model or checking constraints.",
            diagnostics={"mip_backend": "scipy.milp", "exception": str(exc)},
        )

    st = _milp_status(res)
    x = res.x if st == "optimal" and res.x is not None else None
    fun = float(res.fun) if res.fun is not None and np.isfinite(res.fun) else None
    if mat.original_maximize and fun is not None:
        fun = -fun

    diagnostics: dict[str, Any] = {"mip_backend": "scipy.milp"}
    if hasattr(res, "mip_gap"):
        g = res.mip_gap
        if g is not None and np.isfinite(g):
            diagnostics["mip_gap"] = float(g)
    if hasattr(res, "mip_node_count"):
        nc = res.mip_node_count
        if nc is not None and np.isfinite(nc) and nc >= 0:
            diagnostics["mip_node_count"] = int(nc)
    if hasattr(res, "mip_dual_bound") and res.mip_dual_bound is not None and np.isfinite(res.mip_dual_bound):
        diagnostics["mip_dual_bound"] = float(res.mip_dual_bound)

    return SolveResult(
        status=st,
        fun=fun,
        x=x,
        message=str(res.message),
        raw=res,
        diagnostics=diagnostics,
    )


def solve_dispatch(mat: LinprogMatrices, *, is_mip: bool) -> SolveResult:
    """Route to LP or MIP entry points (single orchestration hook for analyze)."""
    return solve_mip(mat) if is_mip else solve_lp(mat)
