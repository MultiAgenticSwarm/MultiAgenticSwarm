"""
Tests for the core state management system.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from multiagenticswarm.core.state import (
    CURRENT_STATE_VERSION,
    AgentState,
    create_initial_state,
    deserialize_state_from_checkpoint,
    serialize_state_for_checkpoint,
    validate_state_schema,
)
from multiagenticswarm.core.state_reducers import (
    aggregate_progress,
    merge_agent_outputs,
    merge_dict_update,
    merge_error_log,
    merge_execution_trace,
    merge_help_requests,
    merge_list_append,
    merge_tool_results,
    resolve_permissions,
)


class TestAgentState:
    """Test AgentState schema and related functions."""

    def test_create_initial_state_minimal(self):
        """Test creating initial state with minimal parameters."""
        prompt = "Test collaboration prompt"
        state = create_initial_state(prompt)

        assert state["collaboration_prompt"] == prompt
        assert state["state_version"] == CURRENT_STATE_VERSION
        assert state["should_continue"] is True
        assert state["requires_human_approval"] is False
        assert isinstance(state["messages"], list)
        assert len(state["messages"]) == 0
        assert isinstance(state["task_progress"], dict)
        assert isinstance(state["agent_outputs"], dict)

    def test_create_initial_state_with_message(self):
        """Test creating initial state with an initial message."""
        prompt = "Test prompt"
        initial_msg = HumanMessage(content="Hello, agents!")

        state = create_initial_state(prompt, initial_message=initial_msg)

        assert len(state["messages"]) == 1
        assert state["messages"][0] == initial_msg

    def test_create_initial_state_with_roles(self):
        """Test creating initial state with agent roles."""
        prompt = "Test prompt"
        roles = {"agent1": "coordinator", "agent2": "executor"}

        state = create_initial_state(prompt, agent_roles=roles)

        assert state["agent_roles"] == roles

    def test_create_initial_state_custom_patterns(self):
        """Test creating initial state with custom patterns."""
        prompt = "Test prompt"
        workflow = "parallel"
        execution = "supervisor"

        state = create_initial_state(
            prompt, workflow_pattern=workflow, execution_mode=execution
        )

        assert state["workflow_pattern"] == workflow
        assert state["execution_mode"] == execution


class TestStateValidation:
    """Test state validation functions."""

    def test_validate_state_schema_valid(self):
        """Test validation with a valid state."""
        state = create_initial_state("test prompt")
        assert validate_state_schema(state) is True

    def test_validate_state_schema_missing_field(self):
        """Test validation with missing required field."""
        state = create_initial_state("test prompt")
        del state["current_task"]

        assert validate_state_schema(state) is False

    def test_validate_state_schema_wrong_type(self):
        """Test validation with wrong field type."""
        state = create_initial_state("test prompt")
        state["should_continue"] = "yes"  # Should be bool

        assert validate_state_schema(state) is False

    def test_validate_state_schema_empty_dict(self):
        """Test validation with empty dictionary."""
        assert validate_state_schema({}) is False


class TestStateSerialization:
    """Test state serialization for checkpointing."""

    def test_serialize_empty_messages(self):
        """Test serialization with empty messages."""
        state = create_initial_state("test prompt")
        serialized = serialize_state_for_checkpoint(state)

        assert "messages" in serialized
        assert isinstance(serialized["messages"], list)
        assert len(serialized["messages"]) == 0

    def test_serialize_with_messages(self):
        """Test serialization with actual messages."""
        msg = HumanMessage(content="Test message")
        state = create_initial_state("test prompt", initial_message=msg)

        serialized = serialize_state_for_checkpoint(state)

        assert len(serialized["messages"]) == 1
        # The message should be converted to a dictionary
        assert isinstance(serialized["messages"][0], dict)

    def test_deserialize_state(self):
        """Test state deserialization."""
        state = create_initial_state("test prompt")
        serialized = serialize_state_for_checkpoint(state)

        # Note: Current implementation just returns the serialized state
        # In a full implementation, this would reconstruct objects
        deserialized = deserialize_state_from_checkpoint(serialized)

        assert isinstance(deserialized, dict)


class TestMergeAgentOutputs:
    """Test merge_agent_outputs reducer."""

    def test_merge_empty_existing(self):
        """Test merging into empty existing outputs."""
        existing = {}
        new = {"agent1": {"result": "success", "data": 123}}

        result = merge_agent_outputs(existing, new)

        assert "agent1" in result
        assert result["agent1"]["current"] == {"result": "success", "data": 123}
        assert len(result["agent1"]["history"]) == 1
        assert "last_updated" in result["agent1"]

    def test_merge_existing_agent(self):
        """Test merging with existing agent output."""
        existing = {
            "agent1": {
                "current": {"result": "old", "data": 100},
                "history": [{"result": "old", "data": 100}],
                "last_updated": "2024-01-01T10:00:00",
            }
        }
        new = {"agent1": {"result": "new", "data": 200}}

        result = merge_agent_outputs(existing, new)

        assert result["agent1"]["current"] == {"result": "new", "data": 200}
        assert len(result["agent1"]["history"]) == 2
        assert result["agent1"]["history"][0] == {"result": "old", "data": 100}
        assert result["agent1"]["history"][1] == {"result": "new", "data": 200}

    def test_merge_history_limit(self):
        """Test that history is limited to 10 entries."""
        # Create existing state with 10 history entries
        history = [{"iteration": i} for i in range(10)]
        existing = {
            "agent1": {
                "current": {"iteration": 9},
                "history": history,
                "last_updated": "2024-01-01T10:00:00",
            }
        }
        new = {"agent1": {"iteration": 10}}

        result = merge_agent_outputs(existing, new)

        # Should still have 10 entries (oldest removed)
        assert len(result["agent1"]["history"]) == 10
        assert result["agent1"]["history"][0] == {"iteration": 1}
        assert result["agent1"]["history"][-1] == {"iteration": 10}


class TestAggregateProgress:
    """Test aggregate_progress reducer."""

    def test_aggregate_empty(self):
        """Test aggregating empty progress."""
        result = aggregate_progress({}, {"task1": 0.5})

        assert result["task1"] == 0.5
        assert result["_overall"] == 0.5

    def test_aggregate_multiple_tasks(self):
        """Test aggregating multiple task progress."""
        existing = {"task1": 0.3, "task2": 0.7}
        new = {"task3": 0.9}

        result = aggregate_progress(existing, new)

        assert result["task1"] == 0.3
        assert result["task2"] == 0.7
        assert result["task3"] == 0.9
        # Overall should be average: (0.3 + 0.7 + 0.9) / 3 = 0.633...
        assert abs(result["_overall"] - 0.6333333333333333) < 0.001

    def test_aggregate_update_existing(self):
        """Test updating existing task progress."""
        existing = {"task1": 0.3, "_overall": 0.3}
        new = {"task1": 0.8}

        result = aggregate_progress(existing, new)

        assert result["task1"] == 0.8
        assert result["_overall"] == 0.8


class TestResolvePermissions:
    """Test resolve_permissions reducer."""

    def test_resolve_new_agent(self):
        """Test adding permissions for new agent."""
        existing = {}
        new = {"agent1": ["tool1", "tool2"]}

        result = resolve_permissions(existing, new)

        assert result["agent1"] == ["tool1", "tool2"]

    def test_resolve_merge_permissions(self):
        """Test merging permissions (union approach)."""
        existing = {"agent1": ["tool1", "tool2"]}
        new = {"agent1": ["tool2", "tool3"]}

        result = resolve_permissions(existing, new)

        # Should have union of permissions
        assert set(result["agent1"]) == {"tool1", "tool2", "tool3"}

    def test_resolve_revoke_permissions(self):
        """Test revoking all permissions."""
        existing = {"agent1": ["tool1", "tool2"]}
        new = {"agent1": []}

        result = resolve_permissions(existing, new)

        assert result["agent1"] == []


class TestMergeToolResults:
    """Test merge_tool_results reducer."""

    def test_merge_new_tool_result(self):
        """Test adding result for new tool."""
        existing = {}
        new = {"tool1": {"output": "success", "status": "completed"}}

        result = merge_tool_results(existing, new)

        assert "tool1" in result
        assert result["tool1"]["latest"] == {"output": "success", "status": "completed"}
        assert result["tool1"]["execution_count"] == 1
        assert len(result["tool1"]["history"]) == 1

    def test_merge_existing_tool_result(self):
        """Test updating result for existing tool."""
        existing = {
            "tool1": {
                "latest": {"output": "old", "status": "completed"},
                "history": [{"output": "old", "status": "completed"}],
                "execution_count": 1,
                "last_executed": "2024-01-01T10:00:00",
            }
        }
        new = {"tool1": {"output": "new", "status": "completed"}}

        result = merge_tool_results(existing, new)

        assert result["tool1"]["latest"] == {"output": "new", "status": "completed"}
        assert result["tool1"]["execution_count"] == 2
        assert len(result["tool1"]["history"]) == 2


class TestMergeHelpRequests:
    """Test merge_help_requests reducer."""

    def test_merge_new_request(self):
        """Test adding new help request."""
        existing = []
        new = [
            {
                "topic": "debugging",
                "requesting_agent": "agent1",
                "details": "Need help with error",
            }
        ]

        result = merge_help_requests(existing, new)

        assert len(result) == 1
        assert result[0]["topic"] == "debugging"
        assert "timestamp" in result[0]
        assert result[0]["status"] == "open"

    def test_merge_duplicate_request(self):
        """Test handling duplicate help requests."""
        existing = [
            {
                "topic": "debugging",
                "requesting_agent": "agent1",
                "status": "open",
                "timestamp": "2024-01-01T10:00:00",
            }
        ]
        new = [
            {
                "topic": "debugging",
                "requesting_agent": "agent1",
                "additional_info": "More details",
            }
        ]

        result = merge_help_requests(existing, new)

        # Should update existing request, not create duplicate
        assert len(result) == 1
        assert "additional_info" in result[0]

    def test_merge_different_requests(self):
        """Test adding different help requests."""
        existing = [
            {
                "topic": "debugging",
                "requesting_agent": "agent1",
                "status": "open",
                "timestamp": "2024-01-01T10:00:00",
            }
        ]
        new = [
            {
                "topic": "performance",
                "requesting_agent": "agent1",
                "details": "Slow execution",
            }
        ]

        result = merge_help_requests(existing, new)

        assert len(result) == 2


class TestMergeExecutionTrace:
    """Test merge_execution_trace reducer."""

    def test_merge_new_trace_entries(self):
        """Test adding new trace entries."""
        existing = []
        new = [
            {"action": "start", "agent": "agent1"},
            {"action": "complete", "agent": "agent1"},
        ]

        result = merge_execution_trace(existing, new)

        assert len(result) == 2
        # Should have timestamps and IDs added
        for entry in result:
            assert "timestamp" in entry
            assert "id" in entry

    def test_merge_preserves_order(self):
        """Test that chronological order is preserved."""
        existing = [
            {"action": "start", "timestamp": "2024-01-01T10:00:00", "id": "trace_0"}
        ]
        new = [
            {
                "action": "middle",
                "timestamp": "2024-01-01T09:30:00",  # Earlier timestamp
            }
        ]

        result = merge_execution_trace(existing, new)

        assert len(result) == 2
        # Should be sorted by timestamp
        assert result[0]["action"] == "middle"
        assert result[1]["action"] == "start"

    def test_merge_trace_limit(self):
        """Test that trace entries are limited to 100."""
        # Create 100 existing entries with valid timestamps
        existing = [
            {
                "action": f"step_{i}",
                "timestamp": f"2024-01-01T{i%24:02d}:{i//24:02d}:00",
            }
            for i in range(100)
        ]
        new = [{"action": "new_step", "timestamp": "2024-01-01T23:59:59"}]

        result = merge_execution_trace(existing, new)

        # Should still have 100 entries (oldest removed)
        assert len(result) == 100
        # The newest entry should be last after sorting
        assert result[-1]["action"] == "new_step"


class TestMergeErrorLog:
    """Test merge_error_log reducer."""

    def test_merge_new_errors(self):
        """Test adding new error messages."""
        existing = []
        new = ["Error 1", "Error 2"]

        result = merge_error_log(existing, new)

        assert len(result) == 2
        # Should have timestamps added
        for error in result:
            assert error.startswith("[20")  # Timestamp prefix

    def test_merge_avoid_duplicates(self):
        """Test avoiding duplicate error messages."""
        timestamp = datetime.now(timezone.utc).isoformat()
        existing = [f"[{timestamp}] Duplicate error"]
        new = [f"[{timestamp}] Duplicate error"]

        result = merge_error_log(existing, new)

        # Should not add duplicate
        assert len(result) == 1

    def test_merge_error_limit(self):
        """Test that error log is limited to 50 entries."""
        # Create 50 existing errors
        existing = [f"Error {i}" for i in range(50)]
        new = ["New error"]

        result = merge_error_log(existing, new)

        # Should still have 50 entries (oldest removed)
        assert len(result) == 50


class TestGenericReducers:
    """Test generic helper reducers."""

    def test_merge_list_append(self):
        """Test generic list append reducer."""
        existing = [1, 2, 3]
        new = [4, 5]

        result = merge_list_append(existing, new)

        assert result == [1, 2, 3, 4, 5]

    def test_merge_list_append_empty(self):
        """Test list append with empty existing."""
        result = merge_list_append([], [1, 2, 3])
        assert result == [1, 2, 3]

        result = merge_list_append(None, [1, 2, 3])
        assert result == [1, 2, 3]

    def test_merge_dict_update(self):
        """Test generic dictionary update."""
        existing = {"a": 1, "b": {"nested": 2}}
        new = {"b": {"nested": 3}, "c": 4}

        result = merge_dict_update(existing, new)

        assert result["a"] == 1
        assert result["b"]["nested"] == 3
        assert result["c"] == 4

    def test_merge_dict_deep_update(self):
        """Test deep dictionary update."""
        existing = {"config": {"setting1": "value1", "setting2": "value2"}}
        new = {"config": {"setting2": "new_value2", "setting3": "value3"}}

        result = merge_dict_update(existing, new)

        assert result["config"]["setting1"] == "value1"  # Preserved
        assert result["config"]["setting2"] == "new_value2"  # Updated
        assert result["config"]["setting3"] == "value3"  # Added


if __name__ == "__main__":
    pytest.main([__file__])
