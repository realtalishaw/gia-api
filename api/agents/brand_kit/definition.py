"""Agent definition for Brand Kit Agent"""
from ..models import AgentDefinition

AGENT_DEFINITION = AgentDefinition(
    name="brand_kit",
    role="Brand Identity Designer",
    description="Generates the visual identity, logo suite, color system, fonts, and branded assets.",
    goal="Produce a full brand kit supporting consistent visual expression across all platforms.",
    requirements=["brand_strategy_document"],
    artifacts=["logo", "social_media_headers", "favicon", "color_system", "font_system"],
    requires_approval=True
)
