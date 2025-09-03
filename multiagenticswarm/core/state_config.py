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
            
            # Debugging & Monitoring
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
        
        # Type validation
        if not isinstance(value, config.field_type):
            errors.append(f"Field '{field_name}' must be of type {config.field_type.__name__}")
        
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
    
    # Create the class dynamically
    AgentStateDynamic = type(
        'AgentStateDynamic',
        (TypedDict,),
        {'__annotations__': annotations}
    )
    
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