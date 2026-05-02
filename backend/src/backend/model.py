from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import linprog

from backend.parser import ParsedLP, RawConstraint


@dataclass
class LinprogMatrices:
    var_names: list[str]
    c: np.ndarray  # minimize sense (length n)
    A_ub: np.ndarray | None
    b_ub: np.ndarray | None
    A_eq: np.ndarray | None
    b_eq: np.ndarray | None
    bounds: list[tuple[float | None, float | None]]
    original_maximize: bool


def _collect_vars(parsed: ParsedLP) -> list[str]:
    names: set[str] = set(parsed.objective.keys())
    for rc in parsed.constraints:
        names.update(rc.coeffs.keys())
    return sorted(names)


def build_matrices(parsed: ParsedLP) -> LinprogMatrices:
    var_names = _collect_vars(parsed)
    if not var_names:
        raise ValueError("no variables")
    n = len(var_names)
    idx = {v: i for i, v in enumerate(var_names)}

    rows_ub: list[np.ndarray] = []
    rhs_ub: list[float] = []
    rows_eq: list[np.ndarray] = []
    rhs_eq: list[float] = []

    for rc in parsed.constraints:
        row = np.zeros(n, dtype=float)
        for v, c in rc.coeffs.items():
            row[idx[v]] = c
        if rc.sense == "<=":
            rows_ub.append(row)
            rhs_ub.append(float(rc.rhs))
        elif rc.sense == "=":
            rows_eq.append(row)
            rhs_eq.append(float(rc.rhs))
        else:
            raise ValueError(f"unsupported sense {rc.sense!r}")

    c_obj = np.array([float(parsed.objective.get(v, 0.0)) for v in var_names], dtype=float)
    original_maximize = parsed.objective_sense == "maximize"
    c_min = -c_obj if original_maximize else c_obj

    A_ub = np.vstack(rows_ub) if rows_ub else None
    b_ub = np.array(rhs_ub, dtype=float) if rhs_ub else None
    A_eq = np.vstack(rows_eq) if rows_eq else None
    b_eq = np.array(rhs_eq, dtype=float) if rhs_eq else None

    bounds = [(0.0, None)] * n

    return LinprogMatrices(
        var_names=var_names,
        c=c_min,
        A_ub=A_ub,
        b_ub=b_ub,
        A_eq=A_eq,
        b_eq=b_eq,
        bounds=bounds,
        original_maximize=original_maximize,
    )


@dataclass
class SolveResult:
    status: str
    fun: float | None
    x: np.ndarray | None
    message: str
    raw: Any


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


def point_dict(mat: LinprogMatrices, x: np.ndarray) -> dict[str, float]:
    return {v: float(x[i]) for i, v in enumerate(mat.var_names)}
