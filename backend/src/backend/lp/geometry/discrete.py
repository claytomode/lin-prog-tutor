"""Enumerate discrete-feasible points in 2D for MILP visualization (LP relaxation + lattice dots)."""

from __future__ import annotations

import numpy as np

from backend.lp.model import LinprogMatrices
from backend.lp.parsing import VarDomain

# Guardrail so huge domains don't freeze the API.
_MAX_AXIS_RANGE = 96


def _halfspace_feasible(p: np.ndarray, A: np.ndarray, b: np.ndarray, tol: float = 1e-7) -> bool:
    if A.size == 0:
        return True
    return bool(np.all(A @ p - b <= tol))


def _axis_candidates(
    domain: VarDomain,
    lo: float | None,
    hi: float | None,
    gmin: float,
    gmax: float,
) -> list[float]:
    """Candidate coordinate values for one axis given domain and relaxation bbox."""
    if domain == "binary":
        out: list[float] = []
        for v in (0.0, 1.0):
            if lo is not None and v < lo - 1e-9:
                continue
            if hi is not None and v > hi + 1e-9:
                continue
            out.append(v)
        return out

    gmin_i = int(np.ceil(max(gmin, lo if lo is not None else gmin)))
    gmax_i = int(np.floor(min(gmax, hi if hi is not None else gmax)))
    if gmax_i < gmin_i:
        return []
    span = gmax_i - gmin_i
    if span > _MAX_AXIS_RANGE:
        gmax_i = gmin_i + _MAX_AXIS_RANGE
    return [float(k) for k in range(gmin_i, gmax_i + 1)]


def discrete_feasible_points_2d(
    mat: LinprogMatrices,
    A_all: np.ndarray,
    b_all: np.ndarray,
    verts_ccw: np.ndarray,
) -> list[tuple[float, float]]:
    """
    List all (x,y) that satisfy stacked inequalities Ax<=b and integrality on both axes.

    If either variable is continuous, returns [] (no finite lattice).
    Uses the polygon bbox (from relaxation vertices) to limit integer scans.
    """
    if len(mat.var_names) != 2:
        return []
    v0, v1 = mat.var_names[0], mat.var_names[1]
    d0, d1 = mat.var_domains[v0], mat.var_domains[v1]
    if d0 == "continuous" or d1 == "continuous":
        return []

    if verts_ccw.shape[0] > 0:
        xs = verts_ccw[:, 0]
        ys = verts_ccw[:, 1]
        pad = 2.0
        xmin, xmax = float(np.min(xs)) - pad, float(np.max(xs)) + pad
        ymin, ymax = float(np.min(ys)) - pad, float(np.max(ys)) + pad
    else:
        xmin, xmax, ymin, ymax = -1.0, 20.0, -1.0, 20.0

    lo0, hi0 = mat.bounds[0]
    lo1, hi1 = mat.bounds[1]

    xv = _axis_candidates(d0, lo0, hi0, xmin, xmax)
    yv = _axis_candidates(d1, lo1, hi1, ymin, ymax)
    if not xv or not yv:
        return []

    out: list[tuple[float, float]] = []
    for x in xv:
        for y in yv:
            p = np.array([x, y], dtype=float)
            if _halfspace_feasible(p, A_all, b_all):
                out.append((x, y))

    out.sort(key=lambda t: (t[0], t[1]))
    return out
