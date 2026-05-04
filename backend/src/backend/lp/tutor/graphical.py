from __future__ import annotations

import numpy as np

from backend.lp.model import LinprogMatrices
from backend.lp.solver import SolveResult
from backend.schemas import TutorStep


def _objective_vector_original(mat: LinprogMatrices) -> np.ndarray:
    """Coefficients in original problem sense (maximize vector if maximize)."""
    base = -mat.c if mat.original_maximize else mat.c
    return np.array(base, dtype=float)


def build_graphical_tutor(
    mat: LinprogMatrices,
    solve: SolveResult,
    vertices_xy: np.ndarray,
) -> list[TutorStep]:
    """2D graphical method: vertices + objective values + optimum highlight."""
    steps: list[TutorStep] = []
    c_orig = _objective_vector_original(mat)

    steps.append(
        TutorStep(
            id="g0",
            title="Feasible region",
            detail="The shaded polygon is the intersection of all half-spaces from your linear constraints (including explicit bounds).",
            highlight_vertex_index=None,
        )
    )

    if vertices_xy.shape[0] == 0:
        steps.append(
            TutorStep(
                id="g_empty",
                title="Vertices",
                detail="No feasible corner points were found in the plane (likely infeasible in 2D, or numerical degeneracy).",
                highlight_vertex_index=None,
            )
        )
        return steps

    ordered = vertices_xy
    vals: list[float] = []
    for k, p in enumerate(ordered):
        z = float(np.dot(c_orig[:2], p))
        vals.append(z)
        steps.append(
            TutorStep(
                id=f"g_vertex_{k + 1}",
                title=f"Vertex {k + 1}",
                detail=f"At ({p[0]:.4g}, {p[1]:.4g}), objective = {z:.4g}.",
                highlight_vertex_index=k,
            )
        )

    if solve.status != "optimal" or solve.x is None:
        steps.append(
            TutorStep(
                id="g_end",
                title="Solver status",
                detail=f"The LP is not optimal in the solver sense ({solve.status}). Compare vertex values above.",
                highlight_vertex_index=None,
            )
        )
        return steps

    x = solve.x
    if len(mat.var_names) < 2:
        return steps
    i0, i1 = 0, 1
    p_star = np.array([x[i0], x[i1]], dtype=float)
    best_k = min(
        range(len(ordered)),
        key=lambda k: float(np.linalg.norm(ordered[k] - p_star)),
    )
    sense_word = "maximum" if mat.original_maximize else "minimum"
    steps.append(
        TutorStep(
            id="g_opt",
            title="Optimal corner",
            detail=f"The solver reports an optimal {sense_word} at ({p_star[0]:.4g}, {p_star[1]:.4g}), matching vertex {best_k + 1} up to tolerance.",
            highlight_vertex_index=best_k,
        )
    )
    return steps


def build_3d_vertex_tutor(
    mat: LinprogMatrices,
    solve: SolveResult,
    vertices_xyz: np.ndarray,
) -> list[TutorStep]:
    """Corner-style narration on polyhedron vertices (3D), analogous to the 2D graphical tutor."""
    steps: list[TutorStep] = []
    c_orig = _objective_vector_original(mat)

    steps.append(
        TutorStep(
            id="t3_0",
            title="Feasible polyhedron",
            detail="Each vertex below is an extreme point of the feasible set in 3D; the objective is linear on this polyhedron.",
            highlight_vertex_index=None,
        )
    )

    if vertices_xyz.ndim != 2 or vertices_xyz.shape[1] != 3:
        return steps

    for k, p in enumerate(vertices_xyz):
        z = float(np.dot(c_orig, p))
        steps.append(
            TutorStep(
                id=f"t3_v{k + 1}",
                title=f"Vertex {k + 1}",
                detail=f"At ({p[0]:.4g}, {p[1]:.4g}, {p[2]:.4g}), objective = {z:.4g}.",
                highlight_vertex_index=k,
            )
        )

    if solve.status != "optimal" or solve.x is None:
        steps.append(
            TutorStep(
                id="t3_end",
                title="Solver status",
                detail=f"The LP is not optimal in the solver sense ({solve.status}). Compare vertex values above.",
                highlight_vertex_index=None,
            )
        )
        return steps

    x = solve.x
    p_star = np.array([float(x[i]) for i in range(min(3, len(x)))], dtype=float)
    best_k = min(
        range(vertices_xyz.shape[0]),
        key=lambda k: float(np.linalg.norm(vertices_xyz[k] - p_star)),
    )
    sense_word = "maximum" if mat.original_maximize else "minimum"
    steps.append(
        TutorStep(
            id="t3_opt",
            title="Optimal corner",
            detail=f"The solver reports an optimal {sense_word} near vertex {best_k + 1} (closest extreme point in Euclidean distance).",
            highlight_vertex_index=best_k,
        )
    )
    return steps
