"""
Integration test demonstrating full AgentState schema capabilities.

This test validates that all 39 state fields work correctly together
and demonstrates real-world usage patterns for multi-agent collaboration.
"""

import pytest
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from multiagenticswarm.core.state import (
    AgentState,
    create_initial_state,
    validate_state,
    serialize_state,
    deserialize_state,
    log_state_change
)
from multiagenticswarm.core.state_reducers import (
    merge_states,
    merge_agent_outputs,
    aggregate_progress,
    resolve_permissions
)


def test_complete_workflow_simulation():
    """Test a complete multi-agent workflow using all state features."""
    
    # === 1. Initialize Workflow ===
    state = create_initial_state(
        collaboration_prompt="Three agents collaborate on building a web application: "
                           "FrontendDev handles UI, BackendDev handles API, and QAEngineer handles testing",
        initial_message="Starting web application development project"
    )
    
    # Set up initial agent roles and permissions
    initial_setup = {
        "agent_roles": {
            "FrontendDev": "UI Development Specialist",
            "BackendDev": "API Development Specialist", 
            "QAEngineer": "Quality Assurance Specialist"
        },
        "tool_permissions": {
            "FrontendDev": ["git", "npm", "browser_tools"],
            "BackendDev": ["git", "database", "api_tools"],
            "QAEngineer": ["git", "testing_tools", "browser_tools"]
        },
        "workflow_pattern": "parallel_with_dependencies",
        "execution_mode": "parallel",
        "debug_flags": {
            "trace_execution": True,  # Enable execution tracing
            "log_state_changes": True,
            "validate_permissions": True,
            "record_performance": True
        },
        "subtasks": [
            {"id": "frontend", "name": "Build Frontend UI", "assignee": "FrontendDev", "dependencies": []},
            {"id": "backend", "name": "Build Backend API", "assignee": "BackendDev", "dependencies": []},
            {"id": "integration", "name": "Integration Testing", "assignee": "QAEngineer", "dependencies": ["frontend", "backend"]}
        ]
    }
    
    state = merge_states(state, initial_setup)
    assert validate_state(state)
    assert len(state["agent_roles"]) == 3
    assert len(state["tool_permissions"]) == 3
    
    # === 2. Agent Execution Phase ===
    
    # Frontend Developer starts work
    frontend_update = {
        "current_agent": "FrontendDev",
        "current_task": "Build Frontend UI",
        "task_progress": {"frontend": 30.0},
        "agent_outputs": {
            "FrontendDev": {
                "status": "in_progress",
                "current_component": "login_page",
                "files_created": ["login.jsx", "dashboard.jsx"],
                "dependencies_needed": ["user_api_spec"]
            }
        },
        "tool_calls": [
            {
                "id": "tool_1", 
                "agent": "FrontendDev",
                "tool": "npm",
                "action": "install react bootstrap",
                "timestamp": datetime.now().isoformat()
            }
        ],
        "tool_results": {
            "tool_1": {"success": True, "output": "Packages installed successfully"}
        },
        "messages": [
            AIMessage(content="Created login page component, need user API specification from backend")
        ]
    }
    
    state = merge_states(state, frontend_update)
    log_state_change(state, "agent_progress", frontend_update, "FrontendDev")
    
    # Backend Developer starts work
    backend_update = {
        "current_agent": "BackendDev",
        "task_progress": {"backend": 45.0},
        "agent_outputs": {
            "BackendDev": {
                "status": "in_progress", 
                "current_module": "user_authentication",
                "apis_created": ["/api/auth/login", "/api/auth/register"],
                "database_schema": "users_table_created"
            }
        },
        "tool_calls": [
            {
                "id": "tool_2",
                "agent": "BackendDev", 
                "tool": "database",
                "action": "create_users_table",
                "timestamp": datetime.now().isoformat()
            }
        ],
        "tool_results": {
            "tool_2": {"success": True, "output": "Users table created with proper indexing"}
        },
        "shared_memory": {
            "user_api_spec": {
                "login_endpoint": "/api/auth/login",
                "register_endpoint": "/api/auth/register",
                "response_format": {"token": "string", "user": "object"}
            }
        },
        "agent_messages": [
            {
                "id": "msg_1",
                "from": "BackendDev",
                "to": "FrontendDev", 
                "content": "User API spec ready - check shared_memory",
                "type": "resource_sharing"
            }
        ]
    }
    
    state = merge_states(state, backend_update)
    log_state_change(state, "api_ready", backend_update, "BackendDev")
    
    # Frontend responds to backend API availability
    frontend_response = {
        "current_agent": "FrontendDev",
        "task_progress": {"frontend": 70.0},
        "agent_outputs": {
            "FrontendDev": {
                "status": "in_progress",
                "current_component": "api_integration", 
                "api_integration": "completed",
                "tests_passing": True
            }
        },
        "agent_messages": [
            {
                "id": "msg_2",
                "from": "FrontendDev",
                "to": "BackendDev",
                "content": "API integration complete, login flow working",
                "type": "status_update"
            }
        ],
        "working_memory": {
            "integration_status": {
                "frontend_backend": "connected",
                "login_flow": "tested",
                "ready_for_qa": True
            }
        }
    }
    
    state = merge_states(state, frontend_response)
    
    # === 3. QA Phase ===
    qa_update = {
        "current_agent": "QAEngineer",
        "task_progress": {"integration": 60.0},
        "agent_outputs": {
            "QAEngineer": {
                "status": "testing",
                "tests_run": ["login_test", "register_test", "ui_responsive_test"],
                "bugs_found": [
                    {"id": "bug_1", "severity": "medium", "description": "Login button spacing issue"}
                ],
                "test_coverage": "85%"
            }
        },
        "help_requests": [
            {
                "id": "help_1",
                "requesting_agent": "QAEngineer",
                "target_agent": "FrontendDev",
                "topic": "UI Bug Fix",
                "details": "Login button has spacing issue on mobile devices",
                "priority": "medium"
            }
        ],
        "error_log": [
            {
                "timestamp": datetime.now().isoformat(),
                "agent": "QAEngineer",
                "error_type": "ui_bug",
                "description": "Login button spacing issue",
                "severity": "medium"
            }
        ]
    }
    
    state = merge_states(state, qa_update)
    
    # === 4. Bug Fix and Completion ===
    bug_fix_update = {
        "current_agent": "FrontendDev",
        "task_progress": {"frontend": 100.0},
        "agent_outputs": {
            "FrontendDev": {
                "status": "completed",
                "bug_fixes": ["fixed_login_button_spacing"],
                "final_status": "ready_for_deployment"
            }
        },
        "pending_responses": [
            {
                "id": "response_1",
                "responding_to": "help_1",
                "from": "FrontendDev",
                "message": "Bug fixed - updated CSS for mobile responsiveness"
            }
        ]
    }
    
    state = merge_states(state, bug_fix_update)
    
    # Final QA approval
    final_qa = {
        "current_agent": "QAEngineer", 
        "task_progress": {"integration": 100.0, "backend": 100.0},
        "agent_outputs": {
            "QAEngineer": {
                "status": "completed",
                "final_approval": True,
                "test_summary": "All tests passing, ready for production"
            }
        },
        "should_continue": False,  # Workflow complete
        "broadcast_messages": [
            {
                "id": "broadcast_1",
                "from": "QAEngineer",
                "content": "🎉 Project completed successfully! All tests passing.",
                "type": "completion_announcement"
            }
        ]
    }
    
    state = merge_states(state, final_qa)
    
    # === 5. Validation and Verification ===
    
    # Verify state integrity
    assert validate_state(state)
    
    # Check all agents contributed
    assert len(state["agent_outputs"]) == 3
    assert "FrontendDev" in state["agent_outputs"]
    assert "BackendDev" in state["agent_outputs"] 
    assert "QAEngineer" in state["agent_outputs"]
    
    # Check progress tracking
    assert state["task_progress"]["frontend"] == 100.0
    assert state["task_progress"]["backend"] == 100.0
    assert state["task_progress"]["integration"] == 100.0
    
    # Check communication flow
    assert len(state["agent_messages"]) == 2
    assert len(state["help_requests"]) == 1
    assert len(state["broadcast_messages"]) == 1
    
    # Check tool usage tracking
    assert len(state["tool_calls"]) == 2
    assert len(state["tool_results"]) == 2
    
    # Check completion status
    assert state["should_continue"] == False
    
    # Check execution trace
    assert len(state["execution_trace"]) > 1  # Initial + logged changes
    
    # === 6. Serialization Test ===
    serialized = serialize_state(state)
    deserialized = deserialize_state(serialized)
    
    # Verify roundtrip maintains critical data
    assert deserialized["collaboration_prompt"] == state["collaboration_prompt"]
    assert len(deserialized["agent_outputs"]) == len(state["agent_outputs"])
    assert deserialized["should_continue"] == state["should_continue"]


