from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import linprog

from backend.model import LinprogMatrices


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
    # HiGHS / linprog: 0 optimal, 2 infeasible, 3 unbounded (see scipy.optimize.OptimizeResult)
    status_map = {0: "optimal", 1: "not_attempted", 2: "infeasible", 3: "unbounded"}
    st = status_map.get(int(res.status), "not_attempted")
    x = res.x if res.success and res.x is not None else None
    fun = float(res.fun) if res.fun is not None and np.isfinite(res.fun) else None
    if mat.original_maximize and fun is not None:
        fun = -fun
    return SolveResult(status=st, fun=fun, x=x, message=str(res.message), raw=res)


def solve_mip(_mat: LinprogMatrices) -> SolveResult:
    return SolveResult(
        status="not_attempted",
        fun=None,
        x=None,
        message="MIP solver integration is not implemented yet.",
        error_code="MIP_NOT_IMPLEMENTED",
        error_hint="This model contains integer/binary variables, but MIP solving is not wired yet.",
        diagnostics={"mip_backend": "stub", "reason": "integration_pending"},
    )
