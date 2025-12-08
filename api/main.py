from fastapi import FastAPI
from routes.root.router import router as root_router
from routes.agent.router import router as agent_router
from routes.webhook.router import router as webhook_router

app = FastAPI(title="General Intelligence Agency API", version="1.0.0")

# Include routers
app.include_router(root_router)
app.include_router(agent_router)
app.include_router(webhook_router)


