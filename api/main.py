# Load environment variables FIRST, before any other imports
# This ensures Supabase credentials are available when the registry initializes
from dotenv import load_dotenv
import os
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.root.router import router as root_router
from routes.agent.router import router as agent_router
from routes.webhook.router import router as webhook_router
from routes.monitoring.router import router as monitoring_router
from routes.context_monitoring.router import router as context_monitoring_router

# Load all agents to trigger registration
from agents.loader import load_all_agents
from agents import sync_all_agents_to_supabase

load_all_agents()

# Sync all agents to Supabase to ensure they're all defined
sync_result = sync_all_agents_to_supabase()
if sync_result.get("synced", 0) > 0:
    print(f"✓ {sync_result['message']}")
if sync_result.get("failed", 0) > 0:
    print(f"⚠ Warning: {sync_result['message']}")
    if sync_result.get("errors"):
        for error in sync_result["errors"][:5]:  # Show first 5 errors
            print(f"  - {error}")

app = FastAPI(title="General Intelligence Agency API", version="1.0.0")

# Configure CORS
# Get allowed origins from environment variable, or default to localhost for dev
allowed_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(root_router)
app.include_router(agent_router)
app.include_router(webhook_router)
app.include_router(monitoring_router)
app.include_router(context_monitoring_router)


