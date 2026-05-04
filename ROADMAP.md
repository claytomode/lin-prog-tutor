# Roadmap

This file tracks what the tutor **already does** and what could still be refined. Major roadmap themes from the original MVP plan are **implemented**; remaining bullets are polish or teaching extensions.

## Modeling & DSL

- **(done)** Strict **`<`** / **`>`** (ε-closure; `modeling_notes` in the API).
- **(done)** Clearer parse errors (line numbers on constraints; objective line cited for parse failures).
- **(done)** Light **broader linear syntax**: commas between terms; optional colon on `subject to:`.

## Tableau / simplex pedagogy

- **(done)** Phase **I / II**, **negative RHS**, **equalities**, **dual** / **big-M** / **Bland** (API + UI); minimize via equivalent max tableau where shown.

## Geometry & graphics

- **(done)** 3D vertex tutor + isoprofit / optimum visualization.
- **(done)** 2D plot polish: axis **tickformat**, titles with standoff, constraint **hover** with full label and inequality, hover label styling.

## Product / interface

- **(done)** Loading / **aria-busy**, focus after analyze, presets, print worksheet.
- **(done)** Short **intro copy** and **humanized** API/parse error strings on the client.

## Engineering

- **(done)** CI on push; root **one-command dev** (`bun run dev`).

## Possible next extensions (not required for “done”)

- Deeper DSL (more grammar, implied multiplication `2x`, etc.).
- Even richer 3D (z-slices UI, full vertex enumeration UX).
- Server-side lint rules or pedagogy-specific validation messages.

Contributions welcome; open an issue or PR with a short design note for larger teaching features.
