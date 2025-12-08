from fastapi import APIRouter, HTTPException
from .models import AgentRequest, FeedbackRequest
from agents import get_agent, get_all_agents

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("")
async def process_agent(agent: AgentRequest):
    """
    Process an agent request with project ID, context, and agent name.
    Returns the agent definition for the requested agent.
    
    Args:
        agent: Agent request containing project_id, context, and agent_name
        
    Returns:
        Agent definition
    """
    agent_definition = get_agent(agent.agent_name)
    if not agent_definition:
        raise HTTPException(status_code=404, detail=f"Agent '{agent.agent_name}' not found")
    
    return agent_definition.model_dump()


@router.get("s")
def get_agents():
    """Get all agents - returns list of agent names and total count"""
    all_agents = get_all_agents()
    agent_names = [agent.name for agent in all_agents]
    
    return {
        "agents": agent_names,
        "total": len(agent_names)
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
