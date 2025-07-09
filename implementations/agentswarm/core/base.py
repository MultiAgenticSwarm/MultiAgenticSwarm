"""
Base classes for all AgentSwarm implementations.
Uses MultiAgenticSwarm as the foundational SDK.
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

# Import MultiAgenticSwarm as the core SDK
try:
    import multiagenticswarm as mas

    MAS_AVAILABLE = True
except ImportError:
    MAS_AVAILABLE = False
    mas = None

from .types import (
    AgentRole,
    CollaborationPattern,
    ExecutionResult,
    TaskContext,
    WorkflowPattern,
)


class BaseAgent(mas.Agent if MAS_AVAILABLE else ABC):
    """
    Base class for all specialized agents.
    Inherits directly from MultiAgenticSwarm Agent for full SDK integration.

    All domain-specific agents inherit from this class and implement
    the abstract methods to provide specialized functionality.
    """

    def __init__(
        self,
        name: str,
        role: Union[AgentRole, str],
        system: Optional[Any] = None,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4",
        temperature: float = 0.7,
        **kwargs,
    ):
        if not MAS_AVAILABLE:
            raise ImportError("MultiAgenticSwarm is required but not available")

        self.role = role if isinstance(role, AgentRole) else AgentRole(role)
        self.mas_system = system or mas.System()

        # Use direct import for logger
        from multiagenticswarm.utils.logger import get_logger

        self.logger = get_logger(f"agentswarm.{name}")

        # Build specialized system prompt
        system_prompt = self._build_instructions()

        # Initialize MAS Agent with proper configuration
        super().__init__(
            name=name,
            description=f"A {self.role.value} agent",
            system_prompt=system_prompt,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_config={"temperature": temperature, **kwargs},
        )

        # Register tools with MAS system
        self._register_tools_with_mas()

        # Register with MAS system
        self.mas_system.register_agent(self)

        # Initialize agent-specific state
        self.context = TaskContext(project_path=".")
        self.execution_history = []

    def _build_instructions(self) -> str:
        """Build instructions combining base role and specialization"""
        base_instructions = f"""You are a {self.role.value} agent in a multi-agent system.

Your core responsibilities:
- Follow software engineering best practices
- Communicate clearly with other agents
- Provide detailed explanations for your decisions
- Handle errors gracefully and report issues
- Maintain consistency across the project

