"""Simplex tableau construction and cross-checks."""

from backend.lp.tableau.verify import verify_tableau_against_solver
from backend.lp.tableau.walkthrough import TableauOptions, build_tableau_if_supported

__all__ = [
    "TableauOptions",
    "build_tableau_if_supported",
    "verify_tableau_against_solver",
]
