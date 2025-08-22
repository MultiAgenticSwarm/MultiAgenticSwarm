"""
Core agent implementation with LLM provider abstraction and LangGraph node support.
"""

import uuid
import time
import asyncio
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING, TypedDict, Annotated
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

# LangGraph imports for node functionality
try:
    from langgraph.prebuilt import create_react_agent
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
    from langchain_core.tools import BaseTool
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    # Fallback types
    BaseMessage = Any
    HumanMessage = Any
    AIMessage = Any
    BaseTool = Any
    def create_react_agent(*args, **kwargs):
        raise ImportError("LangGraph is required for node functionality")

from ..llm.providers import LLMProvider, get_llm_provider
from ..utils.logger import get_logger
from .tool_parser import ToolCallParser


# Minimal AgentState interface - compatible with future full schema from Dev 1
class AgentState(TypedDict, total=False):
    """
    Minimal state schema for LangGraph node compatibility.
    This will be replaced by the full schema when Dev 1 completes Ticket #1.
    """
    # Core message flow
    messages: List[Any]  # Will be List[BaseMessage] when LangGraph is fully integrated

    # Agent execution results
    agent_outputs: Dict[str, Any]

    # Tool permissions and results
    tool_permissions: Dict[str, List[str]]
    tool_results: Dict[str, Any]

    # Execution context
    current_agent: Optional[str]
    execution_context: Dict[str, Any]

    # Error handling
    errors: List[str]

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

    # =====================================================================
    # LangGraph Node Functionality (Ticket #6 Implementation)
    # =====================================================================

    def __call__(self, state: AgentState) -> AgentState:
        """
        Make Agent callable as a LangGraph node.

        This is the main entry point when the agent is used as a node in a StateGraph.
        Reads from state["messages"] and updates state["agent_outputs"].

        Args:
            state: The current AgentState containing messages and context

        Returns:
            Updated AgentState with agent's response and outputs
        """
        if not LANGGRAPH_AVAILABLE:
            logger.warning(f"Agent {self.name}: LangGraph not available, falling back to legacy mode")
            return self._fallback_node_execution(state)

        try:
            # Extract input from state
            messages = state.get("messages", [])
            execution_context = state.get("execution_context", {})

            # Set current agent in state
            state["current_agent"] = self.name

            # Initialize agent outputs if not present
            if "agent_outputs" not in state:
                state["agent_outputs"] = {}

            # Get the latest human message as input
            input_text = ""
            if messages:
                # Find the last human message
                for msg in reversed(messages):
                    if isinstance(msg, dict) and msg.get("role") == "user":
                        input_text = msg.get("content", "")
                        break
                    elif hasattr(msg, 'content'):
                        input_text = str(msg.content)
                        break

            if not input_text:
                input_text = "Continue the conversation"

            logger.info(f"Agent {self.name}: Processing as LangGraph node with input: {input_text[:100]}...")

            # Use create_react_agent if tools are available and LangGraph is ready
            tools = self._get_langchain_tools(state)

            if tools and self._can_use_react_agent():
                result = self._execute_with_react_agent(state, tools)
            else:
                # Direct LLM execution without legacy dependencies
                result = self._execute_direct_llm(state, input_text, execution_context)

            # Update state with results
            state["agent_outputs"][self.name] = {
                "output": result.get("output", ""),
                "execution_time": result.get("execution_time", 0.0),
                "tool_calls_made": result.get("tool_calls_made", 0),
                "success": result.get("success", True),
                "timestamp": datetime.now().isoformat()
            }

            # Add agent response to messages
            if result.get("output"):
                # Convert to proper message format
                if LANGGRAPH_AVAILABLE and hasattr(AIMessage, '__call__'):
                    try:
                        ai_message = AIMessage(content=result["output"])
                        if "messages" not in state:
                            state["messages"] = []
                        state["messages"].append(ai_message)
                    except Exception as e:
                        logger.warning(f"Could not create AIMessage: {e}, using dict format")
                        state["messages"].append({
                            "role": "assistant",
                            "content": result["output"],
                            "agent": self.name
                        })
                else:
                    # Fallback to dict format
                    if "messages" not in state:
                        state["messages"] = []
                    state["messages"].append({
                        "role": "assistant",
                        "content": result["output"],
                        "agent": self.name
                    })

            # Handle any errors
            if not result.get("success", True):
                if "errors" not in state:
                    state["errors"] = []
                state["errors"].append(f"Agent {self.name}: {result.get('error', 'Unknown error')}")

            logger.info(f"Agent {self.name}: Completed node execution successfully")
            return state

        except Exception as e:
            logger.error(f"Agent {self.name}: Error in node execution: {e}")

            # Ensure state is properly updated even on error
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Agent {self.name}: {str(e)}")

            if "agent_outputs" not in state:
                state["agent_outputs"] = {}
            state["agent_outputs"][self.name] = {
                "output": "",
                "error": str(e),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }

            return state

    def _can_use_react_agent(self) -> bool:
        """Check if we can use LangGraph's create_react_agent."""
        if not LANGGRAPH_AVAILABLE:
            return False
        try:
            return hasattr(self.llm_provider, 'get_langchain_llm')
        except Exception:
            # If LLM provider initialization fails, we can't use react agent
            return False

    def _get_langchain_tools(self, state: AgentState) -> List[Any]:
        """
        Get tools in LangChain format for use with create_react_agent.
        This is a placeholder until Dev 3 completes tool conversion (Ticket #9).
        """
        # TODO: This will be properly implemented when Ticket #9 (Tool System conversion) is done
        # For now, return empty list to avoid blocking development
        return []

    def _execute_with_react_agent(self, state: AgentState, tools: List[Any]) -> Dict[str, Any]:
        """
        Execute using LangGraph's create_react_agent.
        This will be the primary execution method once tools are converted.
        """
        try:
            # Get LangChain-compatible LLM
            llm = self.llm_provider.get_langchain_llm()

            # Create react agent
            agent_executor = create_react_agent(llm, tools)

            # Prepare input
            messages = state.get("messages", [])

            # Execute
            start_time = time.time()
            response = agent_executor.invoke({"messages": messages})
            execution_time = time.time() - start_time

            return {
                "output": response.get("output", ""),
                "execution_time": execution_time,
                "tool_calls_made": 0,  # TODO: Extract from response
                "success": True
            }

        except Exception as e:
            logger.error(f"Agent {self.name}: React agent execution failed: {e}")
            return {
                "output": "",
                "error": str(e),
                "execution_time": 0.0,
                "success": False
            }

    def _execute_direct_llm(
        self,
        state: AgentState,
        input_text: str,
        execution_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute using direct LLM call without legacy dependencies.
        This is a simplified execution for LangGraph node usage.
        """
        start_time = time.time()

        try:
            # Prepare messages for LLM
            messages = []

            # Add system prompt
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})

            # Add conversation history from state
            state_messages = state.get("messages", [])
            for msg in state_messages[-5:]:  # Last 5 messages for context
                if isinstance(msg, dict):
                    messages.append(msg)
                else:
                    # Handle LangChain message objects
                    if hasattr(msg, 'content'):
                        role = "user" if hasattr(msg, '__class__') and "Human" in msg.__class__.__name__ else "assistant"
                        messages.append({"role": role, "content": str(msg.content)})

            # Add current input if not already in messages
            if not messages or messages[-1].get("content") != input_text:
                messages.append({"role": "user", "content": input_text})

            # Execute LLM call
            try:
                response = asyncio.run(self.llm_provider.execute(
                    messages=messages,
                    context=execution_context
                ))

                output = response.content if hasattr(response, 'content') else str(response)
                success = True
                error = None

            except Exception as llm_error:
                logger.warning(f"Agent {self.name}: LLM execution failed: {llm_error}")
                output = f"LLM execution failed: {str(llm_error)}"
                success = False
                error = str(llm_error)

            execution_time = time.time() - start_time

            result = {
                "output": output,
                "execution_time": execution_time,
                "tool_calls_made": 0,
                "success": success
            }

            if error:
                result["error"] = error

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Agent {self.name}: Direct LLM execution failed: {e}")
            return {
                "output": f"Agent execution failed: {str(e)}",
                "error": str(e),
                "execution_time": execution_time,
                "tool_calls_made": 0,
                "success": False
            }

    def _fallback_node_execution(self, state: AgentState) -> AgentState:
        """
        Fallback execution when LangGraph is not available.
        Ensures the agent can still work as a node.
        """
        logger.warning(f"Agent {self.name}: Using fallback node execution")

        try:
            # Extract input
            messages = state.get("messages", [])
            input_text = "Continue the conversation"

            if messages:
                last_msg = messages[-1]
                if isinstance(last_msg, dict):
                    input_text = last_msg.get("content", input_text)
                else:
                    input_text = str(last_msg)

            # Execute with direct LLM call
            result = self._execute_direct_llm(
                state, input_text, state.get("execution_context", {})
            )

            # Update state
            if "agent_outputs" not in state:
                state["agent_outputs"] = {}

            state["agent_outputs"][self.name] = result

            # Add to messages
            if result.get("output"):
                if "messages" not in state:
                    state["messages"] = []
                state["messages"].append({
                    "role": "assistant",
                    "content": result["output"],
                    "agent": self.name
                })

            return state

        except Exception as e:
            logger.error(f"Agent {self.name}: Fallback execution failed: {e}")
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Agent {self.name}: {str(e)}")
            return state

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

    def get_node_info(self) -> Dict[str, Any]:
        """
        Get information about this agent as a graph node.

        Useful for graph compilation and visualization.
        """
        try:
            return {
                "name": self.name,
                "id": self.id,
                "type": "agent_node",
                "description": self.description,
                "llm_provider": self.llm_provider_name,
                "llm_model": self.llm_model,
                "supports_tools": len(self.local_tools + self.shared_tools + self.global_tools) > 0,
                "supports_react_agent": self._can_use_react_agent(),
                "node_compatible": True
            }
        except Exception as e:
            logger.error(f"Agent {self.name}: Error getting node info: {e}")
            return {
                "name": self.name,
                "id": self.id,
                "type": "agent_node",
                "error": str(e),
                "node_compatible": True
            }

    def __repr__(self) -> str:
        return f"Agent(name='{self.name}', llm='{self.llm_provider_name}/{self.llm_model}', node_compatible=True)"
