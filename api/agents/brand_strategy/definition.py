"""Agent definition for Brand Strategy Agent"""
from ..models import AgentDefinition

AGENT_DEFINITION = AgentDefinition(
    name="brand_strategy",
    role="Brand Strategist",
    description="Creates a cohesive brand strategy rooted in research and audience psychology.",
    goal="Develop a full brand strategy including personality, tone of voice, creative direction, visual identity vibe, color psychology, and UX tone.",
    requirements=["project_brief", "market_research_report", "audience_definition_report"],
    artifacts=["brand_strategy_document"],
    requires_approval=True
)
