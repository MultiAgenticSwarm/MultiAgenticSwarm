"""
Core state schema for MultiAgenticSwarm.

This module defines the AgentState TypedDict that serves as the single source of truth
for all data flowing through the multi-agent system. The state is designed to be:
- Type-safe with proper annotations
- Serializable for checkpointing
- Reducible for concurrent updates
- Extensible for future needs
"""

from typing import Any, Dict, List, Optional, TypedDict, Union, Callable
import operator
from typing_extensions import Annotated
from datetime import datetime
import re

from packaging.version import Version
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph.message import add_messages

from ..utils.logger import get_logger

logger = get_logger(__name__)

# Current schema version for compatibility checking
SCHEMA_VERSION = "1.0.0"

# Valid agent status values
VALID_AGENT_STATUSES = {
    "active", "idle", "busy", "error", "paused", "completed", 
    "initializing", "waiting", "processing", "stopped"
}

# Valid execution modes
VALID_EXECUTION_MODES = {"sequential", "parallel", "supervisor", "map_reduce", "hierarchical"}

# Valid workflow patterns
VALID_WORKFLOW_PATTERNS = {
    "sequential", "parallel", "pipeline", "map_reduce", "supervisor", 
    "hierarchical", "reactive", "conditional", "loop", "custom"
}

