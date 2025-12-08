from pydantic import BaseModel
from typing import List


class AgentDefinition(BaseModel):
    """Schema for agent definitions"""
    name: str
    role: str
    description: str
    goal: str
    requirements: List[str]
    artifacts: List[str]
    requires_approval: bool
