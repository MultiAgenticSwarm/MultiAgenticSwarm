"""
Core package for multiagenticswarm components.
"""

from .agent import Agent, AgentConfig
from .automation import Automation, AutomationMode, AutomationStatus
from .state import (
    CURRENT_STATE_VERSION,
    AgentState,
    create_initial_state,
    validate_state_schema,
)
from .state_reducers import (
    aggregate_progress,
    merge_agent_outputs,
    merge_error_log,
    merge_execution_trace,
    merge_help_requests,
    merge_tool_results,
    resolve_permissions,
)
from .system import System
from .task import Collaboration, Task, TaskStatus, TaskStep
from .tool import Tool, ToolConfig, ToolScope, create_logger_tool, create_memory_tool
from .tool_parser import ToolCallParser
from .trigger import Trigger, TriggerStatus, TriggerType

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
    "create_initial_state",
    "validate_state_schema",
    "CURRENT_STATE_VERSION",
    # State Reducers
    "merge_agent_outputs",
    "aggregate_progress",
    "resolve_permissions",
    "merge_tool_results",
    "merge_help_requests",
    "merge_execution_trace",
    "merge_error_log",
]