def test_state_field_completeness():
    """Verify all documented state fields are present and working."""
    state = create_initial_state()
    
    # Check all documented fields exist
    expected_fields = [
        # Message Management
        "messages",
        
        # Task Management  
        "current_task", "subtasks", "task_progress", "task_metadata",
        
        # Agent Coordination
        "current_agent", "next_agent", "agent_outputs", "agent_queue", "agent_status",
        
        # Tool Execution
        "tool_calls", "tool_results", "tool_permissions", "pending_tools", "tool_errors",
        
        # Collaboration Context
        "collaboration_prompt", "coordination_rules", "agent_roles", "workflow_pattern", "decision_points",
        
        # Memory Layers
        "short_term_memory", "working_memory", "episodic_memory", "shared_memory", "private_memory",
        
        # Inter-Agent Communication
        "agent_messages", "help_requests", "broadcast_messages", "pending_responses",
        
        # Control Flow
        "should_continue", "requires_human_approval", "interrupt_checkpoint", "resume_point", "execution_mode",
        
        # Thread & Checkpoint Management
        "thread_id", "checkpoint_id", "checkpoint_ts", "parent_checkpoint_id", "checkpoint_ns", "checkpoint_metadata", "is_resuming",
        
        # Graph Execution Context
        "graph_path", "pending_tasks", "branch_results", "channel_values", "config", "recursion_limit",
        
        # Streaming Support
        "stream_mode", "partial_updates", "stream_metadata",
        
        # Subgraph Context
        "subgraph_states", "parent_graph_id", "subgraph_configs",
        
        # Enhanced Interrupts
        "interrupt_before", "interrupt_after", "pending_human_input",
        
        # Debugging & Monitoring
        "state_version", "execution_trace", "error_log", "performance_metrics", "debug_flags"
    ]
    
    for field in expected_fields:
        assert field in state, f"Missing required field: {field}"
    
    # Verify we have exactly the expected number of fields
    assert len(state) == len(expected_fields), f"Expected {len(expected_fields)} fields, got {len(state)}"


