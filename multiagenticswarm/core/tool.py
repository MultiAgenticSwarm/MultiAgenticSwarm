"""
Tool system with hierarchical sharing (local, shared, global).
"""

import uuid
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum

try:
    from pydantic import BaseModel, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # Fallback base class
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        
        def model_dump(self):
            return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    def Field(**kwargs):
        return kwargs.get('default', None)

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ToolScope(str, Enum):
    """Tool sharing scope levels."""
    LOCAL = "local"      # Available to specific agent only
    SHARED = "shared"    # Available to specific set of agents
    GLOBAL = "global"    # Available to all agents


class ToolConfig(BaseModel):
    """Configuration for a tool."""
    name: str
    description: str = ""
    scope: ToolScope = ToolScope.LOCAL
    agents: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class Tool:
    """
    A tool that can be used by agents with hierarchical sharing support.
    
    Tools can be:
    - Local: Available to one specific agent
    - Shared: Available to a specific set of agents  
    - Global: Available to all agents in the system
    """
    
    def __init__(
        self,
        name: str,
        func: Optional[Callable] = None,
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None,
        tool_id: Optional[str] = None,
    ):
        """
        Initialize a tool.
        
        Args:
            name: Unique name for the tool
            func: Callable function that implements the tool
            description: Description of what the tool does
            parameters: Parameter schema for the tool
            tool_id: Optional custom tool ID
        """
        self.id = tool_id or str(uuid.uuid4())
        self.name = name
        self.func = func
        self.description = description
        self.parameters = parameters or {}
        
        # Sharing configuration
        self.scope = ToolScope.LOCAL
        self.local_agent: Optional[str] = None
        self.shared_agents: List[str] = []
        self.is_global = False
        
        # Runtime tracking
        self.usage_count = 0
        self.last_used_by: Optional[str] = None
        self.execution_history: List[Dict[str, Any]] = []
        
        logger.info(f"Created tool '{name}' with scope '{self.scope.value}'")
    
    def set_local(self, agent: Union[str, "Agent"]) -> "Tool":
        """Set tool to be available only to a specific agent."""
        agent_name = agent.name if hasattr(agent, 'name') else str(agent)
        
        self.scope = ToolScope.LOCAL
        self.local_agent = agent_name
        self.shared_agents = []
        self.is_global = False
        
        logger.debug(f"Tool '{self.name}' set to local for agent '{agent_name}'")
        return self
    
    def set_shared(self, *agents: Union[str, "Agent"]) -> "Tool":
        """Set tool to be shared among specific agents."""
        agent_names = []
        for agent in agents:
            name = agent.name if hasattr(agent, 'name') else str(agent)
            agent_names.append(name)
        
        self.scope = ToolScope.SHARED
        self.local_agent = None
        self.shared_agents = agent_names
        self.is_global = False
        
        logger.debug(f"Tool '{self.name}' set to shared for agents: {agent_names}")
        return self
    
    def set_global(self) -> "Tool":
        """Set tool to be available to all agents."""
        self.scope = ToolScope.GLOBAL
        self.local_agent = None
        self.shared_agents = []
        self.is_global = True
        
        logger.debug(f"Tool '{self.name}' set to global")
        return self
    
    def can_be_used_by(self, agent: Union[str, "Agent"]) -> bool:
        """Check if an agent can use this tool."""
        agent_name = agent.name if hasattr(agent, 'name') else str(agent)
        
        if self.is_global:
            return True
        elif self.scope == ToolScope.LOCAL:
            return self.local_agent == agent_name
        elif self.scope == ToolScope.SHARED:
            return agent_name in self.shared_agents
        
        return False
    
    async def execute(
        self, 
        agent: Union[str, "Agent"],
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the tool with given arguments.
        
        Args:
            agent: Agent attempting to use the tool
            *args: Positional arguments for the tool function
            **kwargs: Keyword arguments for the tool function
            
        Returns:
            Dict with execution results
        """
        import time
        start_time = time.time()
        agent_name = agent.name if hasattr(agent, 'name') else str(agent)
        
        # Log tool execution start
        logger.log_tool_execution(
            tool_name=self.name,
            agent_name=agent_name,
            parameters={
                "args": args,
                "kwargs": kwargs,
                "scope": self.scope.value
            }
        )
        
        try:
            # Check permissions
            if not self.can_be_used_by(agent):
                error_msg = f"Agent '{agent_name}' does not have permission to use tool '{self.name}'"
                logger.log_system_event("tool_permission_denied", {
                    "tool": self.name,
                    "agent": agent_name,
                    "scope": self.scope.value,
                    "reason": "permission_denied"
                }, level="WARNING")
                raise PermissionError(error_msg)
            
            # Execute the function
            if self.func is None:
                error_msg = f"Tool '{self.name}' has no function defined"
                logger.log_system_event("tool_execution_error", {
                    "tool": self.name,
                    "agent": agent_name,
                    "error": "no_function_defined"
                }, level="ERROR")
                raise ValueError(error_msg)
            
            # Log pre-execution details
            logger.log_system_event("tool_pre_execution", {
                "tool": self.name,
                "agent": agent_name,
                "function_name": getattr(self.func, '__name__', 'unknown'),
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys())
            })
            
            # Handle async functions
            if hasattr(self.func, '__call__'):
                if hasattr(self.func, '__code__') and self.func.__code__.co_flags & 0x80:
                    # Async function
                    logger.log_system_event("tool_async_execution", {
                        "tool": self.name,
                        "agent": agent_name
                    })
                    result = await self.func(*args, **kwargs)
                else:
                    # Sync function
                    logger.log_system_event("tool_sync_execution", {
                        "tool": self.name,
                        "agent": agent_name
                    })
                    result = self.func(*args, **kwargs)
            else:
                error_msg = f"Tool '{self.name}' function is not callable"
                logger.log_system_event("tool_execution_error", {
                    "tool": self.name,
                    "agent": agent_name,
                    "error": "function_not_callable"
                }, level="ERROR")
                raise ValueError(error_msg)
            
            execution_time = time.time() - start_time
            
            # Update tracking
            self.usage_count += 1
            self.last_used_by = agent_name
            
            execution_record = {
                "agent": agent_name,
                "args": str(args)[:100],  # Truncate for logging
                "kwargs": str(kwargs)[:100],
                "result": str(result)[:100],
                "success": True,
                "timestamp": time.time(),
                "execution_time": execution_time
            }
            self.execution_history.append(execution_record)
            
            # Log successful execution
            logger.log_tool_execution(
                tool_name=self.name,
                agent_name=agent_name,
                parameters={
                    "args": args,
                    "kwargs": kwargs
                },
                result=result,
                execution_time=execution_time
            )
            
            logger.log_system_event("tool_execution_success", {
                "tool": self.name,
                "agent": agent_name,
                "execution_time": execution_time,
                "usage_count": self.usage_count,
                "result_type": type(result).__name__
            })
            
            return {
                "tool_name": self.name,
                "agent": agent_name,
                "result": result,
                "success": True,
                "metadata": {
                    "usage_count": self.usage_count,
                    "execution_time": execution_time,
                    "scope": self.scope.value
                }
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            error_record = {
                "agent": agent_name,
                "args": str(args)[:100],
                "kwargs": str(kwargs)[:100],
                "error": str(e),
                "success": False,
                "timestamp": time.time(),
                "execution_time": execution_time
            }
            self.execution_history.append(error_record)
            
            # Log error
            logger.log_tool_execution(
                tool_name=self.name,
                agent_name=agent_name,
                parameters={
                    "args": args,
                    "kwargs": kwargs
                },
                result=f"ERROR: {str(e)}",
                execution_time=execution_time
            )
            
            logger.log_system_event("tool_execution_error", {
                "tool": self.name,
                "agent": agent_name,
                "error": str(e),
                "error_type": type(e).__name__,
                "execution_time": execution_time
            }, level="ERROR")
            
            return {
                "tool_name": self.name,
                "agent": agent_name,
                "result": None,
                "error": str(e),
                "success": False,
                "metadata": {
                    "execution_time": execution_time,
                    "scope": self.scope.value
                }
            }
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's schema for LLM function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "scope": self.scope.value,
            "usage_count": self.usage_count
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "scope": self.scope.value,
            "local_agent": self.local_agent,
            "shared_agents": self.shared_agents,
            "is_global": self.is_global,
            "usage_count": self.usage_count,
            "last_used_by": self.last_used_by
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], func: Optional[Callable] = None) -> "Tool":
        """Create tool from dictionary representation."""
        tool = cls(
            name=data["name"],
            func=func,
            description=data.get("description", ""),
            parameters=data.get("parameters", {}),
            tool_id=data.get("id")
        )
        
        # Restore sharing configuration
        scope = data.get("scope", "local")
        if scope == "global":
            tool.set_global()
        elif scope == "shared":
            agents = data.get("shared_agents", [])
            if agents:
                tool.set_shared(*agents)
        elif scope == "local":
            local_agent = data.get("local_agent")
            if local_agent:
                tool.set_local(local_agent)
        
        # Restore tracking data
        tool.usage_count = data.get("usage_count", 0)
        tool.last_used_by = data.get("last_used_by")
        
        return tool
    
    @classmethod
    def from_config(cls, config: ToolConfig, func: Optional[Callable] = None) -> "Tool":
        """Create tool from configuration object."""
        tool = cls(
            name=config.name,
            func=func,
            description=config.description,
            parameters=config.parameters
        )
        
        # Apply scope configuration
        if config.scope == ToolScope.GLOBAL:
            tool.set_global()
        elif config.scope == ToolScope.SHARED and config.agents:
            tool.set_shared(*config.agents)
        elif config.scope == ToolScope.LOCAL and config.agents:
            tool.set_local(config.agents[0])
        
        return tool
    
    def __repr__(self) -> str:
        return f"Tool(name='{self.name}', scope='{self.scope.value}')"


# Built-in utility tools
def create_logger_tool() -> Tool:
    """Create a global logging tool."""
    def log_message(message: str, level: str = "info") -> str:
        logger_func = getattr(logger, level.lower(), logger.info)
        logger_func(f"AGENT LOG: {message}")
        return f"Logged: {message}"
    
    tool = Tool(
        name="Logger",
        func=log_message,
        description="Log messages for debugging and tracking",
        parameters={
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Message to log"},
                "level": {"type": "string", "enum": ["debug", "info", "warning", "error"], "default": "info"}
            },
            "required": ["message"]
        }
    )
    tool.set_global()
    return tool


def create_memory_tool() -> Tool:
    """Create a global memory/storage tool."""
    memory_store = {}
    
    def store_memory(key: str, value: str) -> str:
        memory_store[key] = value
        return f"Stored '{key}': {value}"
    
    def retrieve_memory(key: str) -> str:
        return memory_store.get(key, f"No memory found for key '{key}'")
    
    def list_memories() -> str:
        if not memory_store:
            return "No memories stored"
        return "Stored memories: " + ", ".join(memory_store.keys())
    
    # Create multiple tools for memory operations
    store_tool = Tool(
        name="StoreMemory",
        func=store_memory,
        description="Store information in memory",
        parameters={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Key to store under"},
                "value": {"type": "string", "description": "Value to store"}
            },
            "required": ["key", "value"]
        }
    )
    store_tool.set_global()
    
    return store_tool
