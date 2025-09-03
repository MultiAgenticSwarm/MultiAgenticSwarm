"""
Comprehensive tests for state management functionality.
"""

import pytest
import copy
from datetime import datetime, timezone
from typing import Dict, Any, List

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from multiagenticswarm.core.state import (
    AgentState,
    SCHEMA_VERSION,
    create_initial_state,
    validate_state,
    serialize_state,
    deserialize_state,
    log_state_change
)
from multiagenticswarm.core.state_reducers import (
    merge_agent_outputs,
    aggregate_progress,
    resolve_permissions,
    merge_tool_results,
    merge_memory_layers,
    merge_communication_messages,
    merge_execution_trace,
    apply_reducer,
    merge_states,
    REDUCERS
)


class TestAgentStateCreation:
    """Test AgentState creation and initialization."""
    
    def test_create_initial_state_minimal(self):
        """Test creating minimal initial state."""
        state = create_initial_state()
        
        # Verify all required fields are present
        assert "messages" in state
        assert "current_task" in state
        assert "subtasks" in state
        assert "task_progress" in state
        assert "agent_outputs" in state
        assert "tool_permissions" in state
        assert "collaboration_prompt" in state
        assert "state_version" in state
        
        # Verify default values
        assert state["messages"] == []
        assert state["current_task"] is None
        assert state["subtasks"] == []
        assert state["should_continue"] is True
        assert state["state_version"] == SCHEMA_VERSION
        assert len(state["execution_trace"]) == 1  # Initial creation event
        
    def test_create_initial_state_with_prompt(self):
        """Test creating initial state with collaboration prompt."""
        prompt = "Three agents work together on coding tasks"
        state = create_initial_state(collaboration_prompt=prompt)
        
        assert state["collaboration_prompt"] == prompt
        
    def test_create_initial_state_with_message(self):
        """Test creating initial state with initial message."""
        message = "Hello, let's start working!"
        state = create_initial_state(initial_message=message)
        
        assert len(state["messages"]) == 1
        assert isinstance(state["messages"][0], HumanMessage)
        assert state["messages"][0].content == message
        assert state["performance_metrics"]["total_messages"] == 1
        
    def test_create_initial_state_with_overrides(self):
        """Test creating initial state with field overrides."""
        state = create_initial_state(
            execution_mode="parallel",
            debug_flags={"trace_execution": True}
        )
        
        assert state["execution_mode"] == "parallel"
        assert state["debug_flags"]["trace_execution"] is True
        
    def test_create_initial_state_unknown_field_warning(self, caplog):
        """Test warning when providing unknown field."""
        state = create_initial_state(unknown_field="test")
        
        # Should still create valid state
        assert "state_version" in state
        # Should log warning about unknown field
        assert "unknown state field" in caplog.text.lower()


class TestStateValidation:
    """Test state validation functionality."""
    
    def test_validate_valid_state(self):
        """Test validation of a valid state."""
        state = create_initial_state()
        assert validate_state(state) is True
        
    def test_validate_missing_required_field(self):
        """Test validation failure for missing required field."""
        state = create_initial_state()
        del state["messages"]  # Remove required field
        
        with pytest.raises(ValueError, match="Missing required field: messages"):
            validate_state(state)
            
    def test_validate_wrong_type_field(self):
        """Test validation failure for wrong type."""
        state = create_initial_state()
        state["messages"] = "not a list"  # Wrong type
        
        with pytest.raises(ValueError, match="must be a list"):
            validate_state(state)
            
    def test_validate_version_mismatch_warning(self, caplog):
        """Test warning for version mismatch."""
        state = create_initial_state()
        state["state_version"] = "0.5.0"  # Different version
        
        # Should still validate but log warning
        assert validate_state(state) is True
        assert "version mismatch" in caplog.text.lower()


