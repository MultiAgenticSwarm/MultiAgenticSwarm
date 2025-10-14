"""
Core package for multiagenticswarm components.
"""

from .agent import Agent, AgentConfig
from .tool import Tool, ToolConfig, ToolScope, create_logger_tool, create_memory_tool
from .task import Task, TaskStep, TaskStatus, Collaboration
from .trigger import Trigger, TriggerType, TriggerStatus
from .automation import Automation, AutomationStatus, AutomationMode
from .system import System
from .tool_parser import ToolCallParser
from .state import (
    AgentState, 
    SCHEMA_VERSION,
    create_initial_state,
    validate_state,
    serialize_state,
    deserialize_state,
    log_state_change
)
from .state_migration import (
    register_migration,
    migrate_state, 
    auto_migrate_state,
    StateVersionError,
    MigrationError,
    compare_versions,
    is_compatible_version,
    create_migration_backup,
    restore_from_backup,
    validate_migration,
    create_test_state
)
from .state_reducers import (
    merge_agent_outputs,
    aggregate_progress,
    resolve_permissions,
    merge_tool_results,
    merge_memory_layers,
    merge_communication_messages,
    merge_execution_trace,
    apply_reducer,
    merge_states,
    REDUCERS
)

__all__ = [
    # Agent
    "Agent",
    "AgentConfig",
    
    # Tool
    "Tool",
    "ToolConfig", 
    "ToolScope",
    "create_logger_tool",
    "create_memory_tool",
    
    # Task
    "Task",
    "TaskStep",
    "TaskStatus", 
    "Collaboration",
    
    # Trigger
    "Trigger",
    "TriggerType",
    "TriggerStatus",
    
    # Automation
    "Automation",
    "AutomationStatus",
    "AutomationMode",
    
    # System
    "System",
    
    # Tool Parser
    "ToolCallParser",
    
    # State Management
    "AgentState",
    "SCHEMA_VERSION",
    "create_initial_state",
    "validate_state",
    "serialize_state",
    "deserialize_state",
    "log_state_change",
    
    # State Reducers
    "merge_agent_outputs",
    "aggregate_progress",
    "resolve_permissions",
    "merge_tool_results",
    "merge_memory_layers",
    "merge_communication_messages",
    "merge_execution_trace",
    "apply_reducer",
    "merge_states",
    "REDUCERS",
    
    # State Migration
    "register_migration",
    "migrate_state", 
    "auto_migrate_state",
    "StateVersionError",
    "MigrationError",
    "compare_versions",
    "is_compatible_version",
    "create_migration_backup",
    "restore_from_backup",
    "validate_migration",
    "create_test_state",
]
