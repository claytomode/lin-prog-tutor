# Intro to integer optimization

Integer optimization handles decisions that cannot be fractional: yes/no, counts, assignments, selections.

## A quick story: campaign selection

A team can fund projects A, B, C with binary decisions:

$$
y_A, y_B, y_C \in \{0,1\}
$$

maximize impact:

$$
\max\ 8y_A + 7y_B + 6y_C
$$

subject to budget:

$$
5y_A + 4y_B + 3y_C \le 7.
$$

If variables were continuous, you could pick fractions of projects, which is not physically meaningful.

## LP relaxation

Given an IP/MILP:

$$
x \in \mathbb{Z}^n,\ y \in \{0,1\}^k
$$

the LP relaxation replaces domains with:

$$
x \in \mathbb{R}^n,\ 0 \le y \le 1.
$$

For a maximization model, relaxation value is an **upper bound** on integer optimum.
For a minimization model, it is a **lower bound**.

## Mini numerical bound example

Relax:

$$
\max\ 5x_1 + 4x_2,\quad
x_1 + x_2 \le 1,\quad
0 \le x_1,x_2 \le 1.
$$

LP optimum is $x_1=1,x_2=0$ (value $5$), which is already integer.

Now add a coupling constraint:

$$
2x_1 + 2x_2 \le 3,\quad x_1,x_2 \in \{0,1\}.
$$

LP relaxation allows $(1,0.5)$ value $7$, but integer feasible points give max $5$.
So LP bound is optimistic, and branch-and-bound must close that gap.

## Branch-and-bound (concept)

At each node:

1. Solve LP relaxation.
2. If LP infeasible: prune node.
3. If LP solution integer-feasible: update incumbent (best known feasible integer).
4. Else branch on fractional variable $x_i=v$:
   $$
   x_i \le \lfloor v \rfloor \quad \text{and} \quad x_i \ge \lceil v \rceil.
   $$
5. Prune any node whose bound cannot beat current incumbent.

Progress metric (maximization):

$$
\text{gap} = \frac{\text{bestBound} - \text{incumbent}}{|\text{incumbent}|+\epsilon}.
$$

## What production solvers really do

Modern MILP solvers are usually **branch-and-cut**:

- branch-and-bound tree search,
- cutting planes to tighten LP relaxations,
- primal heuristics to find good feasible solutions fast.

In this app's first integer phase, we teach LP relaxation + B&B intuition while keeping solver internals abstracted.

## Try this in Solver

- LP baseline for comparison: [Load LP corner demo](/?example=lp_corner_demo)
- Binary campaign model: [Load campaign binary model](/?example=campaign_binary)

Copy/paste campaign model:

```text
maximize 8 y_a + 7 y_b + 6 y_c
subject to
5 y_a + 4 y_b + 3 y_c <= 7
variables:
y_a binary
y_b binary
y_c binary
```

For how variable domains and strict inequalities interact with the API, see [Modeling pitfalls](/docs/modeling-pitfalls) and the [Error code glossary](/docs/error-code-glossary).

Integer and mixed-integer models in the **Solver** are handled by the API using `scipy.optimize.milp` (HiGHS as the underlying MILP engine). You should get a discrete optimum when the model is feasible and bounded. If the solver reports an internal failure, the UI shows a `MIP_SOLVER_ERROR` hint.
