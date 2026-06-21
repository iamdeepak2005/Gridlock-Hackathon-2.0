"""
TRINETRA AI - Event Driven Traffic Intelligence System
FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.connection import init_db
from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # ── Startup ───────────────────────────────────────────
    print(f"[START] Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Initialize database tables
    try:
        init_db()
        print("[OK] Database initialized")
    except Exception as e:
        print(f"[WARN] Database init warning: {e}")

    # Pre-load ML models (lazy loading, just log availability)
    print("[INFO] ML Models will load lazily on first request")

    yield

    # ── Shutdown ──────────────────────────────────────────
    print(f"[STOP] Shutting down {settings.APP_NAME}")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Event Driven Traffic Intelligence System for Bengaluru.\n\n"
        "## Features\n"
        "- **Impact Scoring**: Predict event severity (0-100)\n"
        "- **Resource Recommendation**: Officers, barricades, tow vehicles\n"
        "- **Similar Events**: Find historical incident matches\n"
        "- **Resolution Prediction**: Estimate resolution time\n"
        "- **Feedback Loop**: Continual learning from outcomes\n"
        "- **Traffic Diversion**: Simulate alternative routes\n\n"
        "## Getting Started\n"
        "1. Train models: `python -m app.training.train_all <csv_path>`\n"
        "2. Start server: `uvicorn app.main:app --reload`\n"
        "3. Open Swagger UI: http://localhost:8000/docs"
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.API_PREFIX)

# Also mount at root for convenience
app.include_router(api_router)


@app.get("/", tags=["Root"])
def root():
    """API root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "endpoints": {
            "predict_impact": "/predict-impact",
            "recommend_resources": "/recommend-resources",
            "similar_events": "/similar-events",
            "predict_resolution": "/predict-resolution",
            "feedback": "/feedback",
            "model_performance": "/model-performance",
            "simulate_diversion": "/simulate-diversion",
            "health": "/health",
        },
    }
