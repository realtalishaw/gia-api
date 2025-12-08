# Load environment variables FIRST, before any other imports
# This ensures Supabase credentials are available when the registry initializes
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from routes.root.router import router as root_router
from routes.agent.router import router as agent_router
from routes.webhook.router import router as webhook_router

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

# Include routers
app.include_router(root_router)
app.include_router(agent_router)
app.include_router(webhook_router)


