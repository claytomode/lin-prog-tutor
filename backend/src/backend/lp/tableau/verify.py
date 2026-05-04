"""Cross-check tableau walkthrough against HiGHS / SciPy solution on the same LP."""

from __future__ import annotations

import numpy as np

from backend.lp.model import LinprogMatrices
from backend.schemas import TableauStep, TableauWalkthrough


def _expanded_values_from_step(st: TableauStep) -> dict[str, float]:
    """Read basic feasible values for every tableau column label (except RHS)."""
    labels = list(st.column_labels)
    if not labels:
        raise ValueError("tableau step has no column_labels")
    T = np.asarray(st.tableau, dtype=float)
    if T.ndim != 2:
        raise ValueError("tableau must be 2-D")
    ncols = T.shape[1]
    if len(labels) != ncols:
        raise ValueError("column_labels length does not match tableau width")
    if labels[-1] != "RHS":
        raise ValueError("expected last column label to be 'RHS'")
    names = labels[:-1]
    rhs_col = ncols - 1
    vals: dict[str, float] = dict.fromkeys(names, 0.0)
    for i, bv in enumerate(st.basis_labels):
        if bv not in vals:
            raise ValueError(f"basis label {bv!r} is not a tableau column")
        vals[bv] = float(T[i, rhs_col])
    return vals


def _max_primal_violation(mat: LinprogMatrices, x: np.ndarray) -> float:
    """Non-negative amount by which x violates primal constraints / bounds (0 = feasible)."""
    worst = 0.0
    if mat.A_ub is not None and mat.b_ub is not None and mat.A_ub.size > 0:
        worst = max(worst, float(np.max(mat.A_ub @ x - mat.b_ub)))
    if mat.A_eq is not None and mat.b_eq is not None and mat.A_eq.size > 0:
        worst = max(worst, float(np.max(np.abs(mat.A_eq @ x - mat.b_eq))))
    worst = max(worst, float(np.max(-x)))
    for j, (lo, hi) in enumerate(mat.bounds):
        if lo is not None and np.isfinite(lo):
            worst = max(worst, float(lo - x[j]))
        if hi is not None and np.isfinite(hi):
            worst = max(worst, float(x[j] - hi))
    return float(worst)


def verify_tableau_against_solver(
    mat: LinprogMatrices,
    tw: TableauWalkthrough,
    solver_x: np.ndarray,
    optimal_value: float | None,
    *,
    feas_tol: float = 1e-5,
    obj_atol: float = 5e-4,
    obj_rtol: float = 1e-5,
    x_compare_atol: float = 2e-3,
) -> tuple[bool, str | None]:
    """
    Rebuild x from the final tableau BFS and compare objective + feasibility to HiGHS.

    Returns (verified_ok, message). message is None on clean match, or an explanation
    on failure; on success with a different optimal vertex, message may carry a short note.
    """
    if tw.outcome != "optimal":
        return True, None
    if not tw.steps:
        return False, "tableau walkthrough has no steps"
    if optimal_value is None or not np.isfinite(optimal_value):
        return False, "solver optimal value missing"
    if solver_x is None or solver_x.shape != (len(mat.var_names),):
        return False, "solver point shape does not match variables"

    try:
        vals = _expanded_values_from_step(tw.steps[-1])
    except (ValueError, IndexError) as exc:
        return False, f"could not read final tableau: {exc}"

    x_tab = np.array([float(vals.get(v, 0.0)) for v in mat.var_names], dtype=float)

    viol = _max_primal_violation(mat, x_tab)
    if viol > feas_tol:
        return False, (
            f"tableau BFS is not primal-feasible for the same LP as HiGHS "
            f"(max constraint/bound violation ≈ {viol:.2e})."
        )

    c_display = (-mat.c if mat.original_maximize else mat.c).astype(float)
    obj_tab = float(np.dot(c_display, x_tab))
    ref = abs(float(optimal_value))
    obj_tol = obj_atol + obj_rtol * max(1.0, ref)
    if abs(obj_tab - float(optimal_value)) > obj_tol:
        return False, (
            f"tableau objective {obj_tab:.8g} differs from HiGHS optimal value "
            f"{float(optimal_value):.8g} (tolerance ≈ {obj_tol:.2e})."
        )

    dx = float(np.max(np.abs(x_tab - solver_x)))
    if dx > x_compare_atol:
        return (
            True,
            "Tableau BFS matches HiGHS objective and feasibility within tolerance, but the "
            f"reported vertex differs from HiGHS (max |Δx| ≈ {dx:.4g}); multiple optimal solutions are possible.",
        )

    return True, None
