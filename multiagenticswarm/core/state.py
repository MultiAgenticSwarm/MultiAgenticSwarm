"""
Core state schema for MultiAgenticSwarm.

This module defines the AgentState TypedDict that serves as the single source of truth
for all data flowing through the LangGraph-based multi-agent system.
"""

from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from .state_reducers import (
    aggregate_progress,
    merge_agent_outputs,
    merge_error_log,
    merge_execution_trace,
    merge_help_requests,
    merge_tool_results,
    resolve_permissions,
)


class AgentState(TypedDict):
    """
    Central state schema for multi-agent collaboration.

    This TypedDict contains all data needed for multi-agent workflows,
    replacing scattered file I/O with a centralized state that flows
    through the LangGraph system.

    All fields are designed to support concurrent modifications through
    custom reducers and maintain consistency across the system.
    """

    # === Message Management ===
    # Conversation history using LangGraph's add_messages reducer
    # Automatically merges new messages, preserves order and metadata
    messages: Annotated[List[BaseMessage], add_messages]

    # === Task Management ===
    # Active task description
    current_task: str
    # Breakdown of main task into subtasks
    subtasks: List[Dict[str, Any]]
    # Percentage completion per subtask with custom aggregation
    task_progress: Annotated[Dict[str, float], aggregate_progress]
    # Additional task context and metadata
    task_metadata: Dict[str, Any]

    # === Agent Coordination ===
    # Currently executing agent ID
    current_agent: str
    # Next agent to execute (optional)
    next_agent: Optional[str]
    # Results from each agent with timestamp-based conflict resolution
    agent_outputs: Annotated[Dict[str, Any], merge_agent_outputs]
    # Pending agent executions
    agent_queue: List[str]
    # Health/availability status per agent
    agent_status: Dict[str, str]

    # === Tool Execution ===
    # History of tool requests
    tool_calls: List[Dict[str, Any]]
    # Results from tool executions with merging support
    tool_results: Annotated[Dict[str, Any], merge_tool_results]
    # Dynamic permission matrix with conflict resolution
    tool_permissions: Annotated[Dict[str, List[str]], resolve_permissions]
    # Queued tool requests
    pending_tools: List[Dict[str, Any]]
    # Failed tool executions
    tool_errors: List[Dict[str, Any]]

    # === Collaboration Context ===
    # Natural language instructions for collaboration
    collaboration_prompt: str
    # Extracted rules and constraints
    coordination_rules: List[Dict[str, Any]]
    # Role assignments per agent
    agent_roles: Dict[str, str]
    # Current collaboration pattern (sequential, parallel, etc.)
    workflow_pattern: str
    # Conditional branch points in workflow
    decision_points: List[Dict[str, Any]]

    # === Memory Layers ===
    # Current conversation context
    short_term_memory: Dict[str, Any]
    # Active task information
    working_memory: Dict[str, Any]
    # Sequence of events
    episodic_memory: List[Dict[str, Any]]
    # Information visible to all agents
    shared_memory: Dict[str, Any]
    # Agent-specific information
    private_memory: Dict[str, Dict[str, Any]]

    # === Communication ===
    # Inter-agent communications
    agent_messages: List[Dict[str, Any]]
    # Assistance requests between agents with merging
    help_requests: Annotated[List[Dict[str, Any]], merge_help_requests]
    # System-wide announcements
    broadcast_messages: List[Dict[str, Any]]
    # Awaiting agent responses
    pending_responses: List[Dict[str, Any]]

    # === Control Flow ===
    # Whether to proceed with execution
    should_continue: bool
    # Pause for human input
    requires_human_approval: bool
    # Where to pause execution
    interrupt_checkpoint: Optional[str]
    # Where to continue after interrupt
    resume_point: Optional[str]
    # Sequential/parallel/supervisor execution mode
    execution_mode: str

    # === Debugging & Monitoring ===
    # Schema version for compatibility checking
    state_version: str
    # Step-by-step execution log with merging
    execution_trace: Annotated[List[Dict[str, Any]], merge_execution_trace]
    # Error messages and stack traces with merging
    error_log: Annotated[List[str], merge_error_log]
    # Timing and resource usage metrics
    performance_metrics: Dict[str, Any]
    # Enable detailed logging flags
    debug_flags: Dict[str, bool]


# State version constant
CURRENT_STATE_VERSION = "1.0.0"


