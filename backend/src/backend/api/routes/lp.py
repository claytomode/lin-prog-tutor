from __future__ import annotations

from fastapi import APIRouter

from backend.lp.analyze import analyze_source
from backend.schemas import AnalyzeRequest, AnalyzeResponse

router = APIRouter(prefix="/api", tags=["lp"])


@router.post("/lp/analyze", response_model=AnalyzeResponse)
def analyze_lp(body: AnalyzeRequest) -> AnalyzeResponse:
    return analyze_source(body)
