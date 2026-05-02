# Roadmap

Planned improvements beyond the current MVP (not ordered).

## Modeling & DSL

- Support strict inequalities **`<`** and **`>`** in the source language (normalize to closed form or document epsilon semantics).
- Broader constraint syntax and clearer parse errors where the model is still linear.

## Tableau / simplex pedagogy

- **Phase I / Phase II** and **negative RHS** (two-phase simplex, artificial variables).
- Additional tableau variants students see in courses: **dual simplex**, **big-M**, **degeneracy** messaging, optional **minimize** tableau conventions.
- Equality constraints in the tableau walkthrough (currently skipped).

## Geometry & graphics

- Richer **graphical tutor** for 3D (slices \(z = \text{const}\), multiple isoprofit planes, or step-through vertices in 3D).
- Clearer **2D** polish (labels, scales, constraint naming).
- Optional export or printable layout for worksheets.

## Product / interface

- **Better graphical interface**: layout, mobile, accessibility, loading states, copy for non-expert users.
- Settings or presets for classroom vs self-study modes.

## Engineering

- CI (lint, test, typecheck) on push.
- Packaging / one-command dev (e.g. compose or script to run API + UI).

Contributions welcome; open an issue or PR with a short design note for larger items (especially tableau and strict inequalities).
