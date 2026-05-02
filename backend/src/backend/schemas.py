from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    source: str = Field(..., description="LP problem text (DSL)")


class ConstraintPlot2D(BaseModel):
    a: float
    b: float
    rhs: float
    sense: Literal["<=", ">=", "="]
    label: str


class FeasibleRegion2D(BaseModel):
    kind: Literal["polygon_2d"] = "polygon_2d"
    vertices: list[tuple[float, float]]
    clipped_to_box: bool = False


class FeasibleRegion1D(BaseModel):
    kind: Literal["interval_1d"] = "interval_1d"
    var: str
    lo: float | None = None
    hi: float | None = None


class TutorStep(BaseModel):
    id: str
    title: str
    detail: str
    highlight_vertex_index: int | None = None


class ParsedProblemView(BaseModel):
    sense: Literal["maximize", "minimize"]
    variables: list[str]
    objective: dict[str, float]
    constraint_labels: list[str]


class TableauStep(BaseModel):
    index: int
    tableau: list[list[float]]
    column_labels: list[str]
    basis_labels: list[str]
    entering_col: int | None = None
    leaving_row: int | None = None
    ratios: list[float | None] | None = None
    narrative: str


class TableauWalkthrough(BaseModel):
    sense_for_tableau: Literal["maximize"]
    initial_narrative: str
    steps: list[TableauStep]
    outcome: Literal["optimal", "unbounded", "infeasible", "max_iterations"]


class AnalyzeResponse(BaseModel):
    ok: bool = True
    error: str | None = None
    problem: ParsedProblemView | None = None
    solve_status: Literal["optimal", "infeasible", "unbounded", "not_attempted"] | None = None
    optimal_value: float | None = None
    optimal_point: dict[str, float] | None = None
    constraints_2d: list[ConstraintPlot2D] = []
    feasible_region: FeasibleRegion1D | FeasibleRegion2D | dict[str, Any] | None = None
    geometry_note: str | None = None
    tutor_steps: list[TutorStep] = []
    tableau_walkthrough: TableauWalkthrough | None = None
    tableau_status: Literal["ok", "not_supported_yet", "skipped"] = "skipped"
    tableau_message: str | None = None
