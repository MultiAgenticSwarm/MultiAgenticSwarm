"""
Standardized tool interface following OpenAPI 3.0 and JSON Schema specifications.
"""

import inspect
import json
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

try:
    from pydantic import BaseModel, Field, ValidationError

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object
    Field = lambda **kwargs: kwargs.get("default", None)

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ToolCallRequest:
    """Standardized tool call request format."""

    id: str
    name: str
    arguments: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCallRequest":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            arguments=data.get("arguments", {}),
        )


@dataclass
class ToolCallResponse:
    """Standardized tool call response format."""

    id: str
    name: str
    result: Any
    success: bool
    error: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "result": self.result,
            "success": self.success,
            "error": self.error,
            "execution_time": self.execution_time,
            "metadata": self.metadata or {},
        }


class ToolScope(str, Enum):
    """Tool sharing scope levels."""

    LOCAL = "local"
    SHARED = "shared"
    GLOBAL = "global"


class BaseTool(ABC):
    """
    Base class for all tools following OpenAPI 3.0 specification.

    This provides a standardized interface that works across all LLM providers
    and follows industry best practices for tool calling.
    """

    def __init__(
        self,
        name: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        scope: ToolScope = ToolScope.LOCAL,
    ):
        self.name = name
        self.description = description
        self.parameters = parameters or self._generate_parameters_schema()
        self.scope = scope
        self.tool_id = str(uuid.uuid4())

        # Access control
        self.local_agent: Optional[str] = None
        self.shared_agents: List[str] = []
        self.is_global = False

        # Runtime tracking
        self.usage_count = 0
        self.last_used_by: Optional[str] = None

        logger.info(f"Created standardized tool '{name}' with scope '{scope.value}'")

    @abstractmethod
    async def _execute_impl(self, **kwargs) -> Any:
        """
        Abstract method that subclasses must implement.
        This contains the actual tool logic.
        """
        pass

    def _generate_parameters_schema(self) -> Dict[str, Any]:
        """
        Generate JSON Schema for parameters.
        Override this if you want custom schema generation.
        """
        return {"type": "object", "properties": {}, "required": []}

    def get_openapi_schema(self) -> Dict[str, Any]:
        """
        Get OpenAPI 3.0 compatible tool schema.
        This is the standard format used by all LLM providers.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def validate_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate arguments against the tool's schema.
        Returns validated arguments or raises ValidationError.
        """
        if not self.parameters:
            return arguments

        # Basic validation - can be enhanced with jsonschema library
        required_fields = self.parameters.get("required", [])
        properties = self.parameters.get("properties", {})

        # Check required fields
        for field in required_fields:
            if field not in arguments:
                raise ValueError(f"Missing required parameter: {field}")

        # Type validation (basic)
        validated = {}
        for key, value in arguments.items():
            if key in properties:
                expected_type = properties[key].get("type")
                if expected_type and not self._validate_type(value, expected_type):
                    logger.warning(
                        f"Type mismatch for {key}: expected {expected_type}, got {type(value)}"
                    )
                validated[key] = value
            else:
                logger.warning(f"Unknown parameter: {key}")
                validated[key] = value  # Allow unknown parameters for flexibility

        return validated

    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Basic type validation."""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        return True

    async def execute(
        self, request: ToolCallRequest, agent_name: str
    ) -> ToolCallResponse:
        """
        Execute the tool with standardized request/response format.
        This is the main entry point for all tool executions.
        """
        start_time = time.time()

        # Log execution start
        logger.log_tool_execution(
            tool_name=self.name, agent_name=agent_name, parameters=request.arguments
        )

        try:
            # Validate access permissions
            if not self.can_be_used_by(agent_name):
                raise PermissionError(
                    f"Agent '{agent_name}' cannot use tool '{self.name}'"
                )

            # Validate arguments
            validated_args = self.validate_arguments(request.arguments)

            # Execute the tool
            result = await self._execute_impl(**validated_args)

            execution_time = time.time() - start_time
            self.usage_count += 1
            self.last_used_by = agent_name

            response = ToolCallResponse(
                id=request.id,
                name=self.name,
                result=result,
                success=True,
                execution_time=execution_time,
                metadata={
                    "agent": agent_name,
                    "usage_count": self.usage_count,
                    "scope": self.scope.value,
                },
            )

            # Log successful execution
            logger.log_tool_execution(
                tool_name=self.name,
                agent_name=agent_name,
                parameters=validated_args,
                result=result,
                execution_time=execution_time,
            )

            return response

        except Exception as e:
            execution_time = time.time() - start_time

            response = ToolCallResponse(
                id=request.id,
                name=self.name,
                result=None,
                success=False,
                error=str(e),
                execution_time=execution_time,
                metadata={"agent": agent_name, "error_type": type(e).__name__},
            )

            # Log error
            logger.log_tool_execution(
                tool_name=self.name,
                agent_name=agent_name,
                parameters=request.arguments,
                result=f"ERROR: {str(e)}",
                execution_time=execution_time,
            )

            return response

    # Access control methods (same as before but updated)
    def set_local(self, agent: Union[str, "Agent"]) -> "BaseTool":
        """Set tool to be available only to a specific agent."""
        agent_name = agent.name if hasattr(agent, "name") else str(agent)
        self.scope = ToolScope.LOCAL
        self.local_agent = agent_name
        self.shared_agents = []
        self.is_global = False
        return self

    def set_shared(self, *agents: Union[str, "Agent"]) -> "BaseTool":
        """Set tool to be shared among specific agents."""
        agent_names = [
            agent.name if hasattr(agent, "name") else str(agent) for agent in agents
        ]
        self.scope = ToolScope.SHARED
        self.local_agent = None
        self.shared_agents = agent_names
        self.is_global = False
        return self

    def set_global(self) -> "BaseTool":
        """Set tool to be available to all agents."""
        self.scope = ToolScope.GLOBAL
        self.local_agent = None
        self.shared_agents = []
        self.is_global = True
        return self

    def can_be_used_by(self, agent: Union[str, "Agent"]) -> bool:
        """Check if an agent can use this tool."""
        agent_name = agent.name if hasattr(agent, "name") else str(agent)

        if self.is_global:
            return True
        elif self.scope == ToolScope.LOCAL:
            return self.local_agent == agent_name
        elif self.scope == ToolScope.SHARED:
            return agent_name in self.shared_agents

        return False

    # Backward compatibility aliases
    def set_local_agent(self, agent: Union[str, "Agent"]) -> "BaseTool":
        """Backward compatibility alias for set_local."""
        return self.set_local(agent)

    def set_shared_agents(self, agents: List[Union[str, "Agent"]]) -> "BaseTool":
        """Backward compatibility alias for set_shared."""
        return self.set_shared(*agents)

    def set_global_agent(self) -> "BaseTool":
        """Backward compatibility alias for set_global."""
        return self.set_global()

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "scope": self.scope.value,
            "tool_id": self.tool_id,
            "local_agent": self.local_agent,
            "shared_agents": self.shared_agents,
            "is_global": self.is_global,
            "usage_count": self.usage_count,
            "last_used_by": self.last_used_by,
        }


class PydanticTool(BaseTool):
    """
    Tool that automatically generates schema from Pydantic models.
    Use this when you want automatic validation and schema generation.
    """

    def __init__(
        self,
        name: str,
        description: str,
        parameters_model: Optional[BaseModel] = None,
        scope: ToolScope = ToolScope.LOCAL,
    ):
        self.parameters_model = parameters_model
        super().__init__(name, description, None, scope)

    def _generate_parameters_schema(self) -> Dict[str, Any]:
        """Generate schema from Pydantic model."""
        if not PYDANTIC_AVAILABLE or not self.parameters_model:
            return super()._generate_parameters_schema()

        # Convert Pydantic model to JSON schema
        return self.parameters_model.model_json_schema()

    def validate_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Use Pydantic for validation if available."""
        if PYDANTIC_AVAILABLE and self.parameters_model:
            try:
                validated_model = self.parameters_model(**arguments)
                return validated_model.model_dump()
            except ValidationError as e:
                raise ValueError(f"Validation error: {e}")

        return super().validate_arguments(arguments)


