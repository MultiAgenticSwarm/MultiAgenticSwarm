"""
Core package for multiagenticswarm components.
"""

from .agent import Agent, AgentConfig
from .automation import Automation, AutomationMode, AutomationStatus
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
]
