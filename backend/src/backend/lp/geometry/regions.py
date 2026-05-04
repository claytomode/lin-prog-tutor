from __future__ import annotations

from typing import Any

import numpy as np
from scipy.optimize import linprog
from scipy.spatial import ConvexHull, HalfspaceIntersection


def _unique_points(points: np.ndarray, tol: float = 1e-7) -> np.ndarray:
    if points.size == 0:
        return points.reshape(0, 2)
    out: list[np.ndarray] = []
    for p in points:
        if not any(np.linalg.norm(p - q) < tol for q in out):
            out.append(p)
    return np.vstack(out) if out else np.zeros((0, 2))


def vertices_2d_halfspaces(A: np.ndarray, b: np.ndarray, tol: float = 1e-9) -> np.ndarray:
    """Vertices of {x in R^2 : A x <= b} from intersection of active pairs of lines."""
    m, n = A.shape
    if n != 2:
        raise ValueError("vertices_2d expects m x 2")
    verts: list[np.ndarray] = []
    for i in range(m):
        for j in range(i + 1, m):
            M = np.stack([A[i], A[j]], axis=0)
            if abs(np.linalg.det(M)) < 1e-12:
                continue
            rhs = np.array([b[i], b[j]], dtype=float)
            try:
                p = np.linalg.solve(M, rhs)
            except np.linalg.LinAlgError:
                continue
            if np.all(A @ p <= b + tol):
                verts.append(p)
    if not verts:
        return np.zeros((0, 2))
    pts = np.vstack(verts)
    return _unique_points(pts, tol=1e-6)


def order_polygon_ccw(pts: np.ndarray) -> np.ndarray:
    if pts.shape[0] <= 1:
        return pts
    if pts.shape[0] == 2:
        return pts
    hull = ConvexHull(pts)
    return pts[hull.vertices]


def feasible_interval_1d(A: np.ndarray, b: np.ndarray) -> tuple[float | None, float | None]:
    """For single variable x with rows a*x <= b, return (lo, hi) on feasible segment."""
    lo = -np.inf
    hi = np.inf
    for ai, bi in zip(A.ravel(), b):
        if abs(ai) < 1e-15:
            if bi < -1e-12:
                return None, None
            continue
        bound = bi / ai
        if ai > 0:
            hi = min(hi, bound)
        else:
            lo = max(lo, bound)
    if lo > hi + 1e-9:
        return None, None
    return float(lo) if np.isfinite(lo) else None, float(hi) if np.isfinite(hi) else None


def _min_slack(A: np.ndarray, b: np.ndarray, x: np.ndarray) -> float:
    return float(np.min(b - A @ np.asarray(x, dtype=float).reshape(-1)))


def strict_interior_point_3d(
    A: np.ndarray,
    b: np.ndarray,
    hint: np.ndarray | None = None,
    qhull_clear: float = 1e-5,
) -> np.ndarray | None:
    """
    A point x with A @ x < b (strictly) on every row — required by Qhull HalfspaceIntersection.

    HiGHS can return a **degenerate** optimum of the max-min-slack LP that still lies on a
    facet of the *original* polyhedron, so Qhull rejects it (distance 0). We therefore prefer
    a plain feasibility LP on a slightly tightened rhs ``b - margin``, which forces a
    uniform slack margin, then fall back to the Chebyshev LP only if we can **verify** slack.
    """
    m, n = A.shape
    if n != 3:
        return None
    A = np.asarray(A, dtype=float)
    b = np.asarray(b, dtype=float)
    scale = max(1.0, float(np.linalg.norm(b, ord=np.inf)))

    c0 = np.zeros(n, dtype=float)
    bounds_free = [(None, None)] * n
    # Largest margin first: more clearance for qhull numerics.
    for mag in (1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-7, 1e-8):
        margin = float(max(mag * scale, 1e-12))
        res = linprog(c0, A_ub=A, b_ub=b - margin, bounds=bounds_free, method="highs")
        if not res.success or res.x is None:
            continue
        x = np.asarray(res.x[:n], dtype=float)
        if _min_slack(A, b, x) > qhull_clear:
            return x

    # Maximize minimum slack t with A x + t 1 <= b; require verified slack on original b.
    c = np.zeros(n + 1, dtype=float)
    c[-1] = -1.0
    A_lp = np.hstack([A, np.ones((m, 1), dtype=float)])
    bounds = [(None, None)] * n + [(0.0, None)]
    res = linprog(c, A_ub=A_lp, b_ub=b, bounds=bounds, method="highs")
    if res.success and res.x is not None and float(res.x[-1]) > 1e-12:
        x = np.asarray(res.x[:n], dtype=float)
        if _min_slack(A, b, x) > qhull_clear:
            return x

    if hint is not None:
        h = np.asarray(hint, dtype=float).reshape(3)
        if _min_slack(A, b, h) > qhull_clear:
            return h
    return None


def geometry_3d_vertices(
    A_ub: np.ndarray,
    b_ub: np.ndarray,
    interior_hint: np.ndarray | None = None,
) -> tuple[np.ndarray | None, str | None]:
    """
    Vertices of {x in R^3 : A_ub x <= b_ub} via scipy HalfspaceIntersection + ConvexHull.

    interior_hint (e.g. LP optimum) is only a fallback; Qhull needs a strictly interior
    point, which we obtain by LP unless the polyhedron has empty interior in R^3.
    """
    if A_ub.shape[1] != 3:
        return None, "expected 3 variables for 3D geometry"
    m = A_ub.shape[0]
    interior = strict_interior_point_3d(A_ub, b_ub, hint=interior_hint)
    if interior is None:
        return None, (
            "no strictly interior point in R^3 (feasible region may be lower-dimensional "
            "or unbounded in a way that prevents an interior witness); 3D hull skipped."
        )
    hs = np.hstack([A_ub, (-b_ub).reshape(-1, 1)])
    try:
        hi = HalfspaceIntersection(hs, interior, incremental=False)
    except Exception as exc:  # noqa: BLE001
        return None, f"3D halfspace intersection failed: {exc}"
    pts = hi.intersections
    if pts.size == 0:
        return None, "empty 3D intersection"
    hull = ConvexHull(pts)
    return pts[hull.vertices], None