class FunctionTool(BaseTool):
    """
    Tool that wraps a Python function with automatic schema generation.
    This is the easiest way to create tools from existing functions.
    """

    def __init__(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        scope: ToolScope = ToolScope.LOCAL,
    ):
        self.func = func

        # Auto-generate name and description if not provided
        name = name or func.__name__
        description = (
            description or func.__doc__ or f"Function tool for {func.__name__}"
        )

        # Use provided parameters or auto-generate
        super().__init__(name, description, parameters, scope)

    def _generate_parameters_schema(self) -> Dict[str, Any]:
        """Generate schema from function signature."""
        sig = inspect.signature(self.func)
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            param_schema = {"type": "string"}  # Default type

            # Try to infer type from annotation
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_schema["type"] = "integer"
                elif param.annotation == float:
                    param_schema["type"] = "number"
                elif param.annotation == bool:
                    param_schema["type"] = "boolean"
                elif param.annotation == list:
                    param_schema["type"] = "array"
                elif param.annotation == dict:
                    param_schema["type"] = "object"

            properties[param_name] = param_schema

            # Check if parameter is required
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        return {"type": "object", "properties": properties, "required": required}

    async def _execute_impl(self, **kwargs) -> Any:
        """Execute the wrapped function."""
        if inspect.iscoroutinefunction(self.func):
            return await self.func(**kwargs)
        else:
            # Run synchronous functions in a thread pool to enable concurrency
            import asyncio
            import concurrent.futures

            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                return await loop.run_in_executor(executor, lambda: self.func(**kwargs))
