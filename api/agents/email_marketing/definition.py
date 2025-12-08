"""Agent definition for Email Marketing Agent"""
from ..models import AgentDefinition

AGENT_DEFINITION = AgentDefinition(
    name="email_marketing",
    role="Lifecycle Marketer",
    description="Creates persuasive launch emails and lifecycle content for user activation.",
    goal="Deliver a complete launch email sequence.",
    requirements=["project_brief", "audience_definition_report"],
    artifacts=["launch_email", "feature_email", "why_now_email", "behind_the_scenes_email"],
    requires_approval=False
)
