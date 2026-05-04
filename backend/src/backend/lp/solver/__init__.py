"""Continuous LP and MILP entry points (HiGHS / SciPy)."""

from backend.lp.solver.engine import SolveResult, solve_dispatch, solve_lp, solve_mip

__all__ = ["SolveResult", "solve_dispatch", "solve_lp", "solve_mip"]
