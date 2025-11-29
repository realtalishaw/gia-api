"""
Test script for /projects/start endpoint.

Tests project creation and first task queuing.
"""
import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def test_start_project():
    """Test starting a new project."""
    print("=" * 60)
    print("Testing /projects/start Endpoint")
    print("=" * 60)
    
    # Test data
    project_id = "test-project-123"
    project_brief = "Build a task management app for teams"
    
    payload = {
        "project_id": project_id,
        "project_brief": project_brief
    }
    
    print(f"\n📤 Sending POST /projects/start")
    print(f"   Project ID: {project_id}")
    print(f"   Brief: {project_brief}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/projects/start",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        print(f"📥 Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"\n✅ Project started successfully!")
                print(f"   Message: {data.get('message')}")
                print(f"\n💡 Next steps:")
                print(f"   1. Check RabbitMQ queue 'discovery_tasks'")
                print(f"   2. Start worker: python agents/runner.py")
                print(f"   3. Worker will pick up 'conduct_market_research' task")
                print(f"   4. Task will complete and move to 'create_brand_identity'")
                print(f"   5. Brand identity will wait for approval")
            else:
                print(f"\n❌ Project start failed: {data.get('message')}")
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"   {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Could not connect to API at {BASE_URL}")
        print(f"   Make sure the API is running: uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    print("\n🧪 Testing GIA Project Start Endpoint\n")
    test_start_project()
    print("\n" + "=" * 60)

