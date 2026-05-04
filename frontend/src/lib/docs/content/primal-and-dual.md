# Primal and dual

Every LP has an associated dual LP. The primal asks for activity levels; the dual asks for consistent resource prices.

## Canonical pair

Primal:

$$
\begin{aligned}
\max\quad & c^\top x\\
\text{s.t.}\quad & Ax \le b\\
& x \ge 0
\end{aligned}
$$

Dual:

$$
\begin{aligned}
\min\quad & b^\top y\\
\text{s.t.}\quad & A^\top y \ge c\\
& y \ge 0
\end{aligned}
$$

If primal has $m$ constraints and $n$ variables, then dual has $m$ variables and $n$ constraints.

## Economic interpretation

- $x_j$: level of activity $j$ (e.g., units produced).
- $y_i$: shadow price of resource $i$ (marginal value of one more unit of resource).

Constraint $A^\top y \ge c$ means: under prices $y$, every activity must cost at least its profit coefficient, otherwise arbitrage would exist.

## Worked numeric example

Primal:

$$
\begin{aligned}
\max\quad & 3x_1 + 2x_2\\
\text{s.t.}\quad & x_1 + x_2 \le 4\\
& x_1 \le 2\\
& x_1,x_2 \ge 0
\end{aligned}
$$

Dual (with $y_1,y_2 \ge 0$):

$$
\begin{aligned}
\min\quad & 4y_1 + 2y_2\\
\text{s.t.}\quad & y_1 + y_2 \ge 3\\
& y_1 \ge 2\\
& y_1,y_2 \ge 0
\end{aligned}
$$

One primal optimum is $(x_1,x_2)=(2,2)$ with value $10$.
One dual optimum is $(y_1,y_2)=(2,1)$ with value $4\cdot2 + 2\cdot1 = 10$.

Matching values illustrate strong duality.

## Core theorems to remember

- **Weak duality:** for any primal-feasible $x$ and dual-feasible $y$,
  $$
  c^\top x \le b^\top y.
  $$
- **Strong duality:** if both problems are feasible and bounded, optimal values are equal.
- **Complementary slackness:** at optimality,
  $$
  y_i(b_i-a_i^\top x)=0,\qquad x_j((A^\top y)_j-c_j)=0.
  $$

Interpretation: either a primal constraint is tight, or its dual price is zero; either a primal variable is positive, or its dual reduced-cost inequality is tight.

## Story problem intuition

Suppose you run a small factory with limited labor and machine time.

- Primal picks production quantities.
- Dual assigns an internal value to labor and machine minutes.

If machine time becomes scarce, its dual price rises. That directly explains why certain products become less attractive unless their margin is high enough.

## Try this in Solver

- Load primal example: [Open primal example model](/?example=primal_dual_primal)

Copy/paste primal example:

```text
maximize 3 x1 + 2 x2
subject to
x1 + x2 <= 4
x1 <= 2
x1 >= 0
x2 >= 0
```

Tip: after solving, compare active constraints against dual-price intuition from this chapter.
