"""
LangGraph integration tests for enhanced state management.

This module contains integration tests that simulate actual LangGraph node execution
and state flow through graph transitions, demonstrating the enhanced state management
capabilities in real-world scenarios.
"""

import pytest
from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage

from multiagenticswarm.core.state import (
    AgentState,
    create_initial_state,
    validate_state,
    log_state_change
)
from multiagenticswarm.core.state_reducers import (
    merge_states,
    ConflictResolutionStrategy
)


class MockLangGraphNode:
    """Mock LangGraph node for testing state flow."""
    
    def __init__(self, name: str, agent_id: str):
        self.name = name
        self.agent_id = agent_id
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """Simulate node execution that modifies state."""
        # Validate input state
        validate_state(state, strict=True)
        
        # Simulate agent processing
        updates = {
            "current_agent": self.agent_id,
            "agent_status": {self.agent_id: "active"},
            "agent_outputs": {
                self.agent_id: {
                    "node_processed": self.name,
                    "processing_time": 0.1,
                    "status": "completed"
                }
            },
            "messages": [
                AIMessage(content=f"Processed by {self.name} node (agent: {self.agent_id})")
            ]
        }
        
        # Log state change
        log_state_change(
            state, 
            "node_execution", 
            {"node": self.name, "agent": self.agent_id}, 
            self.agent_id
        )
        
        # Return state updates
        return updates


class MockLangGraphRouter:
    """Mock LangGraph router for testing conditional flow."""
    
    def __init__(self, routing_logic: Dict[str, str]):
        self.routing_logic = routing_logic
    
    def __call__(self, state: AgentState) -> str:
        """Simulate router decision making."""
        current_agent = state.get("current_agent")
        
        # Simple routing based on current agent
        next_node = self.routing_logic.get(current_agent, "END")
        
        # Log routing decision
        log_state_change(
            state,
            "routing_decision",
            {"current_agent": current_agent, "next_node": next_node},
            "router"
        )
        
        return next_node


