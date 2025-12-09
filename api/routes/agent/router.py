from fastapi import APIRouter, HTTPException
from .models import AgentRequest, FeedbackRequest
from agents import get_agent, get_all_agents
from worker.tasks import agent_initialization_task
from worker.task_storage import save_task
from worker.session_manager import get_session_manager
import uuid
import logging

router = APIRouter(prefix="/agent", tags=["agent"])
router_logger = logging.getLogger(__name__)


@router.post("")
async def process_agent(agent: AgentRequest):
    """
    Create an agent initialization task.
    Posts the task to the agent_initialization_queue, saves it to the database, and returns task information.
    
    Args:
        agent: Agent request containing project_id, context, and agent_name
        
    Returns:
        Dictionary with task_id, queue_name, status, and message
    """
    router_logger.info("=" * 80)
    router_logger.info(f"📥 API ENDPOINT CALLED: POST /agent")
    router_logger.info(f"   Project ID: {agent.project_id}")
    router_logger.info(f"   Agent Name: {agent.agent_name}")
    router_logger.info(f"   Context Length: {len(agent.context) if agent.context else 0}")
    router_logger.info("=" * 80)
    
    # Validate agent exists
    router_logger.info(f"🔍 Validating agent exists: {agent.agent_name}")
    agent_definition = get_agent(agent.agent_name)
    if not agent_definition:
        router_logger.error(f"❌ Agent not found: {agent.agent_name}")
        raise HTTPException(status_code=404, detail=f"Agent '{agent.agent_name}' not found")
    
    router_logger.info(f"✅ Agent found: {agent.agent_name}")
    
    # Route task using session manager BEFORE queuing to Celery
    router_logger.info("=" * 80)
    router_logger.info(f"🎯 ROUTING TASK: Calling session manager to determine execution environment")
    router_logger.info("=" * 80)
    
    session_manager = get_session_manager()
    router_logger.info(f"✅ Session manager instance retrieved: {type(session_manager)}")
    
    # Get agent definition to check execution type (routing logic)
    agent_definition = get_agent(agent.agent_name)
    execution_type = agent_definition.execution_type if agent_definition else "local"
    
    router_logger.info(
        f"📍 Agent execution type: {execution_type} "
        f"(name={agent_definition.name if agent_definition else 'unknown'})"
    )
    
    # Route based on execution type
    if execution_type == "remote":
        # Remote agent - handle via Fly machine (don't queue to Celery)
        router_logger.info(f"🌐 Remote agent detected - routing to Fly machine (placeholder)")
        
        # Generate task ID for remote agent
        task_id = str(uuid.uuid4())
        router_logger.info(f"🔑 Generated task ID for remote agent: {task_id}")
        
        # Create session for remote agent
        session_key = f"{agent.project_id}:{agent.agent_name}:{task_id}"
        fly_machine_id = f"fly_machine_{agent.agent_name}_{agent.project_id}"  # Placeholder
        
        routing_info = {
            "execution_type": "remote",
            "route_to": "fly_machine",
            "session_key": session_key,
            "fly_machine_id": fly_machine_id,
            "message": f"Remote agent '{agent.agent_name}' routed to Fly machine (placeholder)"
        }
        
        # Register session (using route_agent_task which creates the session)
        # For remote agents, we need to create session manually since we're not using Celery
        routing_info_temp = session_manager.route_agent_task(
            project_id=agent.project_id,
            agent_name=agent.agent_name,
            task_id=task_id,
            context=agent.context
        )
        
        # Update to routed_to_fly status
        session_manager.update_session_status(
            routing_info_temp["session_key"],
            status="routed_to_fly",
            fly_machine_id=fly_machine_id
        )
        
        routing_info = {
            "execution_type": "remote",
            "route_to": "fly_machine",
            "session_key": routing_info_temp["session_key"],
            "fly_machine_id": fly_machine_id,
            "message": f"Remote agent '{agent.agent_name}' routed to Fly machine (placeholder)"
        }
        
        # Save task to database with "routed_to_fly" status
        save_task(
            task_id=task_id,
            project_id=agent.project_id,
            queue_name="fly_machine",
            task_type="agent_initialization",
            agent_name=agent.agent_name,
            context=agent.context,
            status="routed_to_fly"
        )
        
        return {
            "task_id": task_id,
            "queue_name": "fly_machine",
            "status": "routed_to_fly",
            "execution_type": "remote",
            "routing_info": routing_info,
            "message": f"Remote agent '{agent.agent_name}' routed to Fly machine (placeholder - Fly integration pending)"
        }
    
    # Local agent - queue to Celery
    router_logger.info(f"⚙️ Local agent detected - queuing to Celery")
    
    # Create Celery task for local agents (this generates the task_id)
    router_logger.info(f"📤 Creating Celery task and queuing to agent_initialization_queue...")
    task = agent_initialization_task.delay(
        project_id=agent.project_id,
        context=agent.context,
        agent_name=agent.agent_name
    )
    router_logger.info(f"✅ Celery task created with ID: {task.id}")
    
    # Create session for local agent with actual Celery task ID
    # Use route_agent_task to create the session (it will detect it's local and route to Celery)
    routing_info = session_manager.route_agent_task(
        project_id=agent.project_id,
        agent_name=agent.agent_name,
        task_id=task.id,
        context=agent.context
    )
    
    router_logger.info(f"✅ Session created for local agent: {routing_info['session_key']}")
    
    # Save task to database immediately with "pending" status
    save_task(
        task_id=task.id,
        project_id=agent.project_id,
        queue_name="agent_initialization_queue",
        task_type="agent_initialization",
        agent_name=agent.agent_name,
        context=agent.context,
        status="pending"
    )
    
    return {
        "task_id": task.id,
        "queue_name": "agent_initialization_queue",
        "status": "pending",
        "execution_type": "local",
        "message": f"Local agent '{agent.agent_name}' queued to Celery worker"
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
