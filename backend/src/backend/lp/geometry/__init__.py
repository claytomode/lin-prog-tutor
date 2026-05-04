"""Feasible-region geometry in low dimensions and MILP lattice points for plots."""

from backend.lp.geometry.discrete import discrete_feasible_points_2d
from backend.lp.geometry.regions import (
    feasible_interval_1d,
    geometry_3d_vertices,
    order_polygon_ccw,
    vertices_2d_halfspaces,
)

__all__ = [
    "discrete_feasible_points_2d",
    "feasible_interval_1d",
    "geometry_3d_vertices",
    "order_polygon_ccw",
    "vertices_2d_halfspaces",
]
