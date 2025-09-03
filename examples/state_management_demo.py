"""
Example demonstrating the transition from file-based state to centralized state management.

This example shows how agent communication transitions from file I/O-based JSON 
updates to direct state manipulation with type safety and reducers.
"""

from multiagenticswarm.core.state import (
    create_initial_state, 
    serialize_state,
    log_state_change
)
from multiagenticswarm.core.state_reducers import merge_states
from multiagenticswarm.tools.collaboration_tools import ProgressBoard
from langchain_core.messages import HumanMessage, AIMessage
import json


def demo_old_approach():
    """Demonstrate the old file-based approach."""
    print("=== OLD APPROACH: File-based Communication ===")
    
    # Create a progress board (old approach)
    board = ProgressBoard(board_file="demo_board.json", workspace_dir="/tmp")
    
    # Agent 1 posts an update
    result1 = board.post_update(
        agent_name="DataAnalyst",
        message="Started data analysis task",
        task="analyze_customer_data",
        progress=25,
        update_type="progress_report"
    )
    print(f"Agent 1 update: {result1['success']}")
    
    # Agent 2 posts an update
    result2 = board.post_update(
        agent_name="ReportGenerator", 
        message="Waiting for analysis results",
        task="generate_report",
        progress=10,
        update_type="status_update"
    )
    print(f"Agent 2 update: {result2['success']}")
    
    # Get project status (requires reading from file)
    status = board.get_project_status()
    print(f"Overall progress: {status['overall_progress']}%")
    print(f"Total updates: {status['total_updates']}")
    
    print("\nIssues with old approach:")
    print("- File I/O for every update (slow)")
    print("- No type safety")
    print("- Manual progress aggregation")
    print("- No checkpointing support")
    print("- Difficult to debug state changes")


def demo_new_approach():
    """Demonstrate the new centralized state approach."""
    print("\n=== NEW APPROACH: Centralized State Management ===")
    
    # Create initial state
    state = create_initial_state(
        collaboration_prompt="DataAnalyst and ReportGenerator work together on customer data analysis",
        initial_message="Starting customer data analysis workflow"
    )
    print("Initial state created with type safety")
    
    # Agent 1 updates state directly
    agent1_updates = {
        "current_agent": "DataAnalyst",
        "current_task": "analyze_customer_data",
        "task_progress": {"analyze_customer_data": 25.0},
        "agent_outputs": {
            "DataAnalyst": {
                "status": "in_progress",
                "message": "Started data analysis task",
                "current_step": "data_cleaning"
            }
        },
        "messages": [AIMessage(content="Data analysis started, cleaning dataset")]
    }
    
    # Use reducers to merge updates safely
    state = merge_states(state, agent1_updates)
    log_state_change(state, "agent_update", agent1_updates, "DataAnalyst")
    print("Agent 1 update applied with reducers")
    
    # Agent 2 updates state
    agent2_updates = {
        "current_agent": "ReportGenerator",
        "task_progress": {"generate_report": 10.0},
        "agent_outputs": {
            "ReportGenerator": {
                "status": "waiting",
                "message": "Waiting for analysis results",
                "dependencies": ["analyze_customer_data"]
            }
        },
        "agent_messages": [{
            "id": "msg1",
            "from": "ReportGenerator",
            "to": "DataAnalyst",
            "content": "Please notify when analysis is complete",
            "type": "dependency_request"
        }]
    }
    
    state = merge_states(state, agent2_updates)
    log_state_change(state, "agent_update", agent2_updates, "ReportGenerator")
    print("Agent 2 update applied with reducers")
    
    # Calculate overall progress automatically
    total_progress = sum(state["task_progress"].values()) / len(state["task_progress"])
    print(f"Overall progress: {total_progress}%")
    print(f"Total messages: {len(state['messages'])}")
    print(f"Active agents: {len(state['agent_outputs'])}")
    
    # Show state can be serialized for checkpointing
    serialized = serialize_state(state)
    print(f"State serialized for checkpointing: {len(serialized)} fields")
    
    print("\nBenefits of new approach:")
    print("✓ In-memory operations (fast)")
    print("✓ Full type safety with TypedDict")
    print("✓ Automatic state merging with reducers")
    print("✓ Built-in checkpointing support")
    print("✓ Execution tracing and debugging")
    print("✓ Message deduplication and ordering")
    print("✓ Permission-based access control")


def compare_performance():
    """Compare performance characteristics."""
    print("\n=== PERFORMANCE COMPARISON ===")
    
    import time
    
    # Old approach timing
    board = ProgressBoard(board_file="perf_test.json", workspace_dir="/tmp")
    
    start_time = time.time()
    for i in range(100):
        board.post_update(
            agent_name=f"Agent{i % 5}",
            message=f"Update {i}",
            progress=i % 100
        )
    old_time = time.time() - start_time
    
    # New approach timing
    state = create_initial_state()
    
    start_time = time.time()
    for i in range(100):
        updates = {
            "agent_outputs": {f"Agent{i % 5}": {"update": i}},
            "task_progress": {f"task{i % 10}": float(i % 100)}
        }
        state = merge_states(state, updates)
    new_time = time.time() - start_time
    
    print(f"Old approach (100 updates): {old_time:.4f} seconds")
    print(f"New approach (100 updates): {new_time:.4f} seconds")
    print(f"Performance improvement: {old_time/new_time:.1f}x faster")


if __name__ == "__main__":
    demo_old_approach()
    demo_new_approach()
    compare_performance()