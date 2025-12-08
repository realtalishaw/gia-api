"""Agent definition for Tech Lead Agent"""
from ..models import AgentDefinition

AGENT_DEFINITION = AgentDefinition(
    name="tech_lead",
    role="Technical Architect",
    description="Designs the architecture, database schema, system interfaces, and technology decisions.",
    goal="Produce a complete system design ready for engineers to implement.",
    requirements=["prd_document"],
    artifacts=["system_architecture", "database_schema", "api_specs"],
    requires_approval=False
)
