"""
Dynamic state field configuration for MultiAgenticSwarm.

This module defines the configuration system for AgentState fields, including:
- Field definitions with types, reducers, and metadata
- Feature flags to enable/disable field groups
- Validation rules for each field
- Memory management policies
"""

import operator
from typing import Any, Dict, List, Optional, Union, Callable, TypedDict
from typing_extensions import Annotated
from dataclasses import dataclass, field
from enum import Enum

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from .state_reducers import (
    merge_agent_outputs,
    aggregate_progress, 
    resolve_permissions,
    merge_tool_results,
    merge_memory_layers,
    merge_communication_messages,
    merge_execution_trace,
    ConflictResolutionStrategy
)


class FieldGroup(str, Enum):
    """Field groups for enabling/disabling related functionality."""
    MESSAGE_MANAGEMENT = "message_management"
    TASK_MANAGEMENT = "task_management"
    AGENT_COORDINATION = "agent_coordination"
    TOOL_EXECUTION = "tool_execution"
    COLLABORATION_CONTEXT = "collaboration_context"
    MEMORY_LAYERS = "memory_layers"
    COMMUNICATION = "communication"
    CONTROL_FLOW = "control_flow"
    THREAD_CHECKPOINT = "thread_checkpoint"
    GRAPH_EXECUTION = "graph_execution"
    STREAMING = "streaming"
    SUBGRAPH = "subgraph"
    INTERRUPTS = "interrupts"
    DEBUGGING = "debugging"


class ReducerType(str, Enum):
    """Types of reducers available for state fields."""
    ADD_MESSAGES = "add_messages"
    OPERATOR_ADD = "operator_add"
    MERGE_AGENT_OUTPUTS = "merge_agent_outputs"
    AGGREGATE_PROGRESS = "aggregate_progress"
    RESOLVE_PERMISSIONS = "resolve_permissions"
    MERGE_TOOL_RESULTS = "merge_tool_results"
    MERGE_MEMORY_LAYERS = "merge_memory_layers"
    MERGE_COMMUNICATION_MESSAGES = "merge_communication_messages"
    MERGE_EXECUTION_TRACE = "merge_execution_trace"
    DEFAULT_REPLACE = "default_replace"


@dataclass
class MemoryPolicy:
    """Memory management policy for a field."""
    max_entries: Optional[int] = None
    archive_after_hours: Optional[int] = None
    cleanup_strategy: str = "fifo"  # fifo, lifo, timestamp_based
    archive_location: Optional[str] = None
    enable_compression: bool = False


@dataclass
class FieldConfig:
    """Configuration for a single state field."""
    name: str
    field_type: type
    reducer_type: ReducerType
    group: FieldGroup
    required: bool = True
    default_value: Any = None
    description: str = ""
    validation_rules: List[str] = field(default_factory=list)
    memory_policy: Optional[MemoryPolicy] = None
    feature_flag: Optional[str] = None
    
    # Metadata for documentation and debugging
    design_rationale: str = ""
    conflict_resolution_strategy: str = ConflictResolutionStrategy.LAST_WRITE_WINS
    
    def get_reducer_function(self) -> Optional[Callable]:
        """Get the actual reducer function for this field."""
        reducer_map = {
            ReducerType.ADD_MESSAGES: add_messages,
            ReducerType.OPERATOR_ADD: operator.add,
            ReducerType.MERGE_AGENT_OUTPUTS: merge_agent_outputs,
            ReducerType.AGGREGATE_PROGRESS: aggregate_progress,
            ReducerType.RESOLVE_PERMISSIONS: resolve_permissions,
            ReducerType.MERGE_TOOL_RESULTS: merge_tool_results,
            ReducerType.MERGE_MEMORY_LAYERS: merge_memory_layers,
            ReducerType.MERGE_COMMUNICATION_MESSAGES: merge_communication_messages,
            ReducerType.MERGE_EXECUTION_TRACE: merge_execution_trace,
            ReducerType.DEFAULT_REPLACE: None,
        }
        return reducer_map.get(self.reducer_type)
    
    def get_annotated_type(self):
        """Get the properly annotated type for this field."""
        reducer_func = self.get_reducer_function()
        if reducer_func:
            return Annotated[self.field_type, reducer_func]
        else:
            return self.field_type


