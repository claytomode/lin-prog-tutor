from __future__ import annotations

from backend.lp.analyze import analyze_source
from backend.schemas import AnalyzeRequest


def test_grobner_mip_request_returns_walkthrough():
    src = """
minimize x + 2 y
subject to
x + y = 3
variables x integer, y integer
"""
    r = analyze_source(AnalyzeRequest(source=src.strip(), mip_method="grobner"))
    assert r.ok
    assert r.solve_status == "optimal"
    assert r.grobner_walkthrough is not None
    assert r.mip_method == "grobner"
    assert len(r.grobner_walkthrough.steps) >= 3
    assert r.grobner_walkthrough.outcome in ("ok", "infeasible_normal_form", "computation_failed")


def test_grobner_classic_cost_order_matches_scipy():
    """NF under c-ordered w-generators should recover SciPy optimum for this tiny equality IP."""
    src = """
minimize x + 2 y
subject to
x + y = 3
variables x integer, y integer
"""
    r = analyze_source(AnalyzeRequest(source=src.strip(), mip_method="grobner"))
    assert r.ok
    assert r.solve_status == "optimal"
    assert r.grobner_walkthrough is not None
    assert r.grobner_walkthrough.point_from_normal_form is not None
    pt = r.grobner_walkthrough.point_from_normal_form
    assert pt.get("x") == 3 and pt.get("y") == 0
    assert r.grobner_walkthrough.agrees_with_scipy_mip is True


def test_grobner_rejects_binary_domains():
    src = """
minimize x
subject to
x = 1
variables x binary
"""
    r = analyze_source(AnalyzeRequest(source=src.strip(), mip_method="grobner"))
    assert r.ok
    assert r.grobner_walkthrough is not None
    assert r.grobner_walkthrough.outcome == "unsupported_model"