# Valid message types for validation
VALID_MESSAGE_TYPES = {HumanMessage, AIMessage, SystemMessage, ToolMessage}


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
    # Uses add_messages reducer because:
    # - Messages must be appended chronologically, never replaced
    # - Multiple agents may add messages concurrently  
    # - LangGraph's add_messages handles deduplication and ordering
    # - Critical for maintaining conversation context
    messages: Annotated[List[BaseMessage], add_messages]
    
    # ========== Task Management ==========
    # Active task being worked on
    current_task: Optional[str]
    # Uses operator.add reducer because:
    # - Agents progressively break down tasks into subtasks
    # - Creates audit trail for debugging and compliance
    # - Enables agents to learn from historical task breakdown patterns
    # - Supports concurrent additions without data loss
    subtasks: Annotated[List[Dict[str, Any]], operator.add]
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
    # Uses operator.add reducer because:
    # - Maintains complete tool execution history for debugging
    # - Creates audit trail for compliance and troubleshooting
    # - Enables agents to learn from historical tool usage patterns
    # - Supports concurrent additions without data loss
    tool_calls: Annotated[List[Dict[str, Any]], operator.add]
    # Results from tool executions
    tool_results: Dict[str, Any]
    # Dynamic permission matrix: agent_id -> [tool_names]
    tool_permissions: Dict[str, List[str]]
    # Queue of pending tool requests
    pending_tools: List[Dict[str, Any]]
    # Uses operator.add reducer because:
    # - Keep error history for debugging and compliance
    # - Enables agents to learn from historical error patterns
    # - Supports concurrent additions without data loss
    # - Critical for system reliability and monitoring
    tool_errors: Annotated[List[Dict[str, Any]], operator.add]
    
    # ========== Collaboration Context ==========
    # Natural language instructions for collaboration
    collaboration_prompt: Optional[str]
    # Uses operator.add reducer because:
    # - Accumulate discovered rules and constraints over time
    # - Creates audit trail for debugging and compliance
    # - Enables agents to learn from historical coordination patterns
    # - Supports concurrent additions without data loss
    coordination_rules: Annotated[List[Dict[str, Any]], operator.add]
    # Role assignments per agent
    agent_roles: Dict[str, str]
    # Current collaboration pattern being used
    workflow_pattern: Optional[str]
    # Conditional branch points in the workflow
    decision_points: List[Dict[str, Any]]
    
    # ========== Memory Layers ==========
    # Uses default replace reducer because:
    # - Represents current state only (no history needed)
    # - Single value that changes atomically
    # - Historical values provide no benefit for current conversation context
    # - Reduces memory usage for frequently updated fields
    short_term_memory: Dict[str, Any]
    # Uses default replace reducer because:
    # - Represents current state only (no history needed)
    # - Active task and working information that changes frequently
    # - Historical values provide no benefit for current working context
    # - Reduces memory usage for frequently updated fields
    working_memory: Dict[str, Any]
    # Uses operator.add reducer because:
    # - Build experience history for learning and decision making
    # - Creates audit trail for debugging and compliance
    # - Enables agents to learn from historical event patterns
    # - Supports concurrent additions without data loss
    episodic_memory: Annotated[List[Dict[str, Any]], operator.add]
    # Uses default replace reducer because:
    # - Information visible to all agents (shared state)
    # - Single value that changes atomically
    # - Historical values stored in episodic_memory
    # - Reduces memory usage for frequently updated fields
    shared_memory: Dict[str, Any]
    # Uses default replace reducer because:
    # - Agent-specific private information (current state)
    # - Single value that changes atomically
    # - Historical values provide no benefit for private context
    # - Reduces memory usage for frequently updated fields
    private_memory: Dict[str, Dict[str, Any]]
    
    # ========== Inter-Agent Communication ==========
    # Uses operator.add reducer because:
    # - Communication logs must preserve chronological order
    # - Creates audit trail for debugging and compliance
    # - Enables agents to learn from historical communication patterns
    # - Supports concurrent additions without data loss
    agent_messages: Annotated[List[Dict[str, Any]], operator.add]
    # Uses operator.add reducer because:
    # - Help request logs for learning and debugging
    # - Creates audit trail for debugging and compliance
    # - Enables agents to learn from historical help patterns
    # - Supports concurrent additions without data loss
    help_requests: Annotated[List[Dict[str, Any]], operator.add]
    # Uses operator.add reducer because:
    # - System-wide announcement logs for debugging
    # - Creates audit trail for debugging and compliance
    # - Enables system monitoring and historical analysis
    # - Supports concurrent additions without data loss
    broadcast_messages: Annotated[List[Dict[str, Any]], operator.add]
    # Responses awaiting from agents
    pending_responses: List[Dict[str, Any]]
    
    # ========== Control Flow ==========
    # Uses default replace reducer because:
    # - Represents current state only (no history needed)
    # - Single value that changes atomically
    # - Historical values provide no benefit
    # - Reduces memory usage for frequently updated fields
    should_continue: bool
    # Uses default replace reducer because:
    # - Represents current state only (no history needed)
    # - Single value that changes atomically
    # - Historical values provide no benefit
    # - Reduces memory usage for frequently updated fields
    requires_human_approval: bool
    # Uses default replace reducer because:
    # - Represents current state only (no history needed)
    # - Single value that changes atomically
    # - Historical values provide no benefit
    # - Reduces memory usage for frequently updated fields
    interrupt_checkpoint: Optional[str]
    # Uses default replace reducer because:
    # - Represents current state only (no history needed)
    # - Single value that changes atomically
    # - Historical values provide no benefit
    # - Reduces memory usage for frequently updated fields
    resume_point: Optional[str]
    # Uses default replace reducer because:
    # - Represents current state only (no history needed)
    # - Single value that changes atomically
    # - Historical values provide no benefit
    # - Reduces memory usage for frequently updated fields
    execution_mode: str
    
    # ========== Thread & Checkpoint Management ==========
    # Unique conversation identifier
    thread_id: Optional[str]
    # Current checkpoint ID
    checkpoint_id: Optional[str]
    # Checkpoint timestamp
    checkpoint_ts: Optional[str]
    # For checkpoint lineage
    parent_checkpoint_id: Optional[str]
    # Namespace for isolation
    checkpoint_ns: Optional[str]
    # Checkpoint-specific metadata
    checkpoint_metadata: Dict[str, Any]
    # Whether resuming from checkpoint
    is_resuming: bool

    # ========== Graph Execution Context ==========
    # Current path through the graph
    graph_path: List[str]
    # Tasks in other branches
    pending_tasks: List[str]
    # Results from parallel branches
    branch_results: Dict[str, Any]
    # LangGraph channel system
    channel_values: Dict[str, Any]
    # LangGraph RunnableConfig
    config: Optional[Dict[str, Any]]
    # Prevent infinite loops (default: 25)
    recursion_limit: int

    # ========== Streaming Support ==========
    # stream_mode options:
    #   'values'  - Stream the current values of the agent state as they change.
    #   'updates' - Stream incremental updates to the agent state (diffs/patches).
    #   'debug'   - Stream detailed debug information for troubleshooting and analysis.
    # Uses default replace reducer because:
    # - Represents current state only (no history needed)
    # - Single value that changes atomically
    # - Historical values provide no benefit
    # - Reduces memory usage for frequently updated fields
    stream_mode: Optional[str]
    # Uses operator.add reducer because:
    # - Streaming updates for debugging and monitoring
    # - Creates audit trail for debugging and compliance
    # - Enables system monitoring and historical analysis
    # - Supports concurrent additions without data loss
    partial_updates: Annotated[List[Dict[str, Any]], operator.add]
    # Uses default replace reducer because:
    # - Represents current state only (no history needed)
    # - Single value that changes atomically
    # - Historical values provide no benefit
    # - Reduces memory usage for frequently updated fields
    stream_metadata: Dict[str, Any]

    # ========== Subgraph Context ==========
    # States from subgraphs
    subgraph_states: Dict[str, Any]
    # Parent graph if this is a subgraph
    parent_graph_id: Optional[str]
    # Subgraph-specific configs
    subgraph_configs: Dict[str, Any]

    # ========== Enhanced Interrupts ==========
    # Nodes to interrupt before
    interrupt_before: List[str]
    # Nodes to interrupt after
    interrupt_after: List[str]
    # Awaiting human input
    pending_human_input: Optional[Dict[str, Any]]

    # ========== Debugging & Monitoring ==========
    # Uses default replace reducer because:
    # - Represents current state only (no history needed)
    # - Single value that changes atomically
    # - Historical values provide no benefit
    # - Reduces memory usage for frequently updated fields
    state_version: str
    # Uses operator.add reducer because:
    # - Step-by-step execution log for debugging
    # - Creates audit trail for debugging and compliance
    # - Enables system monitoring and historical analysis
    # - Supports concurrent additions without data loss
    # Max 1000 entries, older entries archived to persistent storage
    # Cleanup: Entries older than 24 hours moved to archive
    execution_trace: Annotated[List[Dict[str, Any]], operator.add]
    # Uses operator.add reducer because:
    # - Error logs for debugging and monitoring
    # - Creates audit trail for debugging and compliance
    # - Critical for system reliability and troubleshooting
    # - Supports concurrent additions without data loss
    # Max 500 entries, older entries archived to persistent storage
    # Cleanup: Entries older than 48 hours moved to archive
    error_log: Annotated[List[Dict[str, Any]], operator.add]
    # Uses default replace reducer because:
    # - Represents current state only (no history needed)
    # - Single value that changes atomically
    # - Historical values stored in execution_trace
    # - Reduces memory usage for frequently updated fields
    performance_metrics: Dict[str, Any]
    # Uses default replace reducer because:
    # - Represents current state only (no history needed)
    # - Single value that changes atomically
    # - Historical values provide no benefit
    # - Reduces memory usage for frequently updated fields
    debug_flags: Dict[str, bool]


