#!/usr/bin/env python3
"""
Demonstration of the enhanced state management with dynamic configuration.

This script showcases the new features added to the MultiAgenticSwarm state management:
1. Proper reducers for fields requiring append behavior
2. Dynamic field configuration system
3. Memory management with cleanup policies
4. Enhanced migration capabilities
5. Backwards compatibility
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from multiagenticswarm.core.state import (
    create_initial_state, 
    validate_state,
    auto_migrate_state
)
from multiagenticswarm.core.state_config import (
    get_state_config,
    get_field_documentation,
    create_dynamic_agent_state_class
)
from multiagenticswarm.core.state_reducers import apply_reducer


def demo_reducer_enhancements():
    """Demonstrate the enhanced reducers for append-only fields."""
    print("=" * 60)
    print("1. ENHANCED REDUCERS DEMONSTRATION")
    print("=" * 60)
    
    # Demo subtasks with operator.add behavior
    print("\n📋 Subtasks with operator.add reducer:")
    current_subtasks = [{"task": "analyze_requirements", "status": "completed"}]
    new_subtasks = [{"task": "design_architecture", "status": "in_progress"}]
    
    # In actual usage, this would be handled by LangGraph automatically
    # We're using apply_reducer here for demonstration
    merged_subtasks = apply_reducer("subtasks", current_subtasks, new_subtasks)
    print(f"   Current: {current_subtasks}")
    print(f"   New:     {new_subtasks}")
    print(f"   Result:  {merged_subtasks}")
    
    # Demo tool_calls with operator.add behavior  
    print("\n🔧 Tool calls with append behavior:")
    current_calls = [{"tool": "search", "query": "python best practices"}]
    new_calls = [{"tool": "calculator", "expression": "2 + 2"}]
    
    merged_calls = apply_reducer("tool_calls", current_calls, new_calls)
    print(f"   Current: {current_calls}")
    print(f"   New:     {new_calls}")
    print(f"   Result:  {merged_calls}")


def demo_dynamic_configuration():
    """Demonstrate the dynamic field configuration system."""
    print("\n" + "=" * 60)
    print("2. DYNAMIC CONFIGURATION DEMONSTRATION")
    print("=" * 60)
    
    config = get_state_config()
    
    print(f"\n📊 Configuration overview:")
    print(f"   Total fields configured: {len(config.fields)}")
    print(f"   Active fields: {len(config.get_active_fields())}")
    
    # Show field groups
    from multiagenticswarm.core.state_config import FieldGroup
    print(f"\n🏷️  Available field groups:")
    for group in FieldGroup:
        fields_in_group = [f for f in config.get_active_fields().values() if f.group == group]
        print(f"   {group.value}: {len(fields_in_group)} fields")
    
    # Demonstrate feature flag control
    print(f"\n🎛️  Feature flag control:")
    original_count = len(config.get_active_fields())
    print(f"   Before disabling streaming: {original_count} fields")
    
    config.enable_field_group(FieldGroup.STREAMING, False)
    new_count = len(config.get_active_fields())
    print(f"   After disabling streaming: {new_count} fields")
    print(f"   Difference: {original_count - new_count} fields disabled")
    
    # Re-enable for other demos
    config.enable_field_group(FieldGroup.STREAMING, True)


def demo_memory_management():
    """Demonstrate memory management and cleanup policies."""
    print("\n" + "=" * 60)
    print("3. MEMORY MANAGEMENT DEMONSTRATION")
    print("=" * 60)
    
    config = get_state_config()
    
    # Show fields with memory policies
    print(f"\n🧠 Fields with memory management policies:")
    for field_name, field_config in config.get_active_fields().items():
        if field_config.memory_policy:
            policy = field_config.memory_policy
            print(f"   {field_name}:")
            print(f"      Max entries: {policy.max_entries}")
            print(f"      Archive after: {policy.archive_after_hours} hours")
            if policy.archive_location:
                print(f"      Archive to: {policy.archive_location}")
    
    # Demonstrate cleanup
    print(f"\n🧹 Memory cleanup demonstration:")
    test_state = {
        "execution_trace": [{"id": i, "event": f"event_{i}"} for i in range(1500)],
        "messages": [],
        "subtasks": []
    }
    
    print(f"   Before cleanup: execution_trace has {len(test_state['execution_trace'])} entries")
    cleaned_state = config.apply_memory_policies(test_state)
    print(f"   After cleanup: execution_trace has {len(cleaned_state['execution_trace'])} entries")


def demo_backwards_compatibility():
    """Demonstrate backwards compatibility features."""
    print("\n" + "=" * 60)
    print("4. BACKWARDS COMPATIBILITY DEMONSTRATION")
    print("=" * 60)
    
    # Create states using both methods
    print(f"\n🔄 State creation comparison:")
    
    # Static (original) method
    static_state = create_initial_state(collaboration_prompt="Test collaboration")
    print(f"   Static state fields: {len(static_state)} fields")
    
    # Dynamic method
    dynamic_state = create_initial_state(use_dynamic_config=True, collaboration_prompt="Test collaboration")
    print(f"   Dynamic state fields: {len(dynamic_state)} fields")
    
    # They should have the same basic structure
    common_fields = set(static_state.keys()) & set(dynamic_state.keys())
    print(f"   Common fields: {len(common_fields)} fields")
    
    # Validation works with both
    print(f"\n✅ Validation compatibility:")
    static_valid = validate_state(static_state, use_dynamic_config=False)
    dynamic_valid = validate_state(dynamic_state, use_dynamic_config=True)
    print(f"   Static state valid: {static_valid}")
    print(f"   Dynamic state valid: {dynamic_valid}")


def demo_migration_enhancements():
    """Demonstrate enhanced migration capabilities."""
    print("\n" + "=" * 60)
    print("5. MIGRATION ENHANCEMENTS DEMONSTRATION")
    print("=" * 60)
    
    # Simulate an old state that needs migration
    old_state = {
        "state_version": "1.0.0",
        "messages": [],
        "subtasks": [],
        "agent_outputs": {"agent1": "simple_output"},  # Old format
        "execution_trace": [{"event": "start"}],  # Missing timestamp
        # ... other required fields would be here in a real scenario
        "current_task": None,
        "task_progress": {},
        "task_metadata": {},
        "current_agent": None,
        "next_agent": None,
        "agent_queue": [],
        "agent_status": {},
        "tool_calls": [],
        "tool_results": {},
        "tool_permissions": {},
        "pending_tools": [],
        "tool_errors": [],
        "collaboration_prompt": None,
        "coordination_rules": [],
        "agent_roles": {},
        "workflow_pattern": None,
        "decision_points": [],
        "short_term_memory": {},
        "working_memory": {},
        "episodic_memory": [],
        "shared_memory": {},
        "private_memory": {},
        "agent_messages": [],
        "help_requests": [],
        "broadcast_messages": [],
        "pending_responses": [],
        "should_continue": True,
        "requires_human_approval": False,
        "interrupt_checkpoint": None,
        "resume_point": None,
        "execution_mode": "sequential",
        "thread_id": None,
        "checkpoint_id": None,
        "checkpoint_ts": None,
        "parent_checkpoint_id": None,
        "checkpoint_ns": None,
        "checkpoint_metadata": {},
        "is_resuming": False,
        "graph_path": [],
        "pending_tasks": [],
        "branch_results": {},
        "channel_values": {},
        "config": None,
        "recursion_limit": 25,
        "stream_mode": None,
        "partial_updates": [],
        "stream_metadata": {},
        "subgraph_states": {},
        "parent_graph_id": None,
        "subgraph_configs": {},
        "interrupt_before": [],
        "interrupt_after": [],
        "pending_human_input": None,
        "error_log": [],
        "performance_metrics": {},
        "debug_flags": {}
    }
    
    print(f"\n🔄 Migration demonstration:")
    print(f"   Original version: {old_state['state_version']}")
    
    # Migrate with dynamic config
    migrated_state = auto_migrate_state(old_state, use_dynamic_config=True)
    print(f"   Migrated version: {migrated_state['state_version']}")
    
    # Check agent_outputs conversion
    print(f"\n🤖 Agent outputs migration:")
    print(f"   Before: {old_state['agent_outputs']['agent1']}")
    print(f"   After: {type(migrated_state['agent_outputs']['agent1']).__name__} with keys: {list(migrated_state['agent_outputs']['agent1'].keys())}")


def demo_field_documentation():
    """Demonstrate comprehensive field documentation."""
    print("\n" + "=" * 60)
    print("6. FIELD DOCUMENTATION DEMONSTRATION")
    print("=" * 60)
    
    docs = get_field_documentation()
    
    # Show a few examples of well-documented fields
    example_fields = ["messages", "subtasks", "execution_trace", "current_task"]
    
    for field_name in example_fields:
        if field_name in docs:
            doc = docs[field_name]
            print(f"\n📄 {field_name}:")
            print(f"   Description: {doc['description']}")
            print(f"   Reducer: {doc['reducer_type']}")
            print(f"   Rationale: {doc['design_rationale'][:100]}...")
            print(f"   Group: {doc['group']}")


def main():
    """Run all demonstrations."""
    print("🚀 MULTIAGENTICSWARM ENHANCED STATE MANAGEMENT DEMO")
    print("This demo showcases the new dynamic configuration capabilities")
    
    try:
        demo_reducer_enhancements()
        demo_dynamic_configuration()
        demo_memory_management()
        demo_backwards_compatibility()
        demo_migration_enhancements()
        demo_field_documentation()
        
        print("\n" + "=" * 60)
        print("✅ DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nKey benefits of the enhanced state management:")
        print("• 🔄 Proper reducers for all append-only fields")
        print("• ⚙️  Dynamic field configuration with feature flags")
        print("• 🧠 Memory management with automatic cleanup")
        print("• 🔄 Enhanced migration capabilities")
        print("• ↩️  Full backwards compatibility")
        print("• 📚 Comprehensive field documentation")
        print("• 🧪 Extensive test coverage")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()