"""
Task State Manager for Supabase.

Manages task state in the database.
Adapted from spark-api/workflow/task_state_manager.py
"""
import logging
from typing import Dict, Optional
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"


class ActivityType(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    PROGRESS = "progress"


class TaskStateManager:
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.logger = logging.getLogger(__name__)

    async def get_task_state(self, task_id: str) -> Optional[Dict]:
        """Get current task state from database."""
        try:
            result = self.supabase.table('tasks') \
                .select("*") \
                .eq('id', task_id) \
                .execute()
            
            if not result.data:
                self.logger.error(f"Task {task_id} not found")
                return None
                
            return result.data[0]
            
        except Exception as e:
            self.logger.error(f"Error getting task state: {str(e)}")
            return None

    async def update_task_state(self, task_id: str, updates: Dict) -> bool:
        """Update task state in database."""
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.supabase.table('tasks') \
                .update(updates) \
                .eq('id', task_id) \
                .execute()
                
            if not result.data:
                self.logger.error(f"Failed to update task {task_id}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating task state: {str(e)}")
            return False

    async def set_task_in_progress(self, task_id: str) -> bool:
        """Set task status to in_progress."""
        return await self.update_task_state(task_id, {
            "status": TaskStatus.IN_PROGRESS.value
        })

    async def set_task_pending_approval(self, task_id: str, result: Dict) -> bool:
        """Set task status and approval_status to pending."""
        return await self.update_task_state(task_id, {
            "status": TaskStatus.PENDING.value,
            "approval_status": ApprovalStatus.PENDING.value,
            "output_result": result
        })

    async def mark_task_completed(self, task_id: str) -> bool:
        """Mark task as completed and approved."""
        return await self.update_task_state(task_id, {
            "status": TaskStatus.COMPLETED.value,
            "approval_status": ApprovalStatus.APPROVED.value
        })

    async def handle_task_failure(self, task_id: str, error: str) -> bool:
        """Handle task failure."""
        return await self.update_task_state(task_id, {
            "status": TaskStatus.FAILED.value,
            "error": error
        })

    async def can_execute_task(self, task_id: str) -> bool:
        """Check if task can be executed based on its current state."""
        task = await self.get_task_state(task_id)
        if not task:
            return False
            
        allowed_statuses = [
            TaskStatus.PENDING.value,
            TaskStatus.FAILED.value,
            TaskStatus.ERROR.value
        ]
        
        return task["status"].lower() in [s.lower() for s in allowed_statuses]

    async def verify_task_completion(self, task_id: str) -> bool:
        """Verify task is marked as completed."""
        task = await self.get_task_state(task_id)
        if not task:
            return False
            
        return task["status"] == TaskStatus.COMPLETED.value

