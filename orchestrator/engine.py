"""
Agent Orchestrator Engine.

Manages phases, task creation, and workflow progression for Buildbox.
Adapted from spark-api/workflow/workflow_orchestrator.py
"""
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from orchestrator.task_state_manager import TaskStateManager, TaskStatus, ApprovalStatus
from orchestrator.task_queue_manager import TaskQueueManager
from orchestrator.status_updates import StatusUpdateHelper
from config.phase_config import PhaseConfig, Phase


class AgentOrchestrator:
    def __init__(self, supabase_client, rabbitmq_url: Optional[str] = None):
        self.supabase = supabase_client
        self.task_state_manager = TaskStateManager(supabase_client)
        self.task_queue_manager = TaskQueueManager(rabbitmq_url)
        self.status_updates = StatusUpdateHelper(supabase_client)
        self.logger = logging.getLogger(__name__)

    async def initialize_phase(self, project_id: str, phase: str, initial_task_id: str) -> bool:
        """Initialize a new phase."""
        try:
            # Update project status and current_phase
            self.supabase.table('projects').update({
                "current_phase": phase,
                "status": "building",
                "updated_at": datetime.utcnow().isoformat()
            }).eq('id', project_id).execute()

            # Create activity update
            await self.status_updates.create_info(
                project_id=project_id,
                message=f"Initialized {phase} phase",
                task_id=initial_task_id
            )

            return True
        except Exception as e:
            self.logger.error(f"Error initializing phase: {str(e)}")
            return False

    async def transition_to_next_task(self, current_task_id: str, project_id: str, next_task_type: str) -> bool:
        """Transition to the next task in the phase."""
        try:
            # Queue next task
            return await self.task_queue_manager.queue_next_task(
                task_id=current_task_id,
                project_id=project_id,
                task_type=next_task_type
            )
        except Exception as e:
            self.logger.error(f"Error transitioning to next task: {str(e)}")
            return False

    async def handle_task_failure(self, task_id: str, project_id: str, error_message: str) -> Tuple[bool, Optional[str]]:
        """Handle task failure."""
        try:
            # Update task status
            if not await self.task_state_manager.handle_task_failure(task_id, error_message):
                return False, "Failed to update task status"

            # Create activity update
            await self.status_updates.create_error(
                project_id=project_id,
                message=f"Task failed: {error_message}",
                task_id=task_id
            )

            return True, None
        except Exception as e:
            self.logger.error(f"Error handling task failure: {str(e)}")
            return False, str(e)

    async def verify_phase_completion(self, project_id: str, phase: str) -> bool:
        """Verify phase completion."""
        try:
            # Check if all tasks in phase are completed
            phase_tasks = PhaseConfig.get_required_tasks(phase)
            task_types = [task["type"] for task in phase_tasks]
            
            tasks = self.supabase.table('tasks') \
                .select("status, type") \
                .eq('project_id', project_id) \
                .in_('type', task_types) \
                .execute()

            if not tasks.data:
                return False

            for task in tasks.data:
                if task['status'] != TaskStatus.COMPLETED.value:
                    return False

            # Create activity update
            await self.status_updates.create_success(
                project_id=project_id,
                message=f"Phase {phase} completed"
            )

            return True
        except Exception as e:
            self.logger.error(f"Error verifying phase completion: {str(e)}")
            return False

    async def check_phase_blockers(self, project_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check for any blockers preventing phase progression.
        Returns (is_blocked, reason).
        """
        try:
            # Check for failed tasks
            failed_tasks = self.supabase.table('tasks') \
                .select("id,type") \
                .eq('project_id', project_id) \
                .in_('status', [TaskStatus.FAILED.value, TaskStatus.ERROR.value]) \
                .execute()
                
            if failed_tasks.data:
                failed_types = [t.get('type', 'unknown') for t in failed_tasks.data]
                return True, f"Failed tasks found: {', '.join(failed_types)}"

            # Check for pending approvals
            pending_approvals = self.supabase.table('tasks') \
                .select("id,type") \
                .eq('project_id', project_id) \
                .eq('status', TaskStatus.PENDING.value) \
                .eq('approval_status', ApprovalStatus.PENDING.value) \
                .execute()
                
            if pending_approvals.data:
                pending_types = [t.get('type', 'unknown') for t in pending_approvals.data]
                return True, f"Tasks awaiting approval: {', '.join(pending_types)}"

            return False, None

        except Exception as e:
            self.logger.error(f"Error checking phase blockers: {str(e)}")
            return False, None

    async def verify_task_creation(self, project_id: str, task_type: str) -> Tuple[bool, Optional[str]]:
        """
        Verify if a task can be created.
        Returns (can_create, reason).
        """
        try:
            # Check for phase blockers
            is_blocked, reason = await self.check_phase_blockers(project_id)
            if is_blocked:
                return False, reason

            # Check for existing tasks of the same type
            existing_tasks = self.supabase.table('tasks') \
                .select("id, status") \
                .eq('project_id', project_id) \
                .eq('type', task_type) \
                .not_.in_('status', ['completed', 'failed', 'error']) \
                .execute()
                
            if existing_tasks.data:
                return False, f"Task of type {task_type} already exists and is not completed"

            return True, None

        except Exception as e:
            self.logger.error(f"Error verifying task creation: {str(e)}")
            return False, f"Error verifying task creation: {str(e)}"

    async def create_progress_update(
        self,
        project_id: str,
        message: str,
        task_id: Optional[str] = None,
        agent_role: Optional[str] = None,
        activity_type: str = "progress"
    ) -> bool:
        """
        Create a progress update (status_update) for internal subtasks.
        
        This is for visibility only - creates an entry in project_activity table
        but does NOT create a task or queue anything.
        
        Use this when an agent is working through internal steps that don't need
        separate execution (e.g., "Looking up competitors..." during market research).
        
        Args:
            project_id: The project UUID
            message: Progress message (e.g., "Looking up competitors...")
            task_id: Optional parent task ID this progress relates to
            agent_role: Optional agent role for context
            activity_type: Type of activity (progress, info, success, error, warning)
        
        Returns:
            bool: True if successful
        """
        try:
            return await self.status_updates.create_activity(
                project_id=project_id,
                message=message,
                agent_role=agent_role,
                activity_type=activity_type,
                task_id=task_id
            )
        except Exception as e:
            self.logger.error(f"Error creating progress update: {str(e)}")
            return False

    async def create_task(
        self,
        project_id: str,
        task_type: str,
        agent_role: Optional[str] = None,
        parent_task_id: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Create a new task and queue it for execution.
        
        This creates a real task that will be executed (either by the same agent
        or a different agent in a different sandbox).
        
        Args:
            project_id: The project UUID
            task_type: Type of task (e.g., "implement_auth", "build_dashboard")
            agent_role: Optional agent role (defaults to config)
            parent_task_id: Optional parent task ID for task hierarchy
        
        Returns:
            Tuple of (success, task_id, error_message)
        """
        try:
            # Verify task can be created
            can_create, reason = await self.verify_task_creation(project_id, task_type)
            if not can_create:
                return False, None, reason

            # Get agent role from config if not provided
            if not agent_role:
                try:
                    agent_role = PhaseConfig.get_agent_for_task(task_type)
                except ValueError:
                    # Task type not in config - this is okay for agent-created subtasks
                    # Use a default or require agent_role to be provided
                    if not agent_role:
                        agent_role = "developer"  # Default fallback

            # Create task
            task_data = {
                "project_id": project_id,
                "type": task_type,
                "status": TaskStatus.PENDING.value,
                "agent_role": agent_role,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Add parent_task_id if provided (for task hierarchy)
            if parent_task_id:
                task_data["parent_task_id"] = parent_task_id

            task = self.supabase.table('tasks').insert(task_data).execute()

            if not task.data:
                return False, None, "Failed to create task"

            task_id = task.data[0]['id']

            # Queue task for execution
            if not await self.task_queue_manager.queue_task_execution(task_id, project_id, task_type):
                return False, task_id, "Failed to queue task"

            return True, task_id, None

        except Exception as e:
            self.logger.error(f"Error creating task: {str(e)}")
            return False, None, f"Error creating task: {str(e)}"

    async def handle_task_completion(self, task_id: str, project_id: str, task_type: str) -> Tuple[bool, Optional[str]]:
        """
        Handle task completion and phase progression.
        Returns (success, error_message).
        """
        try:
            # Get current phase
            phase_designation = PhaseConfig.get_phase_designation(task_type)
            
            # Check if task requires approval
            if PhaseConfig.requires_approval(task_type):
                # Update task status to pending for approval
                result_data = {}  # Will be populated by agent execution
                if not await self.task_state_manager.set_task_pending_approval(task_id, result_data):
                    return False, "Failed to update task status for approval"
                
                # Create activity update
                await self.status_updates.create_info(
                    project_id=project_id,
                    message=f"Task {task_type} is pending approval",
                    task_id=task_id
                )
                return True, None

            # If task doesn't require approval, mark it as completed
            if not await self.task_state_manager.mark_task_completed(task_id):
                return False, "Failed to mark task as completed"

            # Get next task in sequence
            next_task_type = PhaseConfig.get_next_task(task_type)
            if next_task_type:
                # Create and queue next task
                success, new_task_id, error = await self.create_task(project_id, next_task_type)
                if not success:
                    return False, f"Failed to create next task: {error}"

            # If this was the final task in the phase, handle phase completion
            if PhaseConfig.is_final_task_in_phase(task_type, phase_designation):
                await self.handle_phase_completion(project_id, phase_designation)

            return True, None

        except Exception as e:
            self.logger.error(f"Error handling task completion: {str(e)}")
            return False, f"Error handling task completion: {str(e)}"

    async def handle_phase_completion(self, project_id: str, current_phase: str) -> Tuple[bool, Optional[str]]:
        """
        Handle phase completion and transition.
        Returns (success, error_message).
        """
        try:
            # Verify all tasks in current phase are completed
            phase_tasks = PhaseConfig.get_required_tasks(current_phase)
            task_types = [task["type"] for task in phase_tasks]
            
            for task_type in task_types:
                task = self.supabase.table('tasks') \
                    .select("status") \
                    .eq('project_id', project_id) \
                    .eq('type', task_type) \
                    .order('created_at', desc=True) \
                    .limit(1) \
                    .execute()
                    
                if not task.data or task.data[0]['status'] != TaskStatus.COMPLETED.value:
                    return False, f"Task {task_type} is not completed"

            # Get next phase
            next_phase = PhaseConfig.get_next_phase(current_phase)
            if next_phase:
                # Generate next phase prompt (autonomous)
                next_prompt = await self.generate_next_prompt(project_id, current_phase, next_phase)
                
                # Initialize next phase
                next_phase_tasks = PhaseConfig.get_required_tasks(next_phase)
                if next_phase_tasks:
                    success, task_id, error = await self.create_task(project_id, next_phase_tasks[0]["type"])
                    if not success:
                        return False, f"Failed to create first task of next phase: {error}"
                    
                    await self.initialize_phase(project_id, next_phase, task_id)
            else:
                # All phases complete
                self.supabase.table('projects').update({
                    "status": "completed",
                    "updated_at": datetime.utcnow().isoformat()
                }).eq('id', project_id).execute()
                
                await self.status_updates.create_success(
                    project_id=project_id,
                    message="All phases completed! MVP is ready."
                )

            return True, None

        except Exception as e:
            self.logger.error(f"Error handling phase completion: {str(e)}")
            return False, f"Error handling phase completion: {str(e)}"

    async def handle_task_approval(self, task_id: str, project_id: str, approved: bool, feedback: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Handle task approval or rejection.
        Returns (success, error_message).
        """
        try:
            # Get task details
            task = await self.task_state_manager.get_task_state(task_id)
            if not task:
                return False, "Task not found"

            task_type = task['type']

            if approved:
                # Mark task as completed
                if not await self.task_state_manager.mark_task_completed(task_id):
                    return False, "Failed to mark task as completed"

                # Get next task in sequence
                next_task_type = PhaseConfig.get_next_task(task_type)
                if next_task_type:
                    # Create and queue next task
                    success, new_task_id, error = await self.create_task(project_id, next_task_type)
                    if not success:
                        return False, f"Failed to create next task: {error}"

                # If this was the final task in the phase, handle phase completion
                phase_designation = PhaseConfig.get_phase_designation(task_type)
                if PhaseConfig.is_final_task_in_phase(task_type, phase_designation):
                    await self.handle_phase_completion(project_id, phase_designation)

            else:
                # Queue task for retry with feedback
                if not await self.task_queue_manager.queue_task_retry(task_id, project_id, task_type, feedback or ""):
                    return False, "Failed to queue task for retry"

            return True, None

        except Exception as e:
            self.logger.error(f"Error handling task approval: {str(e)}")
            return False, f"Error handling task approval: {str(e)}"

    async def generate_next_prompt(self, project_id: str, completed_phase: str, next_phase: str) -> str:
        """
        Generate the next phase prompt autonomously.
        
        This will use an LLM in the future to generate prompts based on:
        - Completed phase outputs
        - Project goal
        - Next phase objectives
        
        For now, returns a placeholder prompt.
        """
        # TODO: Implement LLM-based prompt generation
        # This will analyze completed phase outputs and generate
        # specific instructions for the next phase agents
        
        prompt = f"""
        Phase {completed_phase} has been completed successfully.
        Proceeding to {next_phase} phase.
        
        Based on the work completed so far, execute the {next_phase} phase
        following the project requirements and architecture.
        """
        
        self.logger.info(f"Generated next prompt for phase {next_phase}: {prompt}")
        return prompt

