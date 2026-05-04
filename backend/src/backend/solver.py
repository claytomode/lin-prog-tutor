"""Compatibility re-exports for `backend.solver_engine`."""

from backend.solver_engine import SolveResult, solve_dispatch, solve_lp, solve_mip

__all__ = ["SolveResult", "solve_dispatch", "solve_lp", "solve_mip"]