def create_initial_state(
    collaboration_prompt: Optional[str] = None,
    initial_message: Optional[str] = None,
    use_dynamic_config: bool = False,
    **kwargs: Any
) -> AgentState:
    """
    Create an initial AgentState with default values.
    
    Args:
        collaboration_prompt: Initial collaboration instructions
        initial_message: Initial message to add to conversation
        use_dynamic_config: Whether to use dynamic field configuration
        **kwargs: Additional fields to override defaults
        
    Returns:
        Initialized AgentState with default values
    """
    current_time = datetime.now().isoformat()
    
    if use_dynamic_config:
        # Use dynamic configuration to create state
        from .state_config import get_state_config
        config = get_state_config()
        
        state = {}
        for field_name, field_config in config.get_active_fields().items():
            state[field_name] = field_config.default_value
            
        # Override collaboration_prompt if provided
        if collaboration_prompt and "collaboration_prompt" in state:
            state["collaboration_prompt"] = collaboration_prompt
            
    else:
        # Use static configuration (existing behavior)
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
            
            # Thread & Checkpoint Management
            "thread_id": None,
            "checkpoint_id": None,
            "checkpoint_ts": None,
            "parent_checkpoint_id": None,
            "checkpoint_ns": None,
            "checkpoint_metadata": {},
            "is_resuming": False,
            
            # Graph Execution Context
            "graph_path": [],
            "pending_tasks": [],
            "branch_results": {},
            "channel_values": {},
            "config": None,
            "recursion_limit": 25,
            
            # Streaming Support
            "stream_mode": None,
            "partial_updates": [],
            "stream_metadata": {},
            
            # Subgraph Context
            "subgraph_states": {},
            "parent_graph_id": None,
            "subgraph_configs": {},
            
            # Enhanced Interrupts
            "interrupt_before": [],
            "interrupt_after": [],
            "pending_human_input": None,
            
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


