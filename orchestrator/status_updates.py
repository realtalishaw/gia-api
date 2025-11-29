"""
Status Update Helper for Project Activity.

Creates status updates in the project_activity table for real-time streaming.
"""
import logging
from typing import Optional
from datetime import datetime
from orchestrator.task_state_manager import ActivityType, TaskStatus, ApprovalStatus


class StatusUpdateHelper:
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.logger = logging.getLogger(__name__)

    async def create_activity(
        self,
        project_id: str,
        message: str,
        agent_role: Optional[str] = None,
        activity_type: str = ActivityType.INFO.value,
        task_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Create a project activity entry.
        
        Args:
            project_id: The project UUID
            message: Activity message
            agent_role: The agent role (e.g., "researcher", "developer")
            activity_type: Type of activity (success, error, warning, info, progress)
            task_id: Optional task ID
            metadata: Optional JSON metadata
        """
        try:
            data = {
                "project_id": project_id,
                "message": message,
                "agent_role": agent_role,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat()
            }
            
            if task_id:
                data["task_id"] = task_id
                
            result = self.supabase.table('project_activity').insert(data).execute()
            
            if not result.data:
                self.logger.error("Failed to create project activity")
                return False
                
            self.logger.info(f"Created activity: {message}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating project activity: {str(e)}")
            return False

    async def create_success(self, project_id: str, message: str, agent_role: Optional[str] = None, task_id: Optional[str] = None) -> bool:
        """Create a success activity."""
        return await self.create_activity(
            project_id=project_id,
            message=message,
            agent_role=agent_role,
            activity_type=ActivityType.SUCCESS.value,
            task_id=task_id
        )

    async def create_error(self, project_id: str, message: str, agent_role: Optional[str] = None, task_id: Optional[str] = None) -> bool:
        """Create an error activity."""
        return await self.create_activity(
            project_id=project_id,
            message=message,
            agent_role=agent_role,
            activity_type=ActivityType.ERROR.value,
            task_id=task_id
        )

    async def create_progress(self, project_id: str, message: str, agent_role: Optional[str] = None, task_id: Optional[str] = None) -> bool:
        """Create a progress activity."""
        return await self.create_activity(
            project_id=project_id,
            message=message,
            agent_role=agent_role,
            activity_type=ActivityType.PROGRESS.value,
            task_id=task_id
        )

    async def create_info(self, project_id: str, message: str, agent_role: Optional[str] = None, task_id: Optional[str] = None) -> bool:
        """Create an info activity."""
        return await self.create_activity(
            project_id=project_id,
            message=message,
            agent_role=agent_role,
            activity_type=ActivityType.INFO.value,
            task_id=task_id
        )

