from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.health.health import router as health_router
from routes.projects.projects import router as projects_router

app = FastAPI(
    title="GIA API",
    description="GIA API with modular route structure",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(projects_router, prefix="/projects", tags=["Projects"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to GIA API",
        "status": "running",
        "version": "1.0.0"
    }

