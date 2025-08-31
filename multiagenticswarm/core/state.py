"""
Core state schema for MultiAgenticSwarm.

This module defines the AgentState TypedDict that serves as the single source of truth
for all data flowing through the multi-agent system. The state is designed to be:
- Type-safe with proper annotations
- Serializable for checkpointing
- Reducible for concurrent updates
- Extensible for future needs
"""

from typing import Any, Dict, List, Optional, TypedDict, Union
from typing_extensions import Annotated
from datetime import datetime

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from ..utils.logger import get_logger

logger = get_logger(__name__)

# Current schema version for compatibility checking
SCHEMA_VERSION = "1.0.0"


class AgentState(TypedDict):
    """
    Core state schema for multi-agent collaboration.
    
    This TypedDict contains all data needed for multi-agent collaboration,
    including messages, task management, agent coordination, tool execution,
    and various memory layers.
    
    All fields are optional to allow for flexible initialization and updates.
    Default values are provided through the create_initial_state() function.
    """
    
    # ========== Message Management ==========
    # Message history with automatic merging via LangGraph's add_messages reducer
    messages: Annotated[List[BaseMessage], add_messages]
    
    # ========== Task Management ==========
    # Active task being worked on
    current_task: Optional[str]
    # Breakdown of main task into subtasks
    subtasks: List[Dict[str, Any]]
    # Progress percentage (0-100) per subtask
    task_progress: Dict[str, float]
    # Additional task context and metadata
    task_metadata: Dict[str, Any]
    
    # ========== Agent Coordination ==========
    # Currently executing agent identifier
    current_agent: Optional[str]
    # Next agent to execute in the workflow
    next_agent: Optional[str]
    # Results and outputs from each agent
    agent_outputs: Dict[str, Any]
    # Queue of pending agent executions
    agent_queue: List[str]
    # Health and availability status per agent
    agent_status: Dict[str, str]
    
    # ========== Tool Execution ==========
    # History of all tool requests made
    tool_calls: List[Dict[str, Any]]
    # Results from tool executions
    tool_results: Dict[str, Any]
    # Dynamic permission matrix: agent_id -> [tool_names]
    tool_permissions: Dict[str, List[str]]
    # Queue of pending tool requests
    pending_tools: List[Dict[str, Any]]
    # Failed tool executions with error details
    tool_errors: List[Dict[str, Any]]
    
    # ========== Collaboration Context ==========
    # Natural language instructions for collaboration
    collaboration_prompt: Optional[str]
    # Extracted rules and constraints from prompt
    coordination_rules: List[Dict[str, Any]]
    # Role assignments per agent
    agent_roles: Dict[str, str]
    # Current collaboration pattern being used
    workflow_pattern: Optional[str]
    # Conditional branch points in the workflow
    decision_points: List[Dict[str, Any]]
    
    # ========== Memory Layers ==========
    # Current conversation context
    short_term_memory: Dict[str, Any]
    # Active task and working information
    working_memory: Dict[str, Any]
    # Sequence of events and experiences
    episodic_memory: List[Dict[str, Any]]
    # Information visible to all agents
    shared_memory: Dict[str, Any]
    # Agent-specific private information
    private_memory: Dict[str, Dict[str, Any]]
    
    # ========== Inter-Agent Communication ==========
    # Direct messages between agents
    agent_messages: List[Dict[str, Any]]
    # Assistance requests between agents
    help_requests: List[Dict[str, Any]]
    # System-wide announcements
    broadcast_messages: List[Dict[str, Any]]
    # Responses awaiting from agents
    pending_responses: List[Dict[str, Any]]
    
    # ========== Control Flow ==========
    # Whether to continue with execution
    should_continue: bool
    # Pause execution for human input
    requires_human_approval: bool
    # Where to pause execution
    interrupt_checkpoint: Optional[str]
    # Where to continue after interrupt
    resume_point: Optional[str]
    # Execution mode: sequential/parallel/supervisor
    execution_mode: str
    
    # ========== Debugging & Monitoring ==========
    # Schema version for compatibility checking
    state_version: str
    # Step-by-step execution log
    execution_trace: List[Dict[str, Any]]
    # Error messages and stack traces
    error_log: List[Dict[str, Any]]
    # Timing and resource usage metrics
    performance_metrics: Dict[str, Any]
    # Flags to enable detailed logging
    debug_flags: Dict[str, bool]


