"""
Phase configuration for Buildbox autonomous MVP builder.

Defines the phases, tasks, and agent assignments for the build process.
Adapted from spark-api's workflow_config.py structure.
"""
from typing import Dict, List, Optional
from enum import Enum


class Phase(str, Enum):
    """Buildbox phases for MVP development."""
    DISCOVERY = "discovery"  # Phase 0: Research, Brand, PRD
    ARCHITECTURE = "architecture"  # Phase 1: System design, file structure
    DEVELOPMENT = "development"  # Phase 2-5: Feature implementation
    QA = "qa"  # Phase 4: Testing and validation
    DEPLOYMENT = "deployment"  # Phase 6: Deploy and marketing


class PhaseConfig:
    """Configuration for Buildbox phases and tasks."""
    
    # Tasks that require approval before proceeding
    APPROVAL_REQUIRED_TASKS = [
        "write_prd",  # PRD needs user approval
        "design_architecture",  # Architecture needs approval
    ]
    
    # Phase definitions with their tasks and agent assignments
    PHASES = [
        {
            "order": 0,
            "name": "Discovery & Strategy",
            "designation": Phase.DISCOVERY.value,
            "queue": "discovery_tasks",
            "tasks": [
                {
                    "type": "research_market",
                    "agent": "researcher",
                    "description": "Analyze market and competitors"
                },
                {
                    "type": "generate_brand",
                    "agent": "brand_strategist",
                    "description": "Create brand identity and logo"
                },
                {
                    "type": "write_prd",
                    "agent": "planner",
                    "description": "Create Product Requirements Document"
                }
            ],
            "deliverables": ["market_analysis", "brand_kit", "prd"]
        },
        {
            "order": 1,
            "name": "Architecture & Planning",
            "designation": Phase.ARCHITECTURE.value,
            "queue": "build_tasks",
            "tasks": [
                {
                    "type": "design_architecture",
                    "agent": "architect",
                    "description": "Design system architecture and file structure"
                }
            ],
            "deliverables": ["file_structure", "schema", "architecture_doc"]
        },
        {
            "order": 2,
            "name": "Development",
            "designation": Phase.DEVELOPMENT.value,
            "queue": "agent_execution",
            "tasks": [
                {
                    "type": "setup_repo",
                    "agent": "devops",
                    "description": "Initialize git repository"
                },
                {
                    "type": "implement_feature",
                    "agent": "developer",
                    "description": "Implement features from PRD"
                }
            ],
            "deliverables": ["source_code", "git_repo"]
        },
        {
            "order": 3,
            "name": "QA & Testing",
            "designation": Phase.QA.value,
            "queue": "agent_execution",
            "tasks": [
                {
                    "type": "run_qa",
                    "agent": "qa",
                    "description": "Run tests and validation"
                }
            ],
            "deliverables": ["test_report", "qa_results"]
        },
        {
            "order": 4,
            "name": "Deployment & Launch",
            "designation": Phase.DEPLOYMENT.value,
            "queue": "deployment_tasks",
            "tasks": [
                {
                    "type": "deploy_app",
                    "agent": "devops",
                    "description": "Deploy application to production"
                },
                {
                    "type": "generate_marketing",
                    "agent": "marketer",
                    "description": "Generate marketing materials"
                }
            ],
            "deliverables": ["deployment_url", "marketing_assets"]
        }
    ]
    
    @classmethod
    def get_agent_for_task(cls, task_type: str) -> str:
        """Get the agent type for a given task type."""
        task_type = task_type.lower()
        for phase in cls.PHASES:
            for task in phase["tasks"]:
                if task["type"].lower() == task_type:
                    return task["agent"]
        raise ValueError(f"Unknown task type: {task_type}")
    
    @classmethod
    def get_phase_designation(cls, task_type: str) -> str:
        """Get the phase designation for a task type."""
        task_type = task_type.lower()
        for phase in cls.PHASES:
            for task in phase["tasks"]:
                if task["type"].lower() == task_type:
                    return phase["designation"]
        raise ValueError(f"Unknown task type: {task_type}")
    
    @classmethod
    def get_queue_for_task(cls, task_type: str) -> str:
        """Get the RabbitMQ queue name for a task type."""
        task_type = task_type.lower()
        for phase in cls.PHASES:
            for task in phase["tasks"]:
                if task["type"].lower() == task_type:
                    return phase["queue"]
        raise ValueError(f"Unknown task type: {task_type}")
    
    @classmethod
    def get_next_phase(cls, current_phase: str) -> Optional[str]:
        """Get the next phase after the current phase."""
        for phase in cls.PHASES:
            if phase["designation"] == current_phase:
                next_order = phase["order"] + 1
                next_phase = next(
                    (p for p in cls.PHASES if p["order"] == next_order),
                    None
                )
                return next_phase["designation"] if next_phase else None
        return None
    
    @classmethod
    def get_required_tasks(cls, phase: str) -> List[Dict]:
        """Get required tasks for a phase."""
        for p in cls.PHASES:
            if p["designation"] == phase:
                return p["tasks"]
        return []
    
    @classmethod
    def requires_approval(cls, task_type: str) -> bool:
        """Check if a task type requires approval."""
        return task_type.lower() in [t.lower() for t in cls.APPROVAL_REQUIRED_TASKS]
    
    @classmethod
    def get_next_task(cls, current_task: str) -> Optional[str]:
        """Get the next task in the phase sequence."""
        current_task = current_task.lower()
        for phase in cls.PHASES:
            tasks = [t["type"].lower() for t in phase["tasks"]]
            if current_task in tasks:
                task_index = tasks.index(current_task)
                if task_index < len(tasks) - 1:
                    # Next task in the same phase
                    return phase["tasks"][task_index + 1]["type"]
                else:
                    # First task of the next phase
                    next_phase = cls.get_next_phase(phase["designation"])
                    if next_phase:
                        next_phase_tasks = cls.get_required_tasks(next_phase)
                        if next_phase_tasks:
                            return next_phase_tasks[0]["type"]
        return None
    
    @classmethod
    def is_final_task_in_phase(cls, task_type: str, phase: str) -> bool:
        """Check if a task is the final task in its phase."""
        tasks = cls.get_required_tasks(phase)
        if not tasks:
            return False
        return tasks[-1]["type"].lower() == task_type.lower()
    
    @classmethod
    def get_deliverables(cls, phase_designation: str) -> List[str]:
        """Get the deliverables for a given phase designation."""
        for phase in cls.PHASES:
            if phase["designation"] == phase_designation:
                return phase["deliverables"]
        return []

