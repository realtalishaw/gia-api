"""Agent definition for Developer Agent"""
from ..models import AgentDefinition

AGENT_DEFINITION = AgentDefinition(
    name="developer",
    role="Software Engineer",
    description="Implements backend, frontend, APIs, and integrations to build the functional MVP.",
    goal="Write production-ready code for all required features.",
    requirements=["system_architecture", "api_specs", "ui_mockups", "prd_document"],
    artifacts=["production_codebase"],
    requires_approval=False
)
