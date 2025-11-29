"""
Test script for phase configuration and orchestrator logic.

Tests the new SOP structure and helper methods.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.phase_config import PhaseConfig, Phase


def test_phase_structure():
    """Test that all phases are properly structured."""
    print("=" * 60)
    print("Testing Phase Structure")
    print("=" * 60)
    
    phases = PhaseConfig.PHASES
    print(f"\n✅ Found {len(phases)} phases")
    
    for phase in phases:
        print(f"\n📋 Phase {phase['order']}: {phase['name']}")
        print(f"   Designation: {phase['designation']}")
        print(f"   Deterministic: {phase.get('is_deterministic', 'N/A')}")
        print(f"   Queue: {phase['queue']}")
        print(f"   Tasks ({len(phase['tasks'])}):")
        for task in phase['tasks']:
            approval = "✅ REQUIRES APPROVAL" if PhaseConfig.requires_approval(task['type']) else ""
            print(f"      - {task['type']} ({task['agent']}) {approval}")
        print(f"   Dependencies: {phase.get('input_dependencies', [])}")
        print(f"   Deliverables: {phase.get('deliverables', [])}")


def test_phase_helpers():
    """Test phase config helper methods."""
    print("\n" + "=" * 60)
    print("Testing Phase Config Helper Methods")
    print("=" * 60)
    
    # Test get_agent_for_task
    print("\n1. Testing get_agent_for_task():")
    test_tasks = ["conduct_market_research", "create_brand_identity", "build_mvp", "deploy_app"]
    for task_type in test_tasks:
        try:
            agent = PhaseConfig.get_agent_for_task(task_type)
            print(f"   ✅ {task_type} → {agent}")
        except ValueError as e:
            print(f"   ❌ {task_type} → {e}")
    
    # Test requires_approval
    print("\n2. Testing requires_approval():")
    approval_tasks = ["create_brand_identity", "write_prd", "create_ui_ux_mockups", "build_mvp"]
    for task_type in approval_tasks:
        requires = PhaseConfig.requires_approval(task_type)
        status = "✅ REQUIRES" if requires else "❌ No approval"
        print(f"   {status}: {task_type}")
    
    # Test phase designation
    print("\n3. Testing get_phase_designation():")
    for task_type in test_tasks:
        try:
            phase = PhaseConfig.get_phase_designation(task_type)
            print(f"   ✅ {task_type} → {phase}")
        except ValueError as e:
            print(f"   ❌ {task_type} → {e}")
    
    # Test is_phase_deterministic
    print("\n4. Testing is_phase_deterministic():")
    test_phases = [Phase.DISCOVERY.value, Phase.DEVELOPMENT.value, Phase.DEPLOYMENT.value]
    for phase in test_phases:
        is_det = PhaseConfig.is_phase_deterministic(phase)
        status = "Deterministic" if is_det else "Probabilistic"
        print(f"   {phase} → {status}")
    
    # Test dependencies
    print("\n5. Testing get_phase_input_dependencies():")
    for phase in test_phases:
        deps = PhaseConfig.get_phase_input_dependencies(phase)
        print(f"   {phase} needs: {deps if deps else 'nothing'}")
    
    # Test next phase
    print("\n6. Testing get_next_phase():")
    for phase in test_phases:
        next_phase = PhaseConfig.get_next_phase(phase)
        print(f"   {phase} → {next_phase if next_phase else 'END'}")
    
    # Test next task
    print("\n7. Testing get_next_task():")
    test_task_sequence = [
        "conduct_market_research",
        "create_brand_identity",
        "write_prd",
        "create_ui_ux_mockups",
        "build_mvp"
    ]
    for task_type in test_task_sequence:
        next_task = PhaseConfig.get_next_task(task_type)
        print(f"   {task_type} → {next_task if next_task else 'END'}")


def test_workflow_sequence():
    """Test the complete workflow sequence."""
    print("\n" + "=" * 60)
    print("Testing Complete Workflow Sequence")
    print("=" * 60)
    
    print("\n📊 Complete Workflow:")
    current_phase = Phase.DISCOVERY.value
    phase_count = 0
    
    while current_phase and phase_count < 10:  # Safety limit
        phase_count += 1
        tasks = PhaseConfig.get_required_tasks(current_phase)
        is_det = PhaseConfig.is_phase_deterministic(current_phase)
        deps = PhaseConfig.get_phase_input_dependencies(current_phase)
        
        print(f"\n   Phase {phase_count}: {current_phase.upper()}")
        print(f"      Type: {'Deterministic (SOP)' if is_det else 'Probabilistic (Agent creates tasks)'}")
        if deps:
            print(f"      Needs: {', '.join(deps)}")
        print(f"      Tasks:")
        for task in tasks:
            approval = " [APPROVAL REQUIRED]" if PhaseConfig.requires_approval(task['type']) else ""
            print(f"         - {task['type']} ({task['agent']}){approval}")
        
        current_phase = PhaseConfig.get_next_phase(current_phase)


def test_approval_flow():
    """Test approval requirements."""
    print("\n" + "=" * 60)
    print("Testing Approval Flow")
    print("=" * 60)
    
    print("\n🔐 Tasks Requiring Approval:")
    for phase in PhaseConfig.PHASES:
        for task in phase['tasks']:
            if PhaseConfig.requires_approval(task['type']):
                print(f"   ✅ {task['type']} ({phase['name']})")
    
    print("\n📝 Tasks NOT Requiring Approval:")
    for phase in PhaseConfig.PHASES:
        for task in phase['tasks']:
            if not PhaseConfig.requires_approval(task['type']):
                print(f"   ⚪ {task['type']} ({phase['name']})")


if __name__ == "__main__":
    print("\n🧪 Testing GIA Phase Configuration System\n")
    
    try:
        test_phase_structure()
        test_phase_helpers()
        test_workflow_sequence()
        test_approval_flow()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

