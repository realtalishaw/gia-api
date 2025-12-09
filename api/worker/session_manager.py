"""
Agent Session Manager - Routes tasks to appropriate execution environment
(Celery for local agents, Fly machines for remote agents)

IMPORTANT: Sessions are PERMANENT records in Supabase. They are never deleted,
only updated with status changes. This provides a complete audit trail of all
agent executions.
"""
import logging
import sys
import os
from typing import Dict, Any, Optional, Literal
from datetime import datetime

# Add the api directory to Python path to ensure imports work
# This is needed because this module might be imported from different contexts
api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from agents import get_agent
from agents.models import AgentDefinition

logger = logging.getLogger(__name__)

# Global Supabase client (initialized lazily)
_supabase_client = None


def _init_supabase():
    """Initialize Supabase client if credentials are available"""
    global _supabase_client
    
    if _supabase_client is not None:
        logger.debug("Session Manager: Using existing Supabase client")
        return _supabase_client
    
    logger.info("Session Manager: Initializing Supabase client...")
    
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        # Prefer service role key for server-side operations (bypasses RLS)
        # Fall back to anon key if service role is not available
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        logger.info(
            f"Session Manager: Environment check - "
            f"SUPABASE_URL={'✅ set' if supabase_url else '❌ not set'}, "
            f"SUPABASE_SERVICE_ROLE_KEY={'✅ set' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else '❌ not set'}, "
            f"SUPABASE_ANON_KEY={'✅ set' if os.getenv('SUPABASE_ANON_KEY') else '❌ not set'}"
        )
        
        if supabase_url and supabase_key:
            from supabase import create_client, Client
            _supabase_client = create_client(supabase_url, supabase_key)
            key_type = "service role" if os.getenv("SUPABASE_SERVICE_ROLE_KEY") else "anon"
            logger.info(
                f"✅ Session Manager: Supabase client initialized successfully "
                f"({key_type} key, URL: {supabase_url[:30]}...)"
            )
        else:
            _supabase_client = None
            if not supabase_url:
                logger.warning("⚠️ Session Manager: SUPABASE_URL not found in environment")
            if not supabase_key:
                logger.warning(
                    "⚠️ Session Manager: SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY not found in environment"
                )
    except ImportError:
        # Supabase client not installed, continue without it
        logger.error("❌ Session Manager: Supabase Python client not installed. Run: pip install supabase")
        _supabase_client = None
    except Exception as e:
        # Log error but continue without Supabase
        logger.error(f"❌ Session Manager: Could not initialize Supabase client: {e}", exc_info=True)
        _supabase_client = None
    
    return _supabase_client


