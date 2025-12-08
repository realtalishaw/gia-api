# Brand Strategy Agent
from .main import process
from .definition import AGENT_DEFINITION
from ..registry import register_agent

# Register this agent on import
register_agent(AGENT_DEFINITION)

__all__ = ["process", "AGENT_DEFINITION"]
