"""
FastAPI application entry point for Organization Management Service.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import connect_db, close_db
from app.routes import org_routes, auth_routes
from app.routes.deps import bearer_scheme

# Tags metadata for OpenAPI documentation
tags_metadata = [
    {
        "name": "organizations",
        "description": "Organization management operations. Create, read, update, and delete organizations.",
    },
    {
        "name": "authentication",
        "description": "Authentication endpoints. Login to get JWT tokens.",
    },
]

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    openapi_tags=tags_metadata
)

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
    try:
        await connect_db()
    except Exception as e:
        import logging
        logging.error(f"Failed to connect to database: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Close MongoDB connection on application shutdown."""
    await close_db()


def custom_openapi():
    """Customize OpenAPI schema to include HTTPBearer security scheme."""
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=tags_metadata,
    )
    
    # Ensure components section exists
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {}
    
    # Add HTTPBearer security scheme
    openapi_schema["components"]["securitySchemes"]["HTTPBearer"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Enter your JWT token. Get a token by logging in at /admin/login"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

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

