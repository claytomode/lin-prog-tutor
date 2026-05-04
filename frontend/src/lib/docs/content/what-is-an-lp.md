# What is a linear program?

Linear programming (LP) is optimization over linear relationships.

You use LP when:

- decisions can be fractional (continuous variables),
- objective is linear in decision variables,
- constraints are linear equalities/inequalities.

Typical story: allocate limited resources (time, money, labor, machine hours) to activities to maximize profit or minimize cost.

## Learning objectives

After this chapter, you should be able to:

- write an LP in formal matrix form,
- identify decision variables, objective, and constraints from a story,
- explain feasible region, infeasible, and unbounded outcomes.

## Formal definition

One common form (maximization) is:

$$
\begin{aligned}
\max \quad & c^\top x \\
\text{s.t.}\quad & Ax \le b,\\
& x \ge 0.
\end{aligned}
$$

where:

- $x \in \mathbb{R}^n$ are decision variables,
- $c \in \mathbb{R}^n$ are objective coefficients,
- $A \in \mathbb{R}^{m \times n}$ and $b \in \mathbb{R}^m$ encode constraints.

The feasible set

$$
\mathcal{F} = \{x \in \mathbb{R}^n_{\ge 0}: Ax \le b\}
$$

is a convex polyhedron. In LP, optimal solutions (when they exist) occur at extreme points (corners) of this set.

## Story problem: bakery planning

A bakery makes two products each morning:

- $x$ = trays of croissants,
- $y$ = trays of muffins.

Profit per tray: croissant $=\$30$, muffin $=\$20$.

Resource limits:

- oven time: $2x + y \le 100$,
- prep labor: $x + 2y \le 80$,
- nonnegativity: $x, y \ge 0$.

Model:

$$
\begin{aligned}
\max\quad & 30x + 20y\\
\text{s.t.}\quad & 2x + y \le 100\\
& x + 2y \le 80\\
& x, y \ge 0.
\end{aligned}
$$

This is a complete LP: variable definitions, objective, constraints, and domain.

## Worked mini-example

Suppose constraints are:

$$
x + y \le 4,\quad x \ge 0,\quad y \ge 0
$$

and objective is:

$$
\max\ 3x + 2y.
$$

Candidate corner points are $(0,0)$, $(4,0)$, $(0,4)$.

Objective values:

- $(0,0)\to 0$,
- $(4,0)\to 12$,
- $(0,4)\to 8$.

So optimum is at $(x^\star,y^\star)=(4,0)$ with value $12$.

## Possible solver outcomes

- **Optimal:** feasible solution with best objective found.
- **Infeasible:** no point satisfies all constraints.
- **Unbounded:** objective can improve without limit while staying feasible.

## Why LP is foundational

- Many real planning problems are naturally linear or well-approximated as linear.
- LP scales to large models with modern solvers.
- LP is the starting point for MILP/IP via relaxation and decomposition ideas.

## Try this in Solver

- Open bakery model directly: [Load bakery LP in Solver](/?example=bakery_lp)
- Open mini corner demo: [Load corner-point demo](/?example=lp_corner_demo)

Copy/paste version:

```text
maximize 30 x + 20 y
subject to
2 x + y <= 100
x + 2 y <= 80
x >= 0
y >= 0
```
