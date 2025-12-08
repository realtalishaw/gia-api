"""Agent definition for Growth Kit Agent"""
from ..models import AgentDefinition

AGENT_DEFINITION = AgentDefinition(
    name="growth_kit",
    role="Launch Content Producer",
    description="Produces launch videos and promotional media formatted for different platforms.",
    goal="Deliver a complete growth content kit supporting the GTM plan.",
    requirements=["gtm_strategy_document", "brand_strategy_document"],
    artifacts=["launch_video_assets"],
    requires_approval=False
)
