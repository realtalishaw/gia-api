"""
Tests for context worker ingestion functionality.
"""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Check if celery is available before importing modules that depend on it
try:
    import celery
except ImportError:
    pytest.skip("Celery not installed. Activate venv and install with: cd api && pip install -r requirements.txt", allow_module_level=True)

# Add api directory to path for imports
import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent
api_dir = root_dir / "api"
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

# Now safe to import modules that depend on celery
from api.context_engine.worker.context_storage import save_context_data, _init_supabase
from api.context_engine.worker.tasks import ingest_context_data_task


class TestContextStorage:
    """Tests for context storage utility."""
    
    def test_save_context_data_with_mock(self):
        """Test save_context_data with mocked Supabase client."""
        # Mock Supabase client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [{"id": "test-uuid-123", "project_id": "test_project"}]
        mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        # Patch the Supabase client initialization
        with patch('api.context_engine.worker.context_storage._supabase_client', mock_client):
            with patch('api.context_engine.worker.context_storage._init_supabase', return_value=mock_client):
                result = save_context_data(
                    project_id="test_project",
                    data={"key": "value", "nested": {"data": 123}},
                    agent_name="test_agent",
                    data_type="test",
                    metadata={"source": "test"}
                )
        
        assert result is True
        mock_client.table.assert_called_once_with("context_lake")
        insert_call = mock_client.table.return_value.insert
        insert_call.assert_called_once()
        call_args = insert_call.call_args[0][0]
        assert call_args["project_id"] == "test_project"
        assert call_args["raw_data"] == {"key": "value", "nested": {"data": 123}}
        assert call_args["agent_name"] == "test_agent"
        assert call_args["data_type"] == "test"
        assert call_args["metadata"] == {"source": "test"}
    
    def test_save_context_data_minimal(self):
        """Test save_context_data with minimal required fields."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [{"id": "test-uuid-456"}]
        mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        with patch('api.context_engine.worker.context_storage._supabase_client', mock_client):
            with patch('api.context_engine.worker.context_storage._init_supabase', return_value=mock_client):
                result = save_context_data(
                    project_id="test_project",
                    data={"minimal": "data"}
                )
        
        assert result is True
        insert_call = mock_client.table.return_value.insert
        call_args = insert_call.call_args[0][0]
        assert call_args["project_id"] == "test_project"
        assert call_args["raw_data"] == {"minimal": "data"}
        assert "agent_name" not in call_args
        assert "data_type" not in call_args
        assert "metadata" not in call_args
    
    def test_save_context_data_no_supabase(self):
        """Test save_context_data when Supabase is not configured."""
        with patch('api.context_engine.worker.context_storage._init_supabase', return_value=None):
            result = save_context_data(
                project_id="test_project",
                data={"test": "data"}
            )
        
        assert result is False
    
    def test_save_context_data_insert_failure(self):
        """Test save_context_data when insert fails."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = []  # Empty response indicates failure
        mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        with patch('api.context_engine.worker.context_storage._supabase_client', mock_client):
            with patch('api.context_engine.worker.context_storage._init_supabase', return_value=mock_client):
                result = save_context_data(
                    project_id="test_project",
                    data={"test": "data"}
                )
        
        assert result is False
    
    @pytest.mark.integration
    def test_save_context_data_integration(self):
        """Integration test that actually saves to Supabase (requires env vars)."""
        # Skip if Supabase credentials are not available
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            pytest.skip("Supabase credentials not available for integration test")
        
        # Reset the global client to ensure fresh initialization
        import api.context_engine.worker.context_storage as storage_module
        storage_module._supabase_client = None
        
        # Test data
        test_data = {
            "test": "integration_data",
            "timestamp": "2024-01-01T00:00:00Z",
            "nested": {
                "key1": "value1",
                "key2": 42
            }
        }
        
        result = save_context_data(
            project_id="test_project_integration",
            data=test_data,
            agent_name="test_agent",
            data_type="integration_test",
            metadata={"test_run": True}
        )
        
        assert result is True


