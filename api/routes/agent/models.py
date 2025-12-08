from pydantic import BaseModel
from typing import Optional


class AgentRequest(BaseModel):
    name: str
    description: Optional[str] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str


class FeedbackRequest(BaseModel):
    agent_id: str
    feedback: str
    rating: Optional[int] = None
