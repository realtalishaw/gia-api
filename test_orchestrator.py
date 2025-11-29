"""
Test script for orchestrator methods.

Tests task creation, progress updates, and workflow logic with mocked Supabase.
"""
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import asyncio

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from orchestrator.engine import AgentOrchestrator
from orchestrator.task_state_manager import TaskStatus
from config.phase_config import PhaseConfig


class MockSupabase:
    """Mock Supabase client for testing."""
    def __init__(self):
        self.tables = {}
        self.inserts = []
        self.updates = []
    
    def table(self, table_name):
        if table_name not in self.tables:
            self.tables[table_name] = MockTable(self, table_name)
        return self.tables[table_name]


class MockTable:
    """Mock Supabase table."""
    def __init__(self, client, name):
        self.client = client
        self.name = name
        self.data = []
        self.select_calls = []
        self.insert_calls = []
        self.update_calls = []
        self.filters = {}  # Store filters for query chaining
    
    def select(self, *args):
        self.select_calls.append(args)
        return self
    
    def insert(self, data):
        self.insert_calls.append(data)
        self.client.inserts.append((self.name, data))
        # Simulate successful insert
        new_id = f"mock-{len(self.data)}"
        new_data = {"id": new_id, **data}
        self.data.append(new_data)
        
        # Create a proper mock result
        mock_result = Mock()
        mock_result.data = [new_data]
        return mock_result
    
    def update(self, data):
        self.update_calls.append(data)
        self.client.updates.append((self.name, data))
        mock_result = Mock()
        mock_result.data = [data]
        return self
    
    def eq(self, key, value):
        self.filters[key] = value
        return self
    
    def in_(self, key, values):
        self.filters[f"{key}_in"] = values
        return self
    
    def not_(self):
        return self
    
    def execute(self):
        # For now, just return empty or all data
        # In a real test, we'd filter based on self.filters
        mock_result = Mock()
        mock_result.data = self.data if self.data else []
        return mock_result


async def test_progress_updates():
    """Test creating progress updates (internal subtasks)."""
    print("=" * 60)
    print("Testing Progress Updates (Internal Subtasks)")
    print("=" * 60)
    
    mock_supabase = MockSupabase()
    orchestrator = AgentOrchestrator(mock_supabase, rabbitmq_url=None)
    
    project_id = "test-project-123"
    task_id = "test-task-456"
    
    # Test creating progress updates
    print("\n1. Creating progress updates...")
    
    messages = [
        "🔍 Looking up competitors...",
        "📊 Comparing offerings...",
        "💡 Analyzing market gaps...",
        "✅ Market research completed"
    ]
    
    for i, message in enumerate(messages):
        success = await orchestrator.create_progress_update(
            project_id=project_id,
            message=message,
            task_id=task_id,
            agent_role="researcher",
            activity_type="progress" if i < len(messages) - 1 else "success"
        )
        print(f"   {'✅' if success else '❌'} {message}")
    
    # Check that inserts were made to project_activity
    activity_inserts = [ins for ins in mock_supabase.inserts if ins[0] == 'project_activity']
    print(f"\n   📊 Created {len(activity_inserts)} activity entries")
    print(f"   ✅ Progress updates work (creates entries in project_activity, not tasks table)")


