from pydantic import BaseModel
from typing import List, Optional, Literal


class AgentDefinition(BaseModel):
    """Schema for agent definitions"""
    name: str
    role: str
    description: str
    goal: str
    requirements: List[str]
    artifacts: List[str]
    requires_approval: bool
    # Execution configuration
    execution_type: Literal["local", "remote"] = "local"
    s3_bucket_path: Optional[str] = None  # S3 path for remote agent code (e.g., "agents/custom_agent_v1.zip")
    fly_machine_id: Optional[str] = None  # Fly machine ID if agent is running on a Fly machine
