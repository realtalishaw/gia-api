"""Agent definition for Growth Engineer Agent"""
from ..models import AgentDefinition

AGENT_DEFINITION = AgentDefinition(
    name="growth_engineer",
    role="Analytics & Instrumentation Engineer",
    description="Implements analytics pipelines, event tracking, funnels, heatmaps, and experiment scaffolding.",
    goal="Deliver a fully instrumented product with actionable metrics.",
    requirements=["production_codebase", "audience_definition_report", "market_research_report"],
    artifacts=["analytics_events", "funnels", "dashboards"],
    requires_approval=False
)