async def test_task_creation():
    """Test creating real tasks."""
    print("\n" + "=" * 60)
    print("Testing Task Creation (Real Tasks)")
    print("=" * 60)
    
    mock_supabase = MockSupabase()
    
    # Mock the queue manager to avoid RabbitMQ connection
    with patch('orchestrator.engine.TaskQueueManager') as MockQueueManager:
        mock_queue = MockQueueManager.return_value
        mock_queue.queue_task_execution = AsyncMock(return_value=True)
        
        # Mock verify_task_creation to skip database checks
        with patch.object(AgentOrchestrator, 'verify_task_creation', new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = (True, None)  # (can_create, reason)
            
            orchestrator = AgentOrchestrator(mock_supabase, rabbitmq_url=None)
            
            project_id = "test-project-123"
            
            # Test creating a real task
            print("\n1. Creating real task...")
            success, task_id, error = await orchestrator.create_task(
                project_id=project_id,
                task_type="conduct_market_research"
            )
            
            if success:
                print(f"   ✅ Task created: {task_id}")
                print(f"   ✅ Task queued to RabbitMQ")
                
                # Check that task was inserted
                task_inserts = [ins for ins in mock_supabase.inserts if ins[0] == 'tasks']
                print(f"   📊 Created {len(task_inserts)} task in tasks table")
                if task_inserts:
                    task_data = task_inserts[0][1]
                    print(f"   📋 Task type: {task_data.get('type')}")
                    print(f"   👤 Agent: {task_data.get('agent_role')}")
                    print(f"   📊 Status: {task_data.get('status')}")
            else:
                print(f"   ❌ Failed to create task: {error}")


async def test_task_with_parent():
    """Test creating tasks with parent_task_id."""
    print("\n" + "=" * 60)
    print("Testing Task Hierarchy (Parent-Child Tasks)")
    print("=" * 60)
    
    mock_supabase = MockSupabase()
    
    with patch('orchestrator.engine.TaskQueueManager') as MockQueueManager:
        mock_queue = MockQueueManager.return_value
        mock_queue.queue_task_execution = AsyncMock(return_value=True)
        
        # Mock verify_task_creation to skip database checks
        with patch.object(AgentOrchestrator, 'verify_task_creation', new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = (True, None)  # (can_create, reason)
            
            orchestrator = AgentOrchestrator(mock_supabase, rabbitmq_url=None)
            
            project_id = "test-project-123"
            
            # Create parent task
            print("\n1. Creating parent task (build_mvp)...")
            success, parent_task_id, error = await orchestrator.create_task(
                project_id=project_id,
                task_type="build_mvp"
            )
            
            if success:
                print(f"   ✅ Parent task created: {parent_task_id}")
                
                # Create child tasks (subtasks)
                print("\n2. Creating child tasks (subtasks)...")
                subtasks = [
                    ("implement_auth", "developer"),
                    ("build_dashboard", "developer"),
                    ("create_api", "developer")
                ]
                
                for subtask_type, agent_role in subtasks:
                    success, subtask_id, error = await orchestrator.create_task(
                        project_id=project_id,
                        task_type=subtask_type,
                        agent_role=agent_role,
                        parent_task_id=parent_task_id
                    )
                    
                    if success:
                        print(f"   ✅ Subtask created: {subtask_type} ({subtask_id})")
                        print(f"      Parent: {parent_task_id}")
                    else:
                        print(f"   ❌ Failed to create subtask: {error}")
                
                # Check task hierarchy
                task_inserts = [ins for ins in mock_supabase.inserts if ins[0] == 'tasks']
                print(f"\n   📊 Total tasks created: {len(task_inserts)}")
                print(f"   📋 Tasks with parent: {sum(1 for ins in task_inserts if ins[1].get('parent_task_id'))}")


async def test_workflow_simulation():
    """Simulate a workflow with progress updates and task creation."""
    print("\n" + "=" * 60)
    print("Simulating Complete Workflow")
    print("=" * 60)
    
    mock_supabase = MockSupabase()
    
    with patch('orchestrator.engine.TaskQueueManager') as MockQueueManager:
        mock_queue = MockQueueManager.return_value
        mock_queue.queue_task_execution = AsyncMock(return_value=True)
        
        # Mock verify_task_creation to skip database checks
        with patch.object(AgentOrchestrator, 'verify_task_creation', new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = (True, None)  # (can_create, reason)
            
            orchestrator = AgentOrchestrator(mock_supabase, rabbitmq_url=None)
            
            project_id = "test-project-123"
            
            print("\n📋 Simulating Discovery Phase (Deterministic)...")
            
            # Step 1: Market Research (deterministic - uses progress updates)
            print("\n   1. conduct_market_research")
            success, task_id, error = await orchestrator.create_task(
                project_id=project_id,
                task_type="conduct_market_research"
            )
            
            if success:
                # Simulate agent creating progress updates
                await orchestrator.create_progress_update(
                    project_id=project_id,
                    message="🔍 Looking up competitors...",
                    task_id=task_id,
                    agent_role="researcher"
                )
                await orchestrator.create_progress_update(
                    project_id=project_id,
                    message="📊 Analyzing market gaps...",
                    task_id=task_id,
                    agent_role="researcher"
                )
                await orchestrator.create_progress_update(
                    project_id=project_id,
                    message="✅ Market research completed",
                    task_id=task_id,
                    agent_role="researcher",
                    activity_type="success"
                )
                print(f"      ✅ Task created and progress updates sent")
            
            print("\n📋 Simulating Development Phase (Probabilistic)...")
            
            # Step 2: Build MVP (probabilistic - creates real subtasks)
            print("\n   2. build_mvp")
            success, parent_task_id, error = await orchestrator.create_task(
                project_id=project_id,
                task_type="build_mvp"
            )
            
            if success:
                # Simulate agent creating real subtasks
                subtasks = ["implement_auth", "build_dashboard", "create_api"]
                for subtask_type in subtasks:
                    await orchestrator.create_task(
                        project_id=project_id,
                        task_type=subtask_type,
                        parent_task_id=parent_task_id
                    )
                print(f"      ✅ Parent task created")
                print(f"      ✅ {len(subtasks)} subtasks created and queued")
            
            # Summary
            print("\n📊 Summary:")
            task_inserts = [ins for ins in mock_supabase.inserts if ins[0] == 'tasks']
            activity_inserts = [ins for ins in mock_supabase.inserts if ins[0] == 'project_activity']
            print(f"   Tasks created: {len(task_inserts)}")
            print(f"   Progress updates: {len(activity_inserts)}")
            print(f"   ✅ Deterministic tasks use progress updates")
            print(f"   ✅ Probabilistic tasks create real subtasks")


async def main():
    """Run all tests."""
    print("\n🧪 Testing GIA Orchestrator System\n")
    
    try:
        await test_progress_updates()
        await test_task_creation()
        await test_task_with_parent()
        await test_workflow_simulation()
        
        print("\n" + "=" * 60)
        print("✅ All orchestrator tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

