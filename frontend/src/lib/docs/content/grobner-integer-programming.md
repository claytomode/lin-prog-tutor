# Gröbner bases and integer programming (background)

When you choose the **Gröbner normal-form** option for a small **all-integer** MILP, the app builds a short **algebraic walkthrough**: it encodes a nonnegative **equality** form \(Ax = b\), \(x \in \mathbb{Z}_{\ge 0}^n\) using **monomials** in extra variables, computes a **Gröbner basis**, and reads a candidate solution from the **normal form** of a right-hand-side monomial \(z^b\). The UI still uses **SciPy HiGHS MILP** for the reported optimum; the trace is mainly for **pedagogy**.

Related in-app chapters: [Solving LPs in this app](/docs/solving-lps-in-this-app), [Intro to integer optimization](/docs/intro-to-integer-optimization).

---

## From linear equalities to a polynomial ideal

Assume (after reformulation) integer data with \(A \in \mathbb{Z}_{\ge 0}^{m \times n}\), \(b \in \mathbb{Z}_{\ge 0}^m\), and unknowns \(x \in \mathbb{Z}_{\ge 0}^n\) satisfying \(Ax = b\).

Introduce fresh variables \(z_1,\ldots,z_m\) and \(w_1,\ldots,w_n\). For each column \(j\), define the monomial

$$
f_j \;=\; \prod_{i=1}^m z_i^{A_{ij}} \;\in\; \mathbb{Q}[z_1,\ldots,z_m].
$$

Column \(j\) of \(A\) supplies the exponents of \(f_j\); the **binomial** \(f_j - w_j\) packages that column: the auxiliary variable \(w_j\) “tags” the monomial \(f_j\) so that rewriting modulo the ideal encodes balancing the \(z\)-exponents across constraints. Let

$$
I \;=\; \langle f_1 - w_1,\,\ldots,\,f_n - w_n\rangle \;\subset\; R \;=\; \mathbb{Q}[z_1,\ldots,z_m,w_1,\ldots,w_n].
$$

Feasible nonnegative integer solutions of \(Ax = b\) correspond (in this encoding) to certain **monomials** in the \(w\)-variables that appear when the right-hand side monomial \(z^b = \prod_i z_i^{b_i}\) is rewritten modulo \(I\) using the rules encoded in a Gröbner basis.

---

## Monomial order

The app fixes a **pure lexicographic** order on monomials in \(R\): all \(z\)-variables are compared first (in index order), then the \(w\)-variables. The \(w\)-block is **permuted** so that generators are listed in **descending** order of the minimize-\(c\) objective coefficients on the corresponding decision columns. That heuristic tries to align the normal form with the **minimum** of \(c^{\mathsf T}x\) in small nonnegative equality instances; it is not a guarantee for every model.

Every nonzero polynomial in \(R\) has a well-defined **leading monomial** \(\mathrm{LM}(g)\) under this order.

---

## Gröbner bases and “polynomial long division” in many variables

Fix an ideal \(I \subset R\) and a monomial order.

A finite set \(\mathcal{G} \subset I\) is a **Gröbner basis** for \(I\) when the leading monomials of \(\mathcal{G}\) generate the **leading monomial ideal** of \(I\): every leading monomial of an element of \(I\) is divisible by \(\mathrm{LM}(g)\) for some \(g \in \mathcal{G}\).

**Normal form / reduction.** Given \(f \in R\) and a Gröbner basis \(\mathcal{G}\), you **reduce** \(f\) by repeatedly doing the same thing as one step of **long division**:

1. Look at the current remainder \(r\) (initially \(r = f\)).
2. If some term \(t\) of \(r\) is divisible by \(\mathrm{LM}(g)\) for some \(g \in \mathcal{G}\), subtract an appropriate polynomial multiple of \(g\) so that term \(t\) **cancels** or becomes smaller in the monomial order.
3. Stop when **no** term of \(r\) is divisible by any \(\mathrm{LM}(g)\).

The final \(r\) is the **normal form** \(\mathrm{NF}(f)\) (or \(\mathrm{NF}(f,\mathcal{G})\)). For a Gröbner basis, this remainder is **canonical**: it is unique, and \(f - \mathrm{NF}(f) \in I\). So \(\mathrm{NF}(f)\) is the “fully simplified” representative of \(f\) modulo \(I\).

Intuition: in one variable, dividing by a set of polynomials reduces to familiar division with remainder. In several variables, **leading terms** play the role of “highest degree,” and a Gröbner basis is exactly the hypothesis that makes that greedy cancellation process **confluent**—you cannot get stuck in two different incomparable remainders.

In this app, **SymPy** computes a Gröbner basis of the toric generators and then **reduces** the monomial \(z^b\) against it (`groebner` + `reduce`). That reduction is the concrete implementation of the division / normal-form loop above.

---

## What you should read off \(\mathrm{NF}(z^b)\)

- If \(\mathrm{NF}(z^b)\) is a **single monomial** \(\prod_j w_j^{x_j}\) with coefficient \(1\), the exponents \((x_j)\) give a candidate **integer** point (matching the encoding’s intent for feasible instances).
- If \(\mathrm{NF}(z^b)\) still involves some \(z_i\), the trace treats that as a **feasibility / degeneracy** signal for the normal-form recipe (the UI explains this in context).

---

## Practical caveats in this app

- The walkthrough is limited to **small** dimensions and **nonnegative integer** data after reformulation (see API modeling notes when something is rejected).
- **Term order** and the \(w\)-permutation matter; the implementation compares the candidate point to **SciPy HiGHS MILP** when possible.

For broader references (LP/MILP texts, solvers), see [Further reading](/docs/further-reading).

---

## References

1. **David Cox, John Little, and Donal O’Shea**, *Ideals, Varieties, and Algorithms: An Introduction to Computational Algebraic Geometry and Commutative Algebra* (Springer). See the material on **integer programming**, **toric ideals**, and **Gröbner bases** (typically **Chapter 8** in recent editions).

2. **P. Conti and C. Traverso**, *Buchberger algorithm and integer programming*, in *Applied Algebra, Algebraic Algorithms and Error-Correcting Codes (AAECC-9)*, Lecture Notes in Computer Science, vol. **539**, Springer, 1991, pp. **130–139**.  
   [Chapter on SpringerLink](https://link.springer.com/chapter/10.1007/3-540-54522-0_102) (classic source for reducing IP to Gröbner-basis / normal-form computation).
