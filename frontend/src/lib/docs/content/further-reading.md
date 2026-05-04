# Further reading

Use this section like a guided bibliography: pick one text per level and go deeper.

## LP foundations (start here)

- Dimitris Bertsimas and John Tsitsiklis, *Introduction to Linear Optimization*  
  Why read: clean mathematical development plus strong modeling perspective.
- Vasek Chvatal, *Linear Programming*  
  Why read: classic treatment of simplex, duality, and polyhedral ideas.

## Duality and theory depth

- Robert Vanderbei, *Linear Programming: Foundations and Extensions*  
  Why read: accessible but rigorous duality, interior-point context, and extensions.
- Alexander Schrijver, *Theory of Linear and Integer Programming*  
  Why read: advanced reference for deeper polyhedral/combinatorial theory.

## Integer programming / MILP

- Laurence Wolsey, *Integer Programming*  
  Why read: strong practical and theoretical bridge to branch-and-cut thinking.
- Nemhauser and Wolsey, *Integer and Combinatorial Optimization*  
  Why read: foundational text for integer formulations and algorithmic ideas.

## Algebraic / Gröbner viewpoint (optional MILP trace in this app)

- David Cox, John Little, Donal O’Shea, *Ideals, Varieties, and Algorithms* — integer programming and Gröbner bases (typically **Chapter 8**).  
  Why read: the standard “CLO” reference behind the toric/monomial encoding used in the walkthrough.  
  In-app overview: [Gröbner bases and integer programming](/docs/grobner-integer-programming).
- P. Conti and C. Traverso, *Buchberger algorithm and integer programming* (AAECC-9, LNCS 539, Springer, 1991).  
  Why read: the original algorithmic bridge from IP to Gröbner bases and normal forms.  
  [Springer chapter](https://link.springer.com/chapter/10.1007/3-540-54522-0_102).

## Practical solver references

- [HiGHS documentation](https://highs.dev/)  
  Why read: practical LP/MIP solver behavior and interfaces.
- [COIN-OR ecosystem](https://www.coin-or.org/)  
  Why read: open-source optimization tools and libraries.
- [NEOS Guide](https://neos-guide.org/guide/types/linear/)  
  Why read: concise optimization primers and solver workflows.

## Suggested study paths

### Path A: application-first
1. LP modeling chapter in this app.
2. Bertsimas/Tsitsiklis (modeling + duality chapters).
3. Intro MILP chapter + Wolsey selected chapters.

### Path B: theory-first
1. LP formalism + primal/dual chapter in this app.
2. Chvatal or Vanderbei for simplex/duality depth.
3. Nemhauser-Wolsey for integer optimization theory.

## Mini practice set (story prompts)

- Staffing: choose shifts to meet demand at minimum wage cost.
- Production: allocate machine hours across products with capacity limits.
- Facility location: open warehouses (binary) and route flow (continuous).
- Portfolio selection: choose projects with budget and risk caps.
