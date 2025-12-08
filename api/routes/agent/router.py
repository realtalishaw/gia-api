from fastapi import APIRouter
from .models import AgentRequest, FeedbackRequest

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("")
def create_agent(agent: AgentRequest):
    """Create a new agent"""
    return {
        "id": "agent_123",
        "name": agent.name,
        "description": agent.description,
        "status": "active",
        "message": "Agent created successfully"
    }


@router.get("s")
def get_agents():
    """Get all agents"""
    return {
        "agents": [
            {
                "id": "agent_123",
                "name": "Example Agent",
                "description": "An example agent",
                "status": "active"
            },
            {
                "id": "agent_456",
                "name": "Another Agent",
                "description": "Another example agent",
                "status": "inactive"
            }
        ],
        "total": 2
    }


@router.post("s/feedback")
def submit_feedback(feedback: FeedbackRequest):
    """Submit feedback for an agent"""
    return {
        "agent_id": feedback.agent_id,
        "feedback": feedback.feedback,
        "rating": feedback.rating,
        "status": "received",
        "message": "Feedback submitted successfully"
    }
