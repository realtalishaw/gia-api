"""Agent definition for DevOps Agent"""
from ..models import AgentDefinition

AGENT_DEFINITION = AgentDefinition(
    name="devops",
    role="DevOps Engineer",
    description="Handles deployment, infrastructure provisioning, CI/CD, and environment reliability.",
    goal="Deploy the MVP to production with monitoring and rollback capabilities.",
    requirements=["production_codebase"],
    artifacts=["production_deployment", "infrastructure_setup"],
    requires_approval=False
)
