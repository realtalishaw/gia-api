"""Agent definition for Audience Definition Agent"""
from ..models import AgentDefinition

AGENT_DEFINITION = AgentDefinition(
    name="audience_definition",
    role="Audience Strategist",
    description="Analyzes the market research and defines the ideal audience segments for the product.",
    goal="Produce ideal customer profiles, pain points, psychological drivers, adoption triggers, and channel insights.",
    requirements=["market_research_report"],
    artifacts=["audience_definition_report"],
    requires_approval=False
)
