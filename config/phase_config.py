"""
Phase configuration for Buildbox autonomous MVP builder.

Defines the phases, tasks, and agent assignments for the build process.
Adapted from spark-api's workflow_config.py structure.
"""
from typing import Dict, List, Optional
from enum import Enum


class Phase(str, Enum):
    """Buildbox phases for MVP development (SOP/Checklist approach)."""
    DISCOVERY = "discovery"  # Phase 0: Market research, Brand identity, PRD
    DESIGN = "design"  # Phase 1: UI/UX mockups (all screens/pages)
    DEVELOPMENT = "development"  # Phase 2: Build MVP
    MARKETING_SETUP = "marketing_setup"  # Phase 3: Email, Analytics, finishing touches
    DEPLOYMENT = "deployment"  # Phase 4: Deploy and handoff


class PhaseConfig:
    """Configuration for Buildbox phases and tasks."""
    
    # Tasks that require approval before proceeding
    APPROVAL_REQUIRED_TASKS = [
        "create_brand_identity",  # Brand kit needs user approval
        "write_prd",  # PRD needs user approval
        "create_ui_ux_mockups",  # Design mockups need user approval
    ]
    
    # Phase definitions with their tasks and agent assignments
    # These are the "checklist items" - agents have autonomy in HOW to complete them
    PHASES = [
        {
            "order": 0,
            "name": "Discovery",
            "designation": Phase.DISCOVERY.value,
            "queue": "discovery_tasks",
            "is_deterministic": True,  # Follows system prompt/SOP
            "tasks": [
                {
                    "type": "conduct_market_research",
                    "agent": "researcher",
                    "description": "Conduct market research and competitor analysis"
                },
                {
                    "type": "create_brand_identity",
                    "agent": "brand_strategist",
                    "description": "Create brand identity (logo, colors, fonts, favicons)"
                },
                {
                    "type": "write_prd",
                    "agent": "planner",
                    "description": "Create Product Requirements Document"
                }
            ],
            "deliverables": ["market_analysis", "brand_kit", "prd"],
            "input_dependencies": [],  # No dependencies
            "output_required_for": [Phase.DESIGN.value]  # Design phase needs these
        },
        {
            "order": 1,
            "name": "Design",
            "designation": Phase.DESIGN.value,
            "queue": "build_tasks",
            "is_deterministic": True,  # Follows system prompt/SOP
            "tasks": [
                {
                    "type": "create_ui_ux_mockups",
                    "agent": "designer",
                    "description": "Create UI/UX design mockups for all screens and pages"
                }
            ],
            "deliverables": ["design_mockups", "design_system"],
            "input_dependencies": ["create_brand_identity", "write_prd"],  # Needs approved brand + PRD
            "output_required_for": [Phase.DEVELOPMENT.value]  # Development needs designs
        },
        {
            "order": 2,
            "name": "Development",
            "designation": Phase.DEVELOPMENT.value,
            "queue": "agent_execution",
            "is_deterministic": False,  # Agent creates subtasks probabilistically
            "tasks": [
                {
                    "type": "build_mvp",
                    "agent": "developer",
                    "description": "Build the MVP based on PRD and designs"
                }
            ],
            "deliverables": ["source_code", "git_repo", "working_mvp"],
            "input_dependencies": ["create_ui_ux_mockups", "write_prd"],  # Needs approved designs + PRD
            "output_required_for": [Phase.MARKETING_SETUP.value]  # Marketing needs completed MVP
        },
        {
            "order": 3,
            "name": "Marketing & Setup",
            "designation": Phase.MARKETING_SETUP.value,
            "queue": "agent_execution",
            "is_deterministic": True,  # Follows system prompt/SOP
            "tasks": [
                {
                    "type": "setup_email",
                    "agent": "devops",
                    "description": "Set up email infrastructure"
                },
                {
                    "type": "setup_analytics",
                    "agent": "devops",
                    "description": "Set up analytics tracking"
                },
                {
                    "type": "finalize_finishing_touches",
                    "agent": "marketer",
                    "description": "Complete finishing touches and polish"
                }
            ],
            "deliverables": ["email_setup", "analytics_setup", "polished_mvp"],
            "input_dependencies": ["build_mvp"],  # Needs completed MVP
            "output_required_for": [Phase.DEPLOYMENT.value]  # Deployment needs these
        },
        {
            "order": 4,
            "name": "Deployment & Handoff",
            "designation": Phase.DEPLOYMENT.value,
            "queue": "deployment_tasks",
            "is_deterministic": True,  # Follows system prompt/SOP
            "tasks": [
                {
                    "type": "deploy_app",
                    "agent": "devops",
                    "description": "Deploy application to production"
                },
                {
                    "type": "prepare_handoff",
                    "agent": "devops",
                    "description": "Prepare project for handoff (documentation, access, etc.)"
                }
            ],
            "deliverables": ["deployment_url", "handoff_documentation"],
            "input_dependencies": ["finalize_finishing_touches"],  # Needs marketing setup complete
            "output_required_for": []  # Final phase
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
    
    @classmethod
    def is_phase_deterministic(cls, phase_designation: str) -> bool:
        """Check if a phase is deterministic (follows SOP) or probabilistic (agent creates tasks)."""
        for phase in cls.PHASES:
            if phase["designation"] == phase_designation:
                return phase.get("is_deterministic", True)  # Default to True
        return True
    
    @classmethod
    def get_phase_input_dependencies(cls, phase_designation: str) -> List[str]:
        """Get the task types that must be completed before this phase can start."""
        for phase in cls.PHASES:
            if phase["designation"] == phase_designation:
                return phase.get("input_dependencies", [])
        return []

