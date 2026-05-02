from __future__ import annotations

import numpy as np

from backend.model import LinprogMatrices
from backend.schemas import TableauStep, TableauWalkthrough


def run_tableau_max_slack(
    A_ub: np.ndarray,
    b_ub: np.ndarray,
    c_max: np.ndarray,
    var_names: list[str],
    max_steps: int = 128,
    tol: float = 1e-9,
) -> tuple[TableauWalkthrough | None, str | None]:
    """
    Primal simplex for maximize with Ax <= b, x >= 0, slack s >= 0, b >= 0.
    Tableau rows 0..m-1: Ax + Is = b; row m: z - c^T x = 0 => coeffs -c under x.
    """
    if A_ub.ndim != 2:
        return None, "invalid A_ub"
    m, n = A_ub.shape
    if b_ub.shape != (m,) or c_max.shape != (n,):
        return None, "shape mismatch"
    if np.any(b_ub < -1e-10):
        return None, "negative RHS requires Phase I (not implemented)"

    slack_names = [f"s{i + 1}" for i in range(m)]
    col_labels = list(var_names) + slack_names

    T = np.zeros((m + 1, n + m + 1), dtype=float)
    T[:m, :n] = A_ub
    T[:m, n : n + m] = np.eye(m)
    T[:m, -1] = b_ub
    T[m, :n] = -np.asarray(c_max, dtype=float)

    basis = slack_names.copy()
    steps: list[TableauStep] = []

    def snapshot(narrative: str, entering: int | None, leaving: int | None, ratios: list[float | None] | None) -> None:
        steps.append(
            TableauStep(
                index=len(steps),
                tableau=np.round(T, 10).tolist(),
                column_labels=col_labels + ["RHS"],
                basis_labels=list(basis),
                entering_col=entering,
                leaving_row=leaving,
                ratios=ratios,
                narrative=narrative,
            )
        )

    snapshot("Initial tableau: slack variables form a starting feasible basis.", None, None, None)

    for _ in range(max_steps):
        row_z = T[m, :-1]
        if np.all(row_z >= -tol):
            snapshot("Optimality: all coefficients in the z-row are ≥ 0.", None, None, None)
            return (
                TableauWalkthrough(
                    sense_for_tableau="maximize",
                    initial_narrative="Primal simplex on slack form (maximize).",
                    steps=steps,
                    outcome="optimal",
                ),
                None,
            )

        entering = int(np.argmin(row_z))
        col = T[:m, entering]
        pos = col > tol
        if not np.any(pos):
            snapshot("Unbounded: entering column has no positive entries in constraint rows.", entering, None, None)
            return (
                TableauWalkthrough(
                    sense_for_tableau="maximize",
                    initial_narrative="Primal simplex on slack form (maximize).",
                    steps=steps,
                    outcome="unbounded",
                ),
                None,
            )

        ratios: list[float | None] = []
        best_r = np.inf
        leaving = -1
        for i in range(m):
            if col[i] > tol:
                r = float(T[i, -1] / col[i])
                ratios.append(r)
                if r < best_r - tol:
                    best_r = r
                    leaving = i
            else:
                ratios.append(None)

        if leaving < 0:
            snapshot("Could not choose a leaving row (degeneracy).", entering, None, ratios)
            return (
                TableauWalkthrough(
                    sense_for_tableau="maximize",
                    initial_narrative="Primal simplex on slack form (maximize).",
                    steps=steps,
                    outcome="max_iterations",
                ),
                None,
            )

        pivot = float(T[leaving, entering])
        if abs(pivot) < tol:
            snapshot("Zero pivot (degenerate).", entering, leaving, ratios)
            return None, "degenerate pivot"

        snapshot(
            f"Enter {col_labels[entering]} (most negative z-row coefficient). "
            f"Minimum ratio test chooses leaving basic variable in row {leaving + 1}.",
            entering,
            leaving,
            ratios,
        )

        T[leaving] /= pivot
        for r in range(m + 1):
            if r == leaving:
                continue
            factor = T[r, entering]
            if abs(factor) > tol:
                T[r] -= factor * T[leaving]
        basis[leaving] = col_labels[entering]

    snapshot("Stopped after maximum iterations.", None, None, None)
    return (
        TableauWalkthrough(
            sense_for_tableau="maximize",
            initial_narrative="Primal simplex on slack form (maximize).",
            steps=steps,
            outcome="max_iterations",
        ),
        None,
    )


def build_tableau_if_supported(mat: LinprogMatrices) -> tuple[TableauWalkthrough | None, str]:
    if mat.A_eq is not None and mat.A_eq.size > 0:
        return None, "equality constraints require two-phase tableau (not implemented yet)"
    if mat.A_ub is None or mat.b_ub is None:
        return None, "no inequality rows for slack tableau"
    # mat.c is scipy minimize objective; maximizing (-mat.c)^T x matches the same LP.
    c_max = -np.asarray(mat.c, dtype=float)
    tw, err = run_tableau_max_slack(mat.A_ub, mat.b_ub, c_max, mat.var_names)
    if tw is None:
        return None, err or "tableau failed"
    return tw, "ok"
