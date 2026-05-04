from __future__ import annotations

from backend.analyze import analyze_source
from backend.parser import STRICT_EPS
from backend.schemas import AnalyzeRequest, AnalyzeResponse


def _assert_tableau_basis_matches_constraints(r: AnalyzeResponse) -> None:
    tw = r.tableau_walkthrough
    assert tw is not None
    for st in tw.steps:
        n_rows = len(st.tableau)
        assert n_rows >= 1
        m_constraints = n_rows - 1
        assert len(st.basis_labels) == m_constraints, (
            f"basis_labels length {len(st.basis_labels)} != constraint rows {m_constraints}"
        )


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
    _assert_tableau_basis_matches_constraints(r)


def test_tableau_ok_equality_only_lp():
    src = """
maximize x
subject to
x = 3
"""
    r = analyze_source(src)
    assert r.ok
    assert r.solve_status == "optimal"
    assert abs((r.optimal_value or 0.0) - 3.0) < 1e-6
    assert r.tableau_status == "ok"
    _assert_tableau_basis_matches_constraints(r)
    assert r.tableau_verified is True
    assert r.tableau_verify_message is None


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
    _assert_tableau_basis_matches_constraints(r)


def test_strict_lt_relaxation_documented():
    src = """
maximize x
subject to
x < 3
x >= 0
"""
    r = analyze_source(src)
    assert r.ok
    assert r.solve_status == "optimal"
    assert abs(r.optimal_value - (3.0 - STRICT_EPS)) < 1e-5
    assert r.modeling_notes
    joined = " ".join(r.modeling_notes)
    assert "Strict inequalities" in joined
    assert str(STRICT_EPS) in joined or "1e-06" in joined or "1e-6" in joined


def test_strict_gt_relaxation_documented():
    src = """
maximize x
subject to
x > 1
x <= 5
x >= 0
"""
    r = analyze_source(src)
    assert r.ok
    assert r.solve_status == "optimal"
    assert r.optimal_point is not None
    assert r.optimal_point["x"] >= 1.0
    assert r.modeling_notes
    joined = " ".join(r.modeling_notes)
    assert "Strict inequalities" in joined


def test_tableau_ok_with_equality_and_inequality():
    src = """
maximize y
subject to
x + y <= 5
x + y = 2
x >= 0
y >= 0
"""
    r = analyze_source(src)
    assert r.ok
    assert r.solve_status == "optimal"
    assert r.optimal_point is not None
    assert abs(r.optimal_value - 2.0) < 1e-5
    assert r.tableau_status == "ok"
    assert r.tableau_walkthrough is not None
    _assert_tableau_basis_matches_constraints(r)


def test_analyze_request_blands_and_big_m_tableau_stable():
    src = """
maximize x
subject to
x <= 1
x >= 0
"""
    body = src.strip()
    r_bland = analyze_source(AnalyzeRequest(source=body, use_blands_rule=True))
    assert r_bland.ok
    assert r_bland.tableau_status == "ok"
    _assert_tableau_basis_matches_constraints(r_bland)

    r_bm = analyze_source(AnalyzeRequest(source=body, tableau_mode="big_m", big_m_value=1_000.0))
    assert r_bm.ok
    assert r_bm.tableau_status == "ok"
    assert r_bm.tableau_walkthrough is not None
    assert r_bm.tableau_walkthrough.outcome == "optimal"
    _assert_tableau_basis_matches_constraints(r_bm)


def test_commas_in_linear_and_subject_to_colon():
    src = """
maximize 3 x, + 2 y
subject to:
x + y <= 4
x >= 0
y >= 0
"""
    r = analyze_source(src)
    assert r.ok
    assert r.solve_status == "optimal"
    assert abs((r.optimal_value or 0.0) - 12.0) < 1e-5


def test_objective_parse_error_cites_line():
    src = """maximize 2 * x
subject to
x <= 1
x >= 0
"""
    r = analyze_source(src)
    assert not r.ok
    assert r.error is not None
    assert "line 1" in r.error and "objective" in r.error


def test_structured_error_empty_problem():
    r = analyze_source("")
    assert not r.ok
    assert r.error_code == "EMPTY_PROBLEM"
    assert r.error_hint is not None
    assert "objective" in r.error_hint.lower()


def test_structured_error_missing_subject_to():
    src = """
maximize x
x <= 1
"""
    r = analyze_source(src)
    assert not r.ok
    assert r.error_code == "MISSING_SUBJECT_TO"
    assert r.error_hint is not None
    assert "subject to" in r.error_hint.lower()


def test_structured_error_missing_comparator_contains_context():
    src = """
maximize x
subject to
x y
"""
    r = analyze_source(src)
    assert not r.ok
    assert r.error_code == "MISSING_COMPARATOR"
    assert r.error_context is not None
    assert r.error_context.get("section") == "constraint"
    assert r.error_context.get("line") == 3


def test_variable_domains_inline_trigger_mip_not_implemented():
    src = """
maximize 3 x + 2 y
subject to
x + y <= 4
variables x: integer, y: continuous
"""
    r = analyze_source(AnalyzeRequest(source=src.strip(), problem_class="auto"))
    assert not r.ok
    assert r.error_code == "MIP_NOT_IMPLEMENTED"
    assert r.error_context is not None
    assert r.error_context.get("problem_class") == "milp"
    assert r.error_context.get("is_mip") is True
    diag = r.error_context.get("mip_diagnostics")
    assert isinstance(diag, dict)
    assert diag.get("mip_backend") == "stub"


def test_variable_domains_block_parse_error_has_stable_code():
    src = """
maximize x + y
subject to
x + y <= 4
variables:
x binary
y integerish
"""
    r = analyze_source(src)
    assert not r.ok
    assert r.error_code == "UNKNOWN_VARIABLE_DOMAIN"
    assert r.error_hint is not None
    assert "continuous" in r.error_hint
    assert r.error_context is not None
    assert r.error_context.get("section") == "variables"


def test_problem_class_lp_rejects_mip_domains():
    src = """
maximize x
subject to
x <= 4
variables x integer
"""
    r = analyze_source(AnalyzeRequest(source=src.strip(), problem_class="lp"))
    assert not r.ok
    assert r.error_code == "PROBLEM_CLASS_MISMATCH"
