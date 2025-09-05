"""
Core agent implementation with LangGraph subgraph architecture.
"""

import uuid
import time
from typing import Any, Dict, List, Optional, Union, TypedDict, Annotated
import json
import operator
from datetime import datetime

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent, ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool

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
            return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def Field(**kwargs):
        return kwargs.get("default", None)


from ..llm.providers import LLMProvider, get_llm_provider
from ..utils.logger import get_logger

logger = get_logger(__name__)


# State Schemas
class AgentSubgraphState(TypedDict):
    """State for individual agent subgraph execution."""

    messages: Annotated[List[BaseMessage], operator.add]
    agent_name: str
    parent_graph_id: str
    execution_context: Dict[str, Any]
    tool_outputs: List[Dict[str, Any]]


# Placeholder for core state - will be implemented in state management layer
class AgentState(TypedDict):
    """Main state schema for multi-agent system."""

    messages: Annotated[List[BaseMessage], operator.add]
    agent_outputs: Dict[str, Any]
    subgraph_states: Dict[str, AgentSubgraphState]
    parent_graph_id: str
    current_agent: str
    execution_metadata: Dict[str, Any]


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
    LangGraph-native agent implementation that works as a subgraph node.

    Each agent is compiled as a complete subgraph with internal ReAct architecture,
    maintaining its own state within the parent graph execution.
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
        tools: Optional[List[Any]] = None,
    ):
        """
        Initialize an agent as a LangGraph subgraph.

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
            tools: List of tools available to this agent
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
        self.tools = tools or []

        # LangGraph components
        self._compiled_subgraph: Optional[StateGraph] = None
        self._llm_provider: Optional[LLMProvider] = None

        logger.info(f"Created agent '{name}' with {llm_provider}/{llm_model}")

    @property
    def llm_provider(self) -> LLMProvider:
        """Get the LLM provider instance."""
        if self._llm_provider is None:
            self._llm_provider = get_llm_provider(
                provider=self.llm_provider_name, model=self.llm_model, **self.llm_config
            )
        return self._llm_provider

    def _create_agent_subgraph(self) -> StateGraph:
        """
        Create and compile the agent's internal subgraph using LangGraph's create_react_agent.

        Returns:
            Compiled StateGraph representing this agent's execution logic
        """
        logger.debug(f"Compiling subgraph for agent '{self.name}'")

        # Get LLM provider for this agent
        llm = self.llm_provider

        # Convert tools to LangChain format if needed
        # Placeholder - actual tool conversion will depend on tool registry implementation
        langchain_tools = self._convert_tools_to_langchain()

        # Create ReAct agent using LangGraph
        agent_runnable = create_react_agent(llm, langchain_tools)

        # Build the subgraph
        subgraph_builder = StateGraph(AgentSubgraphState)
        subgraph_builder.add_node("agent", agent_runnable)

        # Add tools node if tools are available
        if langchain_tools:
            subgraph_builder.add_node("tools", ToolNode(langchain_tools))
            subgraph_builder.add_conditional_edges(
                "agent",
                lambda state: "tools" if state["messages"][-1].tool_calls else END,
            )
            subgraph_builder.add_edge("tools", "agent")

        subgraph_builder.set_entry_point("agent")

        return subgraph_builder.compile()

    def _convert_tools_to_langchain(self) -> List[Any]:
        """
        Convert internal tools to LangChain tool format.
        Placeholder implementation - actual conversion depends on tool registry.
        """
        # Placeholder: Convert self.tools to LangChain tools
        # This will be implemented when tool registry is available
        langchain_tools = []

        # Example placeholder tool
        @tool
        def placeholder_tool(query: str) -> str:
            """Placeholder tool for agent execution."""
            return f"Placeholder response for: {query}"

        if self.tools:
            langchain_tools.append(placeholder_tool)

        return langchain_tools

    def get_compiled_subgraph(self) -> StateGraph:
        """
        Get or create the compiled subgraph for this agent.

        Returns:
            Compiled StateGraph ready for execution
        """
        if self._compiled_subgraph is None:
            self._compiled_subgraph = self._create_agent_subgraph()
        return self._compiled_subgraph

    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute agent as a LangGraph node.

        This method makes the Agent compatible with StateGraph execution.
        It reads from state, executes the agent subgraph, and returns state updates.

        Args:
            state: Current AgentState from parent graph

        Returns:
            Dictionary of state updates for the parent graph
        """
        start_time = time.time()

        logger.log_agent_action(
            agent_name=self.name,
            action="subgraph_execute",
            input_data=state.get("messages", []),
            context={"parent_graph_id": state.get("parent_graph_id")},
        )

        try:
            # Extract input from parent state
            parent_messages = state.get("messages", [])
            parent_graph_id = state.get("parent_graph_id", "")

            # Prepare subgraph input state
            subgraph_input = {
                "messages": parent_messages,
                "agent_name": self.name,
                "parent_graph_id": parent_graph_id,
                "execution_context": state.get("execution_metadata", {}),
                "tool_outputs": [],
            }

            # Get compiled subgraph
            subgraph = self.get_compiled_subgraph()

            # Execute subgraph with streaming support
            final_subgraph_state = None
            for chunk in subgraph.stream(
                subgraph_input, config={"recursion_limit": self.max_iterations}
            ):
                final_subgraph_state = chunk
                # Here we could emit partial updates if needed

            if not final_subgraph_state:
                raise RuntimeError(f"Agent {self.name} subgraph execution failed")

            # Extract results from final subgraph state
            last_node_key = list(final_subgraph_state.keys())[0]
            final_messages = final_subgraph_state[last_node_key]["messages"]
            final_answer = final_messages[-1].content if final_messages else ""

            # Update parent state
            updated_subgraph_states = state.get("subgraph_states", {}).copy()
            updated_subgraph_states[self.name] = final_subgraph_state[last_node_key]

            updated_agent_outputs = state.get("agent_outputs", {}).copy()
            updated_agent_outputs[self.name] = {
                "output": final_answer,
                "execution_time": time.time() - start_time,
                "messages": final_messages,
                "success": True,
            }

            execution_time = time.time() - start_time

            logger.log_agent_action(
                agent_name=self.name,
                action="subgraph_complete",
                output_data=final_answer,
                context={
                    "execution_time": execution_time,
                    "parent_graph_id": parent_graph_id,
                },
            )

            # Return state updates for parent graph
            return {
                "subgraph_states": updated_subgraph_states,
                "agent_outputs": updated_agent_outputs,
                "current_agent": self.name,
                "messages": final_messages,  # This will be added to existing messages due to Annotated[List, operator.add]
            }

        except Exception as e:
            execution_time = time.time() - start_time

            logger.log_agent_action(
                agent_name=self.name,
                action="subgraph_error",
                context={"error": str(e), "execution_time": execution_time},
            )

            # Return error state update
            updated_agent_outputs = state.get("agent_outputs", {}).copy()
            updated_agent_outputs[self.name] = {
                "output": "",
                "error": str(e),
                "execution_time": execution_time,
                "success": False,
            }

            return {
                "agent_outputs": updated_agent_outputs,
                "current_agent": self.name,
            }

    # Backward compatibility method
    async def execute(
        self, input_text: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Backward compatibility method for legacy execute() calls.

        This method wraps the new __call__ interface to maintain compatibility
        with existing code that uses agent.execute().
        """
        logger.warning(
            f"Using deprecated execute() method for agent {self.name}. Use agent(state) instead."
        )

        # Convert legacy parameters to AgentState format
        legacy_state = {
            "messages": [HumanMessage(content=input_text)],
            "agent_outputs": {},
            "subgraph_states": {},
            "parent_graph_id": str(uuid.uuid4()),
            "current_agent": self.name,
            "execution_metadata": context or {},
        }

        # Execute using new __call__ method
        result_state = self.__call__(legacy_state)

        # Convert back to legacy format
        agent_output = result_state.get("agent_outputs", {}).get(self.name, {})

        return {
            "agent_id": self.id,
            "agent_name": self.name,
            "input": input_text,
            "output": agent_output.get("output", ""),
            "execution_time": agent_output.get("execution_time", 0),
            "success": agent_output.get("success", False),
            "error": agent_output.get("error"),
        }

    def create_subgraph_node_runner(self):
        """
        Factory method to create a function that acts as a node in parent graphs.

        This follows the pattern from the working example you provided.

        Returns:
            Function that can be used as a node in a parent StateGraph
        """

        def run_agent_subgraph(parent_state: AgentState) -> Dict[str, Any]:
            """Node runner function for parent graph execution."""
            return self.__call__(parent_state)

        return run_agent_subgraph

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
            "tools": [str(tool) for tool in self.tools],  # Serialize tools
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
            agent_id=data.get("id"),
            tools=data.get("tools", []),  # Tools will need proper deserialization
        )

        return agent

    @classmethod
    def from_config(cls, config: AgentConfig) -> "Agent":
        """Create agent from configuration object."""
        return cls.from_dict(config.model_dump())

    def __repr__(self) -> str:
        return f"Agent(name='{self.name}', llm='{self.llm_provider_name}/{self.llm_model}', subgraph=True)"
