"""Agent definition for Growth Strategy Agent"""
from ..models import AgentDefinition

AGENT_DEFINITION = AgentDefinition(
    name="growth_strategy",
    role="Go-To-Market Strategist",
    description="Creates a complete GTM strategy with segments, channels, phases, and success metrics.",
    goal="Produce an actionable end-to-end GTM plan.",
    requirements=["market_research_report", "audience_definition_report", "brand_strategy_document"],
    artifacts=["gtm_strategy_document"],
    requires_approval=False
)