class TestStateSerialization:
    """Test state serialization and deserialization."""
    
    def test_serialize_empty_state(self):
        """Test serializing state with no messages."""
        state = create_initial_state()
        serialized = serialize_state(state)
        
        assert isinstance(serialized, dict)
        assert "messages" in serialized
        assert serialized["messages"] == []
        
    def test_serialize_state_with_messages(self):
        """Test serializing state with messages."""
        state = create_initial_state()
        state["messages"] = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!"),
            SystemMessage(content="System message")
        ]
        
        serialized = serialize_state(state)
        
        assert len(serialized["messages"]) == 3
        assert serialized["messages"][0]["type"] == "HumanMessage"
        assert serialized["messages"][0]["content"] == "Hello"
        assert serialized["messages"][1]["type"] == "AIMessage"
        assert serialized["messages"][1]["content"] == "Hi there!"
        
    def test_deserialize_state(self):
        """Test deserializing state back to original form."""
        # Create state with messages
        original_state = create_initial_state()
        original_state["messages"] = [
            HumanMessage(content="Hello", id="msg1"),
            AIMessage(content="Hi!", id="msg2")
        ]
        
        # Serialize and deserialize
        serialized = serialize_state(original_state)
        deserialized = deserialize_state(serialized)
        
        # Check messages were reconstructed correctly
        assert len(deserialized["messages"]) == 2
        assert isinstance(deserialized["messages"][0], HumanMessage)
        assert isinstance(deserialized["messages"][1], AIMessage)
        assert deserialized["messages"][0].content == "Hello"
        assert deserialized["messages"][1].content == "Hi!"
        
    def test_roundtrip_serialization(self):
        """Test full roundtrip serialization preserves state."""
        state = create_initial_state(
            collaboration_prompt="Test prompt",
            initial_message="Initial message"
        )
        state["current_task"] = "Test task"
        state["agent_outputs"]["agent1"] = {"result": "test"}
        
        # Roundtrip
        serialized = serialize_state(state)
        deserialized = deserialize_state(serialized)
        
        # Verify key fields preserved
        assert deserialized["collaboration_prompt"] == "Test prompt"
        assert deserialized["current_task"] == "Test task"
        assert deserialized["agent_outputs"]["agent1"]["result"] == "test"
        assert len(deserialized["messages"]) == 1


class TestStateLogging:
    """Test state change logging functionality."""
    
    def test_log_state_change_disabled(self):
        """Test logging when trace_execution is disabled."""
        state = create_initial_state()
        state["debug_flags"]["trace_execution"] = False
        
        initial_trace_length = len(state["execution_trace"])
        log_state_change(state, "test_change", {"detail": "test"}, "test_agent")
        
        # Should not add to trace when disabled
        assert len(state["execution_trace"]) == initial_trace_length
        
    def test_log_state_change_enabled(self):
        """Test logging when trace_execution is enabled."""
        state = create_initial_state()
        state["debug_flags"]["trace_execution"] = True
        
        initial_trace_length = len(state["execution_trace"])
        log_state_change(state, "test_change", {"detail": "test"}, "test_agent")
        
        # Should add to trace when enabled
        assert len(state["execution_trace"]) == initial_trace_length + 1
        
        new_entry = state["execution_trace"][-1]
        assert new_entry["change_type"] == "test_change"
        assert new_entry["agent"] == "test_agent"
        assert new_entry["details"]["detail"] == "test"
        assert "timestamp" in new_entry


class TestAgentOutputsReducer:
    """Test the merge_agent_outputs reducer."""
    
    def test_merge_agent_outputs_empty_current(self):
        """Test merging into empty current state."""
        current = {}
        update = {"agent1": {"result": "test_result"}}
        
        result = merge_agent_outputs(current, update)
        
        assert "agent1" in result
        assert result["agent1"]["current"]["result"] == "test_result"
        assert result["agent1"]["total_outputs"] == 1
        assert len(result["agent1"]["history"]) == 0  # First output has empty history
        
    def test_merge_agent_outputs_existing_agent(self):
        """Test merging with existing agent output."""
        current = {
            "agent1": {
                "current": {"result": "old_result"},
                "history": [],
                "last_updated": "2023-01-01T00:00:00Z",
                "total_outputs": 1
            }
        }
        update = {"agent1": {"result": "new_result"}}
        
        result = merge_agent_outputs(current, update)
        
        assert result["agent1"]["current"]["result"] == "new_result"
        assert result["agent1"]["total_outputs"] == 2
        assert len(result["agent1"]["history"]) == 1
        assert result["agent1"]["history"][0]["output"]["result"] == "old_result"
        
    def test_merge_agent_outputs_same_output(self):
        """Test merging same output doesn't duplicate history."""
        current = {
            "agent1": {
                "current": {"result": "same_result"},
                "history": [],
                "total_outputs": 1,
                "last_updated": "2024-01-01T00:00:00Z"
            }
        }
        update = {"agent1": {"result": "same_result"}}
        
        result = merge_agent_outputs(current, update)
        
        # History should remain empty since output is the same
        assert len(result["agent1"]["history"]) == 0
        assert result["agent1"]["total_outputs"] == 2


