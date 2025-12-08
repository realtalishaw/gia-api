"""Agent definition for QA Agent"""
from ..models import AgentDefinition

AGENT_DEFINITION = AgentDefinition(
    name="qa",
    role="Quality Assurance Engineer",
    description="Tests the application across all user flows, features, browsers, and device types.",
    goal="Ensure the MVP is bug-free, stable, and meets acceptance criteria.",
    requirements=["production_codebase", "prd_document"],
    artifacts=["qa_test_report", "bug_fixes"],
    requires_approval=False
)
