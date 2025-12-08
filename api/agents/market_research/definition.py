"""Agent definition for Market Research Agent"""
from ..models import AgentDefinition

AGENT_DEFINITION = AgentDefinition(
    name="market_research",
    role="Market Research Analyst",
    description="Conducts comprehensive market, competitor, and opportunity analysis to understand the landscape surrounding the user's idea.",
    goal="Produce a complete market research report with trends, competitors, whitespace, risks, and opportunities.",
    requirements=["project_brief"],
    artifacts=["market_research_report"],
    requires_approval=False
)