def validate_state(state: AgentState, strict: bool = False, use_dynamic_config: bool = False) -> bool:
    """
    Validate that a state object conforms to the AgentState schema.
    
    Args:
        state: The state object to validate
        strict: If True, perform more thorough validation including value checks
        use_dynamic_config: Whether to use dynamic configuration for validation
        
    Returns:
        True if valid, False otherwise
        
    Raises:
        ValueError: If state is invalid with detailed error message
    """
    errors = []
    warnings = []
    
    if use_dynamic_config:
        # Use dynamic configuration for validation
        from .state_config import get_state_config
        config = get_state_config()
        
        # Check required fields exist
        for field_name, field_config in config.get_active_fields().items():
            if field_config.required and field_name not in state:
                errors.append(f"Missing required field: {field_name}")
            
            # Validate field values if present
            if field_name in state:
                field_errors = config.validate_field_value(field_name, state[field_name])
                errors.extend(field_errors)
    
    else:
        # Use static validation (existing behavior)
        # Check required fields exist
        required_fields = [
            "messages", "current_task", "subtasks", "task_progress", "task_metadata",
            "current_agent", "next_agent", "agent_outputs", "agent_queue", "agent_status",
            "tool_calls", "tool_results", "tool_permissions", "pending_tools", "tool_errors",
            "collaboration_prompt", "coordination_rules", "agent_roles", "workflow_pattern", "decision_points",
            "short_term_memory", "working_memory", "episodic_memory", "shared_memory", "private_memory",
            "agent_messages", "help_requests", "broadcast_messages", "pending_responses",
            "should_continue", "requires_human_approval", "interrupt_checkpoint", "resume_point", "execution_mode",
            "thread_id", "checkpoint_id", "checkpoint_ts", "parent_checkpoint_id", "checkpoint_ns", "checkpoint_metadata", "is_resuming",
            "graph_path", "pending_tasks", "branch_results", "channel_values", "config", "recursion_limit",
            "stream_mode", "partial_updates", "stream_metadata",
            "subgraph_states", "parent_graph_id", "subgraph_configs",
            "interrupt_before", "interrupt_after", "pending_human_input",
            "state_version", "execution_trace", "error_log", "performance_metrics", "debug_flags"
        ]
        
        for field in required_fields:
            if field not in state:
                errors.append(f"Missing required field: {field}")
        
        # Basic type validations
        type_checks = [
            ("messages", list, "must be a list"),
            ("subtasks", list, "must be a list"),
            ("task_progress", dict, "must be a dictionary"),
            ("task_metadata", dict, "must be a dictionary"),
            ("agent_outputs", dict, "must be a dictionary"),
            ("agent_queue", list, "must be a list"),
            ("agent_status", dict, "must be a dictionary"),
            ("tool_calls", list, "must be a list"),
            ("tool_results", dict, "must be a dictionary"),
            ("tool_permissions", dict, "must be a dictionary"),
            ("pending_tools", list, "must be a list"),
            ("tool_errors", list, "must be a list"),
            ("coordination_rules", list, "must be a list"),
            ("agent_roles", dict, "must be a dictionary"),
            ("decision_points", list, "must be a list"),
            ("short_term_memory", dict, "must be a dictionary"),
            ("working_memory", dict, "must be a dictionary"),
            ("episodic_memory", list, "must be a list"),
            ("shared_memory", dict, "must be a dictionary"),
            ("private_memory", dict, "must be a dictionary"),
            ("agent_messages", list, "must be a list"),
            ("help_requests", list, "must be a list"),
            ("broadcast_messages", list, "must be a list"),
            ("pending_responses", list, "must be a list"),
            ("should_continue", bool, "must be a boolean"),
            ("requires_human_approval", bool, "must be a boolean"),
            ("is_resuming", bool, "must be a boolean"),
            ("checkpoint_metadata", dict, "must be a dictionary"),
            ("graph_path", list, "must be a list"),
            ("pending_tasks", list, "must be a list"),
            ("branch_results", dict, "must be a dictionary"),
            ("channel_values", dict, "must be a dictionary"),
            ("recursion_limit", int, "must be an integer"),
            ("partial_updates", list, "must be a list"),
            ("stream_metadata", dict, "must be a dictionary"),
            ("subgraph_states", dict, "must be a dictionary"),
            ("subgraph_configs", dict, "must be a dictionary"),
            ("interrupt_before", list, "must be a list"),
            ("interrupt_after", list, "must be a list"),
            ("execution_trace", list, "must be a list"),
            ("error_log", list, "must be a list"),
            ("performance_metrics", dict, "must be a dictionary"),
            ("debug_flags", dict, "must be a dictionary"),
        ]
        
        for field, expected_type, error_msg in type_checks:
            if field in state and not isinstance(state[field], expected_type):
                errors.append(f"Field '{field}' {error_msg}")
    
    # String field validations
    string_fields = ["current_task", "current_agent", "next_agent", "collaboration_prompt", 
                    "workflow_pattern", "interrupt_checkpoint", "resume_point", "execution_mode", "state_version",
                    "thread_id", "checkpoint_id", "checkpoint_ts", "parent_checkpoint_id", "checkpoint_ns",
                    "stream_mode", "parent_graph_id"]
    
    for field in string_fields:
        if field in state and state[field] is not None and not isinstance(state[field], str):
            errors.append(f"Field '{field}' must be a string or None")
    
    # Validate messages are BaseMessage instances
    if "messages" in state and isinstance(state["messages"], list):
        for i, msg in enumerate(state["messages"]):
            if not isinstance(msg, BaseMessage):
                errors.append(f"Message at index {i} is not a BaseMessage instance")
            elif strict and type(msg) not in VALID_MESSAGE_TYPES:
                warnings.append(f"Message at index {i} has unexpected type: {type(msg).__name__}")
    
    # Strict validation (more thorough checks)
    if strict:
        # Validate execution mode
        if "execution_mode" in state and state["execution_mode"] not in VALID_EXECUTION_MODES:
            errors.append(f"Invalid execution_mode '{state['execution_mode']}'. Valid values: {VALID_EXECUTION_MODES}")
        
        # Validate workflow pattern
        if "workflow_pattern" in state and state["workflow_pattern"] is not None:
            if state["workflow_pattern"] not in VALID_WORKFLOW_PATTERNS:
                errors.append(f"Invalid workflow_pattern '{state['workflow_pattern']}'. Valid values: {VALID_WORKFLOW_PATTERNS}")
        
        # Validate agent statuses
        if "agent_status" in state and isinstance(state["agent_status"], dict):
            for agent_id, status in state["agent_status"].items():
                if status not in VALID_AGENT_STATUSES:
                    errors.append(f"Invalid status '{status}' for agent '{agent_id}'. Valid values: {VALID_AGENT_STATUSES}")
        
        # Validate task progress values
        if "task_progress" in state and isinstance(state["task_progress"], dict):
            for task_id, progress in state["task_progress"].items():
                if not isinstance(progress, (int, float)):
                    errors.append(f"Progress for task '{task_id}' must be a number")
                elif not (0 <= progress <= 100):
                    errors.append(f"Progress for task '{task_id}' must be between 0 and 100")
        
        # Validate tool permissions structure
        if "tool_permissions" in state and isinstance(state["tool_permissions"], dict):
            for agent_id, tools in state["tool_permissions"].items():
                if not isinstance(tools, list):
                    errors.append(f"Tool permissions for agent '{agent_id}' must be a list")
                elif not all(isinstance(tool, str) for tool in tools):
                    errors.append(f"All tool names for agent '{agent_id}' must be strings")
        
        # Validate state version format
        if "state_version" in state and state["state_version"]:
            version_pattern = r'^\d+\.\d+\.\d+(-\w+)?$'
            if not re.match(version_pattern, state["state_version"]):
                warnings.append(f"State version '{state['state_version']}' doesn't follow semantic versioning pattern")
        
        # Validate agent queue contains valid agent IDs
        if "agent_queue" in state and isinstance(state["agent_queue"], list):
            for i, agent_id in enumerate(state["agent_queue"]):
                if not isinstance(agent_id, str):
                    errors.append(f"Agent ID at queue position {i} must be a string")
        
        # Validate debug flags
        if "debug_flags" in state and isinstance(state["debug_flags"], dict):
            for flag, value in state["debug_flags"].items():
                if not isinstance(value, bool):
                    warnings.append(f"Debug flag '{flag}' should be a boolean")
        
        # Validate recursion limit
        if "recursion_limit" in state:
            if not isinstance(state["recursion_limit"], int):
                errors.append("Recursion limit must be an integer")
            elif state["recursion_limit"] < 1:
                errors.append("Recursion limit must be at least 1")
            elif state["recursion_limit"] > 1000:
                warnings.append(f"Recursion limit {state['recursion_limit']} is very high, consider lowering")
        
        # Validate stream mode
        valid_stream_modes = {"values", "updates", "debug", None}
        if "stream_mode" in state and state["stream_mode"] not in valid_stream_modes:
            errors.append(f"Invalid stream_mode '{state['stream_mode']}'. Valid values: {valid_stream_modes}")
        
        # Validate graph path contains valid node names
        if "graph_path" in state and isinstance(state["graph_path"], list):
            for i, node in enumerate(state["graph_path"]):
                if not isinstance(node, str):
                    errors.append(f"Graph path node at position {i} must be a string")
        
        # Validate interrupt lists contain valid node names
        for field in ["interrupt_before", "interrupt_after"]:
            if field in state and isinstance(state[field], list):
                for i, node in enumerate(state[field]):
                    if not isinstance(node, str):
                        errors.append(f"{field} node at position {i} must be a string")
    
    # Check state version compatibility
    if "state_version" in state and state["state_version"] != SCHEMA_VERSION:
        warnings.append(f"State version mismatch: expected {SCHEMA_VERSION}, got {state['state_version']}")
    
    # Log warnings
    for warning in warnings:
        logger.warning(f"State validation warning: {warning}")
    
    if errors:
        error_msg = "State validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
        raise ValueError(error_msg)
    
    if warnings and strict:
        logger.info(f"State validation completed with {len(warnings)} warnings")
    
    return True