def test_reducer_integration():
    """Test that all reducers work together correctly."""
    base_state = create_initial_state()
    
    # Test multiple reducers in sequence
    updates = {
        "agent_outputs": {"agent1": {"result": "test1"}},
        "task_progress": {"task1": 50.0},
        "tool_permissions": {"agent1": ["tool1", "tool2"]},
        "agent_messages": [{"id": "msg1", "content": "Hello"}],
    }
    
    merged = merge_states(base_state, updates)
    
    # Verify each reducer worked
    assert "agent1" in merged["agent_outputs"]
    assert merged["task_progress"]["task1"] == 50.0
    assert set(merged["tool_permissions"]["agent1"]) == {"tool1", "tool2"}
    assert len(merged["agent_messages"]) == 1
    
    # Test conflict resolution
    conflict_updates = {
        "task_progress": {"task1": 40.0},  # Should not regress
        "tool_permissions": {"agent1": ["tool1"]},  # Should intersect
    }
    
    final_state = merge_states(merged, conflict_updates)
    
    # Progress should not regress
    assert final_state["task_progress"]["task1"] == 50.0
    
    # Permissions should be intersection (security-first)
    assert set(final_state["tool_permissions"]["agent1"]) == {"tool1"}


if __name__ == "__main__":
    test_complete_workflow_simulation()
    test_state_field_completeness()
    test_reducer_integration()