"""
Core agent implementation with LLM provider abstraction.
"""

import uuid
import time
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
import json
from datetime import datetime

if TYPE_CHECKING:
    from .tool import Tool
    from .tool_executor import ToolExecutor

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

from ..llm.providers import LLMProvider, get_llm_provider
from ..utils.logger import get_logger
from .tool_parser import ToolCallParser

logger = get_logger(__name__)


class AgentConfig(BaseModel):
    """Configuration for an agent."""
    name: str
    description: str = ""
    system_prompt: str = ""
    llm_provider: str = "openai"
    llm_model: str = "gpt-3.5-turbo"
    llm_config: Dict[str, Any] = Field(default_factory=dict)
    max_iterations: int = 10
    memory_enabled: bool = True
    tools: List[str] = Field(default_factory=list)


class Agent:
    """
    A multi-agent system agent with pluggable LLM backend support.
    
    Each agent can be configured with different LLM providers and has
    access to a hierarchical tool system (local, shared, global).
    """
    
    def __init__(
        self,
        name: str,
        description: str = "",
        system_prompt: str = "",
        llm_provider: str = "openai",
        llm_model: str = "gpt-3.5-turbo",
        llm_config: Optional[Dict[str, Any]] = None,
        max_iterations: int = 10,
        memory_enabled: bool = True,
        agent_id: Optional[str] = None,
    ):
        """
        Initialize an agent.
        
        Args:
            name: Unique name for the agent
            description: Description of the agent's purpose
            system_prompt: System prompt to guide the agent's behavior
            llm_provider: LLM provider (openai, anthropic, aws, azure, etc.)
            llm_model: Specific model to use
            llm_config: Additional LLM configuration parameters
            max_iterations: Maximum iterations for complex tasks
            memory_enabled: Whether to maintain conversation memory
            agent_id: Optional custom agent ID
        """
        if not name or not name.strip():
            raise ValueError("Agent name cannot be empty")
            
        self.id = agent_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.llm_provider_name = llm_provider
        self.llm_model = llm_model
        self.llm_config = llm_config or {}
        self.max_iterations = max_iterations
        self.memory_enabled = memory_enabled
        
        # Tool access tracking
        self.local_tools: List[str] = []
        self.shared_tools: List[str] = []
        self.global_tools: List[str] = []
        
        # Runtime state
        self.memory: List[Dict[str, Any]] = []
        self.execution_context: Dict[str, Any] = {}
        self._llm_provider: Optional[LLMProvider] = None
        
        logger.info(f"Created agent '{name}' with {llm_provider}/{llm_model}")
    
    @property
    def llm_provider(self) -> LLMProvider:
        """Get the LLM provider instance."""
        if self._llm_provider is None:
            self._llm_provider = get_llm_provider(
                provider=self.llm_provider_name,
                model=self.llm_model,
                **self.llm_config
            )
        return self._llm_provider
    
    def add_to_memory(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
        """Add a message to the agent's memory."""
        if not self.memory_enabled:
            return
            
        self.memory.append({
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def clear_memory(self) -> None:
        """Clear the agent's memory."""
        self.memory.clear()
        logger.debug(f"Cleared memory for agent '{self.name}'")
    
    def get_available_tools(self, tool_registry: Dict[str, Any]) -> List[str]:
        """Get all tools available to this agent."""
        available = []
        
        # Add local tools
        available.extend(self.local_tools)
        
        # Add shared tools where this agent has access
        for tool_name in self.shared_tools:
            if tool_name in tool_registry:
                tool = tool_registry[tool_name]
                if hasattr(tool, 'shared_agents') and self.name in tool.shared_agents:
                    available.append(tool_name)
        
        # Add global tools
        available.extend(self.global_tools)
        
        return list(set(available))  # Remove duplicates
    
    """
    Fixed Agent execution method that handles tool calls
    """

    async def execute(
        self, 
        input_text: str, 
        context: Optional[Dict[str, Any]] = None,
        tool_executor: Optional["ToolExecutor"] = None,
        available_tools: Optional[List[str]] = None,
        tool_registry: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a task with standardized tool support."""
        start_time = time.time()
        
        # Log the agent action start
        logger.log_agent_action(
            agent_name=self.name,
            action="execute",
            input_data=input_text,
            context=context
        )
        
        try:
            # Add input to memory
            self.add_to_memory("user", input_text)
            
            # Prepare context
            execution_context = context or {}
            
            # Handle tool access - support both new tool_executor and legacy available_tools
            if tool_executor:
                tools_schema = tool_executor.get_tools_schema_for_agent(self.name)
                if tools_schema:
                    execution_context["tools"] = tools_schema
                    # Set tool choice based on provider
                    if self.llm_provider_name == "anthropic":
                        execution_context["tool_choice"] = {"type": "auto"}
                    else:
                        execution_context["tool_choice"] = "auto"
                    logger.debug(f"Agent {self.name}: Providing {len(tools_schema)} tools to LLM")
            elif available_tools and tool_registry:
                # Legacy support: create tool schemas from available_tools and tool_registry
                tools_schemas = []
                for tool_name in available_tools:
                    if tool_name in tool_registry:
                        tool = tool_registry[tool_name]
                        if tool.can_be_used_by(self):
                            schema = tool.get_schema()
                            tools_schemas.append(schema)
                
                if tools_schemas:
                    execution_context["tools"] = tools_schemas
                    if self.llm_provider_name == "anthropic":
                        execution_context["tool_choice"] = {"type": "auto"}
                    else:
                        execution_context["tool_choice"] = "auto"
                    logger.debug(f"Agent {self.name}: Providing {len(tools_schemas)} legacy tools to LLM")
            
            # Prepare messages for LLM
            messages = []
            
            # Add system prompt
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})
            
            # Add conversation history
            for msg in self.memory[-10:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
            
            # Add tool parser
            parser = ToolCallParser()
            
            # Start tool calling loop
            max_iterations = self.max_iterations
            iteration = 0
            final_response = ""
            
            while iteration < max_iterations:
                iteration += 1
                logger.debug(f"Agent {self.name}: Tool calling iteration {iteration}")
                
                # Execute with LLM provider
                response = await self.llm_provider.execute(
                    messages=messages,
                    context=execution_context
                )
                
                # First check if LLM has native tool calling
                tool_calls = []
                if hasattr(self.llm_provider, 'extract_tool_calls'):
                    tool_calls = self.llm_provider.extract_tool_calls(response)
                
                # If no native tool calls, parse from response content
                if not tool_calls and response.content:
                    tool_calls = parser.extract_tool_calls(response.content)
                    logger.debug(f"Parsed {len(tool_calls)} tool calls from response content")
            
                if not tool_calls:
                    # No tool calls, we're done
                    final_response = response.content
                    break
                
                # Execute tool calls using standardized executor or legacy tools
                if tool_executor:
                    logger.debug(f"Agent {self.name}: Executing {len(tool_calls)} tool calls")
                    
                    # Execute all tool calls
                    tool_responses = await tool_executor.execute_tool_calls(tool_calls, self.name)
                    
                    # Add assistant message with tool calls to conversation
                    messages.append({
                        "role": "assistant",
                        "content": response.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.name,
                                    "arguments": json.dumps(tc.arguments)
                                }
                            } for tc in tool_calls
                        ]
                    })
                    
                    # Add tool responses to conversation
                    if hasattr(self.llm_provider, 'create_tool_response_for_llm'):
                        tool_messages = self.llm_provider.create_tool_response_for_llm(tool_responses)
                        if isinstance(tool_messages, list):
                            messages.extend(tool_messages)
                        else:
                            messages.append(tool_messages)
                    
                elif tool_registry and available_tools:
                    # Legacy tool execution support
                    logger.debug(f"Agent {self.name}: Executing {len(tool_calls)} tool calls (legacy mode)")
                    
                    # Execute tool calls using legacy tools
                    tool_results = []
                    for tool_call in tool_calls:
                        if tool_call.name in tool_registry and tool_call.name in available_tools:
                            tool = tool_registry[tool_call.name]
                            try:
                                if tool.can_be_used_by(self):
                                    result = await tool.execute(self, **tool_call.arguments)
                                    tool_results.append({
                                        "tool_call_id": tool_call.id,
                                        "output": str(result.get('output', result))
                                    })
                                else:
                                    tool_results.append({
                                        "tool_call_id": tool_call.id, 
                                        "output": f"Permission denied for tool {tool_call.name}"
                                    })
                            except Exception as e:
                                tool_results.append({
                                    "tool_call_id": tool_call.id,
                                    "output": f"Tool execution error: {str(e)}"
                                })
                    
                    # Add assistant message with tool calls to conversation
                    messages.append({
                        "role": "assistant", 
                        "content": response.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function", 
                                "function": {
                                    "name": tc.name,
                                    "arguments": json.dumps(tc.arguments)
                                }
                            } for tc in tool_calls
                        ]
                    })
                    
                    # Add tool results to conversation  
                    for result in tool_results:
                        # Check if provider is Anthropic and format accordingly
                        if self.llm_provider_name == "anthropic":
                            messages.append({
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": result["tool_call_id"],
                                        "content": json.dumps(result["output"])
                                    }
                                ]
                            })
                        else:
                            messages.append({
                                "role": "tool",
                                "tool_call_id": result["tool_call_id"],
                                "content": json.dumps(result["output"])
                            })
                
                else:
                    # No tool execution available
                    logger.warning(f"Agent {self.name}: Tool calls requested but no tool executor or registry available")
                    final_response = response.content
                    break
            
            # If we ran out of iterations, use the last response
            if iteration >= max_iterations and not final_response:
                final_response = "Maximum tool calling iterations reached."
                logger.warning(f"Agent {self.name}: Reached maximum tool calling iterations")
            
            # Add final response to memory
            self.add_to_memory("assistant", final_response)
            
            execution_time = time.time() - start_time
            
            # Create result
            result = {
                "agent_id": self.id,
                "agent_name": self.name,
                "input": input_text,
                "output": final_response,
                "tool_calls_made": iteration - 1,
                "execution_time": execution_time,
                "success": True
            }
            
            logger.log_agent_action(
                agent_name=self.name,
                action="execute_complete",
                input_data=input_text,
                output_data=final_response,
                context={
                    "execution_time": execution_time,
                    "tool_iterations": iteration - 1
                }
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.log_agent_action(
                agent_name=self.name,
                action="execute_error",
                input_data=input_text,
                context={
                    "error": str(e),
                    "execution_time": execution_time
                }
            )
            
            return {
                "agent_id": self.id,
                "agent_name": self.name,
                "input": input_text,
                "output": "",
                "error": str(e),
                "execution_time": execution_time,
                "success": False
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "llm_provider": self.llm_provider_name,
            "llm_model": self.llm_model,
            "llm_config": self.llm_config,
            "max_iterations": self.max_iterations,
            "memory_enabled": self.memory_enabled,
            "local_tools": self.local_tools,
            "shared_tools": self.shared_tools,
            "global_tools": self.global_tools
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Agent":
        """Create agent from dictionary representation."""
        agent = cls(
            name=data["name"],
            description=data.get("description", ""),
            system_prompt=data.get("system_prompt", ""),
            llm_provider=data.get("llm_provider", "openai"),
            llm_model=data.get("llm_model", "gpt-3.5-turbo"),
            llm_config=data.get("llm_config", {}),
            max_iterations=data.get("max_iterations", 10),
            memory_enabled=data.get("memory_enabled", True),
            agent_id=data.get("id")
        )
        
        # Restore tool assignments
        agent.local_tools = data.get("local_tools", [])
        agent.shared_tools = data.get("shared_tools", [])
        agent.global_tools = data.get("global_tools", [])
        
        return agent
    
    @classmethod
    def from_config(cls, config: AgentConfig) -> "Agent":
        """Create agent from configuration object."""
        return cls.from_dict(config.model_dump())
    
    def __repr__(self) -> str:
        return f"Agent(name='{self.name}', llm='{self.llm_provider_name}/{self.llm_model}')"
