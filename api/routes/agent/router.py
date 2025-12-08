from fastapi import APIRouter, HTTPException
from .models import AgentRequest, FeedbackRequest
from agents import get_agent, get_all_agents
from worker.tasks import agent_initialization_task

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("")
async def process_agent(agent: AgentRequest):
    """
    Create an agent initialization task.
    Posts the task to the agent_initialization_queue and returns task information.
    
    Args:
        agent: Agent request containing project_id, context, and agent_name
        
    Returns:
        Dictionary with task_id, queue_name, status, and message
    """
    # Validate agent exists
    agent_definition = get_agent(agent.agent_name)
    if not agent_definition:
        raise HTTPException(status_code=404, detail=f"Agent '{agent.agent_name}' not found")
    
    # Create Celery task
    task = agent_initialization_task.delay(
        project_id=agent.project_id,
        context=agent.context,
        agent_name=agent.agent_name
    )
    
    return {
        "task_id": task.id,
        "queue_name": "agent_initialization_queue",
        "status": "pending",
        "message": f"Agent initialization task created for {agent.agent_name}"
    }


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
