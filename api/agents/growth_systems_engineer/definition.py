"""Agent definition for Growth Systems Engineer Agent"""
from ..models import AgentDefinition

AGENT_DEFINITION = AgentDefinition(
    name="growth_systems_engineer",
    role="Retention & Referral Engineer",
    description="Implements retention systems, referral loops, feedback mechanisms, and winback flows.",
    goal="Deploy growth systems that keep users active and bring new users.",
    requirements=["production_codebase", "audience_definition_report"],
    artifacts=["retention_flows", "referral_system", "feedback_loop", "winback_sequence"],
    requires_approval=False
)
