"""
main.py – FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import APP_ENV
from app.recommender import recommend_from_message, recommend_with_metadata
from app.parser import parse_message
from app.schemas import (
    HealthResponse,
    ParseRequest,
    ParsedProfile,
    RecommendRequest,
    RecommendResponse,
    StatsResponse,
)

app = FastAPI(
    
    title="Career Finder AI",
    description=(
        "AI-Powered Career Finder for Saudi COOP and Internship Opportunities. "
        "Helps computing students find suitable opportunities based on their profile."
    ),
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check() -> HealthResponse:
    """Return a simple health status to confirm the backend is running."""
    return HealthResponse(status="ok", environment=APP_ENV)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@app.get("/stats", response_model=StatsResponse, tags=["System"])
def get_stats() -> StatsResponse:
    """Return basic dataset statistics (placeholder values for now)."""
    return StatsResponse(
        total_companies=7,
        total_opportunities=7,
        available_cities=["Riyadh", "Jeddah", "Dammam", "Dhahran"],
        available_majors=["CS", "AI", "CYS", "CIS", "DS", "DE", "CE", "FT"],
        available_work_modes=["On-site", "Remote", "Hybrid"],
    )


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

@app.post("/parse", response_model=ParsedProfile, tags=["Recommender"])
def parse_student_message(request: ParseRequest) -> ParsedProfile:
    """
    Parse a free-text student message into structured profile fields.

    - **message**: Natural language description from the student.
    """
    try:
        return parse_message(request.message)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Recommend
# ---------------------------------------------------------------------------

@app.post("/recommend", response_model=RecommendResponse, tags=["Recommender"])
def get_recommendations(request: RecommendRequest) -> RecommendResponse:
    """
    Return the top 5 ranked COOP/internship opportunities for a student.

    - **message**: Natural language description from the student including
      major, city, work mode, and program type.
    """
    try:
        profile = parse_message(request.message)
        result = recommend_with_metadata(profile, top_n=5)

        return RecommendResponse(
            profile=result["profile"],
            recommendations=result["recommendations"],
            total_candidates=result["total_candidates"],
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc