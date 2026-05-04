from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from backend.model import LinprogMatrices
from backend.schemas import TableauStep, TableauWalkthrough

Tol = 1e-9


@dataclass
class TableauOptions:
    tableau_mode: Literal["auto", "primal", "dual", "big_m"] = "auto"
    use_blands_rule: bool = False
    big_m_value: float | None = None


def run_tableau_max_slack(
    A_ub: np.ndarray,
    b_ub: np.ndarray,
    c_max: np.ndarray,
    var_names: list[str],
    max_steps: int = 128,
    tol: float = Tol,
    use_blands_rule: bool = False,
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
        return None, "negative RHS: use the two-phase tableau path (run_general_tableau), not slack-only primal"

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

        entering = _choose_entering_primal(row_z, tol, use_bland=use_blands_rule)
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
                if r < best_r - tol or (abs(r - best_r) <= tol and (leaving < 0 or i < leaving)):
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


def _choose_entering_primal(row_z: np.ndarray, tol: float, use_bland: bool) -> int:
    if not use_bland:
        return int(np.argmin(row_z))
    best = None
    best_val = None
    for j, v in enumerate(row_z):
        if v < -tol and (best_val is None or v < best_val - tol or (abs(v - best_val) <= tol and j < best)):
            best_val = float(v)
            best = j
    return int(best if best is not None else np.argmin(row_z))


def _choose_entering_primal_bland_min_index(row_z: np.ndarray, tol: float) -> int:
    for j, v in enumerate(row_z):
        if v < -tol:
            return j
    return int(np.argmin(row_z))


def _pivot_primal(
    T: np.ndarray,
    basis: list[str],
    col_labels: list[str],
    m: int,
    z_row: int,
    entering: int,
    leaving: int,
    tol: float,
) -> None:
    pivot = float(T[leaving, entering])
    if abs(pivot) < tol:
        raise RuntimeError("zero pivot")
    T[leaving] /= pivot
    for r in range(T.shape[0]):
        if r == leaving:
            continue
        factor = T[r, entering]
        if abs(factor) > tol:
            T[r] -= factor * T[leaving]
    basis[leaving] = col_labels[entering]


def _col_index_map(col_labels: list[str]) -> dict[str, int]:
    return {name: i for i, name in enumerate(col_labels)}


def _is_artificial_name(name: str) -> bool:
    return len(name) >= 2 and name[0] == "a" and name[1:].isdigit()


def _assemble_general_rows(mat: LinprogMatrices, tol: float) -> tuple[np.ndarray, list[str], list[str], list[int], str]:
    """Build constraint-only tableau rows (m x ncols+1) and basis names; return artificial column indices."""
    n = len(mat.var_names)
    var_names = list(mat.var_names)
    col_labels = list(var_names)
    rows_data: list[tuple[float, dict[str, float], str]] = []
    art_indices: list[int] = []
    si = ei = ai = 0

    def col_index(name: str) -> int:
        if name not in col_labels:
            col_labels.append(name)
        return col_labels.index(name)

    if mat.A_ub is not None and mat.b_ub is not None:
        for i in range(mat.A_ub.shape[0]):
            a = np.asarray(mat.A_ub[i], dtype=float)
            b = float(mat.b_ub[i])
            if b >= -tol:
                si += 1
                sname = f"s{si}"
                d: dict[str, float] = {var_names[j]: float(a[j]) for j in range(n)}
                d[sname] = 1.0
                col_index(sname)
                rows_data.append((b, d, sname))
            else:
                ei += 1
                ai += 1
                ename = f"e{ei}"
                aname = f"a{ai}"
                d = {var_names[j]: float(-a[j]) for j in range(n)}
                d[ename] = -1.0
                d[aname] = 1.0
                col_index(ename)
                j_art = col_index(aname)
                rows_data.append((-b, d, aname))
                art_indices.append(j_art)

    if mat.A_eq is not None and mat.b_eq is not None:
        for i in range(mat.A_eq.shape[0]):
            a = np.asarray(mat.A_eq[i], dtype=float)
            b = float(mat.b_eq[i])
            if b < -tol:
                a = -a
                b = -b
            ai += 1
            aname = f"a{ai}"
            d = {var_names[j]: float(a[j]) for j in range(n)}
            d[aname] = 1.0
            j_art = col_index(aname)
            rows_data.append((b, d, aname))
            art_indices.append(j_art)

    if not rows_data:
        return np.zeros((0, 0)), [], [], [], "no constraints for tableau"

    ncols = len(col_labels)
    m = len(rows_data)
    T = np.zeros((m, ncols + 1), dtype=float)
    basis: list[str] = []
    for i, (rhs, d, bv) in enumerate(rows_data):
        for name, val in d.items():
            T[i, col_labels.index(name)] = val
        T[i, -1] = rhs
        basis.append(bv)
    return T, col_labels, basis, art_indices, "ok"


def _artificial_value(T: np.ndarray, basis: list[str], art_idx: set[int], col_of: dict[str, int], tol: float) -> float:
    s = 0.0
    for i, bv in enumerate(basis):
        if bv in col_of and col_of[bv] in art_idx:
            s += max(0.0, float(T[i, -1]))
    return s


def _pivot_out_basic_artificials(
    T: np.ndarray,
    col_labels: list[str],
    basis: list[str],
    m: int,
    z_row: int,
    art_col_indices: set[int],
    tol: float,
) -> None:
    ncols = T.shape[1] - 1
    for _ in range(m * ncols + 2):
        progressed = False
        for i in range(m):
            if not _is_artificial_name(basis[i]):
                continue
            for j in range(ncols):
                if j in art_col_indices:
                    continue
                if abs(T[i, j]) <= tol:
                    continue
                _pivot_primal(T, basis, col_labels, m, z_row, j, i, tol)
                progressed = True
                break
            if progressed:
                break
        if not progressed:
            break


def _drop_nonbasic_columns(
    T_body: np.ndarray,
    col_labels: list[str],
    basis: list[str],
    drop_js: list[int],
) -> tuple[np.ndarray, list[str], list[str]]:
    drop_set = set(drop_js)
    keep = [j for j in range(T_body.shape[1] - 1) if j not in drop_set]
    rhs = T_body[:, -1:]
    core = T_body[:, keep]
    T2 = np.hstack([core, rhs])
    labels2 = [col_labels[j] for j in keep]
    return T2, labels2, list(basis)


def _primal_simplex_loop(
    T: np.ndarray,
    col_labels: list[str],
    basis: list[str],
    z_row: int,
    m: int,
    steps: list[TableauStep],
    phase_tag: str,
    max_steps: int,
    tol: float,
    use_bland: bool,
    allow_degenerate_pivot: bool,
) -> tuple[Literal["optimal", "unbounded", "max_iterations", "degenerate"], str | None]:
    col_of = _col_index_map(col_labels)

    def snap(narrative: str, entering: int | None, leaving: int | None, ratios: list[float | None] | None) -> None:
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

    for _ in range(max_steps):
        row_z = T[z_row, :-1]
        if np.all(row_z >= -tol):
            snap(f"{phase_tag}Optimality: z-row coefficients are all ≥ 0.", None, None, None)
            return "optimal", None

        if use_bland:
            entering = _choose_entering_primal_bland_min_index(row_z, tol)
        else:
            entering = int(np.argmin(row_z))
        col = np.array([T[i, entering] if i < m else 0.0 for i in range(m)], dtype=float)
        pos = col > tol
        if not np.any(pos):
            snap(f"{phase_tag}Unbounded along column {col_labels[entering]}.", entering, None, None)
            return "unbounded", None

        ratios: list[float | None] = []
        best_r = np.inf
        leaving = -1
        for i in range(m):
            if col[i] > tol:
                r = float(T[i, -1] / col[i])
                ratios.append(r)
                better = r < best_r - tol
                tie = abs(r - best_r) <= tol and leaving >= 0 and i < leaving
                if better or tie:
                    best_r = r
                    leaving = i
            else:
                ratios.append(None)

        if leaving < 0:
            snap(f"{phase_tag}Ratio test failed (degenerate).", entering, None, ratios)
            return "max_iterations", None

        pivot = float(T[leaving, entering])
        if abs(pivot) < tol:
            if allow_degenerate_pivot and use_bland:
                snap(f"{phase_tag}Near-zero pivot; continuing with Bland’s rule.", entering, leaving, ratios)
                continue
            snap(f"{phase_tag}Zero pivot (degenerate).", entering, leaving, ratios)
            return "degenerate", "degenerate pivot"

        snap(
            f"{phase_tag}Enter {col_labels[entering]}, leave row {leaving + 1} (min ratio).",
            entering,
            leaving,
            ratios,
        )
        _pivot_primal(T, basis, col_labels, m, z_row, entering, leaving, tol)

    snap(f"{phase_tag}Stopped after maximum iterations.", None, None, None)
    return "max_iterations", None


def _build_phase2_z_row(
    T: np.ndarray,
    col_labels: list[str],
    basis: list[str],
    m: int,
    c_max: np.ndarray,
    n_struct: int,
    tol: float,
) -> np.ndarray:
    ncols = T.shape[1] - 1
    z2 = np.zeros(ncols + 1, dtype=float)
    for j in range(min(n_struct, ncols)):
        z2[j] = -float(c_max[j])
    col_of = _col_index_map(col_labels)
    for i in range(m):
        k = col_of[basis[i]]
        coeff = z2[k]
        if abs(coeff) > tol:
            z2 -= coeff * T[i, :]
    return z2


def _dual_simplex_loop(
    T: np.ndarray,
    col_labels: list[str],
    basis: list[str],
    z_row: int,
    m: int,
    steps: list[TableauStep],
    tag: str,
    max_steps: int,
    tol: float,
    use_bland: bool,
) -> tuple[Literal["optimal", "unbounded", "max_iterations"], str | None]:
    col_of = _col_index_map(col_labels)

    def snap(narrative: str, entering: int | None, leaving: int | None, ratios: list[float | None] | None) -> None:
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

    for _ in range(max_steps):
        row_z = T[z_row, :-1]
        if not np.all(row_z >= -tol):
            snap(f"{tag}Dual simplex requires a dual-feasible z-row; switching to primal.", None, None, None)
            return "max_iterations", "not dual feasible"

        leaving = -1
        for i in range(m):
            if T[i, -1] < -tol:
                if leaving < 0 or T[i, -1] < T[leaving, -1] - tol or (
                    abs(T[i, -1] - T[leaving, -1]) <= tol and (not use_bland or i < leaving)
                ):
                    leaving = i
        if leaving < 0:
            snap(f"{tag}Primal feasibility restored (all RHS ≥ 0).", None, None, None)
            return "optimal", None

        row_idx = leaving
        ratios: list[float | None] = []
        best_ratio = np.inf
        entering = -1
        for j in range(T.shape[1] - 1):
            ar = T[row_idx, j]
            zc = T[z_row, j]
            if ar >= -tol:
                ratios.append(None)
                continue
            if zc <= tol:
                ratios.append(None)
                continue
            r = zc / (-ar)
            ratios.append(float(r))
            if r < best_ratio - tol or (abs(r - best_ratio) <= tol and (entering < 0 or j < entering)):
                best_ratio = r
                entering = j

        if entering < 0:
            snap(f"{tag}Dual unbounded (primal infeasible).", None, row_idx, ratios)
            return "unbounded", None

        snap(
            f"{tag}Dual pivot: leave row {row_idx + 1} (negative RHS), enter {col_labels[entering]} (dual ratio test).",
            entering,
            row_idx,
            ratios,
        )
        _pivot_primal(T, basis, col_labels, m, z_row, entering, row_idx, tol)

    snap(f"{tag}Dual simplex stopped after max iterations.", None, None, None)
    return "max_iterations", None


def run_general_tableau(
    mat: LinprogMatrices,
    options: TableauOptions,
    max_steps: int = 256,
    tol: float = Tol,
) -> tuple[TableauWalkthrough | None, str | None]:
    n = len(mat.var_names)
    c_max = -np.asarray(mat.c, dtype=float)
    sense_label: Literal["maximize", "minimize"] = "maximize" if mat.original_maximize else "minimize"
    narrative0 = (
        "Primal simplex tableau (maximize form for the displayed objective row). "
        if mat.original_maximize
        else "Tableau uses the equivalent maximization problem max (−c)ᵀx with the same optimal x as your minimization. "
    )

    simple = (
        (mat.A_eq is None or mat.A_eq.size == 0)
        and mat.A_ub is not None
        and mat.b_ub is not None
        and np.all(mat.b_ub >= -tol)
        and options.tableau_mode in ("auto", "primal")
    )
    if simple and options.tableau_mode not in ("dual", "big_m"):
        tw, err = run_tableau_max_slack(
            mat.A_ub,
            mat.b_ub,
            c_max,
            mat.var_names,
            max_steps=max_steps,
            tol=tol,
            use_blands_rule=options.use_blands_rule,
        )
        if tw is not None:
            tw = tw.model_copy(update={"sense_for_tableau": sense_label})
        return tw, err

    T0, col_labels, basis, art_list, msg = _assemble_general_rows(mat, tol)
    if msg != "ok":
        return None, msg
    m, ncols = T0.shape[0], T0.shape[1] - 1
    art_set = set(art_list)
    col_of = _col_index_map(col_labels)

    steps: list[TableauStep] = []
    if options.tableau_mode == "big_m":
        M = options.big_m_value
        if M is None:
            M = 10_000.0 * (1.0 + float(np.max(np.abs(c_max))) if c_max.size else 1.0)
        T = np.zeros((m + 1, ncols + 1), dtype=float)
        T[:m, :] = T0
        T[m, :n] = -c_max
        for j in art_set:
            T[m, j] -= M
        for i in range(m):
            if _is_artificial_name(basis[i]):
                T[m, :] -= T[i, :]
        steps.append(
            TableauStep(
                index=0,
                tableau=np.round(T, 10).tolist(),
                column_labels=col_labels + ["RHS"],
                basis_labels=list(basis),
                entering_col=None,
                leaving_row=None,
                ratios=None,
                narrative=f"[Big-M] Initial tableau with M={M:g} penalizing artificial variables in the objective row.",
            )
        )
        st, err = _primal_simplex_loop(
            T,
            col_labels,
            basis,
            m,
            m,
            steps,
            "[Big-M] ",
            max_steps,
            tol,
            options.use_blands_rule,
            allow_degenerate_pivot=True,
        )
        if st == "degenerate":
            return None, err or "degenerate"
        out = "optimal" if st == "optimal" else ("unbounded" if st == "unbounded" else "max_iterations")
        return (
            TableauWalkthrough(
                sense_for_tableau=sense_label,
                initial_narrative=narrative0 + "Single-phase big-M simplex.",
                steps=steps,
                outcome=out,  # type: ignore[arg-type]
            ),
            None,
        )

    # Two-phase path
    T = np.zeros((m + 1, ncols + 1), dtype=float)
    T[:m, :] = T0
    z1 = np.zeros(ncols + 1, dtype=float)
    for j in art_set:
        z1[j] = -1.0
    for i in range(m):
        if _is_artificial_name(basis[i]):
            z1 += T[i, :]
    T[m, :] = z1

    steps.append(
        TableauStep(
            index=0,
            tableau=np.round(T, 10).tolist(),
            column_labels=col_labels + ["RHS"],
            basis_labels=list(basis),
            entering_col=None,
            leaving_row=None,
            ratios=None,
            narrative="[Phase I] Auxiliary objective: maximize −(sum of artificial variables); row initialized to clear artificials from the w-row.",
        )
    )

    st1, err1 = _primal_simplex_loop(
        T,
        col_labels,
        basis,
        m,
        m,
        steps,
        "[Phase I] ",
        max_steps,
        tol,
        options.use_blands_rule,
        allow_degenerate_pivot=options.use_blands_rule,
    )
    if st1 == "degenerate":
        return None, err1 or "degenerate"
    wval = _artificial_value(T, basis, art_set, col_of, tol)
    if wval > 1e-5:
        steps.append(
            TableauStep(
                index=len(steps),
                tableau=np.round(T, 10).tolist(),
                column_labels=col_labels + ["RHS"],
                basis_labels=list(basis),
                entering_col=None,
                leaving_row=None,
                ratios=None,
                narrative="[Phase I] Optimum: artificial variables sum to a positive value — the LP has no feasible solution.",
            )
        )
        return (
            TableauWalkthrough(
                sense_for_tableau=sense_label,
                initial_narrative=narrative0 + "Two-phase simplex (Phase I detected infeasibility).",
                steps=steps,
                outcome="infeasible",
            ),
            None,
        )

    _pivot_out_basic_artificials(T, col_labels, basis, m, m, art_set, tol)
    droplist = sorted([j for j in art_set if all(basis[i] != col_labels[j] for i in range(m))])
    T_body = T[:m, :]
    T_drop, labels2, basis2 = _drop_nonbasic_columns(T_body, col_labels, basis, droplist)
    m2 = T_drop.shape[0]
    z2 = _build_phase2_z_row(T_drop, labels2, basis2, m2, c_max, n, tol)
    T2 = np.vstack([T_drop, z2.reshape(1, -1)])

    steps.append(
        TableauStep(
            index=len(steps),
            tableau=np.round(T2, 10).tolist(),
            column_labels=labels2 + ["RHS"],
            basis_labels=list(basis2),
            entering_col=None,
            leaving_row=None,
            ratios=None,
            narrative="[Phase II] Artificial columns removed; original objective row expressed in the current basis.",
        )
    )

    phase2_narrative = narrative0 + "Two-phase primal simplex."
    if options.tableau_mode == "dual":
        dst, dmsg = _dual_simplex_loop(
            T2, labels2, basis2, m2, m2, steps, "[Dual] ", max_steps, tol, options.use_blands_rule
        )
        if dst == "unbounded":
            return (
                TableauWalkthrough(
                    sense_for_tableau=sense_label,
                    initial_narrative=narrative0 + "Dual simplex indicates primal infeasibility on this starting basis.",
                    steps=steps,
                    outcome="infeasible",
                ),
                None,
            )
        if dst == "optimal":
            return (
                TableauWalkthrough(
                    sense_for_tableau=sense_label,
                    initial_narrative=narrative0 + "Two-phase method with dual simplex on the Phase-II starting basis.",
                    steps=steps,
                    outcome="optimal",
                ),
                None,
            )
        if dst == "max_iterations" and dmsg != "not dual feasible":
            return (
                TableauWalkthrough(
                    sense_for_tableau=sense_label,
                    initial_narrative=narrative0 + "Dual simplex stopped before full convergence.",
                    steps=steps,
                    outcome="max_iterations",
                ),
                None,
            )
        # not dual feasible: continue with primal on the same tableau
        phase2_narrative = narrative0 + "Two-phase method (dual not initially feasible on this basis; primal Phase II)."

    st2, err2 = _primal_simplex_loop(
        T2,
        labels2,
        basis2,
        m2,
        m2,
        steps,
        "[Phase II] ",
        max_steps,
        tol,
        options.use_blands_rule,
        allow_degenerate_pivot=options.use_blands_rule,
    )
    if st2 == "degenerate":
        return None, err2 or "degenerate"
    out = "optimal" if st2 == "optimal" else ("unbounded" if st2 == "unbounded" else "max_iterations")
    return (
        TableauWalkthrough(
            sense_for_tableau=sense_label,
            initial_narrative=phase2_narrative,
            steps=steps,
            outcome=out,  # type: ignore[arg-type]
        ),
        None,
    )


def build_tableau_if_supported(mat: LinprogMatrices, options: TableauOptions | None = None) -> tuple[TableauWalkthrough | None, str]:
    opts = options or TableauOptions()
    has_ub = mat.A_ub is not None and mat.b_ub is not None and mat.A_ub.size > 0
    has_eq = mat.A_eq is not None and mat.b_eq is not None and mat.A_eq.size > 0
    if not has_ub and not has_eq:
        return None, "no constraints for tableau"
    tw, err = run_general_tableau(mat, opts)
    if tw is None:
        return None, err or "tableau failed"
    return tw, "ok"
