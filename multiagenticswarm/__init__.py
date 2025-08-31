"""
MultiAgenticSwarm - A powerful LangGraph-based multi-agent system
with dynamic configuration and hierarchical tool sharing.
"""

# Core imports
try:
    from .core.agent import Agent
    from .core.automation import Automation
    from .core.system import System
    from .core.task import Collaboration, Task
    from .core.tool import Tool
    from .core.trigger import Trigger
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
        LLMProviderType,
        LLMResponse,
        create_provider_from_config,
        get_llm_provider,
        get_provider_info,
        health_check_provider,
        list_available_providers,
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
    from .utils.log_viewer import LogViewer
    from .utils.logger import clear_logs, get_logger, get_logs, setup_logging, view_logs
except ImportError as e:
    # Logging utilities are optional but recommended
    setup_logging = None
    get_logger = None
    get_logs = None
    view_logs = None
    clear_logs = None
    LogViewer = None

# MCP integration components (optional)
try:
    from .core.mcp_integration import (
        MCPCapability,
        MCPClient,
        MCPMessage,
        MCPServer,
        MCPTool,
        MCPToolDescriptor,
        MCPTransportType,
    )
except ImportError as e:
    # MCP integration is optional
    MCPServer = None
    MCPClient = None
    MCPTool = None
    MCPTransportType = None
    MCPMessage = None
    MCPCapability = None
    MCPToolDescriptor = None

# Collaboration tools and systems (new)
try:
    from .core.collaborative_system import CollaborativeSystem, UniversalAgent
    from .core.delegation import SimpleDelegator
    from .tools.collaboration_tools import ProgressBoard
except ImportError as e:
    # Collaboration components are optional
    ProgressBoard = None
    SimpleDelegator = None
    UniversalAgent = None
    CollaborativeSystem = None

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
    "LogViewer",
    # MCP integration components (may be None if import fails)
    "MCPServer",
    "MCPClient",
    "MCPTool",
    "MCPTransportType",
    "MCPMessage",
    "MCPCapability",
    "MCPToolDescriptor",
    # Collaboration components (may be None if import fails)
    "ProgressBoard",
    "SimpleDelegator",
    "UniversalAgent",
    "CollaborativeSystem",
]

# Filter out None values from __all__
__all__ = [name for name in __all__ if globals().get(name) is not None]
