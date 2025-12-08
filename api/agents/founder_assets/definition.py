"""Agent definition for Founder Assets Agent"""
from ..models import AgentDefinition

AGENT_DEFINITION = AgentDefinition(
    name="founder_assets",
    role="Founder Enablement Specialist",
    description="Generates assets that help the founder pitch, sell, and secure partnerships or investment.",
    goal="Produce founder-facing strategic assets.",
    requirements=["project_brief", "market_research_report", "brand_strategy_document", "prd_document", "gtm_strategy_document"],
    artifacts=["pitch_deck", "one_pager", "product_overview", "sales_explainer", "customer_use_cases", "founder_bio", "investor_blurb", "investor_target_list"],
    requires_approval=False
)
