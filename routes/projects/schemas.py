"""
Pydantic schemas for project-related API requests and responses.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


# Request Schemas

class ProjectStartRequest(BaseModel):
    """Request schema for starting a new project."""
    project_id: str = Field(..., description="Unique identifier for the project")
    project_brief: str = Field(..., description="The project brief generated from the discovery call")


class ApprovePhaseRequest(BaseModel):
    """Request schema for approving or rejecting a phase."""
    approved: bool = Field(..., description="Whether the phase is approved")
    feedback: Optional[str] = Field(None, description="Optional feedback if not approved")


# Response Schemas

class ProjectListItem(BaseModel):
    """Schema for a project in the list view."""
    id: str = Field(..., description="Project UUID")
    name: str = Field(..., description="Project name")
    status: str = Field(..., description="Current status: discovery, waiting_approval, building, completed")
    current_phase: str = Field(..., description="Current phase description")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")


class ProjectArtifacts(BaseModel):
    """Schema for project artifacts."""
    prd: Optional[str] = Field(None, description="Product Requirements Document content")
    logo_url: Optional[str] = Field(None, description="URL to the project logo")
    market_analysis: Optional[str] = Field(None, description="Market analysis content")


class ProjectDetail(BaseModel):
    """Schema for detailed project information."""
    id: str = Field(..., description="Project UUID")
    status: str = Field(..., description="Current status")
    current_phase: str = Field(..., description="Current phase description")
    artifacts: ProjectArtifacts = Field(..., description="Project artifacts")
    created_at: str = Field(..., description="ISO timestamp of project creation")


class ProjectStartResponse(BaseModel):
    """Response schema for starting a project."""
    success: bool = Field(..., description="Whether the project was started successfully")
    project_id: str = Field(..., description="The project ID that was started")
    message: str = Field(..., description="Status message")


class ApprovePhaseResponse(BaseModel):
    """Response schema for approving a phase."""
    success: bool = Field(..., description="Whether the approval was processed successfully")
    message: str = Field(..., description="Status message")
    next_phase: Optional[str] = Field(None, description="Next phase if approved")