def validate_agent_status(status: str) -> bool:
    """
    Validate that an agent status is valid.
    
    Args:
        status: The status to validate
        
    Returns:
        True if valid, False otherwise
    """
    return status in VALID_AGENT_STATUSES


def validate_workflow_pattern(pattern: str) -> bool:
    """
    Validate that a workflow pattern is valid.
    
    Args:
        pattern: The pattern to validate
        
    Returns:
        True if valid, False otherwise
    """
    return pattern in VALID_WORKFLOW_PATTERNS


def validate_execution_mode(mode: str) -> bool:
    """
    Validate that an execution mode is valid.
    
    Args:
        mode: The mode to validate
        
    Returns:
        True if valid, False otherwise
    """
    return mode in VALID_EXECUTION_MODES


def validate_tool_permissions(permissions: Dict[str, List[str]]) -> List[str]:
    """
    Validate tool permissions structure and return any errors.
    
    Args:
        permissions: Tool permissions dictionary
        
    Returns:
        List of validation error messages
    """
    errors = []
    
    if not isinstance(permissions, dict):
        return ["Tool permissions must be a dictionary"]
    
    for agent_id, tools in permissions.items():
        if not isinstance(agent_id, str):
            errors.append(f"Agent ID must be a string, got {type(agent_id).__name__}")
        
        if not isinstance(tools, list):
            errors.append(f"Tools for agent '{agent_id}' must be a list")
            continue
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, str):
                errors.append(f"Tool at index {i} for agent '{agent_id}' must be a string")
    
    return errors


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