class TestLangGraphStateFlow:
    """Test state flow through simulated LangGraph execution."""
    
    def test_simple_node_execution(self):
        """Test basic node execution with state updates."""
        # Create initial state with tracing enabled
        state = create_initial_state(
            collaboration_prompt="Simple agent workflow",
            initial_message="Start processing"
        )
        state["debug_flags"]["trace_execution"] = True
        
        # Create mock node
        analyzer_node = MockLangGraphNode("analyzer", "data_analyzer")
        
        # Execute node
        updates = analyzer_node(state)
        updated_state = merge_states(state, updates)
        
        # Validate results
        assert validate_state(updated_state, strict=True)
        assert updated_state["current_agent"] == "data_analyzer"
        assert updated_state["agent_status"]["data_analyzer"] == "active"
        assert "data_analyzer" in updated_state["agent_outputs"]
        # Note: Messages are merged via the enhanced reducers' merge_states function, resulting in 2 total messages (initial + node message are accumulated)
        assert len(updated_state["messages"]) == 2  # initial + node message are accumulated
        assert len(updated_state["execution_trace"]) > 1  # initial + logged change
    
    def test_multi_node_workflow(self):
        """Test state flow through multiple nodes."""
        # Create initial state
        state = create_initial_state(
            collaboration_prompt="Multi-agent data pipeline"
        )
        state["debug_flags"]["trace_execution"] = True
        
        # Create workflow nodes
        collector_node = MockLangGraphNode("data_collector", "collector_agent")
        processor_node = MockLangGraphNode("data_processor", "processor_agent") 
        validator_node = MockLangGraphNode("data_validator", "validator_agent")
        
        # Execute workflow sequence
        # Step 1: Data collection
        updates1 = collector_node(state)
        state = merge_states(state, updates1)
        state["task_progress"]["data_collection"] = 100.0
        
        # Step 2: Data processing
        updates2 = processor_node(state)
        state = merge_states(state, updates2)
        state["task_progress"]["data_processing"] = 100.0
        
        # Step 3: Data validation
        updates3 = validator_node(state)
        state = merge_states(state, updates3)
        state["task_progress"]["data_validation"] = 100.0
        
        # Validate final state
        assert validate_state(state, strict=True)
        assert len(state["agent_outputs"]) == 3
        assert all(task_progress == 100.0 for task_progress in state["task_progress"].values())
        assert state["current_agent"] == "validator_agent"
        assert len(state["execution_trace"]) >= 4  # initial + 3 node executions
    
    def test_conditional_routing(self):
        """Test conditional routing through state-dependent logic."""
        # Create initial state
        state = create_initial_state()
        state["debug_flags"]["trace_execution"] = True
        
        # Create nodes and router
        input_node = MockLangGraphNode("input_handler", "input_agent")
        analysis_node = MockLangGraphNode("analyzer", "analysis_agent")
        error_node = MockLangGraphNode("error_handler", "error_agent")
        
        router = MockLangGraphRouter({
            "input_agent": "analyzer",
            "analysis_agent": "END",
            "error_agent": "END",
            None: "input_handler"
        })
        
        # Execute workflow with routing
        # Step 1: Initial input processing
        updates1 = input_node(state)
        state = merge_states(state, updates1)
        
        # Step 2: Router decision
        next_node = router(state)
        assert next_node == "analyzer"
        
        # Step 3: Analysis processing
        updates2 = analysis_node(state)
        state = merge_states(state, updates2)
        
        # Step 4: Final routing
        final_route = router(state)
        assert final_route == "END"
        
        # Validate execution trace includes routing decisions
        routing_entries = [
            entry for entry in state["execution_trace"] 
            if entry.get("change_type") == "routing_decision"
        ]
        assert len(routing_entries) == 2
    
    def test_error_handling_in_nodes(self):
        """Test error handling during node execution."""
        state = create_initial_state()
        state["debug_flags"]["trace_execution"] = True
        
        # Simulate a node that encounters an error
        def error_node(state: AgentState) -> Dict[str, Any]:
            # Add error to state
            error_info = {
                "timestamp": "2023-01-01T00:00:00Z",
                "node": "error_producer",
                "agent": "error_agent",
                "error": "Simulated processing error",
                "severity": "high"
            }
            
            return {
                "current_agent": "error_agent",
                "agent_status": {"error_agent": "error"},
                "error_log": [error_info],
                "agent_outputs": {
                    "error_agent": {
                        "status": "failed",
                        "error": "Processing failed"
                    }
                }
            }
        
        # Execute error-producing node
        updates = error_node(state)
        state = merge_states(state, updates)
        
        # Validate error handling
        assert validate_state(state, strict=True)
        assert state["agent_status"]["error_agent"] == "error"
        assert len(state["error_log"]) == 1
        assert state["error_log"][0]["error"] == "Simulated processing error"
    
    def test_concurrent_agent_updates(self):
        """Test handling of concurrent updates from multiple agents."""
        state = create_initial_state()
        
        # Simulate concurrent updates from different agents
        agent1_updates = {
            "agent_outputs": {"agent1": {"result": "result1", "timestamp": "2023-01-01T00:00:01Z"}},
            "task_progress": {"task_shared": 30.0},
            "tool_permissions": {"agent1": ["tool1", "tool2"]}
        }
        
        agent2_updates = {
            "agent_outputs": {"agent2": {"result": "result2", "timestamp": "2023-01-01T00:00:02Z"}},
            "task_progress": {"task_shared": 45.0},  # Progress conflict
            "tool_permissions": {"agent1": ["tool1", "tool3"]}  # Permission conflict
        }
        
        # Apply updates sequentially (simulating near-concurrent execution)
        state = merge_states(state, agent1_updates)
        state = merge_states(state, agent2_updates)
        
        # Validate conflict resolution
        assert validate_state(state, strict=True)
        assert "agent1" in state["agent_outputs"]
        assert "agent2" in state["agent_outputs"]
        
        # Progress should be monotonic (higher value wins)
        assert state["task_progress"]["task_shared"] == 45.0
        
        # Permissions should be intersection (most restrictive)
        assert set(state["tool_permissions"]["agent1"]) == {"tool1"}
    
    def test_state_checkpointing_during_execution(self):
        """Test state serialization/deserialization during execution."""
        from multiagenticswarm.core.state import serialize_state, deserialize_state
        
        # Create and execute partial workflow
        state = create_initial_state(
            collaboration_prompt="Checkpointing test workflow"
        )
        
        # Execute first node
        node1 = MockLangGraphNode("preprocessor", "prep_agent")
        updates1 = node1(state)
        state = merge_states(state, updates1)
        
        # Checkpoint state
        serialized = serialize_state(state)
        
        # Simulate interruption and restoration
        restored_state = deserialize_state(serialized)
        
        # Continue execution from checkpoint
        node2 = MockLangGraphNode("processor", "proc_agent")
        updates2 = node2(restored_state)
        final_state = merge_states(restored_state, updates2)
        
        # Validate checkpoint/restore worked
        assert validate_state(final_state, strict=True)
        assert len(final_state["agent_outputs"]) == 2
        assert "prep_agent" in final_state["agent_outputs"]
        assert "proc_agent" in final_state["agent_outputs"]
    
    def test_human_in_the_loop_simulation(self):
        """Test human-in-the-loop workflow interruption."""
        state = create_initial_state()
        
        # Execute node that requires human approval
        def approval_node(state: AgentState) -> Dict[str, Any]:
            return {
                "current_agent": "approval_agent",
                "requires_human_approval": True,
                "interrupt_checkpoint": "awaiting_approval",
                "agent_outputs": {
                    "approval_agent": {
                        "status": "awaiting_approval",
                        "message": "Please review and approve the analysis results"
                    }
                },
                "pending_responses": [{
                    "id": "approval_req_1",
                    "type": "human_approval",
                    "message": "Analysis complete, awaiting approval"
                }]
            }
        
        # Execute approval node
        updates = approval_node(state)
        state = merge_states(state, updates)
        
        # Validate interruption state
        assert state["requires_human_approval"] is True
        assert state["interrupt_checkpoint"] == "awaiting_approval"
        assert len(state["pending_responses"]) == 1
        
        # Simulate human approval and clear pending responses
        approval_updates = {
            "requires_human_approval": False,
            "interrupt_checkpoint": None
        }
        
        # Update agent output separately to avoid conflicts
        agent_update = {
            "agent_outputs": {
                "approval_agent": {
                    "status": "approved", 
                    "approval_received": True
                }
            }
        }
        
        state = merge_states(state, approval_updates)
        state = merge_states(state, agent_update)
        
        # For pending_responses, clear using the reducer system by passing an empty list update
        state = merge_states(state, {"pending_responses": []})
        
        # Validate approval processed
        assert state["requires_human_approval"] is False
        assert state["interrupt_checkpoint"] is None
        assert len(state["pending_responses"]) == 0


if __name__ == "__main__":
    pytest.main([__file__])