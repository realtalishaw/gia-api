"""
Projects API routes for managing buildbox projects.
"""
from fastapi import APIRouter, Path, Query, HTTPException
from typing import List
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from .schemas import (
    ProjectStartRequest,
    ProjectStartResponse,
    ProjectListItem,
    ProjectDetail,
    ProjectArtifacts,
    ApprovePhaseRequest,
    ApprovePhaseResponse,
)

# Import orchestrator and config
from orchestrator.engine import AgentOrchestrator
from config.phase_config import PhaseConfig, Phase

router = APIRouter()

# Initialize Supabase client (commented out until Supabase is set up)
# TODO: Uncomment when Supabase is configured
# from supabase import create_client
# supabase = create_client(
#     os.getenv("SUPABASE_URL", ""),
#     os.getenv("SUPABASE_KEY", "")
# )
supabase = None

# Initialize queue manager directly (works without Supabase)
from orchestrator.task_queue_manager import TaskQueueManager
task_queue_manager = TaskQueueManager(rabbitmq_url=os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/"))

# Initialize orchestrator (only if Supabase is configured)
# TODO: Uncomment when Supabase is configured
# orchestrator = AgentOrchestrator(supabase, rabbitmq_url=os.getenv("RABBITMQ_URL"))
orchestrator = None


@router.post("/start", response_model=ProjectStartResponse)
async def start_project(request: ProjectStartRequest):
    """
    Start a new project with the provided brief.
    
    This endpoint is called by the frontend after payment is completed.
    It creates a project and queues the first task (market research).
    """
    try:
        project_id = request.project_id
        project_brief = request.project_brief
        
        # TODO: Uncomment when Supabase is configured
        # if not supabase:
        #     raise HTTPException(status_code=500, detail="Database not configured")
        # if not orchestrator:
        #     raise HTTPException(status_code=500, detail="Orchestrator not configured")
        
        # Get the first task in Discovery phase
        discovery_tasks = PhaseConfig.get_required_tasks(Phase.DISCOVERY.value)
        if not discovery_tasks:
            raise HTTPException(status_code=500, detail="No tasks found for Discovery phase")
        
        first_task_type = discovery_tasks[0]["type"]  # conduct_market_research
        first_task_agent = discovery_tasks[0]["agent"]  # researcher
        
        # Generate a temporary task_id (UUID format)
        import uuid
        task_id = str(uuid.uuid4())
        
        # If Supabase is configured, use orchestrator
        if supabase and orchestrator:
            # 1. Create project in database
            project_data = {
                "id": project_id,
                "project_brief": project_brief,
                "status": "building",
                "current_phase": Phase.DISCOVERY.value,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            project_result = supabase.table('projects').insert(project_data).execute()
            
            if not project_result.data:
                raise HTTPException(status_code=500, detail="Failed to create project")
            
            # 2. Create and queue the first task using orchestrator
            success, task_id, error = await orchestrator.create_task(
                project_id=project_id,
                task_type=first_task_type
            )
            
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create initial task: {error}"
                )
            
            # 3. Initialize the phase
            await orchestrator.initialize_phase(
                project_id=project_id,
                phase=Phase.DISCOVERY.value,
                initial_task_id=task_id
            )
        else:
            # Without Supabase, queue directly to RabbitMQ
            # This allows testing the worker without database setup
            task_data = {
                "task_id": task_id,
                "project_id": project_id,
                "type": first_task_type,
                "action": "execute",
                "agent_role": first_task_agent,
                "project_brief": project_brief  # Include brief for agent context
            }
            
            # Get the queue name for this task
            queue_name = PhaseConfig.get_queue_for_task(first_task_type)
            
            # Queue the task directly
            success = await task_queue_manager.queue_task(task_data, queue_name=queue_name)
            
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to queue task to RabbitMQ"
                )
        
        return ProjectStartResponse(
            success=True,
            project_id=project_id,
            message=f"Project started successfully. First task '{first_task_type}' queued to '{PhaseConfig.get_queue_for_task(first_task_type)}'."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting project: {str(e)}"
        )