"""

        specialized = self._get_specialized_instructions()
        tools_info = self._get_tools_information()

        return base_instructions + specialized + tools_info

    @abstractmethod
    def _get_specialized_instructions(self) -> str:
        """Get domain-specific instructions for the agent"""
        pass

    @abstractmethod
    def _get_tools(self) -> List[Any]:
        """Get tools this agent needs from MAS"""
        pass

    def get_available_tools(self, system_tools):
        """Get available tools for this agent from system tools"""
        return [
            tool
            for tool in system_tools.values()
            if hasattr(tool, "is_available_to") and tool.is_available_to(self.name)
        ]

    def _get_tools_information(self) -> str:
        """Get information about available tools"""
        tools = self._get_tools()
        if not tools:
            return "\nNo specialized tools available."

        tools_info = "\n\nAvailable tools:\n"
        for tool in tools:
            if isinstance(tool, dict):
                # Handle dictionary format
                name = tool.get("name", "Unknown")
                description = tool.get("description", "No description")
                tools_info += f"- {name}: {description}\n"
            else:
                # Handle object format
                tools_info += f"- {tool.name}: {tool.description}\n"

        return tools_info

    def _register_tools_with_mas(self) -> None:
        """Register tools with MAS system using proper tool sharing"""
        tools = self._get_tools()
        for tool_def in tools:
            if isinstance(tool_def, dict):
                # Create MAS FunctionTool from dictionary definition
                try:
                    from multiagenticswarm.core.base_tool import FunctionTool

                    mas_tool = FunctionTool(
                        func=tool_def.get("func"),
                        name=tool_def.get("name"),
                        description=tool_def.get("description", ""),
                        parameters=tool_def.get("parameters", {}),
                    )

                    # Set tool sharing level
                    scope = tool_def.get("scope", "local")
                    if scope == "local":
                        mas_tool.set_local(self)
                    elif scope == "shared":
                        # For shared tools, we need to specify which agents can use them
                        # This will be handled by the swarm orchestrator
                        pass
                    elif scope == "global":
                        mas_tool.set_global()

                    # Register with MAS system
                    self.mas_system.register_tool(mas_tool)

                except Exception as e:
                    self.logger.warning(
                        f"Failed to register tool {tool_def.get('name', 'unknown')}: {e}"
                    )
            else:
                # Handle object format - assume it's already a proper MAS tool
                if hasattr(tool_def, "set_local"):
                    tool_def.set_local(self)
                self.mas_system.register_tool(tool_def)

    async def execute(
        self,
        task_or_input: Union[str, Dict[str, Any]] = None,
        context: Optional[Union[TaskContext, Dict[str, Any]]] = None,
        tool_executor: Optional[Any] = None,
        available_tools: Optional[List[str]] = None,
        tool_registry: Optional[Dict[str, Any]] = None,
        # Support MAS system parameters
        input_text: Optional[str] = None,
        **kwargs,
    ) -> Union[ExecutionResult, Dict[str, Any]]:
        """Execute task using MAS infrastructure with flexible signature"""

        # Handle MAS system calls that use input_text parameter
        if input_text is not None:
            # This is a MAS system call - delegate to the parent class
            return await super().execute(
                input_text=input_text,
                context=context
                if isinstance(context, dict)
                else (context.__dict__ if context else None),
                tool_executor=tool_executor,
                available_tools=available_tools,
                tool_registry=tool_registry,
                **kwargs,
            )

        # Handle AgentSwarm-style calls
        if task_or_input is None:
            raise ValueError("Either task_or_input or input_text must be provided")

        # This is an AgentSwarm call - handle as before
        if isinstance(context, dict):
            context = TaskContext(**context)

        if context:
            self.context = context

        # Convert task to proper format
        if isinstance(task_or_input, str):
            task_input = task_or_input
        else:
            task_input = task_or_input.get("description", str(task_or_input))

        start_time = time.time()

        try:
            # Use MAS agent execution with tool support
            messages = [
                {"role": "system", "content": self._build_instructions()},
                {"role": "user", "content": task_input},
            ]

            # Get properly formatted tools
            tools = self._get_tools()
            formatted_tools = []
            for tool in tools:
                if isinstance(tool, dict) and "function" in tool:
                    formatted_tools.append(
                        {"type": "function", "function": tool["function"]}
                    )

            # Call LLM with tool support
            if formatted_tools:
                self.logger.info(
                    f"Calling LLM with {len(formatted_tools)} tools available"
                )

                # The MAS Agent.execute method doesn't accept tools parameter directly
                # Instead, we need to make tools available through the tool_registry
                tool_registry = {}
                for tool in formatted_tools:
                    tool_name = tool.get("function", {}).get("name", "unknown")
                    tool_registry[tool_name] = tool

                result = await super().execute(
                    input_text=task_input,
                    context=context.__dict__ if context else None,
                    tool_registry=tool_registry,
                )

                # Handle tool calls if present
                tool_calls_to_execute = []

                # Check for tool calls in different formats
                if hasattr(result, "tool_calls") and result.tool_calls:
                    tool_calls_to_execute = result.tool_calls
                elif isinstance(result, dict) and "tool_calls" in result:
                    tool_calls_to_execute = result["tool_calls"]

                if tool_calls_to_execute:
                    self.logger.info(
                        f"Processing {len(tool_calls_to_execute)} tool calls"
                    )
                    tool_results = await self._execute_tool_calls(tool_calls_to_execute)

                    # Add tool results to the response
                    if hasattr(result, "content"):
                        result.content += f"\n\nTool execution results: {tool_results}"
                    elif isinstance(result, dict) and "output" in result:
                        result[
                            "output"
                        ] += f"\n\nTool execution results: {tool_results}"
                    else:
                        result = f"{result}\n\nTool execution results: {tool_results}"

                    # Log tool execution summary
                    created_files = []
                    created_dirs = []
                    for tool_result in tool_results:
                        if "result" in tool_result and isinstance(
                            tool_result["result"], dict
                        ):
                            tr = tool_result["result"]
                            if tr.get("success") and "write" in str(tr):
                                created_files.append(tr.get("path", "unknown"))
                            elif tr.get("success") and "mkdir" in str(tr):
                                created_dirs.append(tr.get("path", "unknown"))

                    self.logger.info(
                        f"Created {len(created_files)} files: {created_files}"
                    )
                    self.logger.info(
                        f"Created {len(created_dirs)} directories: {created_dirs}"
                    )

            else:
                # No tools available - use standard execution
                result = await super().execute(
                    input_text=task_input, context=context.__dict__ if context else None
                )

            execution_time = time.time() - start_time

            # Create execution result
            execution_result = ExecutionResult(
                success=True,
                agent_name=self.name,
                task_id=f"{self.name}_task_{len(self.execution_history)}",
                output=self._safe_json_dumps(result),
                execution_time=execution_time,
                metadata={"task": task_or_input, "tools_used": len(formatted_tools)},
            )

            # Store in history
            self.execution_history.append(execution_result)

            return execution_result

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Task execution failed: {str(e)}")

            execution_result = ExecutionResult(
                success=False,
                agent_name=self.name,
                task_id=f"{self.name}_task_{len(self.execution_history)}",
                error_message=str(e),
                execution_time=execution_time,
                metadata={"task": task_or_input},
            )

            self.execution_history.append(execution_result)

            return execution_result

    async def collaborate(
        self,
        other_agents: List["BaseAgent"],
        task: Dict[str, Any],
        pattern: Optional[CollaborationPattern] = None,
    ) -> List[ExecutionResult]:
        """Collaborate with other agents using MAS Task and Collaboration system"""

        if pattern:
            return await pattern.execute([self] + other_agents, task)

        # Use MAS Collaboration system
        collaboration = mas.Collaboration(
            name=f"collaboration_{len(self.execution_history)}",
            description=task.get("description", "Multi-agent collaboration"),
            agents=[self] + other_agents,
        )

        # Execute collaboration using MAS system
        result = await self.mas_system.execute_collaboration(
            collaboration=collaboration, task=task
        )

        return [result]  # MAS returns a single result that we wrap in a list

    async def _execute_tool_calls(self, tool_calls: List[Any]) -> List[Dict[str, Any]]:
        """Execute tool calls and return results"""
        results = []

        for tool_call in tool_calls:
            try:
                # Handle different tool call formats
                if hasattr(tool_call, "function"):
                    # OpenAI-style tool call
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except (json.JSONDecodeError, AttributeError):
                        # If arguments is already a dict or not valid JSON
                        arguments = (
                            tool_call.function.arguments
                            if hasattr(tool_call.function, "arguments")
                            else {}
                        )
                    tool_call_id = getattr(tool_call, "id", None)
                elif isinstance(tool_call, dict):
                    # Dictionary-style tool call
                    tool_name = tool_call.get("name") or tool_call.get(
                        "function", {}
                    ).get("name")
                    arguments = tool_call.get("arguments", {})
                    tool_call_id = tool_call.get("id")
                elif hasattr(tool_call, "name") and hasattr(tool_call, "arguments"):
                    # ToolCallRequest object
                    tool_name = tool_call.name
                    arguments = tool_call.arguments
                    if isinstance(arguments, str):
                        try:
                            arguments = json.loads(arguments)
                        except json.JSONDecodeError:
                            pass  # Keep as string if not JSON
                    tool_call_id = getattr(tool_call, "id", None)
                else:
                    self.logger.warning(f"Unknown tool call format: {type(tool_call)}")
                    continue

                # Make sure arguments is a dict
                if not isinstance(arguments, dict):
                    self.logger.warning(
                        f"Arguments is not a dict, converting: {arguments}"
                    )
                    if isinstance(arguments, str):
                        try:
                            arguments = json.loads(arguments)
                        except json.JSONDecodeError:
                            arguments = {"value": arguments}
                    else:
                        arguments = {"value": arguments}

                # Find the tool function
                tool_func = None
                for tool_def in self._get_tools():
                    if isinstance(tool_def, dict):
                        if (
                            tool_def.get("name") == tool_name
                            or tool_def.get("function", {}).get("name") == tool_name
                        ):
                            tool_func = tool_def.get("func")
                            break

                if tool_func is None:
                    self.logger.error(f"Tool function not found: {tool_name}")
                    results.append(
                        {
                            "tool_call_id": tool_call_id,
                            "error": f"Tool function not found: {tool_name}",
                        }
                    )
                    continue

                # Execute the tool
                self.logger.info(f"Executing tool: {tool_name} with args: {arguments}")

                if tool_name == "file_system":
                    result = await tool_func(
                        arguments.get("operation"),
                        arguments.get("path"),
                        content=arguments.get("content"),
                        encoding=arguments.get("encoding", "utf-8"),
                        create_dirs=arguments.get("create_dirs", True),
                    )
                elif tool_name in ["flutter_cli", "dart_cli"]:
                    result = await tool_func(
                        arguments.get("command"), arguments.get("args", [])
                    )
                else:
                    # Generic tool call
                    result = await tool_func(**arguments)

                results.append({"tool_call_id": tool_call_id, "result": result})

                self.logger.info(f"Tool {tool_name} executed successfully")

            except Exception as e:
                self.logger.error(f"Tool execution failed: {str(e)}")
                results.append(
                    {"tool_call_id": getattr(tool_call, "id", None), "error": str(e)}
                )

        return results

    def _safe_json_dumps(self, obj):
        """Safely serialize objects to JSON, handling ToolCallRequest objects."""
        import json  # Import here to avoid any scoping issues

        try:
            # Import the custom encoder
            from multiagenticswarm.core.base_tool import JSONEncoder

            return json.dumps(obj, cls=JSONEncoder)
        except (TypeError, ValueError) as e:
            # Fallback to string representation if JSON serialization fails
            self.logger.warning(f"Failed to serialize object to JSON: {e}")
            return str(obj)

    @abstractmethod
    def _get_specialized_instructions(self) -> str:
        """Get domain-specific instructions for the agent"""
        pass

    @abstractmethod
    def _get_tools(self) -> List[Dict[str, Any]]:
        """Get tools this agent needs. Return list of tool definitions:
        [
            {
                "name": "tool_name",
                "func": callable,
                "description": "Tool description",
                "scope": "local|shared|global"
            }
        ]
        """
        pass


class BaseSwarm(mas.System if MAS_AVAILABLE else ABC):
    """
    Base class for all swarm implementations.
    Inherits directly from MultiAgenticSwarm System for full SDK integration.
    """

    def __init__(
        self,
        name: str,
        project_path: str = ".",
        system: Optional[Any] = None,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4",
        **kwargs,
    ):
        if not MAS_AVAILABLE:
            raise ImportError("MultiAgenticSwarm is required but not available")

        self.name = name
        self.project_path = project_path
        self.llm_provider = llm_provider
        self.llm_model = llm_model

        # Use direct import for the logger
        from multiagenticswarm.utils.logger import get_logger

        self.logger = get_logger(f"agentswarm.{name}")

        # Initialize MAS System
        super().__init__(config_path=None, enable_logging=True, verbose=True)

        # Setup domain-specific components
        self._setup_tools()
        self._setup_agents()
        self._setup_workflows()

    @abstractmethod
    def _setup_tools(self) -> None:
        """Setup domain-specific tools"""
        pass

    @abstractmethod
    def _setup_agents(self) -> None:
        """Setup domain-specific agents"""
        pass

    def _setup_workflows(self) -> None:
        """Setup default workflows using MAS Task system"""
        # Default implementation - can be overridden by subclasses
        pass

    def add_agent(self, agent: BaseAgent) -> None:
        """Add an agent to the swarm"""
        self.register_agent(agent)

    async def execute_workflow(
        self, workflow_name: str, context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """Execute a workflow using MAS Task system"""
        # Execute the task using the MAS system
        task_result = await self.execute_task(workflow_name, context)

        # Convert the result to ExecutionResult format
        return ExecutionResult(
            success=task_result.get("success", False),
            agent_name="FlutterSwarm",
            task_id=workflow_name,
            output=task_result,
            execution_time=task_result.get("execution_time", 0),
            metadata=context or {},
        )

    def get_execution_history(self) -> List[ExecutionResult]:
        """Get the execution history for the entire swarm"""
        return self.execution_history.copy()

    def clear_history(self):
        """Clear the execution history"""
        self.execution_history.clear()
        for agent in self.agents.values():
            agent.clear_history()
