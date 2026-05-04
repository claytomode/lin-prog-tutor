"""Toric ideal Gröbner basis normal form for nonnegative equality ILP (pedagogical trace)."""

from __future__ import annotations

import numpy as np
from sympy import expand, groebner, latex, symbols
from sympy.polys.polytools import Poly

from backend.schemas import GrobnerStep, GrobnerWalkthrough


MAX_ROWS_COLS = 14
MAX_SUM_B = 96


def _trim(s: str, limit: int = 420) -> str:
    s = str(s)
    return s if len(s) <= limit else s[: limit - 3] + "..."


def _nf_to_w_point(
    remainder,
    w_syms: tuple,
    names: list[str],
) -> dict[str, int] | None:
    """If remainder is a monomial ∏ w_j^{x_j} with coeff 1, return name -> exponent."""
    r = expand(remainder)
    if r == 0:
        return {names[j]: 0 for j in range(len(names))}
    try:
        p = Poly(r, *w_syms)
    except (ValueError, TypeError):
        return None
    monoms = p.monoms()
    coeffs = p.coeffs()
    if len(monoms) != 1:
        return None
    if abs(float(coeffs[0]) - 1.0) > 1e-8:
        return None
    monom = monoms[0]
    out: dict[str, int] = {}
    for j, exp in enumerate(monom):
        out[names[j]] = int(exp)
    return out


