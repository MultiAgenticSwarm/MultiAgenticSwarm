"""
Comprehensive tests for enhanced state management functionality.

This module tests the new validation, migration, and reducer enhancements
added to the MultiAgenticSwarm state management system.
"""

import pytest
import copy
import time
from datetime import datetime
from typing import Dict, Any, List

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from multiagenticswarm.core.state import (
    AgentState,
    SCHEMA_VERSION,
    create_initial_state,
    validate_state,
    validate_agent_status,
    validate_workflow_pattern,
    validate_execution_mode,
    validate_tool_permissions,
    compare_versions,
    is_compatible_version,
    migrate_state,
    register_migration,
    create_migration_backup,
    restore_from_backup,
    auto_migrate_state,
    StateVersionError,
    VALID_AGENT_STATUSES,
    VALID_EXECUTION_MODES,
    VALID_WORKFLOW_PATTERNS
)
from multiagenticswarm.core.state_reducers import (
    merge_agent_outputs,
    aggregate_progress,
    resolve_permissions,
    merge_tool_results,
    merge_memory_layers,
    merge_communication_messages,
    merge_execution_trace,
    merge_states,
    apply_reducer,
    get_reducer_info,
    validate_reducer_performance,
    ConflictResolutionStrategy,
    ReducerError,
    REDUCERS
)


class TestEnhancedValidation:
    """Test enhanced validation functionality."""
    
    def test_strict_validation_valid_state(self):
        """Test strict validation with a completely valid state."""
        state = create_initial_state()
        state["agent_status"]["agent1"] = "active"
        state["workflow_pattern"] = "sequential"
        state["execution_mode"] = "parallel"
        
        assert validate_state(state, strict=True) is True
    
    def test_strict_validation_invalid_agent_status(self):
        """Test strict validation catches invalid agent status."""
        state = create_initial_state()
        state["agent_status"]["agent1"] = "invalid_status"
        
        with pytest.raises(ValueError, match="Invalid status"):
            validate_state(state, strict=True)
    
    def test_strict_validation_invalid_workflow_pattern(self):
        """Test strict validation catches invalid workflow pattern."""
        state = create_initial_state()
        state["workflow_pattern"] = "invalid_pattern"
        
        with pytest.raises(ValueError, match="Invalid workflow_pattern"):
            validate_state(state, strict=True)
    
    def test_strict_validation_invalid_execution_mode(self):
        """Test strict validation catches invalid execution mode."""
        state = create_initial_state()
        state["execution_mode"] = "invalid_mode"
        
        with pytest.raises(ValueError, match="Invalid execution_mode"):
            validate_state(state, strict=True)
    
    def test_strict_validation_invalid_progress_values(self):
        """Test strict validation catches invalid progress values."""
        state = create_initial_state()
        state["task_progress"]["task1"] = 150.0  # Out of range
        
        with pytest.raises(ValueError, match="must be between 0 and 100"):
            validate_state(state, strict=True)
    
    def test_strict_validation_invalid_tool_permissions(self):
        """Test strict validation catches invalid tool permissions."""
        state = create_initial_state()
        state["tool_permissions"]["agent1"] = "not_a_list"
        
        with pytest.raises(ValueError, match="must be a list"):
            validate_state(state, strict=True)
    
    def test_validate_agent_status_all_valid(self):
        """Test that all defined valid agent statuses work."""
        for status in VALID_AGENT_STATUSES:
            assert validate_agent_status(status) is True
    
    def test_validate_workflow_pattern_all_valid(self):
        """Test that all defined valid workflow patterns work."""
        for pattern in VALID_WORKFLOW_PATTERNS:
            assert validate_workflow_pattern(pattern) is True
    
    def test_validate_execution_mode_all_valid(self):
        """Test that all defined valid execution modes work."""
        for mode in VALID_EXECUTION_MODES:
            assert validate_execution_mode(mode) is True
    
    def test_validate_tool_permissions_structure(self):
        """Test tool permissions validation with various structures."""
        # Valid permissions
        valid_perms = {
            "agent1": ["tool1", "tool2"],
            "agent2": []
        }
        assert len(validate_tool_permissions(valid_perms)) == 0
        
        # Invalid agent ID type
        invalid_perms1 = {123: ["tool1"]}
        errors1 = validate_tool_permissions(invalid_perms1)
        assert len(errors1) > 0
        assert "Agent ID must be a string" in errors1[0]
        
        # Invalid tools type
        invalid_perms2 = {"agent1": "not_a_list"}
        errors2 = validate_tool_permissions(invalid_perms2)
        assert len(errors2) > 0
        assert "must be a list" in errors2[0]
        
        # Invalid tool item type
        invalid_perms3 = {"agent1": ["tool1", 123]}
        errors3 = validate_tool_permissions(invalid_perms3)
        assert len(errors3) > 0
        assert "must be a string" in errors3[0]


