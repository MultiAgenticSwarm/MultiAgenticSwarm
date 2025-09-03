"""
Tests for dynamic state configuration functionality.
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List

from multiagenticswarm.core.state_config import (
    StateConfiguration,
    FieldConfig,
    MemoryPolicy,
    FieldGroup,
    ReducerType,
    get_state_config,
    create_dynamic_agent_state_class,
    get_field_documentation
)
from multiagenticswarm.core.state import (
    create_initial_state,
    validate_state,
    auto_migrate_state
)


class TestStateConfiguration:
    """Test the StateConfiguration class."""
    
    def test_state_config_initialization(self):
        """Test that state configuration initializes correctly."""
        config = StateConfiguration()
        
        # Check that default fields are configured
        assert len(config.fields) > 0
        assert "messages" in config.fields
        assert "subtasks" in config.fields
        assert "tool_calls" in config.fields
        
        # Check that feature flags are set
        assert config.feature_flags["enable_message_management"] is True
        assert config.feature_flags["enable_task_management"] is True
    
    def test_get_field_config(self):
        """Test getting field configuration."""
        config = StateConfiguration()
        
        messages_config = config.get_field_config("messages")
        assert messages_config is not None
        assert messages_config.reducer_type == ReducerType.ADD_MESSAGES
        assert messages_config.group == FieldGroup.MESSAGE_MANAGEMENT
        
        nonexistent_config = config.get_field_config("nonexistent_field")
        assert nonexistent_config is None
    
    def test_get_active_fields(self):
        """Test getting active fields based on feature flags."""
        config = StateConfiguration()
        
        # All fields should be active by default
        active_fields = config.get_active_fields()
        assert len(active_fields) > 0
        assert "messages" in active_fields
        
        # Disable a field group
        config.enable_field_group(FieldGroup.MESSAGE_MANAGEMENT, False)
        active_fields = config.get_active_fields()
        assert "messages" not in active_fields
        
        # Re-enable the field group
        config.enable_field_group(FieldGroup.MESSAGE_MANAGEMENT, True)
        active_fields = config.get_active_fields()
        assert "messages" in active_fields
    
    def test_field_validation(self):
        """Test field validation functionality."""
        config = StateConfiguration()
        
        # Test valid field value
        errors = config.validate_field_value("messages", [])
        assert len(errors) == 0
        
        # Test invalid field value type
        errors = config.validate_field_value("messages", "invalid")
        assert len(errors) > 0
        assert "must be of type" in errors[0]
        
        # Test unknown field
        errors = config.validate_field_value("unknown_field", "value")
        assert len(errors) == 1
        assert "Unknown field" in errors[0]
    
    def test_memory_policies(self):
        """Test memory policy application."""
        config = StateConfiguration()
        
        # Create test state with long lists
        test_state = {
            "messages": [{"id": i, "content": f"message_{i}"} for i in range(2000)],
            "execution_trace": [{"id": i, "event": f"event_{i}"} for i in range(1500)],
            "tool_calls": [{"id": i, "call": f"call_{i}"} for i in range(1200)],
        }
        
        cleaned_state = config.apply_memory_policies(test_state)
        
        # Check that lists were trimmed based on memory policies
        assert len(cleaned_state["messages"]) <= 1000  # Based on default memory policy
        assert len(cleaned_state["execution_trace"]) <= 1000
        assert len(cleaned_state["tool_calls"]) <= 1000


class TestDynamicStateCreation:
    """Test dynamic state creation functionality."""
    
    def test_create_initial_state_dynamic(self):
        """Test creating initial state with dynamic configuration."""
        state = create_initial_state(use_dynamic_config=True)
        
        # Verify that state contains expected fields
        config = get_state_config()
        active_fields = config.get_active_fields()
        
        for field_name in active_fields.keys():
            assert field_name in state
        
        # Verify that default values are properly set
        assert isinstance(state.get("messages", []), list)
        assert isinstance(state.get("subtasks", []), list)
        assert isinstance(state.get("task_progress", {}), dict)
    
    def test_create_initial_state_backwards_compatibility(self):
        """Test that default behavior is unchanged for backwards compatibility."""
        # Default behavior should be static configuration
        state_static = create_initial_state()
        state_dynamic = create_initial_state(use_dynamic_config=False)
        
        # Both should have the same structure
        assert set(state_static.keys()) == set(state_dynamic.keys())
        
        # Values should be the same for basic fields
        assert state_static["messages"] == state_dynamic["messages"]
        assert state_static["subtasks"] == state_dynamic["subtasks"]
        assert state_static["should_continue"] == state_dynamic["should_continue"]
    
    def test_validate_state_dynamic(self):
        """Test state validation with dynamic configuration."""
        state = create_initial_state(use_dynamic_config=True)
        
        # Should validate successfully
        assert validate_state(state, use_dynamic_config=True) is True
        
        # Test with missing required field
        incomplete_state = dict(state)
        del incomplete_state["messages"]
        
        with pytest.raises(ValueError) as exc_info:
            validate_state(incomplete_state, use_dynamic_config=True)
        assert "Missing required field: messages" in str(exc_info.value)


class TestReducerIntegration:
    """Test that new reducers work correctly with the AgentState."""
    
    def test_subtasks_reducer(self):
        """Test that subtasks field uses operator.add correctly."""
        from multiagenticswarm.core.state_reducers import apply_reducer
        import operator
        
        current = [{"task": "task1", "status": "completed"}]
        update = [{"task": "task2", "status": "in_progress"}]
        
        # The reducer registry includes subtasks, so it will use append (operator.add) behavior
        result = apply_reducer("subtasks", current, update)
        
        # Since subtasks uses append behavior, the result should be the concatenation of current and update
        # The test should expect both tasks in the result
        assert result == [
            {"task": "task1", "status": "completed"},
            {"task": "task2", "status": "in_progress"}
        ]
    
    def test_tool_calls_reducer(self):
        """Test that tool_calls field uses operator.add correctly."""
        from multiagenticswarm.core.state_reducers import apply_reducer
        
        current = [{"tool": "search", "args": {"query": "test1"}}]
        update = [{"tool": "calculator", "args": {"expression": "2+2"}}]
        
        result = apply_reducer("tool_calls", current, update)
        
        # Should concatenate the lists
        assert len(result) == 2
        assert result[0]["tool"] == "search"
        assert result[1]["tool"] == "calculator"
    
    def test_execution_trace_reducer(self):
        """Test that execution_trace field uses operator.add correctly."""
        from multiagenticswarm.core.state_reducers import apply_reducer
        
        current = [{"event": "start", "timestamp": "2024-01-01T00:00:00Z"}]
        update = [{"event": "end", "timestamp": "2024-01-01T00:01:00Z"}]
        
        result = apply_reducer("execution_trace", current, update)
        
        # Should concatenate the lists
        assert len(result) == 2
        assert result[0]["event"] == "start"
        assert result[1]["event"] == "end"


class TestMigrationEnhancements:
    """Test enhanced migration functionality."""
    
    def test_auto_migrate_with_dynamic_config(self):
        """Test auto migration with dynamic configuration."""
        # Create an old-format state with all required fields
        old_state = {
            "state_version": "1.0.0",
            "messages": [],
            "current_task": None,
            "subtasks": [],
            "task_progress": {},
            "task_metadata": {},
            "current_agent": None,
            "next_agent": None,
            "agent_outputs": {"agent1": "simple_output"},
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
            "execution_trace": [{"event": "test"}],  # Missing timestamp
            "error_log": [],
            "performance_metrics": {},
            "debug_flags": {}
        }
        
        migrated = auto_migrate_state(old_state, use_dynamic_config=True)
        
        # Should have current version
        assert migrated["state_version"] == "1.1.0"  # After migration
        
        # Agent outputs should be converted to structured format
        assert isinstance(migrated["agent_outputs"]["agent1"], dict)
        assert "current" in migrated["agent_outputs"]["agent1"]
        assert "history" in migrated["agent_outputs"]["agent1"]
        
        # Execution trace should have timestamps added
        if migrated["execution_trace"]:
            assert "timestamp" in migrated["execution_trace"][0]
    
    def test_migration_backwards_compatibility(self):
        """Test that migration maintains backwards compatibility."""
        # Create current state
        current_state = create_initial_state()
        
        # Auto migration should work without issues
        migrated = auto_migrate_state(current_state)
        
        # Should be essentially the same (no changes needed)
        assert migrated["state_version"] == current_state["state_version"]


class TestFieldDocumentation:
    """Test field documentation functionality."""
    
    def test_get_field_documentation(self):
        """Test getting field documentation."""
        docs = get_field_documentation()
        
        # Should have documentation for all active fields
        assert len(docs) > 0
        assert "messages" in docs
        
        # Check structure of documentation
        messages_doc = docs["messages"]
        assert "description" in messages_doc
        assert "reducer_type" in messages_doc
        assert "design_rationale" in messages_doc
        assert "conflict_resolution" in messages_doc
        assert "group" in messages_doc
    
    def test_field_config_annotations(self):
        """Test that field configurations generate correct type annotations."""
        config = get_state_config()
        
        messages_config = config.get_field_config("messages")
        annotated_type = messages_config.get_annotated_type()
        
        # Should be properly annotated
        assert hasattr(annotated_type, "__metadata__")
        
        # Reducer function should be accessible
        reducer_func = messages_config.get_reducer_function()
        assert reducer_func is not None


class TestMemoryManagement:
    """Test memory management enhancements."""
    
    def test_memory_policy_creation(self):
        """Test creating memory policies."""
        policy = MemoryPolicy(
            max_entries=100,
            archive_after_hours=24,
            cleanup_strategy="fifo",
            archive_location="persistent_storage"
        )
        
        assert policy.max_entries == 100
        assert policy.archive_after_hours == 24
        assert policy.cleanup_strategy == "fifo"
        assert policy.archive_location == "persistent_storage"
    
    def test_field_config_with_memory_policy(self):
        """Test field configuration with memory management."""
        policy = MemoryPolicy(max_entries=50, archive_after_hours=12)
        
        config = FieldConfig(
            name="test_field",
            field_type=List[Dict[str, Any]],
            reducer_type=ReducerType.OPERATOR_ADD,
            group=FieldGroup.DEBUGGING,
            memory_policy=policy
        )
        
        assert config.memory_policy.max_entries == 50
        assert config.memory_policy.archive_after_hours == 12
    
    def test_state_cleanup_with_policies(self):
        """Test state cleanup based on memory policies."""
        config = get_state_config()
        
        # Create a state with overly long lists
        test_state = {
            "execution_trace": [{"id": i} for i in range(2000)],
            "error_log": [{"id": i} for i in range(1000)],
            "messages": [],  # Empty, should remain unchanged
        }
        
        cleaned = config.apply_memory_policies(test_state)
        
        # Lists should be trimmed based on their memory policies
        trace_config = config.get_field_config("execution_trace")
        if trace_config and trace_config.memory_policy:
            max_entries = trace_config.memory_policy.max_entries
            if max_entries:
                assert len(cleaned["execution_trace"]) <= max_entries
        
        # Messages should be unchanged (empty list)
        assert cleaned["messages"] == []


class TestDynamicAgentStateClass:
    """Test dynamic AgentState class generation."""
    
    def test_create_dynamic_agent_state_class(self):
        """Test creating a dynamic AgentState class."""
        AgentStateDynamic = create_dynamic_agent_state_class()
        
        # Should have proper annotations
        assert hasattr(AgentStateDynamic, "__annotations__")
        annotations = AgentStateDynamic.__annotations__
        
        # Should include expected fields
        config = get_state_config()
        active_fields = config.get_active_fields()
        
        for field_name in active_fields.keys():
            assert field_name in annotations
    
    def test_dynamic_class_type_checking(self):
        """Test that dynamic class supports proper type checking."""
        AgentStateDynamic = create_dynamic_agent_state_class()
        
        # Should be a TypedDict
        assert issubclass(AgentStateDynamic, dict)
        
        # Should have the right name
        assert AgentStateDynamic.__name__ == "AgentStateDynamic"