"""Agent definition for Social Media Agent"""
from ..models import AgentDefinition

AGENT_DEFINITION = AgentDefinition(
    name="social_media",
    role="Social Media Strategist",
    description="Creates a cross-platform launch content pack tailored to the product and audience.",
    goal="Deliver social content that supports virality and distribution.",
    requirements=["project_brief", "audience_definition_report", "brand_strategy_document"],
    artifacts=["twitter_thread", "linkedin_post", "reddit_post", "product_hunt_assets", "content_calendar"],
    requires_approval=False
)