@router.get("", response_model=List[ProjectListItem])
async def list_projects(
    user_id: str = Query(..., description="The UUID of the user whose projects to retrieve")
):
    """
    List all projects for a specific user.
    
    Returns a list of projects with basic information for the given user.
    
    Args:
        user_id: The UUID of the user whose projects to retrieve (required query parameter)
    """
    # TODO: In the future, this will:
    # 1. Get user_id from auth token (instead of query param)
    # 2. Validate user exists
    # 3. Query database for user's projects
    # 4. Return formatted list
    
    # Dummy data for now - filtered by user_id
    # In real implementation, this would come from the database
    return [
        ProjectListItem(
            id="123e4567-e89b-12d3-a456-426614174000",
            name="Tinder for Dogs",
            status="building",
            current_phase="Phase 2: Development",
            progress=45
        ),
        ProjectListItem(
            id="223e4567-e89b-12d3-a456-426614174001",
            name="Task Management App",
            status="waiting_approval",
            current_phase="Phase 0: Strategy Review",
            progress=20
        ),
        ProjectListItem(
            id="323e4567-e89b-12d3-a456-426614174002",
            name="Social Media Platform",
            status="completed",
            current_phase="Phase 6: Launch Complete",
            progress=100
        ),
    ]


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(project_id: str = Path(..., description="The project UUID")):
    """
    Get detailed information about a specific project.
    
    Returns full project details including artifacts (PRD, logo, etc.).
    """
    # TODO: In the future, this will:
    # 1. Validate user has access to this project
    # 2. Query database for project details
    # 3. Fetch artifacts from database
    # 4. Return formatted response
    
    # Dummy data for now
    if project_id == "123e4567-e89b-12d3-a456-426614174000":
        return ProjectDetail(
            id=project_id,
            status="waiting_approval",
            current_phase="Phase 0: Strategy Review",
            artifacts=ProjectArtifacts(
                prd="# Product Requirements Document\n\n## Overview\nThis is a Tinder-like app for dog owners to find playdates for their dogs...",
                logo_url="https://s3.amazonaws.com/buildbox-assets/project-123/logo.png",
                market_analysis="## Market Analysis\n\n### Competitors\n- Rover: Focuses on dog walking services\n- Wag: Similar to Rover\n\n### Opportunity\nNo app currently focuses on social connection between dog owners..."
            ),
            created_at=datetime.utcnow().isoformat()
        )
    
    # Return a generic project if ID doesn't match
    return ProjectDetail(
        id=project_id,
        status="discovery",
        current_phase="Phase 0: Discovery",
        artifacts=ProjectArtifacts(
            prd=None,
            logo_url=None,
            market_analysis=None
        ),
        created_at=datetime.utcnow().isoformat()
    )


@router.post("/{project_id}/approve_phase", response_model=ApprovePhaseResponse)
async def approve_phase(
    project_id: str = Path(..., description="The project UUID"),
    request: ApprovePhaseRequest = ...
):
    """
    Approve or reject the current phase of a project.
    
    If approved, moves to the next phase. If rejected, re-runs current phase with feedback.
    """
    # TODO: In the future, this will:
    # 1. Validate user has access and project is in waiting_approval status
    # 2. If approved: Queue build_tasks to RabbitMQ
    # 3. If rejected: Queue discovery_tasks with feedback to RabbitMQ
    # 4. Update project status in database
    # 5. Return response
    
    # Dummy data for now
    if request.approved:
        return ApprovePhaseResponse(
            success=True,
            message="Phase approved. Moving to next phase.",
            next_phase="Phase 1: Architecture & Planning"
        )
    else:
        return ApprovePhaseResponse(
            success=True,
            message=f"Phase rejected. Feedback received: {request.feedback or 'No feedback provided'}. Re-running phase with feedback.",
            next_phase=None
        )