def create_initial_state(
    collaboration_prompt: str,
    initial_message: Optional[BaseMessage] = None,
    agent_roles: Optional[Dict[str, str]] = None,
    workflow_pattern: str = "sequential",
    execution_mode: str = "sequential",
) -> AgentState:
    """
    Create an initial AgentState with default values.

    Args:
        collaboration_prompt: Natural language instructions for the collaboration
        initial_message: Optional initial message to add to the conversation
        agent_roles: Optional role assignments per agent
        workflow_pattern: Collaboration pattern (sequential, parallel, etc.)
        execution_mode: Execution mode (sequential, parallel, supervisor)

    Returns:
        AgentState: Initialized state with defaults and provided values
    """
    state = AgentState(
        # Message Management
        messages=[initial_message] if initial_message else [],
        # Task Management
        current_task="",
        subtasks=[],
        task_progress={},
        task_metadata={},
        # Agent Coordination
        current_agent="",
        next_agent=None,
        agent_outputs={},
        agent_queue=[],
        agent_status={},
        # Tool Execution
        tool_calls=[],
        tool_results={},
        tool_permissions={},
        pending_tools=[],
        tool_errors=[],
        # Collaboration Context
        collaboration_prompt=collaboration_prompt,
        coordination_rules=[],
        agent_roles=agent_roles or {},
        workflow_pattern=workflow_pattern,
        decision_points=[],
        # Memory Layers
        short_term_memory={},
        working_memory={},
        episodic_memory=[],
        shared_memory={},
        private_memory={},
        # Communication
        agent_messages=[],
        help_requests=[],
        broadcast_messages=[],
        pending_responses=[],
        # Control Flow
        should_continue=True,
        requires_human_approval=False,
        interrupt_checkpoint=None,
        resume_point=None,
        execution_mode=execution_mode,
        # Debugging & Monitoring
        state_version=CURRENT_STATE_VERSION,
        execution_trace=[],
        error_log=[],
        performance_metrics={},
        debug_flags={},
    )

    return state


def validate_state_schema(state: Dict[str, Any]) -> bool:
    """
    Validate that a state dictionary conforms to the AgentState schema.

    Args:
        state: Dictionary to validate

    Returns:
        bool: True if state is valid, False otherwise
    """
    try:
        # Check required fields exist
        required_fields = [
            "messages",
            "current_task",
            "subtasks",
            "task_progress",
            "task_metadata",
            "current_agent",
            "next_agent",
            "agent_outputs",
            "agent_queue",
            "agent_status",
            "tool_calls",
            "tool_results",
            "tool_permissions",
            "pending_tools",
            "tool_errors",
            "collaboration_prompt",
            "coordination_rules",
            "agent_roles",
            "workflow_pattern",
            "decision_points",
            "short_term_memory",
            "working_memory",
            "episodic_memory",
            "shared_memory",
            "private_memory",
            "agent_messages",
            "help_requests",
            "broadcast_messages",
            "pending_responses",
            "should_continue",
            "requires_human_approval",
            "interrupt_checkpoint",
            "resume_point",
            "execution_mode",
            "state_version",
            "execution_trace",
            "error_log",
            "performance_metrics",
            "debug_flags",
        ]

        for field in required_fields:
            if field not in state:
                return False

        # Check basic type constraints
        if not isinstance(state["messages"], list):
            return False
        if not isinstance(state["current_task"], str):
            return False
        if not isinstance(state["should_continue"], bool):
            return False
        if not isinstance(state["state_version"], str):
            return False

        return True

    except Exception:
        return False


def serialize_state_for_checkpoint(state: AgentState) -> Dict[str, Any]:
    """
    Serialize state for checkpointing, handling complex objects.

    Args:
        state: AgentState to serialize

    Returns:
        Dict: Serializable representation of the state
    """
    serialized = dict(state)

    # Convert BaseMessage objects to dictionaries for serialization
    if "messages" in serialized:
        serialized_messages = []
        for msg in serialized["messages"]:
            if hasattr(msg, "model_dump"):
                serialized_messages.append(msg.model_dump())
            elif hasattr(msg, "dict"):
                serialized_messages.append(msg.dict())
            elif hasattr(msg, "to_dict"):
                serialized_messages.append(msg.to_dict())
            else:
                # Fallback for custom message types
                serialized_messages.append(
                    {"content": str(msg), "type": type(msg).__name__}
                )
        serialized["messages"] = serialized_messages

    return serialized


def deserialize_state_from_checkpoint(serialized_state: Dict[str, Any]) -> AgentState:
    """
    Deserialize state from checkpoint, reconstructing complex objects.

    Args:
        serialized_state: Serialized state dictionary

    Returns:
        AgentState: Reconstructed state object
    """
    # This would need to be implemented based on the specific message types
    # For now, return the serialized state as-is
    # In a full implementation, you'd reconstruct BaseMessage objects
    return AgentState(serialized_state)
