"""Agent definition for PRD Agent"""
from ..models import AgentDefinition

AGENT_DEFINITION = AgentDefinition(
    name="prd",
    role="Product Requirements Architect",
    description="Creates a structured, detailed PRD based on strategy, research, and constraints.",
    goal="Produce a comprehensive PRD containing user stories, flows, features, constraints, acceptance criteria, and success metrics.",
    requirements=["project_brief", "brand_strategy_document", "market_research_report", "audience_definition_report"],
    artifacts=["prd_document"],
    requires_approval=True
)