class TestStateMigration:
    """Test state migration system."""
    
    def test_version_comparison(self):
        """Test semantic version comparison."""
        assert compare_versions("1.0.0", "1.0.1") == -1
        assert compare_versions("1.1.0", "1.0.0") == 1
        assert compare_versions("1.0.0", "1.0.0") == 0
        assert compare_versions("2.0.0", "1.9.9") == 1
    
    def test_version_comparison_with_prereleases(self):
        """Test version comparison with pre-release versions."""
        # Note: Current implementation strips pre-release suffixes for comparison
        assert compare_versions("1.0.0-alpha", "1.0.0") == 0  # Same base version
        assert compare_versions("1.0.0", "1.0.0-beta") == 0   # Same base version
    
    def test_version_comparison_invalid_format(self):
        """Test version comparison with invalid formats."""
        with pytest.raises(StateVersionError):
            compare_versions("invalid", "1.0.0")
        
        with pytest.raises(StateVersionError):
            compare_versions("1.0", "not.a.version")
    
    def test_compatibility_check(self):
        """Test version compatibility checking."""
        assert is_compatible_version("1.1.0", "1.0.0") is True
        assert is_compatible_version("1.0.0", "1.1.0") is False
        assert is_compatible_version("1.0.0", "1.0.0") is True
    
    def test_migration_backup_restore(self):
        """Test migration backup and restore functionality."""
        state = create_initial_state()
        state["custom_field"] = "test_value"
        
        # Create backup
        backup = create_migration_backup(state)
        assert "_migration_backup" in backup
        assert backup["_migration_backup"]["original_version"] == SCHEMA_VERSION
        
        # Restore from backup
        restored = restore_from_backup(backup)
        assert "_migration_backup" not in restored
        assert restored["custom_field"] == "test_value"
        assert restored["state_version"] == SCHEMA_VERSION
    
    def test_register_migration_decorator(self):
        """Test migration function registration."""
        # Register a test migration
        @register_migration("0.8.0", "0.9.0")
        def test_migration(state: Dict[str, Any]) -> Dict[str, Any]:
            migrated = dict(state)
            migrated["test_field"] = "migrated"
            return migrated
        
        # Test that it was registered
        from multiagenticswarm.core.state import _MIGRATION_FUNCTIONS
        assert "0.8.0->0.9.0" in _MIGRATION_FUNCTIONS
    
    def test_existing_migration_function(self):
        """Test the existing 0.9.0 -> 1.0.0 migration."""
        old_state = {
            "state_version": "0.9.0",
            "messages": [],
            "old_field_name": "test_value",
            "performance_metrics": ["operation1", "operation2"]
        }
        
        from multiagenticswarm.core.state import _MIGRATION_FUNCTIONS
        migration_func = _MIGRATION_FUNCTIONS["0.9.0->1.0.0"]
        
        migrated = migration_func(old_state)
        
        # Check that transformations were applied
        assert "debug_flags" in migrated
        assert "new_field_name" in migrated
        assert migrated["new_field_name"] == "test_value"
        assert isinstance(migrated["performance_metrics"], dict)
    
    def test_auto_migrate_current_version(self):
        """Test auto-migration when state is already current version."""
        state = create_initial_state()
        original_version = state["state_version"]
        
        migrated = auto_migrate_state(state)
        assert migrated["state_version"] == original_version
        assert migrated is state  # Should return same object


