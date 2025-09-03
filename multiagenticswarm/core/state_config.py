"""
Dynamic state field configuration for MultiAgenticSwarm.

This module defines the configuration system for AgentState fields, including:
- Field definitions with types, reducers, and metadata loaded from YAML
- Feature flags to enable/disable field groups
- Validation rules for each field
- Memory management policies
"""

import operator
import yaml
import os
from pathlib import Path
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
    """Central configuration for AgentState fields loaded from YAML."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.fields: Dict[str, FieldConfig] = {}
        self.feature_flags: Dict[str, bool] = {}
        self.group_configs: Dict[FieldGroup, Dict[str, Any]] = {}
        self._load_configuration_from_yaml(config_path)
    
    def _get_config_path(self, config_path: Optional[str] = None) -> str:
        """Get the path to the state configuration YAML file."""
        if config_path:
            return config_path
        
        # Default to config/state_config.yaml relative to the project root
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent  # Go up to project root
        default_path = project_root / "config" / "state_config.yaml"
        
        if not default_path.exists():
            raise FileNotFoundError(f"State configuration file not found at {default_path}")
        
        return str(default_path)
    
    def _parse_field_type(self, type_str: str) -> type:
        """Parse a field type string into an actual type."""
        # Map common type strings to actual types
        type_map = {
            "List[BaseMessage]": List[BaseMessage],
            "Optional[str]": Optional[str],
            "List[Dict[str, Any]]": List[Dict[str, Any]],
            "Dict[str, float]": Dict[str, float],
            "Dict[str, Any]": Dict[str, Any],
            "List[str]": List[str],
            "Dict[str, str]": Dict[str, str],
            "Dict[str, List[str]]": Dict[str, List[str]],
            "Dict[str, bool]": Dict[str, bool],
            "bool": bool,
            "str": str,
            "int": int,
            "Optional[Dict[str, Any]]": Optional[Dict[str, Any]],
            "Dict[str, Dict[str, Any]]": Dict[str, Dict[str, Any]],
        }
        
        return type_map.get(type_str, str)  # Default to str if not found
    
    def _load_configuration_from_yaml(self, config_path: Optional[str] = None):
        """Load field configuration from YAML file."""
        yaml_path = self._get_config_path(config_path)
        
        try:
            with open(yaml_path, 'r', encoding='utf-8') as file:
                config_data = yaml.safe_load(file)
        except Exception as e:
            raise RuntimeError(f"Failed to load state configuration from {yaml_path}: {e}")
        
        # Load feature flags
        self.feature_flags = config_data.get('feature_flags', {})
        
        # Load field groups
        self.group_configs = config_data.get('field_groups', {})
        
        # Load field configurations
        fields_data = config_data.get('fields', {})
        
        for field_name, field_data in fields_data.items():
            # Parse field type
            field_type = self._parse_field_type(field_data.get('field_type', 'str'))
            
            # Parse reducer type
            reducer_type_str = field_data.get('reducer_type', 'default_replace')
            reducer_type = ReducerType(reducer_type_str)
            
            # Parse field group
            group_str = field_data.get('group', 'debugging')
            group = FieldGroup(group_str)
            
            # Parse memory policy if present
            memory_policy = None
            if 'memory_policy' in field_data and field_data['memory_policy']:
                mp_data = field_data['memory_policy']
                memory_policy = MemoryPolicy(
                    max_entries=mp_data.get('max_entries'),
                    archive_after_hours=mp_data.get('archive_after_hours'),
                    cleanup_strategy=mp_data.get('cleanup_strategy', 'fifo'),
                    archive_location=mp_data.get('archive_location'),
                    enable_compression=mp_data.get('enable_compression', False)
                )
            
            # Create field config
            field_config = FieldConfig(
                name=field_name,
                field_type=field_type,
                reducer_type=reducer_type,
                group=group,
                required=field_data.get('required', True),
                default_value=field_data.get('default_value'),
                description=field_data.get('description', ''),
                validation_rules=field_data.get('validation_rules', []),
                memory_policy=memory_policy,
                feature_flag=field_data.get('feature_flag'),
                design_rationale=field_data.get('design_rationale', ''),
                conflict_resolution_strategy=field_data.get('conflict_resolution_strategy', ConflictResolutionStrategy.LAST_WRITE_WINS)
            )
            
            self.fields[field_name] = field_config
    
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


def reload_state_config(config_path: Optional[str] = None) -> StateConfiguration:
    """Reload the state configuration from YAML file."""
    global state_config
    state_config = StateConfiguration(config_path)
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