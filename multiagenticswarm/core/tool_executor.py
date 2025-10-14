"""
Centralized tool execution engine with standardized request/response handling.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from .base_tool import BaseTool, ToolCallRequest, ToolCallResponse
from .tool_matrix import ToolMatrix
from .tool_conditions import get_conditions
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ToolExecutor:
    """
    Centralized tool execution engine that handles tool calling in a standardized way.
    This abstracts the tool execution process and provides consistent behavior.
    """
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.conditions = get_conditions()
        self.permission_matrix = ToolMatrix()
        self.context: Dict[str, Any] = {}
    
    def set_context(self, context: Dict[str, Any]):
        """Set the current execution context for conditional permissions."""
        self.context.update(context)
        logger.debug(f"Updated execution context: {context}")
    
    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool with the executor."""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool '{tool.name}' with executor")
    
    def get_available_tools_for_agent(self, agent_name: str) -> List[BaseTool]:
        """Get all tools available to a specific agent based on permissions."""
        available = []
        for tool in self.tools.values():
            # Check both old system compatibility and new permission system
            if (tool.can_be_used_by(agent_name) or 
                self.permission_matrix.check_permission(agent_name, tool.name, self.context)):
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
        self,
        tool_call: Union[Dict[str, Any], ToolCallRequest],
        agent_name: str
    ) -> ToolCallResponse:
        """
        Execute a single tool call with permission checking.
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
                error=f"Tool '{request.name}' not found"
            )
        
        # Check permissions using the new permission matrix
        if not self.permission_matrix.check_permission(agent_name, request.name, self.context):
            return ToolCallResponse(
                id=request.id,
                name=request.name,
                result=None,
                success=False,
                error=f"Permission denied: Agent '{agent_name}' cannot use tool '{request.name}'"
            )
        
        # Execute the tool
        response = await tool.execute(request, agent_name)
        
        # Update quota usage if successful
        if response.success:
            self.permission_matrix.use_quota(agent_name, request.name)
        
        # Log execution
        self.execution_history.append({
            "tool_name": request.name,
            "agent": agent_name,
            "success": response.success,
            "execution_time": response.execution_time,
            "timestamp": logger.name  # Placeholder for actual timestamp
        })
        
        return response
    
    async def execute_tool_calls(
        self,
        tool_calls: List[Union[Dict[str, Any], ToolCallRequest]],
        agent_name: str
    ) -> List[ToolCallResponse]:
        """
        Execute multiple tool calls, potentially in parallel.
        """
        # Execute all tool calls
        tasks = [
            self.execute_tool_call(tool_call, agent_name)
            for tool_call in tool_calls
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
                
                final_responses.append(ToolCallResponse(
                    id=request.id,
                    name=request.name,
                    result=None,
                    success=False,
                    error=str(response)
                ))
            else:
                final_responses.append(response)
        
        return final_responses
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a specific tool by name."""
        return self.tools.get(tool_name)
    
    def get_all_tools(self) -> List[BaseTool]:
        """Get all registered tools."""
        return list(self.tools.values())
    
    # Permission management methods
    
    def register_agent(self, agent_id: str, custom_permissions: Optional[Dict[str, str]] = None):
        """Register an agent with the permission system."""
        self.permission_matrix.register_agent(agent_id, custom_permissions)
    
    def update_permission(self, agent_id: str, tool_name: str, permission: str):
        """Update permission for an agent-tool combination at runtime."""
        self.permission_matrix.update_permission(agent_id, tool_name, permission)
    
    def get_agent_permissions(self, agent_id: str) -> Dict[str, str]:
        """Get all permissions for an agent."""
        return self.permission_matrix.get_agent_permissions(agent_id)
    
    def load_permissions_from_config(self, config: Dict[str, Any]):
        """Load permissions from configuration."""
        self.permission_matrix.load_from_config(config)
        self.conditions.load_from_config(config)
    
    def get_audit_trail(self, agent_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit trail from permission matrix."""
        return self.permission_matrix.get_audit_trail(agent_id, limit)