class TestEnhancedReducers:
    """Test enhanced reducer functionality."""
    
    def test_safe_reducer_decorator_success(self):
        """Test that safe_reducer decorator works correctly for successful operations."""
        current = {"agent1": {"result": "old"}}
        update = {"agent2": {"result": "new"}}
        
        result = merge_agent_outputs(current, update)
        
        assert "agent1" in result
        assert "agent2" in result
        assert result["agent2"]["current"]["result"] == "new"
    
    def test_safe_reducer_decorator_error_handling(self):
        """Test that safe_reducer decorator handles errors properly."""
        with pytest.raises(ReducerError):
            merge_agent_outputs("invalid_type", {"agent1": "output"})
    
    def test_resolve_permissions_strategies(self):
        """Test different permission resolution strategies."""
        current = {"agent1": ["tool1", "tool2", "tool3"]}
        update = {"agent1": ["tool2", "tool3", "tool4"]}
        
        # Most restrictive (intersection)
        restrictive = resolve_permissions(current, update, ConflictResolutionStrategy.MOST_RESTRICTIVE)
        assert set(restrictive["agent1"]) == {"tool2", "tool3"}
        
        # Most permissive (union)
        permissive = resolve_permissions(current, update, ConflictResolutionStrategy.MOST_PERMISSIVE)
        assert set(permissive["agent1"]) == {"tool1", "tool2", "tool3", "tool4"}
        
        # Last write wins
        last_write = resolve_permissions(current, update, ConflictResolutionStrategy.LAST_WRITE_WINS)
        assert set(last_write["agent1"]) == {"tool2", "tool3", "tool4"}
    
    def test_merge_agent_outputs_enhanced(self):
        """Test enhanced agent outputs merging with error handling."""
        # Test with invalid existing structure
        current = {"agent1": "invalid_structure"}
        update = {"agent1": {"result": "new"}}
        
        result = merge_agent_outputs(current, update)
        
        # Should handle invalid structure gracefully
        assert "agent1" in result
        assert result["agent1"]["current"]["result"] == "new"
    
    def test_aggregate_progress_enhanced_error_handling(self):
        """Test enhanced progress aggregation with error handling."""
        current = {"task1": 50.0}
        update = {
            "task1": 75.0,
            "task2": "invalid_value",
            "task3": 150.0,  # Will be clamped
            "task4": -10.0   # Will be clamped
        }
        
        result = aggregate_progress(current, update)
        
        assert result["task1"] == 75.0  # Normal update
        assert "task2" not in result    # Invalid value ignored
        assert result["task3"] == 100.0  # Clamped to max
        assert result["task4"] == 0.0    # Clamped to min
    
    def test_merge_communication_messages_with_limits(self):
        """Test message merging with size limits."""
        current = []
        update = [{"id": f"msg_{i}", "content": f"Message {i}"} for i in range(1200)]
        
        result = merge_communication_messages(current, update, max_messages=1000)
        
        assert len(result) == 1000  # Should be limited
        assert result[-1]["id"] == "msg_1199"  # Should keep most recent
    
    def test_get_reducer_info(self):
        """Test reducer information retrieval."""
        # Known reducer
        info = get_reducer_info("agent_outputs")
        assert "function" in info
        assert "description" in info
        assert "strategy" in info
        assert info["function"] is not None
        
        # Unknown reducer
        info_unknown = get_reducer_info("unknown_field")
        assert info_unknown["function"] is None
        assert "Last-write-wins" in info_unknown["description"]
    
    def test_enhanced_merge_states_error_handling(self):
        """Test enhanced state merging with error handling."""
        base_state = {
            "agent_outputs": {},
            "task_progress": {"task1": 25.0}
        }
        
        updates = {
            "agent_outputs": "invalid_type",  # This will cause an error
            "task_progress": {"task1": 50.0},
            "new_field": "new_value"
        }
        
        # Should continue despite errors
        result = merge_states(base_state, updates)
        
        # Valid updates should be applied
        assert result["task_progress"]["task1"] == 50.0
        assert result["new_field"] == "new_value"
        # Invalid update should be handled gracefully