class AgentSessionManager:
    """
    Manages agent execution sessions and routes tasks to appropriate workers.
    
    Responsibilities:
    - Detect agent type (local vs remote)
    - Route local agents to Celery workers
    - Route remote agents to Fly machines (TODO: implement Fly machine management)
    - Track active sessions (project_id + agent_name + task_id)
    """
    
    def __init__(self):
        """Initialize the session manager"""
        # TODO: Add session tracking storage (database or in-memory cache)
        # This will track active sessions: {session_key: {project_id, agent_name, task_id, worker_id, status}}
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
    
    def route_agent_task(
        self,
        project_id: str,
        agent_name: str,
        task_id: str,
        context: str
    ) -> Dict[str, Any]:
        """
        Route an agent task to the appropriate execution environment.
        
        Args:
            project_id: The project ID
            agent_name: The name of the agent
            task_id: The Celery task ID
            context: The task context
            
        Returns:
            Dictionary with routing information:
            {
                "execution_type": "local" | "remote",
                "route_to": "celery" | "fly_machine",
                "session_key": str,
                "fly_machine_id": Optional[str],  # Only for remote agents
                "message": str
            }
        """
        logger.info(
            f"🔀 Session Manager: Routing task - project_id={project_id}, "
            f"agent_name={agent_name}, task_id={task_id}"
        )
        
        # Get agent definition to check execution type
        agent_definition = get_agent(agent_name)
        if not agent_definition:
            logger.error(f"❌ Session Manager: Agent '{agent_name}' not found in registry")
            raise ValueError(f"Agent '{agent_name}' not found in registry")
        
        logger.info(
            f"📋 Session Manager: Agent definition found - "
            f"name={agent_definition.name}, execution_type={agent_definition.execution_type}"
        )
        
        # Create session key for tracking
        session_key = f"{project_id}:{agent_name}:{task_id}"
        logger.info(f"🔑 Session Manager: Created session_key={session_key}")
        
        # Route based on execution type
        logger.info(
            f"🎯 Session Manager: Routing based on execution_type={agent_definition.execution_type}"
        )
        
        if agent_definition.execution_type == "local":
            logger.info(f"📍 Session Manager: Routing to Celery (local agent)")
            return self._route_to_celery(
                project_id=project_id,
                agent_name=agent_name,
                task_id=task_id,
                context=context,
                session_key=session_key,
                agent_definition=agent_definition
            )
        elif agent_definition.execution_type == "remote":
            logger.info(f"📍 Session Manager: Routing to Fly machine (remote agent)")
            return self._route_to_fly_machine(
                project_id=project_id,
                agent_name=agent_name,
                task_id=task_id,
                context=context,
                session_key=session_key,
                agent_definition=agent_definition
            )
        else:
            logger.error(
                f"❌ Session Manager: Invalid execution_type '{agent_definition.execution_type}' "
                f"for agent '{agent_name}'"
            )
            raise ValueError(
                f"Invalid execution_type '{agent_definition.execution_type}' "
                f"for agent '{agent_name}'. Must be 'local' or 'remote'."
            )
    
    def _route_to_celery(
        self,
        project_id: str,
        agent_name: str,
        task_id: str,
        context: str,
        session_key: str,
        agent_definition: AgentDefinition
    ) -> Dict[str, Any]:
        """
        Route a local agent task to Celery worker.
        
        Args:
            project_id: The project ID
            agent_name: The name of the agent
            task_id: The Celery task ID
            context: The task context
            session_key: Unique session identifier
            agent_definition: The agent definition
            
        Returns:
            Routing information for Celery execution
        """
        logger.info(
            f"Routing local agent '{agent_name}' to Celery worker: "
            f"project_id={project_id}, task_id={task_id}"
        )
        
        routing_info = {
            "execution_type": "local",
            "route_to": "celery",
            "session_key": session_key,
            "fly_machine_id": None,
            "message": f"Local agent '{agent_name}' routed to Celery worker"
        }
        
        # Register session
        self._register_session(
            session_key=session_key,
            project_id=project_id,
            agent_name=agent_name,
            task_id=task_id,
            execution_type="local",
            worker_id="celery",
            status="routed",
            context=context,
            routing_info=routing_info
        )
        
        return routing_info
    
    def _route_to_fly_machine(
        self,
        project_id: str,
        agent_name: str,
        task_id: str,
        context: str,
        session_key: str,
        agent_definition: AgentDefinition
    ) -> Dict[str, Any]:
        """
        Route a remote agent task to Fly machine.
        
        TODO: Implement Fly machine management:
        1. Check if agent already has an active Fly machine (fly_machine_id in agent_definition)
        2. If no active machine, create/start a new Fly machine:
           - Download agent code from S3 (s3_bucket_path)
           - Create Fly machine with agent code
           - Start the machine
           - Update agent_definition.fly_machine_id
        3. Send task to Fly machine via API/HTTP
        4. Track machine lifecycle (start, stop, cleanup)
        5. Handle machine failures and retries
        
        Args:
            project_id: The project ID
            agent_name: The name of the agent
            task_id: The Celery task ID
            context: The task context
            session_key: Unique session identifier
            agent_definition: The agent definition
            
        Returns:
            Routing information for Fly machine execution (placeholder for now)
        """
        logger.info(
            f"Routing remote agent '{agent_name}' to Fly machine: "
            f"project_id={project_id}, task_id={task_id}, "
            f"s3_path={agent_definition.s3_bucket_path}"
        )
        
        # TODO: Check if agent has an active Fly machine
        # existing_machine_id = agent_definition.fly_machine_id
        # if existing_machine_id:
        #     # Check if machine is still running
        #     # If yes, use it; if no, create new one
        
        # TODO: Create/start Fly machine if needed
        # fly_machine_id = self._get_or_create_fly_machine(
        #     agent_name=agent_name,
        #     s3_bucket_path=agent_definition.s3_bucket_path,
        #     project_id=project_id
        # )
        
        # TODO: Send task to Fly machine
        # self._send_task_to_fly_machine(
        #     fly_machine_id=fly_machine_id,
        #     project_id=project_id,
        #     agent_name=agent_name,
        #     task_id=task_id,
        #     context=context
        # )
        
        # Placeholder: Return a string indicating Fly machine routing
        fly_machine_id = f"fly_machine_{agent_name}_{project_id}"  # Placeholder
        
        routing_info = {
            "execution_type": "remote",
            "route_to": "fly_machine",
            "session_key": session_key,
            "fly_machine_id": fly_machine_id,
            "message": f"Remote agent '{agent_name}' routed to Fly machine (placeholder: {fly_machine_id})"
        }
        
        # Register session
        self._register_session(
            session_key=session_key,
            project_id=project_id,
            agent_name=agent_name,
            task_id=task_id,
            execution_type="remote",
            worker_id=fly_machine_id,
            status="routed",
            context=context,
            routing_info=routing_info,
            fly_machine_id=fly_machine_id
        )
        
        return routing_info
    
    def _register_session(
        self,
        session_key: str,
        project_id: str,
        agent_name: str,
        task_id: str,
        execution_type: str,
        worker_id: str,
        status: str,
        context: Optional[str] = None,
        routing_info: Optional[Dict[str, Any]] = None,
        fly_machine_id: Optional[str] = None
    ) -> None:
        """
        Register a new agent session in both memory and database.
        
        Args:
            session_key: Unique session identifier
            project_id: The project ID
            agent_name: The name of the agent
            task_id: The task ID
            execution_type: "local" or "remote"
            worker_id: ID of the worker (Celery or Fly machine)
            status: Session status
            context: Optional task context
            routing_info: Optional routing information
            fly_machine_id: Optional Fly machine ID
        """
        logger.info(
            f"💾 Session Manager: Registering session - session_key={session_key}, "
            f"project_id={project_id}, agent_name={agent_name}, "
            f"execution_type={execution_type}, status={status}"
        )
        
        # Store in memory for quick access
        self._active_sessions[session_key] = {
            "project_id": project_id,
            "agent_name": agent_name,
            "task_id": task_id,
            "execution_type": execution_type,
            "worker_id": worker_id,
            "status": status,
            "created_at": datetime.utcnow().isoformat(),
        }
        logger.info(f"✅ Session Manager: Session stored in memory: {session_key}")
        
        # Save to database for persistence and real-time updates
        # NOTE: Sessions are permanent records - they are never deleted, only updated
        logger.info(f"💾 Session Manager: Attempting to save session to database: {session_key}")
        client = _init_supabase()
        
        if client:
            logger.info(f"✅ Session Manager: Supabase client initialized, proceeding with database insert")
            try:
                data = {
                    "session_key": session_key,
                    "project_id": project_id,
                    "agent_name": agent_name,
                    "task_id": task_id,
                    "execution_type": execution_type,
                    "worker_id": worker_id,
                    "status": status,
                }
                
                if context:
                    data["context"] = context
                    logger.debug(f"📝 Session Manager: Including context (length={len(context)})")
                if routing_info:
                    data["routing_info"] = routing_info
                    logger.debug(f"📝 Session Manager: Including routing_info")
                if fly_machine_id:
                    data["fly_machine_id"] = fly_machine_id
                    logger.debug(f"📝 Session Manager: Including fly_machine_id={fly_machine_id}")
                
                logger.info(f"💾 Session Manager: Inserting session data: {list(data.keys())}")
                response = client.table("agent_sessions").insert(data).execute()
                
                if response.data and len(response.data) > 0:
                    logger.info(
                        f"✅ Session Manager: Session successfully registered in database: {session_key}. "
                        f"Database ID: {response.data[0].get('id', 'unknown')}"
                    )
                else:
                    logger.warning(
                        f"⚠️ Session Manager: Session insert returned no data: {session_key}. "
                        f"Response: {response}"
                    )
            except Exception as e:
                logger.error(
                    f"❌ Session Manager: Failed to register session in database: {session_key}: {e}",
                    exc_info=True
                )
                # Continue with in-memory storage even if database save fails
        else:
            logger.warning(
                f"⚠️ Session Manager: Supabase client not initialized. "
                f"Session registered in memory only: {session_key}"
            )
        
        logger.info(f"✅ Session Manager: Session registration complete: {session_key}")
    
    def get_session(self, session_key: str) -> Optional[Dict[str, Any]]:
        """
        Get session information by session key.
        Checks memory first, then database.
        
        Args:
            session_key: Unique session identifier
            
        Returns:
            Session information or None if not found
        """
        # Check memory first
        if session_key in self._active_sessions:
            return self._active_sessions[session_key]
        
        # Check database
        client = _init_supabase()
        if client:
            try:
                response = client.table("agent_sessions").select("*").eq("session_key", session_key).execute()
                if response.data and len(response.data) > 0:
                    session_data = response.data[0]
                    # Convert to dict format matching in-memory structure
                    return {
                        "project_id": session_data.get("project_id"),
                        "agent_name": session_data.get("agent_name"),
                        "task_id": session_data.get("task_id"),
                        "execution_type": session_data.get("execution_type"),
                        "worker_id": session_data.get("worker_id"),
                        "status": session_data.get("status"),
                        "created_at": session_data.get("created_at"),
                    }
            except Exception as e:
                logger.error(f"❌ Failed to get session from database: {session_key}: {e}", exc_info=True)
        
        return None
    
    def update_session_status(
        self,
        session_key: str,
        status: str,
        **kwargs
    ) -> bool:
        """
        Update session status and optional fields in both memory and database.
        NOTE: Sessions are permanent records - updates never delete them, only modify status/fields.
        
        Args:
            session_key: Unique session identifier
            status: New status
            **kwargs: Additional fields to update (e.g., fly_machine_id, routing_info)
            
        Returns:
            True if session was updated, False if not found
        """
        logger.info(
            f"🔄 Session Manager: Updating session status - session_key={session_key}, "
            f"status={status}, kwargs={list(kwargs.keys()) if kwargs else []}"
        )
        
        # Update in memory
        if session_key in self._active_sessions:
            self._active_sessions[session_key]["status"] = status
            self._active_sessions[session_key].update(kwargs)
            logger.info(f"✅ Session Manager: Updated session in memory: {session_key}")
        else:
            logger.warning(f"⚠️ Session Manager: Session not found in memory: {session_key}")
        
        # Update in database (sessions are permanent - never deleted, only updated)
        logger.info(f"💾 Session Manager: Attempting to update session in database: {session_key}")
        client = _init_supabase()
        
        if client:
            logger.info(f"✅ Session Manager: Supabase client initialized, proceeding with database update")
            try:
                data = {"status": status, **kwargs}
                
                # Set completed_at if status is completed or failed
                if status in ("completed", "failed"):
                    data["completed_at"] = datetime.utcnow().isoformat()
                    logger.info(f"📅 Session Manager: Setting completed_at timestamp for status={status}")
                
                logger.info(f"💾 Session Manager: Updating session with data: {list(data.keys())}")
                response = client.table("agent_sessions").update(data).eq("session_key", session_key).execute()
                
                if response.data and len(response.data) > 0:
                    logger.info(
                        f"✅ Session Manager: Session successfully updated in database: {session_key}: "
                        f"status={status}. Updated rows: {len(response.data)}"
                    )
                    return True
                else:
                    logger.warning(
                        f"⚠️ Session Manager: Session update returned no data: {session_key}. "
                        f"This might mean the session doesn't exist in the database yet. Response: {response}"
                    )
                    # Session might not exist in database yet - this is okay, it will be created on next insert
                    return False
            except Exception as e:
                logger.error(
                    f"❌ Session Manager: Failed to update session in database: {session_key}: {e}",
                    exc_info=True
                )
                return False
        else:
            logger.warning(
                f"⚠️ Session Manager: Supabase client not initialized. "
                f"Session updated in memory only: {session_key}"
            )
            return session_key in self._active_sessions
        
        logger.info(f"✅ Session Manager: Session update complete: {session_key}: status={status}")
        return True
    
    def get_active_sessions_for_project(
        self,
        project_id: str
    ) -> list[Dict[str, Any]]:
        """
        Get all active sessions for a project from database.
        
        Args:
            project_id: The project ID
            
        Returns:
            List of session dictionaries
        """
        client = _init_supabase()
        if client:
            try:
                response = client.table("agent_sessions").select("*").eq("project_id", project_id).order("created_at", desc=True).execute()
                if response.data:
                    return response.data
            except Exception as e:
                logger.error(f"❌ Failed to get sessions for project from database: {project_id}: {e}", exc_info=True)
        
        # Fallback to in-memory
        return [
            session
            for session_key, session in self._active_sessions.items()
            if session.get("project_id") == project_id
        ]
    
    def get_active_sessions_for_agent(
        self,
        agent_name: str
    ) -> list[Dict[str, Any]]:
        """
        Get all active sessions for an agent from database.
        
        Args:
            agent_name: The agent name
            
        Returns:
            List of session dictionaries
        """
        client = _init_supabase()
        if client:
            try:
                response = client.table("agent_sessions").select("*").eq("agent_name", agent_name).order("created_at", desc=True).execute()
                if response.data:
                    return response.data
            except Exception as e:
                logger.error(f"❌ Failed to get sessions for agent from database: {agent_name}: {e}", exc_info=True)
        
        # Fallback to in-memory
        return [
            session
            for session_key, session in self._active_sessions.items()
            if session.get("agent_name") == agent_name
        ]


# Global session manager instance
_session_manager = AgentSessionManager()


def get_session_manager() -> AgentSessionManager:
    """Get the global session manager instance"""
    return _session_manager