class TestProgressReducer:
    """Test the aggregate_progress reducer."""
    
    def test_aggregate_progress_new_tasks(self):
        """Test aggregating progress for new tasks."""
        current = {}
        update = {"task1": 25.5, "task2": 75.0}
        
        result = aggregate_progress(current, update)
        
        assert result["task1"] == 25.5
        assert result["task2"] == 75.0
        
    def test_aggregate_progress_monotonic(self):
        """Test progress is monotonic (no regression)."""
        current = {"task1": 50.0, "task2": 80.0}
        update = {"task1": 75.0, "task2": 70.0}  # task2 tries to go backwards
        
        result = aggregate_progress(current, update)
        
        assert result["task1"] == 75.0  # Increased normally
        assert result["task2"] == 80.0  # Kept higher value
        
    def test_aggregate_progress_bounds_checking(self):
        """Test progress values are bounded to [0, 100]."""
        current = {}
        update = {"task1": -10, "task2": 150, "task3": 50.5}
        
        result = aggregate_progress(current, update)
        
        assert result["task1"] == 0.0   # Clamped to 0
        assert result["task2"] == 100.0 # Clamped to 100
        assert result["task3"] == 50.5  # Normal value
        
    def test_aggregate_progress_invalid_values(self, caplog):
        """Test handling of invalid progress values."""
        current = {}
        update = {"task1": "invalid", "task2": 50}
        
        result = aggregate_progress(current, update)
        
        assert "task1" not in result  # Invalid value ignored
        assert result["task2"] == 50
        assert "invalid progress value" in caplog.text.lower()


class TestPermissionsReducer:
    """Test the resolve_permissions reducer."""
    
    def test_resolve_permissions_new_agent(self):
        """Test resolving permissions for new agent."""
        current = {}
        update = {"agent1": ["tool1", "tool2"]}
        
        result = resolve_permissions(current, update)
        
        assert set(result["agent1"]) == {"tool1", "tool2"}
        
    def test_resolve_permissions_intersection(self):
        """Test permission intersection (security-first)."""
        current = {"agent1": ["tool1", "tool2", "tool3"]}
        update = {"agent1": ["tool2", "tool3", "tool4"]}
        
        result = resolve_permissions(current, update)
        
        # Should only have intersection
        assert set(result["agent1"]) == {"tool2", "tool3"}
        
    def test_resolve_permissions_revoke_all(self):
        """Test revoking all permissions."""
        current = {"agent1": ["tool1", "tool2"]}
        update = {"agent1": []}  # Empty list revokes all
        
        result = resolve_permissions(current, update)
        
        assert result["agent1"] == []
        
    def test_resolve_permissions_no_intersection(self, caplog):
        """Test conflict with no intersection."""
        current = {"agent1": ["tool1", "tool2"]}
        update = {"agent1": ["tool3", "tool4"]}  # No overlap
        
        result = resolve_permissions(current, update)
        
        # Most restrictive: no permissions
        assert result["agent1"] == []
        assert "permission conflict" in caplog.text.lower()
        
    def test_resolve_permissions_invalid_format(self, caplog):
        """Test handling invalid permission format."""
        current = {}
        update = {"agent1": "not_a_list"}
        
        result = resolve_permissions(current, update)
        
        assert "agent1" not in result
        assert "invalid permissions format" in caplog.text.lower()


