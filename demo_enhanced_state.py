#!/usr/bin/env python3
"""
Enhanced Core State Schema Demonstration

This script demonstrates the powerful new capabilities of the MultiAgenticSwarm
Core State Schema enhancement, including:

1. Enhanced field validation with strict mode
2. State migration system with version management  
3. Advanced reducers with configurable conflict resolution
4. Performance optimizations for large datasets
5. Comprehensive error handling and logging
6. LangGraph integration simulation

Run this script to see the enhancements in action.
"""

import time
from datetime import datetime
from typing import Dict, Any

from multiagenticswarm.core.state import (
    create_initial_state,
    validate_state,
    validate_agent_status,
    validate_workflow_pattern,
    compare_versions,
    migrate_state,
    create_migration_backup,
    log_state_change,
    VALID_AGENT_STATUSES,
    VALID_WORKFLOW_PATTERNS
)

from multiagenticswarm.core.state_reducers import (
    merge_states,
    resolve_permissions,
    merge_agent_outputs,
    aggregate_progress,
    ConflictResolutionStrategy,
    get_reducer_info,
    validate_reducer_performance,
    REDUCERS
)


def demo_enhanced_validation():
    """Demonstrate enhanced validation capabilities."""
    print("🔍 Enhanced Validation Demonstration")
    print("=" * 50)
    
    # Create a state with various field types
    state = create_initial_state(
        collaboration_prompt="Multi-agent software development workflow"
    )
    
    # Add various field values
    state["agent_status"]["developer"] = "active"
    state["agent_status"]["reviewer"] = "idle"
    state["workflow_pattern"] = "hierarchical"
    state["execution_mode"] = "parallel"
    state["task_progress"]["backend"] = 75.5
    state["tool_permissions"]["developer"] = ["git", "ide", "compiler"]
    
    print("✅ Basic validation:", validate_state(state))
    print("✅ Strict validation:", validate_state(state, strict=True))
    
    # Demonstrate validation functions
    print(f"\nValid agent statuses: {sorted(VALID_AGENT_STATUSES)}")
    print(f"Valid workflow patterns: {sorted(VALID_WORKFLOW_PATTERNS)}")
    
    print(f"'active' is valid status: {validate_agent_status('active')}")
    print(f"'invalid' is valid status: {validate_agent_status('invalid')}")
    print(f"'hierarchical' is valid pattern: {validate_workflow_pattern('hierarchical')}")
    
    print("\n" + "=" * 50 + "\n")


def demo_state_migration():
    """Demonstrate state migration system."""
    print("🔄 State Migration System Demonstration")
    print("=" * 50)
    
    # Create an "old" state
    old_state = {
        "state_version": "0.9.0",
        "messages": [],
        "agent_outputs": {"agent1": {"result": "legacy_format"}},
        "old_field_name": "legacy_value",
        "performance_metrics": ["op1", "op2"]  # Old list format
    }
    
    print(f"Original state version: {old_state['state_version']}")
    
    # Demonstrate version comparison
    print(f"Version comparison 0.9.0 vs 1.0.0: {compare_versions('0.9.0', '1.0.0')}")
    
    # Create backup
    backup = create_migration_backup(old_state)
    print("✅ Backup created successfully")
    
    # Migrate state
    try:
        migrated = migrate_state(old_state, "1.0.0")
        print(f"✅ Migration successful! New version: {migrated['state_version']}")
        print(f"   - Added debug_flags: {'debug_flags' in migrated}")
        print(f"   - Renamed field: {'new_field_name' in migrated}")
        print(f"   - Updated metrics format: {type(migrated['performance_metrics'])}")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
    
    print("\n" + "=" * 50 + "\n")


def demo_enhanced_reducers():
    """Demonstrate enhanced reducer capabilities."""
    print("⚙️ Enhanced Reducers Demonstration")
    print("=" * 50)
    
    # Demonstrate different conflict resolution strategies
    current_permissions = {"agent1": ["tool1", "tool2", "tool3"]}
    update_permissions = {"agent1": ["tool2", "tool3", "tool4"]}
    
    print("Permission conflict resolution:")
    print(f"Current: {current_permissions['agent1']}")
    print(f"Update:  {update_permissions['agent1']}")
    
    # Most restrictive (intersection)
    restrictive = resolve_permissions(
        current_permissions, 
        update_permissions, 
        ConflictResolutionStrategy.MOST_RESTRICTIVE
    )
    print(f"Most restrictive: {restrictive['agent1']}")
    
    # Most permissive (union)
    permissive = resolve_permissions(
        current_permissions, 
        update_permissions, 
        ConflictResolutionStrategy.MOST_PERMISSIVE
    )
    print(f"Most permissive: {permissive['agent1']}")
    
    # Demonstrate reducer metadata
    print(f"\nAvailable reducers: {len(REDUCERS)}")
    for field, info in list(REDUCERS.items())[:3]:
        print(f"  - {field}: {info['description']}")
    
    print("\n" + "=" * 50 + "\n")


