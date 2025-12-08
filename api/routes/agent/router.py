from fastapi import APIRouter
from .models import AgentRequest, FeedbackRequest

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("")
async def process_agent(agent: AgentRequest):
    """
    Process an agent request with project ID, context, and agent name.
    Creates an initialization task and enqueues it for processing.
    
    Args:
        agent: Agent request containing project_id, context, and agent_name
        
    Returns:
        Success response indicating agent successfully initialized
    """
    return {
        "message": "Agent successfully initialized"
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