# ========== State Migration System ==========

class StateVersionError(Exception):
    """Raised when state version operations fail."""
    pass


def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two semantic version strings using the packaging library.
    
    This implementation uses the well-established packaging.version library
    that handles edge cases, pre-releases, and build metadata more robustly
    than custom implementations.
    
    Args:
        version1: First version string (e.g., "1.0.0", "2.0.0-alpha.1")
        version2: Second version string (e.g., "1.1.0", "2.0.0-beta.2")
        
    Returns:
        -1 if version1 < version2
         0 if version1 == version2
         1 if version1 > version2
         
    Raises:
        StateVersionError: If version format is invalid
    """
    try:
        v1 = Version(version1)
        v2 = Version(version2)
        
        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1
        else:
            return 0
    except Exception as e:
        raise StateVersionError(f"Invalid version format: {e}") from e


def is_compatible_version(state_version: str, required_version: str) -> bool:
    """
    Check if a state version is compatible with the required version.
    
    Args:
        state_version: Version of the state
        required_version: Required minimum version
        
    Returns:
        True if compatible, False otherwise
    """
    try:
        return compare_versions(state_version, required_version) >= 0
    except StateVersionError:
        logger.warning(f"Unable to compare versions: {state_version} vs {required_version}")
        return False


# Migration function registry
_MIGRATION_FUNCTIONS: Dict[str, Callable] = {}


def register_migration(from_version: str, to_version: str):
    """
    Decorator to register a migration function.
    
    Args:
        from_version: Source version
        to_version: Target version
    """
    def decorator(func):
        key = f"{from_version}->{to_version}"
        _MIGRATION_FUNCTIONS[key] = func
        logger.debug(f"Registered migration function: {key}")
        return func
    return decorator


def migrate_state(state: Dict[str, Any], target_version: str) -> Dict[str, Any]:
    """
    Migrate state from its current version to the target version.
    
    Args:
        state: State dictionary to migrate
        target_version: Target schema version
        
    Returns:
        Migrated state dictionary
        
    Raises:
        StateVersionError: If migration is not possible
    """
    current_version = state.get("state_version", "0.0.0")
    
    if current_version == target_version:
        return state
    
    logger.info(f"Migrating state from version {current_version} to {target_version}")
    
    # Find migration path
    migration_path = _find_migration_path(current_version, target_version)
    if not migration_path:
        raise StateVersionError(
            f"No migration path found from {current_version} to {target_version}"
        )
    
    # Apply migrations step by step
    migrated_state = dict(state)
    for from_ver, to_ver in migration_path:
        migration_key = f"{from_ver}->{to_ver}"
        if migration_key not in _MIGRATION_FUNCTIONS:
            raise StateVersionError(f"Missing migration function: {migration_key}")
        
        logger.debug(f"Applying migration: {migration_key}")
        try:
            migrated_state = _MIGRATION_FUNCTIONS[migration_key](migrated_state)
            migrated_state["state_version"] = to_ver
        except Exception as e:
            raise StateVersionError(f"Migration failed at {migration_key}: {str(e)}") from e
    
    # Validate migrated state
    try:
        validate_state(migrated_state)  # type: ignore
        logger.info(f"State migration completed successfully: {current_version} -> {target_version}")
    except ValueError as e:
        raise StateVersionError(f"Migrated state validation failed: {str(e)}") from e
    
    return migrated_state


def _find_migration_path(from_version: str, to_version: str) -> List[tuple]:
    """
    Find a migration path from source to target version.
    
    Args:
        from_version: Source version
        to_version: Target version
        
    Returns:
        List of (from_ver, to_ver) tuples representing the migration path
    """
    # For now, implement simple direct migration
    # In the future, this could implement graph search for multi-step migrations
    direct_key = f"{from_version}->{to_version}"
    if direct_key in _MIGRATION_FUNCTIONS:
        return [(from_version, to_version)]
    
    # Could implement more sophisticated path finding here
    # For example: BFS to find shortest migration path through multiple versions
    
    return []


def create_migration_backup(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a backup of state before migration.
    
    Args:
        state: State to backup
        
    Returns:
        Deep copy of the state
    """
    import copy
    backup = copy.deepcopy(state)
    backup["_migration_backup"] = {
        "timestamp": datetime.now().isoformat(),
        "original_version": state.get("state_version", "unknown")
    }
    return backup


