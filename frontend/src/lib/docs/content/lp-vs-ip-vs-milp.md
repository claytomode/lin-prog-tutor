# LP vs IP vs MILP

Most linear optimization models share the same objective/constraint structure. The major difference is **variable domain**.

## Formal comparison

### LP (Linear Program)

$$
\max \ c^\top x \quad \text{s.t. } Ax \le b,\ x \in \mathbb{R}^n_{\ge 0}
$$

- all variables continuous.

### IP (Integer Program)

$$
\max \ c^\top x \quad \text{s.t. } Ax \le b,\ x \in \mathbb{Z}^n_{\ge 0}
$$

- all variables integer.

### MILP (Mixed-Integer Linear Program)

$$
\max \ c^\top x + d^\top y \quad \text{s.t. } A x + B y \le b,\ x \in \mathbb{R}^p,\ y \in \mathbb{Z}^q
$$

- mix of continuous and integer/binary variables.

## Why integrality changes difficulty

LP feasible sets are convex polyhedra. IP/MILP feasible sets are discrete points (or slices containing discrete coordinates), so search becomes combinatorial.

Even when constraints are linear, integer restrictions can make problems much harder.

## Story problem: warehouse opening

A company may open up to two candidate warehouses:

- binary variables $y_1,y_2 \in \{0,1\}$ (open or not),
- shipment variables $x_{ij}\ge 0$ (continuous flow from warehouse $i$ to region $j$).

If opening warehouse $i$ costs $f_i$, and shipping cost is $c_{ij}$:

$$
\min \sum_i f_i y_i + \sum_{i,j} c_{ij}x_{ij}
$$

with demand and capacity constraints, including linking constraints:

$$
\sum_j x_{ij} \le \text{cap}_i \, y_i.
$$

This is MILP because it mixes binary and continuous decisions.

## Quick modeling cues

- Use **LP** when fractional decisions are acceptable.
- Use **IP** when all decisions are counts/yes-no.
- Use **MILP** when only some decisions are discrete.

## LP relaxation connection

Given an IP/MILP, the LP relaxation replaces integer/binary domains by continuous ones:

$$
y \in \{0,1\} \ \rightarrow\ 0 \le y \le 1,\qquad
z \in \mathbb{Z} \ \rightarrow\ z \in \mathbb{R}.
$$

This relaxed LP gives valuable bounds and sensitivity insight before full integer search.

## Try this in Solver

- LP baseline: [Load LP corner demo](/?example=lp_corner_demo)
- MILP story model: [Load warehouse MILP draft](/?example=warehouse_milp)

Copy/paste MILP draft:

```text
minimize 18 x11 + 22 x12 + 20 x21 + 16 x22 + 70 y1 + 60 y2
subject to
x11 + x21 >= 8
x12 + x22 >= 6
x11 + x12 <= 12 y1
x21 + x22 <= 10 y2
x11 >= 0
x12 >= 0
x21 >= 0
x22 >= 0
variables:
y1 binary
y2 binary
```
