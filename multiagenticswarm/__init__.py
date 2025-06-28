"""
MultiAgenticSwarm - A powerful LangGraph-based multi-agent system
with dynamic configuration and hierarchical tool sharing.
"""

# Core imports
try:
    from .core.agent import Agent
    from .core.tool import Tool
    from .core.task import Task, Collaboration
    from .core.trigger import Trigger
    from .core.automation import Automation
    from .core.system import System
except ImportError as e:
    # Handle potential circular import issues
    Agent = None
    Tool = None
    Task = None
    Collaboration = None
    Trigger = None
    Automation = None
    System = None

# LLM providers
try:
    from .llm.providers import (
        LLMProvider,
        LLMResponse,
        LLMProviderType,
        get_llm_provider,
        list_available_providers,
        get_provider_info,
        health_check_provider,
        create_provider_from_config
    )
except ImportError as e:
    # LLM providers are optional
    LLMProvider = None
    LLMResponse = None
    LLMProviderType = None
    get_llm_provider = None
    list_available_providers = None
    get_provider_info = None
    health_check_provider = None
    create_provider_from_config = None

# Logging utilities
try:
    from .utils.logger import (
        setup_logging,
        get_logger,
        get_logs,
        view_logs,
        clear_logs
    )
    from .utils.log_viewer import LogViewer
except ImportError as e:
    # Logging utilities are optional but recommended
    setup_logging = None
    get_logger = None
    get_logs = None
    view_logs = None
    clear_logs = None
    LogViewer = None

__version__ = "0.1.0"
__author__ = "MultiAgenticSwarm Team"
__email__ = "contact@multiagenticswarm.dev"

__all__ = [
    # Core components (may be None if import fails)
    "Agent",
    "Tool", 
    "Task",
    "Collaboration",
    "Trigger",
    "Automation",
    "System",
    # LLM providers (may be None if import fails)
    "LLMProvider",
    "LLMResponse", 
    "LLMProviderType",
    "get_llm_provider",
    "list_available_providers",
    "get_provider_info",
    "health_check_provider",
    "create_provider_from_config",
    # Logging utilities (may be None if import fails)
    "setup_logging",
    "get_logger",
    "get_logs", 
    "view_logs",
    "clear_logs",
    "LogViewer"
]

# Filter out None values from __all__
__all__ = [name for name in __all__ if globals().get(name) is not None]