def restore_from_backup(backup: Dict[str, Any]) -> Dict[str, Any]:
    """
    Restore state from a migration backup.
    
    Args:
        backup: Backup state dictionary
        
    Returns:
        Restored state without backup metadata
    """
    import copy
    restored = copy.deepcopy(backup)
    restored.pop("_migration_backup", None)
    return restored


# Example migration functions (these would be defined based on actual schema changes)

@register_migration("0.9.0", "1.0.0")
def migrate_0_9_to_1_0(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example migration from version 0.9.0 to 1.0.0.
    
    This is a template for how migration functions should be structured.
    """
    migrated = dict(state)
    
    # Example: Add new fields that were introduced in 1.0.0
    if "debug_flags" not in migrated:
        migrated["debug_flags"] = {
            "trace_execution": False,
            "log_state_changes": False,
            "validate_permissions": True,
            "record_performance": True
        }
    
    # Example: Rename or restructure fields
    if "old_field_name" in migrated:
        migrated["new_field_name"] = migrated.pop("old_field_name")
    
    # Example: Update field formats
    if "performance_metrics" in migrated and isinstance(migrated["performance_metrics"], list):
        # Convert old list format to new dict format
        migrated["performance_metrics"] = {
            "total_operations": len(migrated["performance_metrics"]),
            "operations": migrated["performance_metrics"]
        }
    
    logger.debug("Applied migration 0.9.0 -> 1.0.0")
    return migrated


def auto_migrate_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Automatically migrate state to the current schema version.
    
    Args:
        state: State to migrate
        
    Returns:
        Migrated state
        
    Raises:
        StateVersionError: If automatic migration fails
    """
    current_version = state.get("state_version", "0.0.0")
    
    if current_version == SCHEMA_VERSION:
        return state
    
    # Create backup before migration
    backup = create_migration_backup(state)
    
    try:
        return migrate_state(state, SCHEMA_VERSION)
    except StateVersionError as e:
        logger.error(f"Auto-migration failed: {e}")
        logger.info("State left unchanged due to migration failure")
        raise  # Raise the exception to alert users of incompatibility