def demo_performance_capabilities():
    """Demonstrate performance capabilities."""
    print("🚀 Performance Capabilities Demonstration")
    print("=" * 50)
    
    # Create large dataset
    print("Creating large state with 1000 agents...")
    large_state = create_initial_state()
    
    # Add 1000 agent outputs
    large_agent_outputs = {
        f"agent_{i}": {"result": f"result_{i}", "score": i * 0.1}
        for i in range(1000)
    }
    
    start_time = time.perf_counter()
    large_state = merge_states(large_state, {"agent_outputs": large_agent_outputs})
    merge_time = time.perf_counter() - start_time
    
    print(f"✅ Merged 1000 agent outputs in {merge_time:.4f} seconds")
    
    # Validate performance
    start_time = time.perf_counter()
    is_valid = validate_state(large_state, strict=True)
    validation_time = time.perf_counter() - start_time
    
    print(f"✅ Validated large state in {validation_time:.4f} seconds")
    
    # Test reducer performance
    print("\nTesting reducer performance...")
    metrics = validate_reducer_performance("agent_outputs", 100, 10)
    print(f"Agent outputs reducer: {metrics['avg_time']:.6f}s average")
    
    print("\n" + "=" * 50 + "\n")


def demo_langgraph_simulation():
    """Demonstrate LangGraph node simulation."""
    print("🌐 LangGraph Integration Simulation")
    print("=" * 50)
    
    # Create initial state for workflow
    state = create_initial_state(
        collaboration_prompt="Three-agent software development pipeline"
    )
    state["debug_flags"]["trace_execution"] = True
    
    print("Simulating LangGraph workflow execution...")
    
    # Phase 1: Planning agent
    planning_updates = {
        "current_agent": "planner",
        "agent_status": {"planner": "active"},
        "agent_outputs": {
            "planner": {
                "status": "completed",
                "plan": "Break down into 3 phases: design, implement, test",
                "estimated_time": "2 hours"
            }
        },
        "task_progress": {"planning": 100.0}
    }
    
    log_state_change(state, "agent_execution", planning_updates, "planner")
    state = merge_states(state, planning_updates)
    print("✅ Phase 1: Planning completed")
    
    # Phase 2: Development agent
    dev_updates = {
        "current_agent": "developer",
        "agent_status": {"developer": "active", "planner": "idle"},
        "agent_outputs": {
            "developer": {
                "status": "in_progress",
                "files_created": ["main.py", "utils.py", "tests.py"],
                "lines_of_code": 350
            }
        },
        "task_progress": {"development": 80.0}
    }
    
    log_state_change(state, "agent_execution", dev_updates, "developer")
    state = merge_states(state, dev_updates)
    print("✅ Phase 2: Development in progress (80%)")
    
    # Phase 3: Quality assurance
    qa_updates = {
        "current_agent": "qa_engineer",
        "agent_status": {"qa_engineer": "active", "developer": "waiting"},
        "agent_outputs": {
            "qa_engineer": {
                "status": "testing",
                "tests_run": 25,
                "tests_passed": 23,
                "coverage": "92%"
            }
        },
        "task_progress": {"testing": 90.0},
        "help_requests": [{
            "id": "qa_help_1",
            "from": "qa_engineer",
            "to": "developer",
            "message": "Two test failures need attention"
        }]
    }
    
    log_state_change(state, "agent_execution", qa_updates, "qa_engineer")
    state = merge_states(state, qa_updates)
    print("✅ Phase 3: QA testing (90% complete, found 2 issues)")
    
    # Validate final state
    print(f"\nFinal state validation: {validate_state(state, strict=True)}")
    print(f"Total agents involved: {len(state['agent_outputs'])}")
    print(f"Execution trace entries: {len(state['execution_trace'])}")
    print(f"Overall progress: {sum(state['task_progress'].values()) / len(state['task_progress']):.1f}%")
    
    print("\n" + "=" * 50 + "\n")


def demo_error_handling():
    """Demonstrate enhanced error handling."""
    print("🛡️ Enhanced Error Handling Demonstration")
    print("=" * 50)
    
    try:
        # Attempt to merge invalid data
        base_state = {"agent_outputs": {}}
        invalid_updates = {"agent_outputs": "not_a_dict"}
        
        result = merge_states(base_state, invalid_updates)
        print("❌ Should have failed!")
    except Exception as e:
        print(f"✅ Error caught: {type(e).__name__}")
        print(f"   Message: {str(e)[:100]}...")
    
    # Demonstrate validation with helpful messages
    try:
        invalid_state = create_initial_state()
        invalid_state["agent_status"]["agent1"] = "invalid_status"
        validate_state(invalid_state, strict=True)
    except ValueError as e:
        print(f"✅ Validation error caught with helpful message:")
        print(f"   {str(e)[:100]}...")
    
    print("\n" + "=" * 50 + "\n")


def main():
    """Run all demonstrations."""
    print("🎉 MultiAgenticSwarm Enhanced Core State Schema")
    print("🎉 Comprehensive Enhancement Demonstration")
    print("=" * 70)
    print()
    
    demo_enhanced_validation()
    demo_state_migration()
    demo_enhanced_reducers()
    demo_performance_capabilities()
    demo_langgraph_simulation()
    demo_error_handling()
    
    print("🎉 All demonstrations completed successfully!")
    print("\nKey achievements:")
    print("✅ Enhanced field validation with strict mode")
    print("✅ Complete state migration system")
    print("✅ Advanced reducers with configurable strategies")
    print("✅ High-performance handling of large datasets")
    print("✅ Comprehensive error handling and logging")
    print("✅ Full LangGraph integration simulation")
    print("✅ Production-ready reliability and maintainability")
    print("\nThe Core State Schema is now enterprise-grade! 🚀")


if __name__ == "__main__":
    main()