"""Agent definition for Design Agent"""
from ..models import AgentDefinition

AGENT_DEFINITION = AgentDefinition(
    name="design",
    role="Product Designer",
    description="Creates production-ready UI mockups and screen layouts based on the PRD and brand.",
    goal="Deliver full mockup designs for all required screens.",
    requirements=["brand_strategy_document", "brand_kit_assets", "prd_document"],
    artifacts=["ui_mockups", "figma_export"],
    requires_approval=True
)
