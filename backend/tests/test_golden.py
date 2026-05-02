from __future__ import annotations

from backend.analyze import analyze_source


def test_classic_2d_max():
    src = """
maximize 3 x + 2 y
subject to
x + y <= 4
x >= 0
y >= 0
"""
    r = analyze_source(src)
    assert r.ok
    assert r.solve_status == "optimal"
    assert r.optimal_point is not None
    assert abs(r.optimal_value - 12.0) < 1e-6
    assert abs(r.optimal_point["x"] - 4.0) < 1e-6 and abs(r.optimal_point["y"]) < 1e-6
    assert r.feasible_region is not None
    assert r.tableau_status == "ok"


def test_infeasible():
    src = """
minimize x
subject to
x <= -1
x >= 0
"""
    r = analyze_source(src)
    assert r.ok
    assert r.solve_status == "infeasible"


def test_3d_polyhedron_max_3x2y1z_vertex_optimum():
    """Regression: optimum on x+y+z=6; interior witness must not be that vertex."""
    src = """
maximize 3 x + 2 y + z
subject to
x + y + z <= 6
2 x + y <= 8
x <= 4
"""
    r = analyze_source(src)
    assert r.ok
    assert r.solve_status == "optimal"
    assert r.feasible_region is not None
    assert isinstance(r.feasible_region, dict)
    assert r.feasible_region.get("kind") == "polyhedron_3d"
    assert not r.geometry_note or "halfspace intersection failed" not in r.geometry_note


def test_3d_polyhedron_when_optimum_on_facet():
    """LP optimum is often on the boundary; Qhull needs a strictly interior witness."""
    src = """
maximize z
subject to
x + y <= 4
z <= 12
x >= 0
y >= 0
z >= 0
"""
    r = analyze_source(src)
    assert r.ok
    assert r.solve_status == "optimal"
    assert r.feasible_region is not None
    assert isinstance(r.feasible_region, dict)
    assert r.feasible_region.get("kind") == "polyhedron_3d"
    verts = r.feasible_region.get("vertices") or []
    assert len(verts) >= 4
    assert not r.geometry_note or "halfspace intersection failed" not in r.geometry_note


def test_tableau_matches_solver_tiny():
    src = """
maximize x
subject to
x <= 1
x >= 0
"""
    r = analyze_source(src)
    assert r.ok
    assert r.solve_status == "optimal"
    assert abs(r.optimal_value - 1.0) < 1e-6
    assert r.tableau_walkthrough is not None
    assert r.tableau_walkthrough.outcome == "optimal"
