"""Build nonnegative equality standard form for the toric / Gröbner encoding."""

from __future__ import annotations

import numpy as np

from backend.lp.model.matrices import LinprogMatrices
from backend.lp.parsing import ParsedLP


def _near_int(x: float, *, tol: float = 1e-6) -> int | None:
    r = round(float(x))
    if abs(x - r) <= tol:
        return int(r)
    return None


def build_nonneg_equality_ilp(
    mat: LinprogMatrices,
    _parsed: ParsedLP,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str], list[str]]:
    """
    Augment to Ax = b with x >= 0 integer, A,b entrywise nonnegative integers.

    Returns:
        A_int (m x n'), b_int (m), c_int (n') in minimize sense,
        full variable names (original + slacks),
        list of human-readable modeling notes (slack rows, etc.).

    Raises ValueError with a short reason if this encoding is not supported.
    """
    notes: list[str] = []
    for v, dom in mat.var_domains.items():
        if dom == "binary":
            raise ValueError("Gröbner IP encoding does not support binary variables in this version.")
        if dom == "continuous":
            raise ValueError("Gröbner IP encoding requires all variables to be integer.")

    n0 = len(mat.var_names)
    names = list(mat.var_names)

    rows: list[np.ndarray] = []
    rhs: list[float] = []

    # Equality rows (may need slack if RHS negative — reject for now).
    if mat.A_eq is not None and mat.b_eq is not None and mat.A_eq.size:
        for i in range(mat.A_eq.shape[0]):
            rows.append(np.asarray(mat.A_eq[i], dtype=float))
            rhs.append(float(mat.b_eq[i]))

    # <= rows become equalities with nonnegative slack columns.
    if mat.A_ub is not None and mat.b_ub is not None and mat.A_ub.size:
        n_cur = n0
        slack_counter = 0
        for i in range(mat.A_ub.shape[0]):
            slack = f"_slack{slack_counter}"
            slack_counter += 1
            row = np.zeros(n_cur + 1, dtype=float)
            row[:n_cur] = mat.A_ub[i]
            row[n_cur] = 1.0
            # Extend all existing rows with a new zero column.
            rows = [np.concatenate([r, np.zeros(1)]) for r in rows]
            rows.append(row)
            rhs.append(float(mat.b_ub[i]))
            names.append(slack)
            n_cur += 1
            notes.append(f"Introduced slack variable {slack} to rewrite a ≤ row as an equality.")

    # Explicit upper bounds x_j <= hi as rows x_j + s = hi when hi is finite.
    ub_slack_counter = 0
    for j, (_lo, hi) in enumerate(mat.bounds):
        if hi is not None and hi < 1e100:
            slack = f"_ubslack{ub_slack_counter}"
            ub_slack_counter += 1
            n_cur = len(names)
            row = np.zeros(n_cur + 1, dtype=float)
            row[j] = 1.0
            row[n_cur] = 1.0
            rows = [np.concatenate([r, np.zeros(1)]) for r in rows]
            rows.append(row)
            rhs.append(float(hi))
            names.append(slack)
            notes.append(f"Introduced slack variable {slack} for upper bound on {mat.var_names[j]}.")

    if not rows:
        raise ValueError("Need at least one constraint to form an equality-constrained IP.")

    A = np.vstack(rows)
    b = np.asarray(rhs, dtype=float)
    m, n = A.shape

    # Objective on extended variables: original costs + zero on slacks.
    c_ext = np.zeros(n, dtype=float)
    for j, name in enumerate(mat.var_names):
        if name in names:
            idx = names.index(name)
            c_ext[idx] = float(mat.c[j])

    # Integer + nonnegativity checks.
    A_int = np.zeros_like(A, dtype=int)
    for i in range(m):
        for j in range(n):
            v = _near_int(A[i, j])
            if v is None:
                raise ValueError("Gröbner encoding requires integer coefficients in A.")
            if v < 0:
                raise ValueError(
                    "Gröbner encoding needs entrywise nonnegative A; "
                    "rewrite constraints so coefficients and RHS are nonnegative integers."
                )
            A_int[i, j] = v

    b_int = np.zeros(m, dtype=int)
    for i in range(m):
        v = _near_int(b[i])
        if v is None:
            raise ValueError("Gröbner encoding requires integer RHS values.")
        if v < 0:
            raise ValueError("Gröbner encoding requires nonnegative RHS after reformulation.")
        b_int[i] = v

    c_int = np.zeros(n, dtype=int)
    for j in range(n):
        v = _near_int(c_ext[j])
        if v is None:
            raise ValueError("Gröbner encoding requires integer objective coefficients.")
        c_int[j] = v

    if np.any(A_int < 0) or np.any(b_int < 0):
        raise ValueError("Internal error: nonnegative matrix expected.")

    return A_int, b_int, c_int, names, notes