def create_initial_state(
    collaboration_prompt: Optional[str] = None,
    initial_message: Optional[str] = None,
    **kwargs: Any
) -> AgentState:
    """
    Create an initial AgentState with default values.
    
    Args:
        collaboration_prompt: Initial collaboration instructions
        initial_message: Initial message to add to conversation
        **kwargs: Additional fields to override defaults
        
    Returns:
        Initialized AgentState with default values
    """
    current_time = datetime.now().isoformat()
    
    # Create base state with defaults
    state: AgentState = {
        # Message Management
        "messages": [],
        
        # Task Management
        "current_task": None,
        "subtasks": [],
        "task_progress": {},
        "task_metadata": {},
        
        # Agent Coordination
        "current_agent": None,
        "next_agent": None,
        "agent_outputs": {},
        "agent_queue": [],
        "agent_status": {},
        
        # Tool Execution
        "tool_calls": [],
        "tool_results": {},
        "tool_permissions": {},
        "pending_tools": [],
        "tool_errors": [],
        
        # Collaboration Context
        "collaboration_prompt": collaboration_prompt,
        "coordination_rules": [],
        "agent_roles": {},
        "workflow_pattern": None,
        "decision_points": [],
        
        # Memory Layers
        "short_term_memory": {},
        "working_memory": {},
        "episodic_memory": [],
        "shared_memory": {},
        "private_memory": {},
        
        # Inter-Agent Communication
        "agent_messages": [],
        "help_requests": [],
        "broadcast_messages": [],
        "pending_responses": [],
        
        # Control Flow
        "should_continue": True,
        "requires_human_approval": False,
        "interrupt_checkpoint": None,
        "resume_point": None,
        "execution_mode": "sequential",
        
        # Debugging & Monitoring
        "state_version": SCHEMA_VERSION,
        "execution_trace": [
            {
                "event": "state_initialized",
                "timestamp": current_time,
                "details": "Initial state created"
            }
        ],
        "error_log": [],
        "performance_metrics": {
            "created_at": current_time,
            "total_tool_calls": 0,
            "total_messages": 0,
            "total_agents_used": 0
        },
        "debug_flags": {
            "trace_execution": False,
            "log_state_changes": False,
            "validate_permissions": True,
            "record_performance": True
        }
    }
    
    # Add initial message if provided
    if initial_message:
        from langchain_core.messages import HumanMessage
        state["messages"] = [HumanMessage(content=initial_message)]
        state["performance_metrics"]["total_messages"] = 1
    
    # Override with any provided kwargs
    for key, value in kwargs.items():
        if key in state:
            state[key] = value  # type: ignore
        else:
            logger.warning(f"Unknown state field '{key}' provided to create_initial_state")
    
    logger.debug(f"Created initial state with schema version {SCHEMA_VERSION}")
    return state


