"""
Comprehensive test suite for BaseTool functionality.
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest

from multiagenticswarm.core.base_tool import (
    BaseTool,
    FunctionTool,
    ToolCallRequest,
    ToolCallResponse,
    ToolScope,
)


class TestToolCallRequest:
    """Test ToolCallRequest data class."""

    def test_basic_creation(self):
        """Test basic ToolCallRequest creation."""
        request = ToolCallRequest(
            id="test-id", name="test_tool", arguments={"param1": "value1"}
        )

        assert request.id == "test-id"
        assert request.name == "test_tool"
        assert request.arguments == {"param1": "value1"}

    def test_from_dict(self):
        """Test creating ToolCallRequest from dictionary."""
        data = {"id": "dict-id", "name": "dict_tool", "arguments": {"x": 10, "y": 20}}

        request = ToolCallRequest.from_dict(data)

        assert request.id == "dict-id"
        assert request.name == "dict_tool"
        assert request.arguments == {"x": 10, "y": 20}

    def test_from_dict_minimal(self):
        """Test creating ToolCallRequest with minimal data."""
        data = {"name": "minimal_tool"}

        request = ToolCallRequest.from_dict(data)

        assert request.name == "minimal_tool"
        assert request.arguments == {}
        assert request.id is not None  # Auto-generated

    def test_from_dict_missing_name(self):
        """Test error handling when name is missing."""
        data = {"arguments": {"param": "value"}}

        with pytest.raises(KeyError):
            ToolCallRequest.from_dict(data)


class TestToolCallResponse:
    """Test ToolCallResponse data class."""

    def test_basic_creation(self):
        """Test basic ToolCallResponse creation."""
        response = ToolCallResponse(
            id="resp-id", name="test_tool", result="success", success=True
        )

        assert response.id == "resp-id"
        assert response.name == "test_tool"
        assert response.result == "success"
        assert response.success is True
        assert response.error is None
        assert response.execution_time is None
        assert response.metadata is None

    def test_full_creation(self):
        """Test ToolCallResponse with all fields."""
        response = ToolCallResponse(
            id="full-id",
            name="full_tool",
            result={"data": "result"},
            success=True,
            error=None,
            execution_time=0.123,
            metadata={"version": "1.0"},
        )

        assert response.execution_time == 0.123
        assert response.metadata == {"version": "1.0"}

    def test_error_response(self):
        """Test error response creation."""
        response = ToolCallResponse(
            id="error-id",
            name="error_tool",
            result=None,
            success=False,
            error="Tool execution failed",
        )

        assert response.success is False
        assert response.error == "Tool execution failed"
        assert response.result is None

    def test_to_dict(self):
        """Test converting response to dictionary."""
        response = ToolCallResponse(
            id="dict-id",
            name="dict_tool",
            result="dict_result",
            success=True,
            execution_time=0.456,
            metadata={"key": "value"},
        )

        result_dict = response.to_dict()

        expected = {
            "id": "dict-id",
            "name": "dict_tool",
            "result": "dict_result",
            "success": True,
            "error": None,
            "execution_time": 0.456,
            "metadata": {"key": "value"},
        }

        assert result_dict == expected

    def test_to_dict_minimal(self):
        """Test to_dict with minimal data."""
        response = ToolCallResponse(
            id="min-id", name="min_tool", result="min_result", success=True
        )

        result_dict = response.to_dict()

        assert result_dict["metadata"] == {}  # Should default to empty dict


class TestFunctionTool:
    """Test FunctionTool implementation."""

    def test_basic_function_tool(self):
        """Test creating a basic function tool."""

        def add_numbers(x: int, y: int) -> int:
            return x + y

        tool = FunctionTool(
            name="add_tool", func=add_numbers, description="Adds two numbers"
        )

        assert tool.name == "add_tool"
        assert tool.description == "Adds two numbers"
        assert tool.func == add_numbers
        assert tool.scope == ToolScope.LOCAL

    def test_function_tool_with_parameters(self):
        """Test function tool with explicit parameters."""

        def multiply(x: float, y: float) -> float:
            return x * y

        parameters = {
            "type": "object",
            "properties": {"x": {"type": "number"}, "y": {"type": "number"}},
            "required": ["x", "y"],
        }

        tool = FunctionTool(
            name="multiply_tool",
            func=multiply,
            description="Multiplies two numbers",
            parameters=parameters,
        )

        assert tool.parameters == parameters

    @pytest.mark.asyncio
    async def test_function_tool_execution(self):
        """Test executing a function tool."""

        def concat_strings(a: str, b: str) -> str:
            return f"{a} {b}"

        tool = FunctionTool(
            name="concat_tool", func=concat_strings, description="Concatenates strings"
        )
        # Set tool to global access for testing
        tool.set_global()

        request = ToolCallRequest(
            id="exec-id", name="concat_tool", arguments={"a": "Hello", "b": "World"}
        )

        response = await tool.execute(request, "test_agent")

        assert response.success is True
        assert response.result == "Hello World"
        assert response.id == "exec-id"
        assert response.name == "concat_tool"
        assert response.error is None
        assert response.execution_time is not None

    @pytest.mark.asyncio
    async def test_function_tool_execution_error(self):
        """Test function tool execution with errors."""

        def failing_func(x: int) -> int:
            raise ValueError("This function always fails")

        tool = FunctionTool(
            name="failing_tool",
            func=failing_func,
            description="A tool that always fails",
        )
        # Set tool to global access for testing
        tool.set_global()

        request = ToolCallRequest(
            id="fail-id", name="failing_tool", arguments={"x": 10}
        )

        response = await tool.execute(request, "test_agent")

        assert response.success is False
        assert response.result is None
        assert "This function always fails" in response.error
        assert response.execution_time is not None

    @pytest.mark.asyncio
    async def test_async_function_tool(self):
        """Test tool with async function."""

        async def async_operation(delay: float) -> str:
            await asyncio.sleep(delay)
            return f"Completed after {delay} seconds"

        tool = FunctionTool(
            name="async_tool", func=async_operation, description="An async operation"
        )
        # Set tool to global access for testing
        tool.set_global()

        request = ToolCallRequest(
            id="async-id", name="async_tool", arguments={"delay": 0.1}
        )

        start_time = time.time()
        response = await tool.execute(request, "test_agent")
        execution_time = time.time() - start_time

        assert response.success is True
        assert "Completed after 0.1 seconds" in response.result
        assert execution_time >= 0.1  # Should take at least the delay time

    def test_generate_parameters_schema_simple(self):
        """Test automatic parameter schema generation for simple function."""

        def simple_func(x: int, y: str = "default") -> str:
            return f"{x}: {y}"

        tool = FunctionTool(
            name="simple_tool", func=simple_func, description="Simple function"
        )

        schema = tool.parameters

        assert schema["type"] == "object"
        assert "x" in schema["properties"]
        assert "y" in schema["properties"]
        assert schema["properties"]["x"]["type"] == "integer"
        assert schema["properties"]["y"]["type"] == "string"
        assert schema["required"] == ["x"]  # y has default, so not required

    def test_generate_parameters_schema_complex(self):
        """Test parameter schema generation for complex function."""
        from typing import List, Optional

        def complex_func(
            items: List[str], count: int = 10, filter_value: Optional[str] = None
        ) -> List[str]:
            return items[:count]

        tool = FunctionTool(
            name="complex_tool", func=complex_func, description="Complex function"
        )

        schema = tool.parameters

        assert "items" in schema["properties"]
        assert "count" in schema["properties"]
        assert "filter_value" in schema["properties"]
        assert schema["required"] == ["items"]  # Only items is required

    def test_get_openapi_schema(self):
        """Test OpenAPI schema generation."""

        def api_func(param1: str, param2: int = 5) -> dict:
            return {"param1": param1, "param2": param2}

        tool = FunctionTool(
            name="api_tool", func=api_func, description="API function tool"
        )

        schema = tool.get_openapi_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "api_tool"
        assert schema["function"]["description"] == "API function tool"
        assert "parameters" in schema["function"]

        params = schema["function"]["parameters"]
        assert params["type"] == "object"
        assert "param1" in params["properties"]
        assert "param2" in params["properties"]


class TestToolScope:
    """Test tool scope functionality."""

    def test_scope_enum_values(self):
        """Test ToolScope enum values."""
        assert ToolScope.LOCAL == "local"
        assert ToolScope.SHARED == "shared"
        assert ToolScope.GLOBAL == "global"

    def test_scope_comparison(self):
        """Test scope comparison."""
        assert ToolScope.LOCAL != ToolScope.SHARED
        assert ToolScope.SHARED != ToolScope.GLOBAL
        assert ToolScope.GLOBAL != ToolScope.LOCAL

    def test_scope_in_tool(self):
        """Test scope usage in tool."""

        def test_func():
            return "test"

        tool = FunctionTool(name="scope_tool", func=test_func, scope=ToolScope.GLOBAL)

        assert tool.scope == ToolScope.GLOBAL


class TestToolAccessControl:
    """Test tool access control mechanisms."""

    def test_local_tool_access(self):
        """Test local tool access control."""

        def test_func():
            return "test"

        tool = FunctionTool(name="local_tool", func=test_func)
        tool.set_local_agent("agent1")

        assert tool.can_be_used_by("agent1") is True
        assert tool.can_be_used_by("agent2") is False
        assert tool.local_agent == "agent1"

    def test_shared_tool_access(self):
        """Test shared tool access control."""

        def test_func():
            return "test"

        tool = FunctionTool(name="shared_tool", func=test_func)
        tool.set_shared_agents(["agent1", "agent2"])

        assert tool.can_be_used_by("agent1") is True
        assert tool.can_be_used_by("agent2") is True
        assert tool.can_be_used_by("agent3") is False
        assert tool.shared_agents == ["agent1", "agent2"]

    def test_global_tool_access(self):
        """Test global tool access control."""

        def test_func():
            return "test"

        tool = FunctionTool(name="global_tool", func=test_func)
        tool.set_global()

        assert tool.can_be_used_by("agent1") is True
        assert tool.can_be_used_by("agent2") is True
        assert tool.can_be_used_by("any_agent") is True
        assert tool.is_global is True

    def test_access_control_transitions(self):
        """Test changing tool access control."""

        def test_func():
            return "test"

        tool = FunctionTool(name="transition_tool", func=test_func)

        # Start as local
        tool.set_local_agent("agent1")
        assert tool.can_be_used_by("agent1") is True
        assert tool.can_be_used_by("agent2") is False

        # Change to shared
        tool.set_shared_agents(["agent2", "agent3"])
        assert tool.can_be_used_by("agent1") is False
        assert tool.can_be_used_by("agent2") is True
        assert tool.can_be_used_by("agent3") is True

        # Change to global
        tool.set_global()
        assert tool.can_be_used_by("agent1") is True
        assert tool.can_be_used_by("agent2") is True
        assert tool.can_be_used_by("any_agent") is True


class TestToolEdgeCases:
    """Test edge cases and error conditions."""

    def test_tool_with_no_function(self):
        """Test tool creation without function."""

        # This should work for abstract tools
        class TestTool(BaseTool):
            async def _execute_impl(self, **kwargs):
                return "test result"

        tool = TestTool(name="no_func_tool", description="No function tool")
        assert tool.name == "no_func_tool"

    def test_function_tool_without_type_hints(self):
        """Test function tool with no type hints."""

        def no_hints_func(x, y):
            return x + y

        tool = FunctionTool(
            name="no_hints_tool", func=no_hints_func, description="No type hints"
        )

        # Should still work, but parameters might be less specific
        schema = tool.parameters
        assert schema["type"] == "object"
        assert "x" in schema["properties"]
        assert "y" in schema["properties"]

    @pytest.mark.asyncio
    async def test_tool_execution_with_invalid_arguments(self):
        """Test tool execution with invalid arguments."""

        def strict_func(x: int, y: int) -> int:
            return x + y

        tool = FunctionTool(
            name="strict_tool", func=strict_func, description="Strict typing tool"
        )

        # Test with wrong argument types
        request = ToolCallRequest(
            id="invalid-id", name="strict_tool", arguments={"x": "not_a_number", "y": 5}
        )

        response = await tool.execute(request, "test_agent")

        # Should handle the error gracefully
        assert response.success is False
        assert response.error is not None

    @pytest.mark.asyncio
    async def test_tool_execution_with_missing_arguments(self):
        """Test tool execution with missing required arguments."""

        def required_args_func(x: int, y: int) -> int:
            return x + y

        tool = FunctionTool(
            name="required_tool",
            func=required_args_func,
            description="Required args tool",
        )

        # Test with missing arguments
        request = ToolCallRequest(
            id="missing-id", name="required_tool", arguments={"x": 5}  # Missing 'y'
        )

        response = await tool.execute(request, "test_agent")

        # Should handle the error gracefully
        assert response.success is False
        assert response.error is not None

    def test_tool_with_very_long_name(self):
        """Test tool with extremely long name."""
        long_name = "a" * 1000

        def test_func():
            return "test"

        tool = FunctionTool(
            name=long_name, func=test_func, description="Long name tool"
        )

        assert tool.name == long_name

    def test_tool_with_special_characters_in_name(self):
        """Test tool with special characters in name."""
        special_name = "tool-with_special.chars@123"

        def test_func():
            return "test"

        tool = FunctionTool(
            name=special_name, func=test_func, description="Special chars tool"
        )

        assert tool.name == special_name


class TestToolPerformance:
    """Test tool performance characteristics."""

    @pytest.mark.asyncio
    async def test_tool_execution_timing(self):
        """Test that execution timing is recorded."""

        def slow_func(delay: float = 0.1) -> str:
            import time

            time.sleep(delay)
            return "completed"

        tool = FunctionTool(
            name="timing_tool", func=slow_func, description="Timing test tool"
        )
        # Set tool to global access for testing
        tool.set_global()

        request = ToolCallRequest(
            id="timing-id", name="timing_tool", arguments={"delay": 0.1}
        )

        response = await tool.execute(request, "test_agent")

        assert response.success is True
        assert response.execution_time is not None
        assert response.execution_time >= 0.1  # Should be at least the delay

    @pytest.mark.asyncio
    async def test_concurrent_tool_executions(self):
        """Test multiple concurrent tool executions."""

        def concurrent_func(value: int) -> int:
            import time

            time.sleep(0.1)  # Small delay
            return value * 2

        tool = FunctionTool(
            name="concurrent_tool",
            func=concurrent_func,
            description="Concurrent test tool",
        )
        # Set tool to global access for testing
        tool.set_global()

        # Create multiple requests
        requests = [
            ToolCallRequest(
                id=f"concurrent-{i}", name="concurrent_tool", arguments={"value": i}
            )
            for i in range(5)
        ]

        # Execute concurrently
        tasks = [tool.execute(request, "test_agent") for request in requests]

        start_time = time.time()
        responses = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # All should succeed
        for i, response in enumerate(responses):
            assert response.success is True
            assert response.result == i * 2

        # Should take less time than sequential execution
        # (5 * 0.1 = 0.5 seconds sequential, should be much less concurrent)
        assert total_time < 0.4


class TestToolSerialization:
    """Test tool serialization capabilities."""

    def test_tool_metadata_serialization(self):
        """Test serializing tool metadata."""

        def serializable_func(x: int) -> int:
            return x * 2

        tool = FunctionTool(
            name="serializable_tool",
            func=serializable_func,
            description="Serializable tool",
        )

        # Get tool metadata (without the function itself)
        metadata = {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
            "scope": tool.scope.value,
            "tool_id": tool.tool_id,
        }

        # Should be JSON serializable
        json_str = json.dumps(metadata)
        restored = json.loads(json_str)

        assert restored["name"] == tool.name
        assert restored["description"] == tool.description
        assert restored["scope"] == tool.scope.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
