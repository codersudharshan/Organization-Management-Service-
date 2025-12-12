"""
FastAPI application entry point for Organization Management Service.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import connect_db, close_db
from app.routes import org_routes, auth_routes

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Connect to MongoDB on application startup."""
    await connect_db()


@app.on_event("shutdown")
async def shutdown_event():
    """Close MongoDB connection on application shutdown."""
    await close_db()


# Mount routers
app.include_router(org_routes.router, prefix="/org", tags=["organizations"])
app.include_router(auth_routes.router, prefix="/admin", tags=["authentication"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Organization Management Service API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