def validate_state(state: AgentState) -> bool:
    """
    Validate that a state object conforms to the AgentState schema.
    
    Args:
        state: The state object to validate
        
    Returns:
        True if valid, False otherwise
        
    Raises:
        ValueError: If state is invalid with detailed error message
    """
    errors = []
    
    # Check required fields exist
    required_fields = [
        "messages", "current_task", "subtasks", "task_progress", "task_metadata",
        "current_agent", "next_agent", "agent_outputs", "agent_queue", "agent_status",
        "tool_calls", "tool_results", "tool_permissions", "pending_tools", "tool_errors",
        "collaboration_prompt", "coordination_rules", "agent_roles", "workflow_pattern", "decision_points",
        "short_term_memory", "working_memory", "episodic_memory", "shared_memory", "private_memory",
        "agent_messages", "help_requests", "broadcast_messages", "pending_responses",
        "should_continue", "requires_human_approval", "interrupt_checkpoint", "resume_point", "execution_mode",
        "state_version", "execution_trace", "error_log", "performance_metrics", "debug_flags"
    ]
    
    for field in required_fields:
        if field not in state:
            errors.append(f"Missing required field: {field}")
    
    # Type validations
    if "messages" in state and not isinstance(state["messages"], list):
        errors.append("Field 'messages' must be a list")
    
    if "should_continue" in state and not isinstance(state["should_continue"], bool):
        errors.append("Field 'should_continue' must be a boolean")
    
    if "requires_human_approval" in state and not isinstance(state["requires_human_approval"], bool):
        errors.append("Field 'requires_human_approval' must be a boolean")
    
    if "state_version" in state and not isinstance(state["state_version"], str):
        errors.append("Field 'state_version' must be a string")
    
    # Check state version compatibility
    if "state_version" in state and state["state_version"] != SCHEMA_VERSION:
        logger.warning(f"State version mismatch: expected {SCHEMA_VERSION}, got {state['state_version']}")
    
    if errors:
        error_msg = "State validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
        raise ValueError(error_msg)
    
    return True


def serialize_state(state: AgentState) -> Dict[str, Any]:
    """
    Serialize an AgentState for checkpointing.
    
    Args:
        state: The state to serialize
        
    Returns:
        Serializable dictionary representation
    """
    # Convert BaseMessage objects to serializable format
    serialized = dict(state)
    
    if "messages" in serialized:
        serialized["messages"] = [
            {
                "type": msg.__class__.__name__,
                "content": msg.content,
                "additional_kwargs": getattr(msg, "additional_kwargs", {}),
                "id": getattr(msg, "id", None)
            }
            for msg in serialized["messages"]
        ]
    
    return serialized


def deserialize_state(serialized: Dict[str, Any]) -> AgentState:
    """
    Deserialize a state from checkpoint data.
    
    Args:
        serialized: Serialized state data
        
    Returns:
        Reconstructed AgentState
    """
    state = dict(serialized)
    
    # Reconstruct BaseMessage objects
    if "messages" in state:
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
        
        message_classes = {
            "HumanMessage": HumanMessage,
            "AIMessage": AIMessage,
            "SystemMessage": SystemMessage,
            "ToolMessage": ToolMessage
        }
        
        reconstructed_messages = []
        for msg_data in state["messages"]:
            msg_type = msg_data.get("type", "HumanMessage")
            msg_class = message_classes.get(msg_type, HumanMessage)
            
            msg = msg_class(
                content=msg_data["content"],
                additional_kwargs=msg_data.get("additional_kwargs", {}),
                id=msg_data.get("id")
            )
            reconstructed_messages.append(msg)
        
        state["messages"] = reconstructed_messages
    
    return state  # type: ignore


def log_state_change(
    state: AgentState,
    change_type: str,
    details: Dict[str, Any],
    agent_name: Optional[str] = None
) -> None:
    """
    Log a state change to the execution trace.
    
    Args:
        state: The state being modified
        change_type: Type of change (e.g., 'agent_update', 'tool_call', 'task_progress')
        details: Additional details about the change
        agent_name: Name of agent making the change
    """
    if not state.get("debug_flags", {}).get("trace_execution", False):
        return
    
    trace_entry = {
        "timestamp": datetime.now().isoformat(),
        "change_type": change_type,
        "agent": agent_name,
        "details": details
    }
    
    state["execution_trace"].append(trace_entry)
    logger.debug(f"State change logged: {change_type} by {agent_name}")