class TestContextIngestionTask:
    """Tests for context ingestion Celery task."""
    
    def test_ingest_context_data_task_success(self):
        """Test successful context ingestion task."""
        # Create a mock task instance (self)
        mock_task = Mock()
        mock_request = Mock()
        mock_request.id = "test-task-id-123"
        mock_task.request = mock_request
        mock_task.update_state = Mock()
        
        # Mock save_context_data to return success
        with patch('api.context_engine.worker.tasks.save_context_data', return_value=True):
            # Call the task function directly with mock self
            result = ingest_context_data_task(
                mock_task,
                project_id="test_project",
                data={"test": "data", "number": 42},
                agent_name="test_agent",
                data_type="test",
                metadata={"source": "unit_test"}
            )
        
        assert result["status"] == "completed"
        assert result["project_id"] == "test_project"
        assert result["agent_name"] == "test_agent"
        assert result["data_type"] == "test"
        assert result["task_id"] == "test-task-id-123"
        assert "message" in result
        # Verify update_state was called
        assert mock_task.update_state.called
    
    def test_ingest_context_data_task_validation_error_missing_project_id(self):
        """Test ingestion task with missing project_id."""
        mock_task = Mock()
        mock_request = Mock()
        mock_request.id = "test-task-id-456"
        mock_task.request = mock_request
        mock_task.update_state = Mock()
        
        with pytest.raises(ValueError, match="project_id is required"):
            ingest_context_data_task(
                mock_task,
                project_id="",
                data={"test": "data"}
            )
    
    def test_ingest_context_data_task_validation_error_missing_data(self):
        """Test ingestion task with missing data."""
        mock_task = Mock()
        mock_request = Mock()
        mock_request.id = "test-task-id-789"
        mock_task.request = mock_request
        mock_task.update_state = Mock()
        
        with pytest.raises(ValueError, match="data is required"):
            ingest_context_data_task(
                mock_task,
                project_id="test_project",
                data={}
            )
    
    def test_ingest_context_data_task_validation_error_invalid_data_type(self):
        """Test ingestion task with invalid data type (not a dict)."""
        mock_task = Mock()
        mock_request = Mock()
        mock_request.id = "test-task-id-invalid"
        mock_task.request = mock_request
        mock_task.update_state = Mock()
        
        with pytest.raises(ValueError, match="data must be a dictionary"):
            ingest_context_data_task(
                mock_task,
                project_id="test_project",
                data="not a dict"  # Invalid type
            )
    
    def test_ingest_context_data_task_save_failure(self):
        """Test ingestion task when save_context_data fails."""
        mock_task = Mock()
        mock_request = Mock()
        mock_request.id = "test-task-id-fail"
        mock_task.request = mock_request
        mock_task.update_state = Mock()
        
        with patch('api.context_engine.worker.tasks.save_context_data', return_value=False):
            with pytest.raises(Exception, match="Failed to save context data"):
                ingest_context_data_task(
                    mock_task,
                    project_id="test_project",
                    data={"test": "data"}
                )
    
    def test_ingest_context_data_task_optional_fields(self):
        """Test ingestion task with only required fields."""
        mock_task = Mock()
        mock_request = Mock()
        mock_request.id = "test-task-id-minimal"
        mock_task.request = mock_request
        mock_task.update_state = Mock()
        
        with patch('api.context_engine.worker.tasks.save_context_data', return_value=True):
            result = ingest_context_data_task(
                mock_task,
                project_id="test_project",
                data={"minimal": "data"}
            )
        
        assert result["status"] == "completed"
        assert result["project_id"] == "test_project"
        assert result["agent_name"] is None
        assert result["data_type"] is None
    
    @pytest.mark.integration
    def test_ingest_context_data_task_real_queue(self):
        """
        Integration test that actually queues a task to the context worker.
        
        This test requires:
        - A running Celery worker: celery -A api.context_engine.worker.celery_app worker --queues=context_queue
        - A running RabbitMQ broker (CloudAMQP_URL or RABBITMQ_URL env var)
        - Supabase credentials (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)
        
        The test will be skipped if these are not available.
        """
        import time
        from celery.result import AsyncResult
        from api.context_engine.worker.celery_app import celery_app
        
        # Check if broker is configured
        rabbitmq_url = os.getenv("CLOUDAMQP_URL") or os.getenv("RABBITMQ_URL")
        if not rabbitmq_url:
            pytest.skip("RabbitMQ broker not configured (CLOUDAMQP_URL or RABBITMQ_URL required)")
        
        # Check if Supabase is configured
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not supabase_url or not supabase_key:
            pytest.skip("Supabase credentials not available for integration test")
        
        # Test data
        test_project_id = f"test_project_queue_{int(time.time())}"
        test_data = {
            "test": "queued_task_data",
            "timestamp": time.time(),
            "integration_test": True,
            "nested": {
                "level1": "value1",
                "level2": {
                    "level3": 42
                }
            }
        }
        
        try:
            # Actually queue the task using .delay() - this sends it to the broker
            # Use apply_async with a timeout wrapper to prevent hanging
            print(f"\n📤 Queuing task to context_queue for project: {test_project_id}")
            print(f"   Broker URL: {rabbitmq_url[:50]}..." if len(rabbitmq_url) > 50 else f"   Broker URL: {rabbitmq_url}")
            
            # Use threading to add a timeout to the task queuing
            import threading
            task_result_container = [None]
            exception_container = [None]
            
            def queue_task():
                try:
                    task_result_container[0] = ingest_context_data_task.apply_async(
                        args=(),
                        kwargs={
                            "project_id": test_project_id,
                            "data": test_data,
                            "agent_name": "test_agent",
                            "data_type": "integration_test",
                            "metadata": {"source": "pytest", "test_name": "test_ingest_context_data_task_real_queue"}
                        },
                        queue="context_queue",
                        time_limit=30 * 60,  # 30 minutes
                        soft_time_limit=25 * 60,  # 25 minutes
                    )
                except Exception as e:
                    exception_container[0] = e
            
            # Start queuing in a thread with timeout
            queue_thread = threading.Thread(target=queue_task, daemon=True)
            queue_thread.start()
            queue_thread.join(timeout=10)  # 10 second timeout for queuing
            
            if queue_thread.is_alive():
                pytest.fail(
                    "Task queuing timed out after 10 seconds. "
                    "This usually means the broker is not reachable. "
                    f"Check that:\n"
                    f"  1. RabbitMQ broker is running and accessible at the configured URL\n"
                    f"  2. CLOUDAMQP_URL or RABBITMQ_URL is correct\n"
                    f"  3. Network connectivity to the broker"
                )
            
            if exception_container[0]:
                raise exception_container[0]
            
            if task_result_container[0] is None:
                pytest.fail("Task queuing failed - no result returned")
            
            task_result = task_result_container[0]
            task_id = task_result.id
            print(f"✅ Task queued with ID: {task_id}")
            
            # Wait for the task to complete (with timeout)
            max_wait = 60  # 60 seconds timeout
            wait_interval = 0.5  # Check every 500ms
            elapsed = 0
            
            while not task_result.ready() and elapsed < max_wait:
                time.sleep(wait_interval)
                elapsed += wait_interval
                if elapsed % 5 == 0:  # Print status every 5 seconds
                    print(f"⏳ Waiting for task... ({elapsed:.1f}s elapsed, state: {task_result.state})")
            
            if not task_result.ready():
                pytest.fail(f"Task {task_id} did not complete within {max_wait} seconds. "
                          f"Current state: {task_result.state}. "
                          f"Make sure the context worker is running: "
                          f"celery -A api.context_engine.worker.celery_app worker --queues=context_queue")
            
            # Check if task succeeded
            if task_result.failed():
                error_info = task_result.info
                pytest.fail(f"Task {task_id} failed: {error_info}")
            
            # Get the result
            result = task_result.get(timeout=5)
            print(f"✅ Task completed successfully!")
            print(f"   Result: {result}")
            
            # Verify the result structure
            assert result is not None, "Task result should not be None"
            assert isinstance(result, dict), "Task result should be a dictionary"
            assert result.get("status") == "completed", f"Expected status 'completed', got '{result.get('status')}'"
            assert result.get("project_id") == test_project_id, "Project ID should match"
            assert result.get("agent_name") == "test_agent", "Agent name should match"
            assert result.get("data_type") == "integration_test", "Data type should match"
            assert "task_id" in result, "Result should include task_id"
            assert "message" in result, "Result should include message"
            
            print(f"✅ All assertions passed!")
            
        except Exception as e:
            # Check if it's a connection error (broker/worker not running)
            error_str = str(e).lower()
            if "connection" in error_str or "timeout" in error_str or "not connected" in error_str:
                pytest.skip(
                    f"Could not connect to broker/worker: {e}. "
                    f"Make sure:\n"
                    f"  1. RabbitMQ broker is running and accessible\n"
                    f"  2. Context worker is running: celery -A api.context_engine.worker.celery_app worker --queues=context_queue\n"
                    f"  3. CLOUDAMQP_URL or RABBITMQ_URL is set correctly"
                )
            else:
                # Re-raise other exceptions
                raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
