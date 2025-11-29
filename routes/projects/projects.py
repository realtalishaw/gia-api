"""
Projects API routes for managing buildbox projects.
"""
from fastapi import APIRouter, Path, Query
from typing import List
from datetime import datetime

from .schemas import (
    ProjectStartRequest,
    ProjectStartResponse,
    ProjectListItem,
    ProjectDetail,
    ProjectArtifacts,
    ApprovePhaseRequest,
    ApprovePhaseResponse,
)

router = APIRouter()


@router.post("/start", response_model=ProjectStartResponse)
async def start_project(request: ProjectStartRequest):
    """
    Start a new project with the provided brief.
    
    This endpoint is called by the frontend after payment is completed.
    It creates a project and queues the discovery phase.
    """
    # TODO: In the future, this will:
    # 1. Create project in database
    # 2. Queue discovery_tasks to RabbitMQ
    # 3. Return success
    
    # For now, just return success
    return ProjectStartResponse(
        success=True,
        project_id=request.project_id,
        message="Project started successfully. Discovery phase queued."
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

