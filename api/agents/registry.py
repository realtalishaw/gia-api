"""Agent Registry - Manages agent registration and synchronization with Supabase"""
import os
from typing import Dict, Optional, List
from .models import AgentDefinition


class AgentRegistry:
    """Registry for managing agent definitions with Supabase sync"""
    
    def __init__(self):
        self._agents: Dict[str, AgentDefinition] = {}
        self._supabase_client = None
        self._init_supabase()
    
    def _init_supabase(self):
        """Initialize Supabase client if credentials are available"""
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            # Prefer service role key for server-side operations (bypasses RLS)
            # Fall back to anon key if service role is not available
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
            
            if supabase_url and supabase_key:
                from supabase import create_client, Client
                self._supabase_client: Optional[Client] = create_client(supabase_url, supabase_key)
                key_type = "service role" if os.getenv("SUPABASE_SERVICE_ROLE_KEY") else "anon"
                print(f"✓ Supabase client initialized successfully ({key_type} key)")
            else:
                self._supabase_client = None
                if not supabase_url:
                    print(f"⚠ SUPABASE_URL not found in environment")
                if not supabase_key:
                    if not os.getenv("SUPABASE_SERVICE_ROLE_KEY") and not os.getenv("SUPABASE_ANON_KEY"):
                        print(f"⚠ SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY not found in environment")
                    elif not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
                        print(f"⚠ SUPABASE_SERVICE_ROLE_KEY not found - using anon key (may have RLS restrictions)")
        except ImportError:
            # Supabase client not installed, continue without it
            print(f"⚠ Supabase Python client not installed. Run: pip install supabase")
            self._supabase_client = None
        except Exception as e:
            # Log error but continue without Supabase
            print(f"⚠ Warning: Could not initialize Supabase client: {e}")
            self._supabase_client = None
    
    def reinitialize_supabase(self):
        """Reinitialize Supabase client - useful if env vars were loaded after registry creation"""
        print("🔄 Reinitializing Supabase client...")
        self._init_supabase()
        if self._supabase_client:
            print("✓ Supabase client reinitialized successfully")
        else:
            print("⚠ Supabase client still not initialized after reinitialize")
    
    def register_agent(self, agent: AgentDefinition) -> bool:
        """
        Register a new agent or update an existing one.
        Ensures agent name is unique.
        
        Args:
            agent: AgentDefinition to register
            
        Returns:
            bool: True if registration was successful
            
        Raises:
            ValueError: If agent name is not unique
        """
        # Validate agent name is not empty
        if not agent.name or not agent.name.strip():
            raise ValueError("Agent name cannot be empty")
        
        # Normalize name (lowercase, no spaces) for uniqueness check
        normalized_name = agent.name.lower().strip()
        
        # Check if agent with this name already exists in registry (case-insensitive)
        for existing_name, existing_agent in self._agents.items():
            if existing_name.lower() == normalized_name and existing_name != agent.name:
                raise ValueError(f"Agent name '{agent.name}' conflicts with existing agent '{existing_name}' (names must be unique)")
        
        self._agents[agent.name] = agent
        
        # Sync with Supabase
        if self._supabase_client:
            try:
                self._sync_to_supabase(agent)
            except Exception as e:
                print(f"Warning: Failed to sync agent {agent.name} to Supabase: {e}")
        
        return True
    
    def get_agent(self, name: str) -> Optional[AgentDefinition]:
        """
        Get an agent definition by name.
        
        Args:
            name: Agent name
            
        Returns:
            AgentDefinition or None if not found
        """
        return self._agents.get(name)
    
    def get_all_agents(self) -> List[AgentDefinition]:
        """
        Get all registered agents.
        
        Returns:
            List of all AgentDefinition objects
        """
        return list(self._agents.values())
    
    def delete_agent(self, name: str) -> bool:
        """
        Delete an agent from the registry.
        
        Args:
            name: Agent name to delete
            
        Returns:
            bool: True if agent was deleted, False if not found
        """
        if name not in self._agents:
            return False
        
        del self._agents[name]
        
        # Sync deletion with Supabase
        if self._supabase_client:
            try:
                self._delete_from_supabase(name)
            except Exception as e:
                print(f"Warning: Failed to delete agent {name} from Supabase: {e}")
        
        return True
    
    def update_agent(self, name: str, agent: AgentDefinition) -> bool:
        """
        Update an existing agent definition.
        
        Args:
            name: Current agent name (must match agent.name if renaming)
            agent: Updated AgentDefinition
            
        Returns:
            bool: True if update was successful
        """
        if name not in self._agents:
            return False
        
        # If name changed, delete old entry
        if name != agent.name:
            del self._agents[name]
        
        self._agents[agent.name] = agent
        
        # Sync with Supabase
        if self._supabase_client:
            try:
                # Delete old entry if name changed
                if name != agent.name:
                    self._delete_from_supabase(name)
                self._sync_to_supabase(agent)
            except Exception as e:
                print(f"Warning: Failed to sync agent update to Supabase: {e}")
        
        return True
    
    def _sync_to_supabase(self, agent: AgentDefinition):
        """
        Sync agent definition to Supabase.
        Strategy: Check if exists first, then create or update only if changed.
        This avoids the need for unique constraints and prevents unnecessary updates.
        """
        if not self._supabase_client:
            return
        
        data = {
            "name": agent.name,
            "role": agent.role,
            "description": agent.description,
            "goal": agent.goal,
            "requirements": agent.requirements,
            "artifacts": agent.artifacts,
            "requires_approval": agent.requires_approval,
        }
        
        try:
            # Check if agent exists by querying by name
            existing = self._supabase_client.table("agents").select("*").eq("name", agent.name).execute()
            
            if existing.data and len(existing.data) > 0:
                # Agent exists - check if there are changes
                existing_data = existing.data[0]
                
                # Normalize lists for comparison (they might be stored as arrays)
                existing_requirements = existing_data.get("requirements", [])
                existing_artifacts = existing_data.get("artifacts", [])
                
                # Compare all fields to see if update is needed
                needs_update = (
                    existing_data.get("role") != agent.role or
                    existing_data.get("description") != agent.description or
                    existing_data.get("goal") != agent.goal or
                    existing_requirements != agent.requirements or
                    existing_artifacts != agent.artifacts or
                    existing_data.get("requires_approval") != agent.requires_approval
                )
                
                if needs_update:
                    # Update existing agent - use the first match (in case of duplicates)
                    agent_id = existing.data[0].get("id")  # Try to use ID if available
                    if agent_id:
                        self._supabase_client.table("agents").update(data).eq("id", agent_id).execute()
                    else:
                        # Fallback to name-based update (may update multiple if duplicates exist)
                        self._supabase_client.table("agents").update(data).eq("name", agent.name).execute()
                # If no changes, do nothing (exit silently - no update needed)
            else:
                # Agent doesn't exist - create it
                self._supabase_client.table("agents").insert(data).execute()
        except Exception as e:
            # Handle specific error types
            error_msg = str(e)
            error_code = None
            if isinstance(e, dict):
                error_code = e.get("code")
                error_msg = e.get("message", str(e))
            
            # RLS (Row Level Security) error
            if "42501" in error_msg or "row-level security" in error_msg.lower() or error_code == "42501":
                raise Exception(
                    f"RLS Policy Error for agent {agent.name}: {error_msg}\n"
                    f"Solution: Use SUPABASE_SERVICE_ROLE_KEY instead of SUPABASE_ANON_KEY, "
                    f"or configure RLS policies to allow inserts/updates. "
                    f"See docs/agent-registry.md for RLS setup instructions."
                ) from e
            
            # Constraint error
            if "42P10" in error_msg or "constraint" in error_msg.lower():
                # Table might not have proper constraints - try direct insert/update
                try:
                    # Try insert first
                    self._supabase_client.table("agents").insert(data).execute()
                except Exception as insert_error:
                    # If insert fails (likely duplicate), try update
                    try:
                        self._supabase_client.table("agents").update(data).eq("name", agent.name).execute()
                    except Exception as update_error:
                        # If all fail, raise the original error with context
                        raise Exception(f"Failed to sync agent {agent.name}: {str(e)}") from e
            else:
                # Re-raise other errors
                raise
    
    def _delete_from_supabase(self, name: str):
        """Delete agent from Supabase"""
        if not self._supabase_client:
            return
        
        self._supabase_client.table("agents").delete().eq("name", name).execute()
    
    def sync_all_to_supabase(self) -> dict:
        """
        Sync all registered agents to Supabase.
        Useful for ensuring all agents are in the database after startup.
        
        Returns:
            dict with sync results: {"synced": count, "failed": count, "errors": list}
        """
        if not self._supabase_client:
            return {
                "synced": 0,
                "failed": len(self._agents),
                "errors": ["Supabase client not initialized"],
                "message": "Supabase not configured - agents not synced"
            }
        
        synced = 0
        failed = 0
        errors = []
        
        for agent_name, agent in self._agents.items():
            try:
                self._sync_to_supabase(agent)
                synced += 1
            except Exception as e:
                failed += 1
                errors.append(f"{agent_name}: {str(e)}")
        
        return {
            "synced": synced,
            "failed": failed,
            "errors": errors,
            "total": len(self._agents),
            "message": f"Synced {synced} of {len(self._agents)} agents to Supabase"
        }


# Global registry instance
_registry = AgentRegistry()


def register_agent(agent: AgentDefinition) -> bool:
    """Convenience function to register an agent"""
    return _registry.register_agent(agent)


def get_agent(name: str) -> Optional[AgentDefinition]:
    """Convenience function to get an agent"""
    return _registry.get_agent(name)


def get_all_agents() -> List[AgentDefinition]:
    """Convenience function to get all agents"""
    return _registry.get_all_agents()


def delete_agent(name: str) -> bool:
    """Convenience function to delete an agent"""
    return _registry.delete_agent(name)


def update_agent(name: str, agent: AgentDefinition) -> bool:
    """Convenience function to update an agent"""
    return _registry.update_agent(name, agent)


def sync_all_agents_to_supabase() -> dict:
    """Convenience function to sync all agents to Supabase"""
    # Reinitialize Supabase in case env vars were loaded after registry creation
    _registry.reinitialize_supabase()
    return _registry.sync_all_to_supabase()
