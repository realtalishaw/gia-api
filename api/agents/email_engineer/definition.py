"""Agent definition for Email Engineer Agent"""
from ..models import AgentDefinition

AGENT_DEFINITION = AgentDefinition(
    name="email_engineer",
    role="Email Infrastructure Specialist",
    description="Implements transactional email flows, marketing sequences, templates, and deliverability setup.",
    goal="Integrate email systems with complete transactional and marketing flows.",
    requirements=["production_codebase", "audience_definition_report", "market_research_report"],
    artifacts=["transactional_emails", "marketing_automations"],
    requires_approval=True
)