class StateConfiguration:
    """Central configuration for AgentState fields."""
    
    def __init__(self):
        self.fields: Dict[str, FieldConfig] = {}
        self.feature_flags: Dict[str, bool] = {}
        self.group_configs: Dict[FieldGroup, Dict[str, Any]] = {}
        self._initialize_default_configuration()
    
    def _initialize_default_configuration(self):
        """Initialize the default field configuration."""
        
        # Feature flags - all enabled by default
        self.feature_flags = {
            "enable_message_management": True,
            "enable_task_management": True,
            "enable_agent_coordination": True,
            "enable_tool_execution": True,
            "enable_collaboration_context": True,
            "enable_memory_layers": True,
            "enable_communication": True,
            "enable_control_flow": True,
            "enable_thread_checkpoint": True,
            "enable_graph_execution": True,
            "enable_streaming": True,
            "enable_subgraph": True,
            "enable_interrupts": True,
            "enable_debugging": True,
        }
        
        # Define field configurations
        field_configs = [
            # Message Management
            FieldConfig(
                name="messages",
                field_type=List[BaseMessage],
                reducer_type=ReducerType.ADD_MESSAGES,
                group=FieldGroup.MESSAGE_MANAGEMENT,
                required=True,
                default_value=[],
                description="Conversation history using LangGraph's add_messages reducer",
                design_rationale="Uses add_messages reducer because messages must be appended chronologically, never replaced. Multiple agents may add messages concurrently. LangGraph's add_messages handles deduplication and ordering. Critical for maintaining conversation context.",
                memory_policy=MemoryPolicy(max_entries=1000, archive_after_hours=24),
                conflict_resolution_strategy=ConflictResolutionStrategy.MERGE_UNION
            ),
            
            # Task Management
            FieldConfig(
                name="current_task",
                field_type=Optional[str],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.TASK_MANAGEMENT,
                required=False,
                default_value=None,
                description="Active task description",
                design_rationale="Uses default replace reducer because it represents current state only (no history needed). Single value that changes atomically. Historical values provide no benefit. Reduces memory usage for frequently updated fields.",
                conflict_resolution_strategy=ConflictResolutionStrategy.LAST_WRITE_WINS
            ),
            
            FieldConfig(
                name="subtasks",
                field_type=List[Dict[str, Any]],
                reducer_type=ReducerType.OPERATOR_ADD,
                group=FieldGroup.TASK_MANAGEMENT,
                required=True,
                default_value=[],
                description="Breakdown of main task into subtasks",
                design_rationale="Uses operator.add reducer because agents progressively break down tasks. Creates audit trail for debugging and compliance. Enables agents to learn from historical patterns. Supports concurrent additions without data loss.",
                memory_policy=MemoryPolicy(max_entries=500, archive_after_hours=48),
                conflict_resolution_strategy=ConflictResolutionStrategy.MERGE_UNION
            ),
            
            FieldConfig(
                name="task_progress",
                field_type=Dict[str, float],
                reducer_type=ReducerType.AGGREGATE_PROGRESS,
                group=FieldGroup.TASK_MANAGEMENT,
                required=True,
                default_value={},
                description="Progress percentage (0-100) per subtask",
                design_rationale="Uses aggregate_progress reducer to ensure monotonic progress and handle concurrent updates intelligently.",
                validation_rules=["progress_range_0_100", "monotonic_increase"],
                conflict_resolution_strategy=ConflictResolutionStrategy.MONOTONIC_INCREASE
            ),
            
            FieldConfig(
                name="task_metadata",
                field_type=Dict[str, Any],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.TASK_MANAGEMENT,
                required=True,
                default_value={},
                description="Additional task context and metadata",
                design_rationale="Uses default replace reducer because it represents current metadata state only.",
                conflict_resolution_strategy=ConflictResolutionStrategy.LAST_WRITE_WINS
            ),
            
            # Agent Coordination
            FieldConfig(
                name="current_agent",
                field_type=Optional[str],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.AGENT_COORDINATION,
                required=False,
                default_value=None,
                description="Currently executing agent identifier",
                design_rationale="Uses default replace reducer because it represents current state only (no history needed). Single value that changes atomically.",
                conflict_resolution_strategy=ConflictResolutionStrategy.LAST_WRITE_WINS
            ),
            
            FieldConfig(
                name="next_agent",
                field_type=Optional[str],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.AGENT_COORDINATION,
                required=False,
                default_value=None,
                description="Next agent to execute in the workflow",
                design_rationale="Uses default replace reducer because it represents current state only (no history needed). Single value that changes atomically.",
                conflict_resolution_strategy=ConflictResolutionStrategy.LAST_WRITE_WINS
            ),
            
            FieldConfig(
                name="agent_outputs",
                field_type=Dict[str, Any],
                reducer_type=ReducerType.MERGE_AGENT_OUTPUTS,
                group=FieldGroup.AGENT_COORDINATION,
                required=True,
                default_value={},
                description="Results and outputs from each agent",
                design_rationale="Uses merge_agent_outputs reducer to preserve historical outputs and resolve conflicts based on timestamp.",
                memory_policy=MemoryPolicy(max_entries=100, archive_after_hours=24),
                conflict_resolution_strategy=ConflictResolutionStrategy.TIMESTAMP_BASED
            ),
            
            FieldConfig(
                name="agent_queue",
                field_type=List[str],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.AGENT_COORDINATION,
                required=True,
                default_value=[],
                description="Queue of pending agent executions",
                design_rationale="Uses default replace reducer because it represents current queue state only.",
                conflict_resolution_strategy=ConflictResolutionStrategy.LAST_WRITE_WINS
            ),
            
            FieldConfig(
                name="agent_status",
                field_type=Dict[str, str],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.AGENT_COORDINATION,
                required=True,
                default_value={},
                description="Health and availability status per agent",
                design_rationale="Uses default replace reducer because it represents current status only.",
                validation_rules=["valid_agent_status"],
                conflict_resolution_strategy=ConflictResolutionStrategy.LAST_WRITE_WINS
            ),
            
            # Tool Execution
            FieldConfig(
                name="tool_calls",
                field_type=List[Dict[str, Any]],
                reducer_type=ReducerType.OPERATOR_ADD,
                group=FieldGroup.TOOL_EXECUTION,
                required=True,
                default_value=[],
                description="History of all tool requests made",
                design_rationale="Uses operator.add reducer because it maintains complete tool execution history for debugging. Creates audit trail for compliance and troubleshooting. Enables agents to learn from historical tool usage patterns. Supports concurrent additions without data loss.",
                memory_policy=MemoryPolicy(max_entries=1000, archive_after_hours=24),
                conflict_resolution_strategy=ConflictResolutionStrategy.MERGE_UNION
            ),
            
            FieldConfig(
                name="tool_results",
                field_type=Dict[str, Any],
                reducer_type=ReducerType.MERGE_TOOL_RESULTS,
                group=FieldGroup.TOOL_EXECUTION,
                required=True,
                default_value={},
                description="Results from tool executions",
                design_rationale="Uses merge_tool_results reducer to preserve history and handle duplicates intelligently.",
                memory_policy=MemoryPolicy(max_entries=500, archive_after_hours=48),
                conflict_resolution_strategy=ConflictResolutionStrategy.KEEP_BOTH
            ),
            
            FieldConfig(
                name="tool_permissions",
                field_type=Dict[str, List[str]],
                reducer_type=ReducerType.RESOLVE_PERMISSIONS,
                group=FieldGroup.TOOL_EXECUTION,
                required=True,
                default_value={},
                description="Dynamic permission matrix: agent_id -> [tool_names]",
                design_rationale="Uses resolve_permissions reducer with security-first approach (most restrictive wins).",
                validation_rules=["valid_tool_permissions"],
                conflict_resolution_strategy=ConflictResolutionStrategy.MOST_RESTRICTIVE
            ),
            
            FieldConfig(
                name="pending_tools",
                field_type=List[Dict[str, Any]],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.TOOL_EXECUTION,
                required=True,
                default_value=[],
                description="Queue of pending tool requests",
                design_rationale="Uses default replace reducer because it represents current queue state only.",
                conflict_resolution_strategy=ConflictResolutionStrategy.LAST_WRITE_WINS
            ),
            
            FieldConfig(
                name="tool_errors",
                field_type=List[Dict[str, Any]],
                reducer_type=ReducerType.OPERATOR_ADD,
                group=FieldGroup.TOOL_EXECUTION,
                required=True,
                default_value=[],
                description="Failed tool executions with error details",
                design_rationale="Uses operator.add reducer because it keeps error history for debugging and compliance. Enables agents to learn from historical error patterns. Supports concurrent additions without data loss. Critical for system reliability and monitoring.",
                memory_policy=MemoryPolicy(max_entries=500, archive_after_hours=48),
                conflict_resolution_strategy=ConflictResolutionStrategy.MERGE_UNION
            ),
            
            # Add more field configurations here...
            # For brevity, I'll add a few more key ones and indicate where others would go
            
            # Collaboration Context
            FieldConfig(
                name="collaboration_prompt",
                field_type=Optional[str],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.COLLABORATION_CONTEXT,
                required=False,
                default_value=None,
                description="Natural language instructions for collaboration",
                design_rationale="Uses default replace reducer because it represents current state only (no history needed).",
                conflict_resolution_strategy=ConflictResolutionStrategy.LAST_WRITE_WINS
            ),
            
            FieldConfig(
                name="coordination_rules",
                field_type=List[Dict[str, Any]],
                reducer_type=ReducerType.OPERATOR_ADD,
                group=FieldGroup.COLLABORATION_CONTEXT,
                required=True,
                default_value=[],
                description="Extracted rules and constraints from prompt",
                design_rationale="Uses operator.add reducer because it accumulates discovered rules and constraints over time. Creates audit trail for debugging and compliance. Enables agents to learn from historical coordination patterns. Supports concurrent additions without data loss.",
                memory_policy=MemoryPolicy(max_entries=200, archive_after_hours=72),
                conflict_resolution_strategy=ConflictResolutionStrategy.MERGE_UNION
            ),
            
            # Add other missing fields with minimal configurations for completeness
            FieldConfig(
                name="agent_roles",
                field_type=Dict[str, str],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.COLLABORATION_CONTEXT,
                required=True,
                default_value={},
                description="Role assignments per agent"
            ),
            
            FieldConfig(
                name="workflow_pattern",
                field_type=Optional[str],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.COLLABORATION_CONTEXT,
                required=False,
                default_value=None,
                description="Current collaboration pattern being used"
            ),
            
            FieldConfig(
                name="decision_points",
                field_type=List[Dict[str, Any]],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.COLLABORATION_CONTEXT,
                required=True,
                default_value=[],
                description="Conditional branch points in the workflow"
            ),
            
            # Memory Layers
            FieldConfig(
                name="short_term_memory",
                field_type=Dict[str, Any],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.MEMORY_LAYERS,
                required=True,
                default_value={},
                description="Current conversation context"
            ),
            
            FieldConfig(
                name="working_memory",
                field_type=Dict[str, Any],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.MEMORY_LAYERS,
                required=True,
                default_value={},
                description="Active task and working information"
            ),
            
            FieldConfig(
                name="episodic_memory",
                field_type=List[Dict[str, Any]],
                reducer_type=ReducerType.OPERATOR_ADD,
                group=FieldGroup.MEMORY_LAYERS,
                required=True,
                default_value=[],
                description="Sequence of events and experiences",
                design_rationale="Uses operator.add reducer because it builds experience history for learning and decision making.",
                memory_policy=MemoryPolicy(max_entries=1000, archive_after_hours=24)
            ),
            
            FieldConfig(
                name="shared_memory",
                field_type=Dict[str, Any],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.MEMORY_LAYERS,
                required=True,
                default_value={},
                description="Information visible to all agents"
            ),
            
            FieldConfig(
                name="private_memory",
                field_type=Dict[str, Dict[str, Any]],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.MEMORY_LAYERS,
                required=True,
                default_value={},
                description="Agent-specific private information"
            ),
            
            # Communication
            FieldConfig(
                name="agent_messages",
                field_type=List[Dict[str, Any]],
                reducer_type=ReducerType.OPERATOR_ADD,
                group=FieldGroup.COMMUNICATION,
                required=True,
                default_value=[],
                description="Direct messages between agents",
                design_rationale="Uses operator.add reducer because communication logs must preserve chronological order. Creates audit trail for debugging and compliance. Enables agents to learn from historical communication patterns. Supports concurrent additions without data loss.",
                memory_policy=MemoryPolicy(max_entries=1000, archive_after_hours=24),
                conflict_resolution_strategy=ConflictResolutionStrategy.MERGE_UNION
            ),
            
            FieldConfig(
                name="help_requests",
                field_type=List[Dict[str, Any]],
                reducer_type=ReducerType.OPERATOR_ADD,
                group=FieldGroup.COMMUNICATION,
                required=True,
                default_value=[],
                description="Assistance requests between agents"
            ),
            
            FieldConfig(
                name="broadcast_messages",
                field_type=List[Dict[str, Any]],
                reducer_type=ReducerType.OPERATOR_ADD,
                group=FieldGroup.COMMUNICATION,
                required=True,
                default_value=[],
                description="System-wide announcements"
            ),
            
            FieldConfig(
                name="pending_responses",
                field_type=List[Dict[str, Any]],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.COMMUNICATION,
                required=True,
                default_value=[],
                description="Responses awaiting from agents"
            ),
            
            # Control Flow
            FieldConfig(
                name="should_continue",
                field_type=bool,
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.CONTROL_FLOW,
                required=True,
                default_value=True,
                description="Whether to continue with execution"
            ),
            
            FieldConfig(
                name="requires_human_approval",
                field_type=bool,
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.CONTROL_FLOW,
                required=True,
                default_value=False,
                description="Pause execution for human input"
            ),
            
            FieldConfig(
                name="interrupt_checkpoint",
                field_type=Optional[str],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.CONTROL_FLOW,
                required=False,
                default_value=None,
                description="Where to pause execution"
            ),
            
            FieldConfig(
                name="resume_point",
                field_type=Optional[str],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.CONTROL_FLOW,
                required=False,
                default_value=None,
                description="Where to continue after interrupt"
            ),
            
            FieldConfig(
                name="execution_mode",
                field_type=str,
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.CONTROL_FLOW,
                required=True,
                default_value="sequential",
                description="Execution mode: sequential/parallel/supervisor"
            ),
            
            # Add remaining fields with minimal configurations for completeness
            # Thread & Checkpoint Management
            FieldConfig(
                name="thread_id",
                field_type=Optional[str],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.THREAD_CHECKPOINT,
                required=False,
                default_value=None,
                description="Unique conversation identifier"
            ),
            
            FieldConfig(
                name="checkpoint_id",
                field_type=Optional[str],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.THREAD_CHECKPOINT,
                required=False,
                default_value=None,
                description="Current checkpoint ID"
            ),
            
            FieldConfig(
                name="checkpoint_ts",
                field_type=Optional[str],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.THREAD_CHECKPOINT,
                required=False,
                default_value=None,
                description="Checkpoint timestamp"
            ),
            
            FieldConfig(
                name="parent_checkpoint_id",
                field_type=Optional[str],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.THREAD_CHECKPOINT,
                required=False,
                default_value=None,
                description="For checkpoint lineage"
            ),
            
            FieldConfig(
                name="checkpoint_ns",
                field_type=Optional[str],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.THREAD_CHECKPOINT,
                required=False,
                default_value=None,
                description="Namespace for isolation"
            ),
            
            FieldConfig(
                name="checkpoint_metadata",
                field_type=Dict[str, Any],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.THREAD_CHECKPOINT,
                required=True,
                default_value={},
                description="Checkpoint-specific metadata"
            ),
            
            FieldConfig(
                name="is_resuming",
                field_type=bool,
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.THREAD_CHECKPOINT,
                required=True,
                default_value=False,
                description="Whether resuming from checkpoint"
            ),
            
            # Graph Execution Context
            FieldConfig(
                name="graph_path",
                field_type=List[str],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.GRAPH_EXECUTION,
                required=True,
                default_value=[],
                description="Current path through the graph"
            ),
            
            FieldConfig(
                name="pending_tasks",
                field_type=List[str],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.GRAPH_EXECUTION,
                required=True,
                default_value=[],
                description="Tasks in other branches"
            ),
            
            FieldConfig(
                name="branch_results",
                field_type=Dict[str, Any],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.GRAPH_EXECUTION,
                required=True,
                default_value={},
                description="Results from parallel branches"
            ),
            
            FieldConfig(
                name="channel_values",
                field_type=Dict[str, Any],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.GRAPH_EXECUTION,
                required=True,
                default_value={},
                description="LangGraph channel system"
            ),
            
            FieldConfig(
                name="config",
                field_type=Optional[Dict[str, Any]],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.GRAPH_EXECUTION,
                required=False,
                default_value=None,
                description="LangGraph RunnableConfig"
            ),
            
            FieldConfig(
                name="recursion_limit",
                field_type=int,
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.GRAPH_EXECUTION,
                required=True,
                default_value=25,
                description="Prevent infinite loops (default: 25)"
            ),
            
            # Streaming Support
            FieldConfig(
                name="stream_mode",
                field_type=Optional[str],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.STREAMING,
                required=False,
                default_value=None,
                description="Stream mode: values/updates/debug"
            ),
            
            FieldConfig(
                name="partial_updates",
                field_type=List[Dict[str, Any]],
                reducer_type=ReducerType.OPERATOR_ADD,
                group=FieldGroup.STREAMING,
                required=True,
                default_value=[],
                description="For streaming partial state",
                design_rationale="Uses operator.add reducer because streaming updates are critical for debugging and monitoring.",
                memory_policy=MemoryPolicy(max_entries=500, archive_after_hours=12)
            ),
            
            FieldConfig(
                name="stream_metadata",
                field_type=Dict[str, Any],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.STREAMING,
                required=True,
                default_value={},
                description="Streaming-specific metadata"
            ),
            
            # Subgraph Context
            FieldConfig(
                name="subgraph_states",
                field_type=Dict[str, Any],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.SUBGRAPH,
                required=True,
                default_value={},
                description="States from subgraphs"
            ),
            
            FieldConfig(
                name="parent_graph_id",
                field_type=Optional[str],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.SUBGRAPH,
                required=False,
                default_value=None,
                description="Parent graph if this is a subgraph"
            ),
            
            FieldConfig(
                name="subgraph_configs",
                field_type=Dict[str, Any],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.SUBGRAPH,
                required=True,
                default_value={},
                description="Subgraph-specific configs"
            ),
            
            # Enhanced Interrupts
            FieldConfig(
                name="interrupt_before",
                field_type=List[str],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.INTERRUPTS,
                required=True,
                default_value=[],
                description="Nodes to interrupt before"
            ),
            
            FieldConfig(
                name="interrupt_after",
                field_type=List[str],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.INTERRUPTS,
                required=True,
                default_value=[],
                description="Nodes to interrupt after"
            ),
            
            FieldConfig(
                name="pending_human_input",
                field_type=Optional[Dict[str, Any]],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.INTERRUPTS,
                required=False,
                default_value=None,
                description="Awaiting human input"
            ),
            
            # Debugging & Monitoring
            FieldConfig(
                name="state_version",
                field_type=str,
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.DEBUGGING,
                required=True,
                default_value="1.1.0",
                description="Schema version for compatibility checking"
            ),
            
            FieldConfig(
                name="execution_trace",
                field_type=List[Dict[str, Any]],
                reducer_type=ReducerType.OPERATOR_ADD,
                group=FieldGroup.DEBUGGING,
                required=True,
                default_value=[],
                description="Step-by-step execution log",
                design_rationale="Uses operator.add reducer because it provides step-by-step execution log for debugging. Creates audit trail for debugging and compliance. Enables system monitoring and historical analysis. Supports concurrent additions without data loss. Max 1000 entries, older entries archived to persistent storage. Cleanup: Entries older than 24 hours moved to archive.",
                memory_policy=MemoryPolicy(max_entries=1000, archive_after_hours=24, archive_location="persistent_storage"),
                conflict_resolution_strategy=ConflictResolutionStrategy.MERGE_UNION
            ),
            
            FieldConfig(
                name="error_log",
                field_type=List[Dict[str, Any]],
                reducer_type=ReducerType.OPERATOR_ADD,
                group=FieldGroup.DEBUGGING,
                required=True,
                default_value=[],
                description="Error messages and stack traces",
                design_rationale="Uses operator.add reducer because error logs are critical for debugging and monitoring. Creates audit trail for debugging and compliance. Critical for system reliability and troubleshooting. Supports concurrent additions without data loss. Max 500 entries, older entries archived to persistent storage. Cleanup: Entries older than 48 hours moved to archive.",
                memory_policy=MemoryPolicy(max_entries=500, archive_after_hours=48, archive_location="persistent_storage"),
                conflict_resolution_strategy=ConflictResolutionStrategy.MERGE_UNION
            ),
            
            FieldConfig(
                name="performance_metrics",
                field_type=Dict[str, Any],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.DEBUGGING,
                required=True,
                default_value={},
                description="Timing and resource usage metrics"
            ),
            
            FieldConfig(
                name="debug_flags",
                field_type=Dict[str, bool],
                reducer_type=ReducerType.DEFAULT_REPLACE,
                group=FieldGroup.DEBUGGING,
                required=True,
                default_value={},
                description="Flags to enable detailed logging"
            ),
        ]
        
        # Register all field configurations
        for config in field_configs:
            self.fields[config.name] = config
    
    def get_field_config(self, field_name: str) -> Optional[FieldConfig]:
        """Get configuration for a specific field."""
        return self.fields.get(field_name)
    
    def get_active_fields(self) -> Dict[str, FieldConfig]:
        """Get all fields that are currently enabled based on feature flags."""
        active_fields = {}
        
        for field_name, config in self.fields.items():
            # Check if field group is enabled
            group_flag = f"enable_{config.group.value}"
            if not self.feature_flags.get(group_flag, True):
                continue
            
            # Check specific feature flag if defined
            if config.feature_flag and not self.feature_flags.get(config.feature_flag, True):
                continue
            
            active_fields[field_name] = config
        
        return active_fields
    
    def enable_field_group(self, group: FieldGroup, enabled: bool = True):
        """Enable or disable an entire field group."""
        flag_name = f"enable_{group.value}"
        self.feature_flags[flag_name] = enabled
    
    def get_field_type_annotations(self) -> Dict[str, Any]:
        """Get type annotations for all active fields."""
        annotations = {}
        for field_name, config in self.get_active_fields().items():
            annotations[field_name] = config.get_annotated_type()
        return annotations
    
    def validate_field_value(self, field_name: str, value: Any) -> List[str]:
        """Validate a field value against its configuration rules."""
        config = self.get_field_config(field_name)
        if not config:
            return [f"Unknown field: {field_name}"]
        
        errors = []
        
        # Type validation - handle generic types properly
        try:
            # For complex generic types, we'll do basic checks
            if hasattr(config.field_type, "__origin__"):
                # This is a generic type like List[Something] or Dict[K, V]
                origin_type = config.field_type.__origin__
                if not isinstance(value, origin_type):
                    errors.append(f"Field '{field_name}' must be of type {origin_type.__name__}")
            else:
                # Simple type check
                if not isinstance(value, config.field_type):
                    errors.append(f"Field '{field_name}' must be of type {config.field_type.__name__}")
        except (TypeError, AttributeError):
            # Fallback for complex types - just check basic structure
            if config.field_type.__name__.startswith("List") and not isinstance(value, list):
                errors.append(f"Field '{field_name}' must be a list")
            elif config.field_type.__name__.startswith("Dict") and not isinstance(value, dict):
                errors.append(f"Field '{field_name}' must be a dictionary")
        
        # Custom validation rules
        for rule in config.validation_rules:
            if rule == "progress_range_0_100" and isinstance(value, dict):
                for task_id, progress in value.items():
                    if not isinstance(progress, (int, float)) or not (0 <= progress <= 100):
                        errors.append(f"Progress for task '{task_id}' must be between 0 and 100")
            
            elif rule == "valid_agent_status" and isinstance(value, dict):
                from .state import VALID_AGENT_STATUSES
                for agent_id, status in value.items():
                    if status not in VALID_AGENT_STATUSES:
                        errors.append(f"Invalid status '{status}' for agent '{agent_id}'")
            
            elif rule == "valid_tool_permissions" and isinstance(value, dict):
                for agent_id, tools in value.items():
                    if not isinstance(tools, list):
                        errors.append(f"Tool permissions for agent '{agent_id}' must be a list")
                    elif not all(isinstance(tool, str) for tool in tools):
                        errors.append(f"All tool names for agent '{agent_id}' must be strings")
        
        return errors
    
    def apply_memory_policies(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply memory management policies to clean up state fields."""
        cleaned_state = dict(state)
        
        for field_name, config in self.get_active_fields().items():
            if not config.memory_policy or field_name not in cleaned_state:
                continue
            
            policy = config.memory_policy
            field_value = cleaned_state[field_name]
            
            # Apply max_entries limit for list fields
            if isinstance(field_value, list) and policy.max_entries:
                if len(field_value) > policy.max_entries:
                    # Keep the most recent entries
                    cleaned_state[field_name] = field_value[-policy.max_entries:]
        
        return cleaned_state


# Global state configuration instance
state_config = StateConfiguration()


def get_state_config() -> StateConfiguration:
    """Get the global state configuration instance."""
    return state_config


def create_dynamic_agent_state_class():
    """Create AgentState class dynamically based on configuration."""
    annotations = state_config.get_field_type_annotations()
    
    # Create a simple TypedDict directly
    AgentStateDynamic = TypedDict('AgentStateDynamic', annotations)
    
    return AgentStateDynamic


def get_field_documentation() -> Dict[str, Dict[str, str]]:
    """Get comprehensive documentation for all fields."""
    docs = {}
    
    for field_name, config in state_config.get_active_fields().items():
        docs[field_name] = {
            "description": config.description,
            "reducer_type": config.reducer_type.value,
            "design_rationale": config.design_rationale,
            "conflict_resolution": config.conflict_resolution_strategy,
            "group": config.group.value,
            "memory_policy": str(config.memory_policy) if config.memory_policy else "None"
        }
    
    return docs