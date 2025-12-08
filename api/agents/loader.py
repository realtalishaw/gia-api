"""Agent Loader - Imports all agents to trigger registration"""
# Import all agents to trigger their registration
from .market_research import AGENT_DEFINITION as _market_research
from .audience_definition import AGENT_DEFINITION as _audience_definition
from .brand_strategy import AGENT_DEFINITION as _brand_strategy
from .brand_kit import AGENT_DEFINITION as _brand_kit
from .prd import AGENT_DEFINITION as _prd
from .design import AGENT_DEFINITION as _design
from .product_manager import AGENT_DEFINITION as _product_manager
from .tech_lead import AGENT_DEFINITION as _tech_lead
from .developer import AGENT_DEFINITION as _developer
from .qa import AGENT_DEFINITION as _qa
from .devops import AGENT_DEFINITION as _devops
from .growth_engineer import AGENT_DEFINITION as _growth_engineer
from .email_engineer import AGENT_DEFINITION as _email_engineer
from .social_media import AGENT_DEFINITION as _social_media
from .email_marketing import AGENT_DEFINITION as _email_marketing
from .ad_creative import AGENT_DEFINITION as _ad_creative
from .growth_strategy import AGENT_DEFINITION as _growth_strategy
from .growth_kit import AGENT_DEFINITION as _growth_kit
from .growth_systems_engineer import AGENT_DEFINITION as _growth_systems_engineer
from .founder_assets import AGENT_DEFINITION as _founder_assets


def load_all_agents():
    """Load all agents - this function is called to ensure all agents are registered"""
    # All agents are registered on import, so just importing them is enough
    pass
