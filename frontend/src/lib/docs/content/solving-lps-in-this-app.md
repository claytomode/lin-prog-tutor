# Solving linear programs in this app

This chapter connects the pieces you see on the **Solver** page: parsing your model, the numerical solver, the feasible-set sketch (when dimension allows), the graphical tutor (2D/3D), and the simplex **tableau** walkthrough for continuous LPs.

## Learning objectives

After this chapter, you should be able to:

- read the model text format this app accepts and know where domains and options go,
- explain which visualizations are available for 1D, 2D, 3D, and higher dimensions,
- use **error codes** and hints to fix a model quickly (see also the [error code glossary](/docs/error-code-glossary)).

## Prerequisites

- [What is an LP?](/docs/what-is-an-lp) (objective, constraints, feasible set)
- Optional: [Primal and dual](/docs/primal-and-dual) for shadow-price intuition when you are ready

## Key terms

- **DSL** — the small text language for `maximize` / `minimize`, `subject to`, and constraints.
- **Tableau** — a pedagogical primal (or dual) simplex view for **continuous** LPs.
- **HiGHS** — the open-source interior-point / simplex backend used for continuous models here.

## The workflow

1. **Write the model** in the source box: objective line, `subject to`, then one constraint per line, then nonnegativity (or use defaults).
2. **Choose options** (tableau mode, Bland’s rule, optional Big M) in the details section if you are teaching the tableau path.
3. **Analyze** sends the text to the API, which parses, builds matrices, and calls the solver.
4. **Results** show status, objective value, and a point (when optimal). For two variables you get a 2D feasible polygon and constraint lines; for three, a 3D polyhedron sketch when available. For **more than three** variables, the region is not drawn (the problem still solves in full dimension).
5. **Tutor and tableau** apply to **continuous** LPs only. Mixed-integer models are still solved numerically (HiGHS MILP via SciPy), but the tableau and 2D/3D vertex tutors stay disabled because they teach continuous simplex geometry—see [Intro to integer optimization](/docs/intro-to-integer-optimization).

## Try it (deep links)

Open the solver with a prefilled example (query parameters):

- [Classic 2D corner solution](/?example=lp_corner_demo) — `lp_corner_demo`
- [Bakery-style product mix](/?example=bakery_lp) — `bakery_lp`
- [Primal form used in the dual chapter](/?example=primal_dual_primal) — `primal_dual_primal`

You can also pass raw text with `?source=` (URL-encoded), or set variable domains in the model panel after a first successful run.

## How options map to the engine

- **Tableau mode** only affects the **pedagogical** tableau construction, not HiGHS. The tableau is cross-checked against the continuous optimum when possible.
- **Strict inequalities** (`<`, `>`) are relaxed with a tiny epsilon to obtain a closed feasible set; a modeling note is emitted—see [modeling pitfalls](/docs/modeling-pitfalls).

## Common pitfalls (preview)

- Missing `subject to`, typos in comparators, or nonlinear fragments (`*`, `/`) → structured parse errors with line hints.
- Declaring **integer/binary** variables → MILP class; the backend solves with HiGHS MILP. Rare failures surface as `MIP_SOLVER_ERROR` (see [Error code glossary](/docs/error-code-glossary)).

For a full list of stable codes, see [Error code glossary](/docs/error-code-glossary).
