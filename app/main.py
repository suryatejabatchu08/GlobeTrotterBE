from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from app.core.config import settings
from app.routes import auth, trips, profile, budget, search, itinerary
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app with security scheme
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="1.0.0",
    description="GlobeTrotter API - Plan and share your trips"
)

# Add security scheme for Swagger UI
security = HTTPBearer()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(trips.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(profile.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(budget.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(search.router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(itinerary.router, prefix=f"{settings.API_V1_PREFIX}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
