# Modeling pitfalls and strict inequalities

Small formulation mistakes cause confusing solver outcomes. This chapter collects the ones this app surfaces explicitly—often with a **stable error code** or a **modeling note** in the API response.

## Learning objectives

- understand why strict inequalities need relaxation in digital solvers,
- avoid duplicate or conflicting variable-domain declarations,
- recognize when integer domains trigger MILP handling versus pure LP.

## Prerequisites

- [What is an LP?](/docs/what-is-an-lp)
- [Solving LPs in this app](/docs/solving-lps-in-this-app)

## Key terms

- **Closed feasible set** — includes its boundary; standard LP solvers expect weak inequalities after preprocessing.
- **Epsilon relaxation** — replacing `<` or `>` by `≤` or `≥` with a tiny offset.
- **Variable domain** — `continuous`, `integer`, or `binary` for each decision variable.

## Strict inequalities (`<`, `>`)

In mathematics you might write \(x < 3\). Practical LP software almost always works with **closed** halfspaces. This app rewrites strict inequalities using a small \(\varepsilon\) (see modeling notes in the response):

- \(x < 3\) becomes \(x \leq 3 - \varepsilon\)
- \(x > 1\) becomes \(-x \leq -1 - \varepsilon\) in the internal \(\leq\) form

The optimum value may land \(\varepsilon\) away from the informal strict boundary—that is expected.

## Variable domains

You can declare domains in the source:

```text
variables:
x integer
y binary
```

Or use inline syntax such as `variables x: integer, y continuous`.

Rules enforced by the parser:

- **One declaration per variable** — duplicate conflicting lines raise `DUPLICATE_VARIABLE_DOMAIN`.
- **Known domains only** — typos like `integerish` raise `UNKNOWN_VARIABLE_DOMAIN`.
- You may also set domains from the **Solver UI** after a successful analyze; client-supplied domains **override** embedded declarations for that request.

## MILP expectations

If any variable is `integer` or `binary`, the model class becomes MILP. Continuous relaxation geometry (polygon or polyhedron sketches) describes the **LP relaxation**, not the discrete feasible set; the solver still returns an integer-feasible optimum when one exists. See [Intro to integer optimization](/docs/intro-to-integer-optimization).

## Further navigation

- Stable machine-readable errors: [Error code glossary](/docs/error-code-glossary)
- LP vs IP vs MILP concepts: [LP vs IP vs MILP](/docs/lp-vs-ip-vs-milp)