def compute_grobner_walkthrough(
    A: np.ndarray,
    b: np.ndarray,
    c_minimize: np.ndarray,
    names: list[str],
    scipy_point: dict[str, float] | None,
    *,
    model_notes: list[str] | None = None,
) -> GrobnerWalkthrough:
    """Compute Gröbner basis of toric encoding and normal form of z^b (pedagogical trace)."""
    notes_prefix = list(model_notes or [])
    m, n = A.shape
    if c_minimize.shape != (n,):
        return GrobnerWalkthrough(
            initial_narrative="Internal error: objective length does not match column count.",
            steps=[],
            outcome="computation_failed",
        )
    if m + n > MAX_ROWS_COLS:
        return GrobnerWalkthrough(
            initial_narrative=(
                "Gröbner IP mode is limited to small dimensions for interactive use "
                f"(m+n ≤ {MAX_ROWS_COLS})."
            ),
            steps=[],
            outcome="unsupported_model",
        )

    if int(np.sum(b)) > MAX_SUM_B:
        return GrobnerWalkthrough(
            initial_narrative=(
                f"Sum of RHS entries Σ b_i must be ≤ {MAX_SUM_B} for the demo Gröbner path "
                "(prevents enormous monomial z^b)."
            ),
            steps=[],
            outcome="unsupported_model",
        )

    steps: list[GrobnerStep] = []

    steps.append(
        GrobnerStep(
            index=0,
            title="Problem (nonnegative equality form)",
            detail=(
                "Work with minimize $c^{\\mathsf T} x$ subject to $Ax = b$ and "
                r"$x \in \mathbb{Z}_{\ge 0}^n$, with $A \in \mathbb{Z}_{\ge 0}^{m \times n}$ and "
                r"$b \in \mathbb{Z}_{\ge 0}^m$ (after any slack reformulation performed earlier)."
            ),
        )
    )

    if m == 1:
        z_syms = (symbols("z1", real=True),)
    else:
        z_syms = symbols(" ".join(f"z{i}" for i in range(1, m + 1)), real=True)
    if n == 1:
        w_syms = (symbols("w1", real=True),)
    else:
        w_syms = symbols(" ".join(f"w{i}" for i in range(1, n + 1)), real=True)

    order_w = sorted(range(n), key=lambda j: (-int(c_minimize[j]), j))
    all_syms = tuple(z_syms) + tuple(w_syms[j] for j in order_w)
    w_order_labels = ", ".join(names[j] for j in order_w)

    steps.append(
        GrobnerStep(
            index=len(steps),
            title="Polynomial ring and toric generators",
            detail=(
                "Let $R = \\mathbb{Q}[" + ", ".join(latex(s) for s in all_syms) + "]$. "
                r"For column $j$, set $f_j = \prod_i z_i^{A_{ij}}$ and consider the ideal "
                r"$\langle f_1 - w_1,\ldots,f_n - w_n\rangle$. "
                "We use pure **lex** with $z_1,\\ldots,z_m$ first, then $w$-variables in **descending** "
                "minimize-$c$ order on the corresponding decision columns "
                f"(here: `{w_order_labels}`) so the Gröbner normal form tracks the objective."
            ),
        )
    )

    gens: list = []
    fj_lines: list[str] = []
    for j in range(n):
        prod = 1
        for i in range(m):
            prod *= z_syms[i] ** int(A[i, j])
        gens.append(prod - w_syms[j])
        fj_lines.append(
            _trim(
                rf"$f_{{{j + 1}}} - w_{{{j + 1}}}$ with $f_{{{j + 1}}} = {latex(prod)}$ "
                rf"(column ${latex(w_syms[j])}$ ↔ decision variable `{names[j]}`)."
            )
        )

    detail_gens = "\n\n".join(f"- {ln}" for ln in fj_lines[: min(8, len(fj_lines))])
    if len(fj_lines) > 8:
        detail_gens += "\n\n*(Further generators omitted.)*"
    steps.append(
        GrobnerStep(
            index=len(steps),
            title=r"Ideal generators $f_j - w_j$",
            detail=detail_gens,
        )
    )

    target = 1
    for i in range(m):
        target *= z_syms[i] ** int(b[i])

    steps.append(
        GrobnerStep(
            index=len(steps),
            title=r"Right-hand side monomial $z^b$",
            detail=_trim(
                rf"Form $z^b = \prod_i z_i^{{b_i}} = {latex(target)}$. "
                r"The normal form $\mathrm{NF}(z^b)$ modulo a Gröbner basis encodes feasibility / "
                "a candidate solution."
            ),
        )
    )

    try:
        gb = groebner(gens, *all_syms, order="lex")
    except Exception as exc:  # noqa: BLE001
        return GrobnerWalkthrough(
            initial_narrative="Could not compute a Gröbner basis for this instance.",
            steps=steps
            + [
                GrobnerStep(
                    index=len(steps),
                    title="Gröbner basis computation failed",
                    detail=str(exc),
                )
            ],
            outcome="computation_failed",
            grobner_basis_strs=[],
            remainder_str=None,
            point_from_normal_form=None,
            agrees_with_scipy_mip=None,
        )

    gb_polys = list(gb)[:12]
    gb_strs = [_trim(latex(p)) for p in gb_polys]
    steps.append(
        GrobnerStep(
            index=len(steps),
            title="Gröbner basis (truncated listing)",
            detail="\n\n".join(f"- $\\displaystyle {s}$" for s in gb_strs[:8])
            + ("\n\n*(Further basis elements omitted.)*" if len(gb_polys) > 8 else ""),
        )
    )

    try:
        _, rem = gb.reduce(target)
    except Exception as exc:  # noqa: BLE001
        return GrobnerWalkthrough(
            initial_narrative="Gröbner basis computed; normal-form reduction failed.",
            steps=steps
            + [
                GrobnerStep(
                    index=len(steps),
                    title="Normal-form reduction error",
                    detail=str(exc),
                )
            ],
            outcome="computation_failed",
            grobner_basis_strs=gb_strs,
            remainder_str=None,
            point_from_normal_form=None,
            agrees_with_scipy_mip=None,
        )

    rem_s = _trim(latex(expand(rem)), limit=200)
    steps.append(
        GrobnerStep(
            index=len(steps),
            title=r"Normal form of $z^b$ modulo $\mathcal{G}$",
            detail=rf"$\mathrm{{NF}}(z^b) = {rem_s}$",
        )
    )

    z_set = set(z_syms)
    if rem.free_symbols & z_set:
        steps.append(
            GrobnerStep(
                index=len(steps),
                title="Feasibility signal",
                detail=(
                    r"The normal form still involves some $z_i$. In this encoding, a feasible nonnegative "
                    r"integer solution corresponds to $\mathrm{NF}$ involving only $w_1,\ldots,w_n$ "
                    "(a monomial in the $w$-variables)."
                ),
            )
        )
        return GrobnerWalkthrough(
            initial_narrative=("Gröbner / normal-form trace (infeasible or degenerate signal). " + " ".join(notes_prefix)),
            steps=steps,
            outcome="infeasible_normal_form",
            grobner_basis_strs=gb_strs,
            remainder_str=rem_s,
            point_from_normal_form=None,
            agrees_with_scipy_mip=None,
            optimality_note=(
                r"Even with $c$-ordered $w$-generators, $\mathrm{NF}$ can still involve $z_i$ if the model "
                "is infeasible or degeneracies break the toric normal-form recipe."
            ),
        )

    pt = _nf_to_w_point(rem, tuple(w_syms), names)
    if pt is None:
        steps.append(
            GrobnerStep(
                index=len(steps),
                title="Could not read exponent vector",
                detail=(
                    r"Expected $\mathrm{NF}$ to be a single monomial $\prod_j w_j^{x_j}$; "
                    "this remainder does not have that form."
                ),
            )
        )
        return GrobnerWalkthrough(
            initial_narrative="Gröbner trace computed; remainder format was unexpected.",
            steps=steps,
            outcome="computation_failed",
            grobner_basis_strs=gb_strs,
            remainder_str=rem_s,
            point_from_normal_form=None,
            agrees_with_scipy_mip=None,
        )

    agrees: bool | None = None
    if scipy_point is not None:
        compared_any = False
        agrees = True
        for name, xv in pt.items():
            if name.startswith("_"):
                continue
            if name not in scipy_point:
                continue
            compared_any = True
            if abs(float(scipy_point[name]) - float(xv)) > 5e-3:
                agrees = False
                break
        if not compared_any:
            agrees = None

    pt_decision = {k: int(pt[k]) for k in names if not k.startswith("_")}
    steps.append(
        GrobnerStep(
            index=len(steps),
            title="Exponent vector (candidate solution)",
            detail=(
                r"Identify $x_j$ as the exponent on $w_j$ so $\mathrm{NF} = \prod_j w_j^{x_j}$. "
                f"Integer vector (decision variables only): `{pt_decision}` "
                "(slack columns are still listed in the JSON below when present)."
            ),
        )
    )

    return GrobnerWalkthrough(
        initial_narrative=("Gröbner / normal-form trace for a nonnegative equality integer program. " + " ".join(notes_prefix)),
        steps=steps,
        outcome="ok",
        grobner_basis_strs=gb_strs,
        remainder_str=rem_s,
        point_from_normal_form={k: int(v) for k, v in pt.items()},
        agrees_with_scipy_mip=agrees,
        optimality_note=(
            "SciPy MILP uses branch-and-cut on the original formulation. "
            r"Here **lex** uses a $z$-block then a $w$-block permuted by descending minimize-$c$ on each "
            "column, which often aligns the normal form with the minimize-$c$ objective on small nonnegative "
            r"equality instances, but $\mathrm{NF}$ and SciPy can still disagree on degenerate cases."
        ),
    )
