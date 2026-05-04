# Error code glossary

When something goes wrong, the API prefers **structured errors**: `error_code`, `error_hint`, and optional `error_context`. This page lists the stable codes emitted by the tutor backend so you can fix models quickly and link help text from assignments.

## Learning objectives

- map a failing analyze request to a probable modeling fix,
- know where syntax vs semantics vs capability limits apply.

## Prerequisites

- [Solving LPs in this app](/docs/solving-lps-in-this-app)

## Key terms

- **`error_code`** — short snake-case identifier; safe to branch on in UI automation.
- **`error_hint`** — human-readable suggestion (also surfaced in the web UI when present).

## Parser and empty model

| Code | Typical cause |
|------|----------------|
| `EMPTY_PROBLEM` | Source is empty or only comments. |
| `MISSING_OBJECTIVE` | No `maximize` / `minimize` line. |
| `MISSING_SUBJECT_TO` | Constraints without a `subject to` header. |
| `MISSING_COMPARATOR` | A constraint line lacks `<=`, `>=`, `=`, `<`, or `>`. |
| `NON_LINEAR_EXPRESSION` | Uses `*`, `/`, powers—only linear sums are allowed. |
| `INVALID_TERM` | A token in a sum could not be parsed. |
| `OBJECTIVE_NO_VARIABLES` | Objective has constants only—needs at least one variable. |
| `EMPTY_EXPRESSION` | Malformed empty linear expression. |

## Domains and problem class

| Code | Typical cause |
|------|----------------|
| `INVALID_DOMAIN_DECLARATION` | Variable domain line does not match `x integer`, `y: binary`, etc. |
| `UNKNOWN_VARIABLE_DOMAIN` | Domain keyword not in `continuous`, `integer`, `binary` (and aliases). |
| `DUPLICATE_VARIABLE_DOMAIN` | Two different domains for the same variable. |
| `UNKNOWN_DOMAIN_VARIABLE` | Request JSON lists a variable not appearing in the objective or constraints. |
| `PROBLEM_CLASS_MISMATCH` | `problem_class` is `lp` but integer/binary domains were set. |
| `MIP_NOT_IMPLEMENTED` | Reserved for builds without MILP support (normally MILP uses HiGHS via SciPy). |
| `MIP_SOLVER_ERROR` | The MILP backend raised an error; simplify the model or check constraints. |

## Model build

| Code | Typical cause |
|------|----------------|
| `NO_VARIABLES` | No symbols were identified as variables. |
| `MODEL_ERROR` | Catch-all for inconsistent internal model construction. |

## Using this in the UI

The Solver page maps codes to friendly sentences when a hint is missing. For teaching, prefer fixing the **root cause** using `error_context` (line numbers, sections) when the API provides them.

Related chapters: [Modeling pitfalls](/docs/modeling-pitfalls), [LP vs IP vs MILP](/docs/lp-vs-ip-vs-milp).