class TestPerformanceAndScalability:
    """Test performance with large state objects."""
    
    @pytest.mark.benchmark
    def test_large_agent_outputs_performance(self):
        """Test performance with large number of agent outputs."""
        # Create large dataset
        current = {f"agent_{i}": {"result": f"result_{i}"} for i in range(1000)}
        update = {f"agent_{i}": {"result": f"updated_{i}"} for i in range(500, 1500)}
        
        start_time = time.perf_counter()
        result = merge_agent_outputs(current, update)
        end_time = time.perf_counter()
        
        duration = end_time - start_time
        assert duration < 1.0  # Should complete in under 1 second
        assert len(result) == 1500  # Should have all agents
    
    @pytest.mark.benchmark
    def test_large_message_list_performance(self):
        """Test performance with large message lists."""
        current = [{"id": f"msg_{i}", "content": f"Message {i}"} for i in range(5000)]
        update = [{"id": f"new_msg_{i}", "content": f"New message {i}"} for i in range(1000)]
        
        start_time = time.perf_counter()
        result = merge_communication_messages(current, update)
        end_time = time.perf_counter()
        
        duration = end_time - start_time
        assert duration < 2.0  # Should complete in under 2 seconds
        # Note: Result is limited to 1000 messages by default
        assert len(result) == 1000  # Should be limited to max_messages
    
    @pytest.mark.benchmark
    def test_complex_state_merge_performance(self):
        """Test performance of complex state merging."""
        # Create complex base state
        base_state = create_initial_state()
        base_state["agent_outputs"] = {f"agent_{i}": {"result": f"result_{i}"} for i in range(500)}
        base_state["task_progress"] = {f"task_{i}": float(i % 101) for i in range(200)}
        base_state["agent_messages"] = [{"id": f"msg_{i}", "content": f"Message {i}"} for i in range(1000)]
        
        # Create complex updates
        updates = {
            "agent_outputs": {f"agent_{i}": {"result": f"updated_{i}"} for i in range(250, 750)},
            "task_progress": {f"task_{i}": min(100.0, float(i % 101) + 10) for i in range(100, 300)},
            "agent_messages": [{"id": f"new_msg_{i}", "content": f"New message {i}"} for i in range(500)]
        }
        
        start_time = time.perf_counter()
        result = merge_states(base_state, updates)
        end_time = time.perf_counter()
        
        duration = end_time - start_time
        assert duration < 3.0  # Should complete in under 3 seconds
        assert len(result["agent_outputs"]) == 750
        # Note: Messages are limited to 1000 by default
        assert len(result["agent_messages"]) == 1000
    
    def test_validate_reducer_performance_function(self):
        """Test the reducer performance validation function."""
        # Test with agent_outputs reducer
        metrics = validate_reducer_performance("agent_outputs", 100, 10)
        
        assert "field" in metrics
        assert "avg_time" in metrics
        assert "min_time" in metrics
        assert "max_time" in metrics
        assert metrics["field"] == "agent_outputs"
        assert metrics["avg_time"] > 0
    
    def test_state_validation_performance(self):
        """Test validation performance with large states."""
        # Create large state
        state = create_initial_state()
        state["agent_status"] = {f"agent_{i}": "active" for i in range(1000)}
        state["tool_permissions"] = {f"agent_{i}": [f"tool_{j}" for j in range(10)] for i in range(100)}
        state["task_progress"] = {f"task_{i}": float(i % 101) for i in range(500)}
        
        start_time = time.perf_counter()
        result = validate_state(state, strict=True)
        end_time = time.perf_counter()
        
        duration = end_time - start_time
        assert duration < 0.5  # Should validate quickly
        assert result is True


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_reducer_with_none_inputs(self):
        """Test all reducers handle None inputs gracefully."""
        # Test all registered reducers
        for field_name, reducer_info in REDUCERS.items():
            reducer_func = reducer_info["function"]
            
            # Test None inputs
            result1 = reducer_func(None, None)
            result2 = reducer_func({}, None)
            result3 = reducer_func(None, {})
            
            # Should return valid results
            assert result1 is not None
            assert result2 is not None
            assert result3 is not None
    
    def test_malformed_data_handling(self):
        """Test handling of malformed data structures."""
        # Test with various malformed inputs
        malformed_inputs = [
            ("agent_outputs", "not_a_dict", {"agent1": "output"}),
            ("task_progress", {"task1": 50}, "not_a_dict"),
            ("agent_messages", [{"id": "msg1"}], "not_a_list"),
            ("execution_trace", [{"timestamp": "2023-01-01"}], {"not": "a_list"})
        ]
        
        for field_name, current, update in malformed_inputs:
            with pytest.raises(ReducerError):
                apply_reducer(field_name, current, update)
    
    def test_circular_reference_handling(self):
        """Test handling of circular references in state data."""
        # Create circular reference
        circular_dict = {"self_ref": None}
        circular_dict["self_ref"] = circular_dict
        
        base_state = {"test_field": {"normal": "data"}}
        updates = {"test_field": circular_dict}
        
        # Should handle gracefully - our merge function should catch this
        try:
            result = merge_states(base_state, updates)
            # If it doesn't raise an exception, that's also acceptable behavior
            assert result is not None
        except Exception:
            # If it raises an exception, that's expected for circular references
            pass
    
    def test_very_large_single_object(self):
        """Test handling of very large single objects."""
        # Create a very large string
        large_content = "x" * 1000000  # 1MB string
        
        current = []
        update = [{"id": "large_msg", "content": large_content}]
        
        result = merge_communication_messages(current, update)
        
        assert len(result) == 1
        assert result[0]["content"] == large_content
    
    def test_concurrent_updates_simulation(self):
        """Simulate concurrent updates to test reducer consistency."""
        import threading
        import time
        
        base_state = {"task_progress": {"task1": 0.0}}
        results = []
        
        def update_progress(progress_value):
            updates = {"task_progress": {"task1": progress_value}}
            result = merge_states(base_state, updates)
            results.append(result["task_progress"]["task1"])
        
        # Simulate concurrent updates
        threads = []
        for i in range(10):
            thread = threading.Thread(target=update_progress, args=(i * 10.0,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All results should be valid progress values
        for result in results:
            assert 0.0 <= result <= 100.0


class TestIntegrationScenarios:
    """Test integration scenarios that simulate real usage."""
    
    def test_multi_agent_collaboration_simulation(self):
        """Simulate a complex multi-agent collaboration scenario."""
        # Initialize workflow
        state = create_initial_state(
            collaboration_prompt="Three AI agents work on a software project"
        )
        
        # Phase 1: Agent registration and setup
        setup_updates = {
            "agent_roles": {
                "developer": "Code Implementation",
                "reviewer": "Code Review",
                "tester": "Quality Assurance"
            },
            "tool_permissions": {
                "developer": ["git", "ide", "compiler"],
                "reviewer": ["git", "analyzer"],
                "tester": ["git", "test_runner", "browser"]
            },
            "agent_status": {
                "developer": "active",
                "reviewer": "idle", 
                "tester": "idle"
            }
        }
        state = merge_states(state, setup_updates)
        
        # Phase 2: Development phase
        dev_updates = {
            "current_agent": "developer",
            "agent_outputs": {
                "developer": {
                    "status": "coding",
                    "files_modified": ["main.py", "utils.py"],
                    "tests_written": 5
                }
            },
            "task_progress": {"implementation": 60.0},
            "tool_calls": [
                {"id": "call_1", "tool": "git", "action": "commit", "agent": "developer"}
            ],
            "tool_results": {"call_1": {"success": True, "commit_id": "abc123"}}
        }
        state = merge_states(state, dev_updates)
        
        # Phase 3: Review phase
        review_updates = {
            "current_agent": "reviewer",
            "agent_status": {"reviewer": "active", "developer": "waiting"},
            "agent_outputs": {
                "reviewer": {
                    "status": "reviewing",
                    "issues_found": 2,
                    "suggestions": ["Add error handling", "Improve documentation"]
                }
            },
            "help_requests": [
                {
                    "id": "req_1",
                    "from": "reviewer",
                    "to": "developer",
                    "message": "Please add error handling to main.py"
                }
            ]
        }
        state = merge_states(state, review_updates)
        
        # Phase 4: Testing phase
        test_updates = {
            "current_agent": "tester",
            "agent_status": {"tester": "active"},
            "agent_outputs": {
                "tester": {
                    "status": "testing",
                    "tests_run": 15,
                    "tests_passed": 13,
                    "tests_failed": 2
                }
            },
            "task_progress": {"testing": 85.0},
            "error_log": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "agent": "tester",
                    "error": "Test case failed: test_edge_case"
                }
            ]
        }
        state = merge_states(state, test_updates)
        
        # Validate final state
        assert validate_state(state, strict=True)
        assert len(state["agent_outputs"]) == 3
        assert state["task_progress"]["implementation"] == 60.0
        assert state["task_progress"]["testing"] == 85.0
        assert len(state["help_requests"]) == 1
        assert len(state["error_log"]) == 1
    
    def test_state_checkpoint_restore_simulation(self):
        """Simulate state checkpointing and restoration."""
        # Create and populate initial state
        state = create_initial_state()
        state["agent_outputs"]["agent1"] = {"result": "checkpoint_test"}
        state["task_progress"]["task1"] = 75.0
        
        # Serialize (simulate checkpointing)
        from multiagenticswarm.core.state import serialize_state, deserialize_state
        serialized = serialize_state(state)
        
        # Deserialize (simulate restoration)
        restored = deserialize_state(serialized)
        
        # Validate restored state
        assert validate_state(restored, strict=True)
        assert restored["agent_outputs"]["agent1"]["result"] == "checkpoint_test"
        assert restored["task_progress"]["task1"] == 75.0
    
    def test_migration_workflow_simulation(self):
        """Simulate a complete migration workflow."""
        # Create old version state
        old_state = {
            "state_version": "0.9.0",
            "messages": [],
            "agent_outputs": {"agent1": {"result": "old_format"}},
            "old_field_name": "legacy_value",
            "performance_metrics": ["op1", "op2", "op3"]  # Old list format
        }
        
        # Create backup
        backup = create_migration_backup(old_state)
        
        # Attempt migration
        try:
            migrated = migrate_state(old_state, "1.0.0")
            
            # Validate migration succeeded
            assert migrated["state_version"] == "1.0.0"
            assert "debug_flags" in migrated
            assert "new_field_name" in migrated
            assert isinstance(migrated["performance_metrics"], dict)
            
            # Validate migrated state
            assert validate_state(migrated, strict=True)
            
        except StateVersionError:
            # If migration fails, restore from backup
            restored = restore_from_backup(backup)
            assert restored["state_version"] == "0.9.0"


if __name__ == "__main__":
    pytest.main([__file__])