class TestCommunicationMessagesReducer:
    """Test the merge_communication_messages reducer."""
    
    def test_merge_communication_messages_empty(self):
        """Test merging into empty message list."""
        current = []
        update = [
            {"id": "msg1", "content": "Hello", "from": "agent1"},
            {"id": "msg2", "content": "Hi", "from": "agent2"}
        ]
        
        result = merge_communication_messages(current, update)
        
        assert len(result) == 2
        assert result[0]["id"] == "msg1"
        assert result[1]["id"] == "msg2"
        
    def test_merge_communication_messages_deduplication(self):
        """Test message deduplication by ID."""
        current = [{"id": "msg1", "content": "Hello", "timestamp": "2023-01-01T00:00:00Z"}]
        update = [
            {"id": "msg1", "content": "Hello again"},  # Duplicate ID
            {"id": "msg2", "content": "New message"}
        ]
        
        result = merge_communication_messages(current, update)
        
        assert len(result) == 2  # Duplicate should be skipped
        assert any(msg["id"] == "msg2" for msg in result)
        
    def test_merge_communication_messages_timestamp_ordering(self):
        """Test messages are ordered by timestamp."""
        current = []
        update = [
            {"id": "msg2", "content": "Second", "timestamp": "2023-01-01T02:00:00Z"},
            {"id": "msg1", "content": "First", "timestamp": "2023-01-01T01:00:00Z"},
            {"id": "msg3", "content": "Third", "timestamp": "2023-01-01T03:00:00Z"}
        ]
        
        result = merge_communication_messages(current, update)
        
        # Should be ordered by timestamp
        assert result[0]["id"] == "msg1"
        assert result[1]["id"] == "msg2"
        assert result[2]["id"] == "msg3"
        
    def test_merge_communication_messages_auto_timestamp(self):
        """Test automatic timestamp addition."""
        current = []
        update = [{"id": "msg1", "content": "No timestamp"}]
        
        result = merge_communication_messages(current, update)
        
        assert "timestamp" in result[0]
        assert result[0]["timestamp"] is not None


class TestStateReducerRegistry:
    """Test the reducer registry and application."""
    
    def test_apply_reducer_known_field(self):
        """Test applying reducer for known field."""
        current = {"task1": 50.0}
        update = {"task1": 75.0}
        
        result = apply_reducer("task_progress", current, update)
        
        assert result["task1"] == 75.0
        
    def test_apply_reducer_unknown_field(self):
        """Test applying reducer for unknown field (last-write-wins)."""
        current = "old_value"
        update = "new_value"
        
        result = apply_reducer("unknown_field", current, update)
        
        assert result == "new_value"
        
    def test_apply_reducer_none_update(self):
        """Test applying reducer with None update."""
        current = "current_value"
        update = None
        
        result = apply_reducer("unknown_field", current, update)
        
        # With enhanced last-write-wins, None can override existing values
        assert result is None
        
    def test_merge_states_multiple_fields(self):
        """Test merging multiple state fields."""
        base_state = {
            "task_progress": {"task1": 25.0},
            "agent_outputs": {},
            "current_task": "old_task"
        }
        
        updates = {
            "task_progress": {"task1": 50.0, "task2": 30.0},
            "agent_outputs": {"agent1": {"result": "test"}},
            "current_task": "new_task"
        }
        
        result = merge_states(base_state, updates)
        
        # Check progress was aggregated correctly
        assert result["task_progress"]["task1"] == 50.0
        assert result["task_progress"]["task2"] == 30.0
        
        # Check agent outputs were merged
        assert "agent1" in result["agent_outputs"]
        
        # Check simple field was overwritten
        assert result["current_task"] == "new_task"


class TestReducerEdgeCases:
    """Test edge cases and error handling in reducers."""
    
    def test_merge_agent_outputs_none_inputs(self):
        """Test merge_agent_outputs with None inputs."""
        assert merge_agent_outputs(None, None) == {}
        assert merge_agent_outputs({}, None) == {}
        
        result = merge_agent_outputs(None, {"agent1": {"result": "test"}})
        assert "agent1" in result
        assert result["agent1"]["current"] == {"result": "test"}
        
    def test_aggregate_progress_none_inputs(self):
        """Test aggregate_progress with None inputs."""
        assert aggregate_progress(None, None) == {}
        assert aggregate_progress({}, None) == {}
        assert aggregate_progress(None, {"task1": 50}) == {"task1": 50.0}
        
    def test_resolve_permissions_none_inputs(self):
        """Test resolve_permissions with None inputs."""
        assert resolve_permissions(None, None) == {}
        assert resolve_permissions({}, None) == {}
        assert resolve_permissions(None, {"agent1": ["tool1"]}) == {"agent1": ["tool1"]}

    def test_merge_communication_messages_empty_list_clearing(self):
        """Test that empty list updates clear the current messages."""
        from multiagenticswarm.core.state_reducers import merge_communication_messages
        
        # Start with some messages
        current = [
            {"id": "msg1", "message": "first message"},
            {"id": "msg2", "message": "second message"}
        ]
        
        # Verify we have messages
        assert len(current) == 2
        
        # Clear with empty list
        result = merge_communication_messages(current, [])
        assert len(result) == 0
        
        # Test that None update doesn't clear
        result = merge_communication_messages(current, None)
        assert len(result) == 2


if __name__ == "__main__":
    pytest.main([__file__])