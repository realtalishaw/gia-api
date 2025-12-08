"""Agent definition for Product Manager Agent"""
from ..models import AgentDefinition

AGENT_DEFINITION = AgentDefinition(
    name="product_manager",
    role="Product Manager",
    description="Coordinates the software development process, plans sprints, clarifies requirements, and ensures delivery.",
    goal="Produce a build plan and ensure all components of the MVP come together.",
    requirements=["prd_document", "ui_mockups"],
    artifacts=["build_plan"],
    requires_approval=False
)
