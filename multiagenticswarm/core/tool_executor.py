"""
Centralized tool execution engine with standardized request/response handling.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Union

from ..utils.logger import get_logger
from .base_tool import BaseTool, ToolCallRequest, ToolCallResponse

logger = get_logger(__name__)


class ToolExecutor:
    """
    Centralized tool execution engine that handles tool calling in a standardized way.
    This abstracts the tool execution process and provides consistent behavior.
    """

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.execution_history: List[Dict[str, Any]] = []

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool with the executor."""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool '{tool.name}' with executor")

    def get_available_tools_for_agent(self, agent_name: str) -> List[BaseTool]:
        """Get all tools available to a specific agent."""
        available = []
        for tool in self.tools.values():
            if tool.can_be_used_by(agent_name):
                available.append(tool)
        return available

    def get_tools_schema_for_agent(self, agent_name: str) -> List[Dict[str, Any]]:
        """
        Get OpenAPI-compatible tool schemas for an agent.
        This is what gets sent to the LLM.
        """
        available_tools = self.get_available_tools_for_agent(agent_name)
        return [tool.get_openapi_schema() for tool in available_tools]

    async def execute_tool_call(
        self, tool_call: Union[Dict[str, Any], ToolCallRequest], agent_name: str
    ) -> ToolCallResponse:
        """
        Execute a single tool call.
        """
        # Convert to standardized format
        if isinstance(tool_call, dict):
            request = ToolCallRequest.from_dict(tool_call)
        else:
            request = tool_call

        # Get the tool
        tool = self.tools.get(request.name)
        if not tool:
            return ToolCallResponse(
                id=request.id,
                name=request.name,
                result=None,
                success=False,
                error=f"Tool '{request.name}' not found",
            )

        # Execute the tool
        response = await tool.execute(request, agent_name)

        # Log execution
        self.execution_history.append(
            {
                "tool_name": request.name,
                "agent": agent_name,
                "success": response.success,
                "execution_time": response.execution_time,
                "timestamp": logger.name,  # Placeholder for actual timestamp
            }
        )

        return response

    async def execute_tool_calls(
        self, tool_calls: List[Union[Dict[str, Any], ToolCallRequest]], agent_name: str
    ) -> List[ToolCallResponse]:
        """
        Execute multiple tool calls, potentially in parallel.
        """
        # Execute all tool calls
        tasks = [
            self.execute_tool_call(tool_call, agent_name) for tool_call in tool_calls
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        final_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                # Create error response
                request = tool_calls[i]
                if isinstance(request, dict):
                    request = ToolCallRequest.from_dict(request)

                final_responses.append(
                    ToolCallResponse(
                        id=request.id,
                        name=request.name,
                        result=None,
                        success=False,
                        error=str(response),
                    )
                )
            else:
                final_responses.append(response)

        return final_responses

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a specific tool by name."""
        return self.tools.get(tool_name)

    def get_all_tools(self) -> List[BaseTool]:
        """Get all registered tools."""
        return list(self.tools.values())

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        total_executions = len(self.execution_history)
        successful_executions = sum(
            1 for exec in self.execution_history if exec["success"]
        )

        tool_usage = {}
        for exec in self.execution_history:
            tool_name = exec["tool_name"]
            if tool_name not in tool_usage:
                tool_usage[tool_name] = {"count": 0, "success_rate": 0}
            tool_usage[tool_name]["count"] += 1

        # Calculate success rates
        for tool_name in tool_usage:
            tool_executions = [
                e for e in self.execution_history if e["tool_name"] == tool_name
            ]
            successful = sum(1 for e in tool_executions if e["success"])
            tool_usage[tool_name]["success_rate"] = (
                successful / len(tool_executions) if tool_executions else 0
            )

        return {
            "total_executions": total_executions,
            "success_rate": (
                successful_executions / total_executions if total_executions > 0 else 0
            ),
            "tool_usage": tool_usage,
        }
