"""Agent definition for Ad Creative Agent"""
from ..models import AgentDefinition

AGENT_DEFINITION = AgentDefinition(
    name="ad_creative",
    role="Creative Strategist",
    description="Generates ad concepts, images, and performance-oriented copy.",
    goal="Produce ad creative sets optimized for cold, warm, and retargeting traffic.",
    requirements=["audience_definition_report", "brand_strategy_document"],
    artifacts=["ad_images", "ad_copy"],
    requires_approval=False
)
