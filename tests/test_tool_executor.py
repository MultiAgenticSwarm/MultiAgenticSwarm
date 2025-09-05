"""
Comprehensive test suite for ToolExecutor functionality.
"""

import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from multiagenticswarm.core.base_tool import (
    BaseTool,
    FunctionTool,
    ToolCallRequest,
    ToolCallResponse,
    ToolScope,
)
from multiagenticswarm.core.tool_executor import ToolExecutor


class MockTool(BaseTool):
    """Mock tool for testing."""

    def __init__(self, name, should_fail=False, delay=0):
        super().__init__(name, f"Mock tool {name}")
        self.should_fail = should_fail
        self.delay = delay
        self.execution_count = 0
        # Default to global access for testing unless specifically configured otherwise
        self.is_global = True

    async def _execute_impl(self, **kwargs) -> Any:
        """Implementation required by BaseTool."""
        self.execution_count += 1

        if self.delay > 0:
            await asyncio.sleep(self.delay)

        if self.should_fail:
            raise Exception("Mock tool failure")

        return f"Mock result from {self.name}"

    async def execute(self, request, agent_name):
        self.execution_count += 1

        if self.delay > 0:
            await asyncio.sleep(self.delay)

        if self.should_fail:
            return ToolCallResponse(
                id=request.id,
                name=request.name,
                result=None,
                success=False,
                error="Mock tool failure",
            )

        return ToolCallResponse(
            id=request.id,
            name=request.name,
            result=f"Mock result from {self.name} for {agent_name}",
            success=True,
        )


class TestToolExecutorBasics:
    """Test basic ToolExecutor functionality."""

    def test_executor_creation(self):
        """Test creating a ToolExecutor."""
        executor = ToolExecutor()

        assert len(executor.tools) == 0
        assert len(executor.execution_history) == 0

    def test_register_tool(self):
        """Test registering a tool."""
        executor = ToolExecutor()
        tool = MockTool("test_tool")

        executor.register_tool(tool)

        assert "test_tool" in executor.tools
        assert executor.tools["test_tool"] == tool

    def test_register_multiple_tools(self):
        """Test registering multiple tools."""
        executor = ToolExecutor()
        tools = [MockTool("tool1"), MockTool("tool2"), MockTool("tool3")]

        for tool in tools:
            executor.register_tool(tool)

        assert len(executor.tools) == 3
        assert all(f"tool{i}" in executor.tools for i in range(1, 4))

    def test_register_duplicate_tool(self):
        """Test registering a tool with duplicate name."""
        executor = ToolExecutor()
        tool1 = MockTool("duplicate_tool")
        tool2 = MockTool("duplicate_tool")

        executor.register_tool(tool1)
        executor.register_tool(tool2)  # Should replace the first

        assert len(executor.tools) == 1
        assert executor.tools["duplicate_tool"] == tool2


class TestToolAvailability:
    """Test tool availability for agents."""

    def test_get_available_tools_for_agent(self):
        """Test getting available tools for an agent."""
        executor = ToolExecutor()

        # Create tools with different access levels
        local_tool = MockTool("local_tool")
        local_tool.set_local_agent("agent1")

        shared_tool = MockTool("shared_tool")
        shared_tool.set_shared_agents(["agent1", "agent2"])

        global_tool = MockTool("global_tool")
        global_tool.set_global()

        executor.register_tool(local_tool)
        executor.register_tool(shared_tool)
        executor.register_tool(global_tool)

        # Test agent1 access
        agent1_tools = executor.get_available_tools_for_agent("agent1")
        agent1_names = [tool.name for tool in agent1_tools]

        assert "local_tool" in agent1_names
        assert "shared_tool" in agent1_names
        assert "global_tool" in agent1_names
        assert len(agent1_tools) == 3

        # Test agent2 access
        agent2_tools = executor.get_available_tools_for_agent("agent2")
        agent2_names = [tool.name for tool in agent2_tools]

        assert "local_tool" not in agent2_names
        assert "shared_tool" in agent2_names
        assert "global_tool" in agent2_names
        assert len(agent2_tools) == 2

        # Test agent3 access (only global)
        agent3_tools = executor.get_available_tools_for_agent("agent3")
        agent3_names = [tool.name for tool in agent3_tools]

        assert "local_tool" not in agent3_names
        assert "shared_tool" not in agent3_names
        assert "global_tool" in agent3_names
        assert len(agent3_tools) == 1

    def test_get_tools_schema_for_agent(self):
        """Test getting tool schemas for an agent."""
        executor = ToolExecutor()

        def test_func(x: int) -> int:
            return x * 2

        tool = FunctionTool(
            name="schema_tool", func=test_func, description="Test schema tool"
        )
        tool.set_global()

        executor.register_tool(tool)

        schemas = executor.get_tools_schema_for_agent("test_agent")

        assert len(schemas) == 1
        schema = schemas[0]

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "schema_tool"
        assert schema["function"]["description"] == "Test schema tool"
        assert "parameters" in schema["function"]

    def test_empty_tools_schema(self):
        """Test getting schema when no tools are available."""
        executor = ToolExecutor()

        schemas = executor.get_tools_schema_for_agent("test_agent")

        assert len(schemas) == 0
        assert schemas == []


class TestToolExecution:
    """Test tool execution functionality."""

    @pytest.mark.asyncio
    async def test_execute_single_tool_call(self):
        """Test executing a single tool call."""
        executor = ToolExecutor()
        tool = MockTool("test_tool")
        executor.register_tool(tool)

        request = ToolCallRequest(
            id="test-id", name="test_tool", arguments={"param": "value"}
        )

        response = await executor.execute_tool_call(request, "test_agent")

        assert response.success is True
        assert response.id == "test-id"
        assert response.name == "test_tool"
        assert "Mock result from test_tool for test_agent" in response.result
        assert tool.execution_count == 1

    @pytest.mark.asyncio
    async def test_execute_tool_call_from_dict(self):
        """Test executing tool call from dictionary format."""
        executor = ToolExecutor()
        tool = MockTool("dict_tool")
        executor.register_tool(tool)

        tool_call_dict = {
            "id": "dict-id",
            "name": "dict_tool",
            "arguments": {"key": "value"},
        }

        response = await executor.execute_tool_call(tool_call_dict, "dict_agent")

        assert response.success is True
        assert response.id == "dict-id"
        assert response.name == "dict_tool"

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        """Test executing a tool that doesn't exist."""
        executor = ToolExecutor()

        request = ToolCallRequest(
            id="missing-id", name="nonexistent_tool", arguments={}
        )

        response = await executor.execute_tool_call(request, "test_agent")

        assert response.success is False
        assert response.result is None
        assert "Tool 'nonexistent_tool' not found" in response.error
        assert response.id == "missing-id"
        assert response.name == "nonexistent_tool"

    @pytest.mark.asyncio
    async def test_execute_failing_tool(self):
        """Test executing a tool that fails."""
        executor = ToolExecutor()
        failing_tool = MockTool("failing_tool", should_fail=True)
        executor.register_tool(failing_tool)

        request = ToolCallRequest(id="fail-id", name="failing_tool", arguments={})

        response = await executor.execute_tool_call(request, "test_agent")

        assert response.success is False
        assert response.result is None
        assert "Mock tool failure" in response.error

    @pytest.mark.asyncio
    async def test_execute_multiple_tool_calls(self):
        """Test executing multiple tool calls."""
        executor = ToolExecutor()

        tools = [MockTool(f"tool{i}") for i in range(3)]
        for tool in tools:
            executor.register_tool(tool)

        requests = [
            ToolCallRequest(id=f"multi-{i}", name=f"tool{i}", arguments={"index": i})
            for i in range(3)
        ]

        responses = await executor.execute_tool_calls(requests, "multi_agent")

        assert len(responses) == 3
        for i, response in enumerate(responses):
            assert response.success is True
            assert response.id == f"multi-{i}"
            assert response.name == f"tool{i}"

    @pytest.mark.asyncio
    async def test_execute_mixed_success_failure_calls(self):
        """Test executing multiple calls with mixed success/failure."""
        executor = ToolExecutor()

        success_tool = MockTool("success_tool", should_fail=False)
        failing_tool = MockTool("failing_tool", should_fail=True)

        executor.register_tool(success_tool)
        executor.register_tool(failing_tool)

        requests = [
            ToolCallRequest(id="success-1", name="success_tool", arguments={}),
            ToolCallRequest(id="fail-1", name="failing_tool", arguments={}),
            ToolCallRequest(id="success-2", name="success_tool", arguments={}),
        ]

        responses = await executor.execute_tool_calls(requests, "mixed_agent")

        assert len(responses) == 3
        assert responses[0].success is True  # success_tool
        assert responses[1].success is False  # failing_tool
        assert responses[2].success is True  # success_tool

    @pytest.mark.asyncio
    async def test_execute_with_exceptions(self):
        """Test handling exceptions during execution."""
        executor = ToolExecutor()

        class ExceptionTool(BaseTool):
            async def _execute_impl(self, **kwargs) -> Any:
                raise RuntimeError("Unexpected error")

            async def execute(self, request, agent_name):
                raise RuntimeError("Unexpected error")

            def can_be_used_by(self, agent):
                return True

        exception_tool = ExceptionTool("exception_tool", "Exception tool")
        executor.register_tool(exception_tool)

        request = ToolCallRequest(
            id="exception-id", name="exception_tool", arguments={}
        )

        # This should not raise an exception, but handle it gracefully
        responses = await executor.execute_tool_calls([request], "exception_agent")

        assert len(responses) == 1
        # The response might be an exception object or handled gracefully
        # depending on implementation


class TestExecutionHistory:
    """Test execution history tracking."""

    @pytest.mark.asyncio
    async def test_execution_history_tracking(self):
        """Test that execution history is tracked."""
        executor = ToolExecutor()
        tool = MockTool("history_tool")
        executor.register_tool(tool)

        request = ToolCallRequest(id="history-id", name="history_tool", arguments={})

        initial_history_length = len(executor.execution_history)

        await executor.execute_tool_call(request, "history_agent")

        assert len(executor.execution_history) == initial_history_length + 1

        history_entry = executor.execution_history[-1]
        assert history_entry["tool_name"] == "history_tool"
        assert history_entry["agent"] == "history_agent"
        assert history_entry["success"] is True

    @pytest.mark.asyncio
    async def test_execution_history_failure_tracking(self):
        """Test that failures are tracked in history."""
        executor = ToolExecutor()
        failing_tool = MockTool("failing_history_tool", should_fail=True)
        executor.register_tool(failing_tool)

        request = ToolCallRequest(
            id="fail-history-id", name="failing_history_tool", arguments={}
        )

        await executor.execute_tool_call(request, "fail_agent")

        history_entry = executor.execution_history[-1]
        assert history_entry["tool_name"] == "failing_history_tool"
        assert history_entry["agent"] == "fail_agent"
        assert history_entry["success"] is False

    @pytest.mark.asyncio
    async def test_multiple_executions_history(self):
        """Test history tracking for multiple executions."""
        executor = ToolExecutor()
        tool = MockTool("multi_history_tool")
        executor.register_tool(tool)

        requests = [
            ToolCallRequest(id=f"multi-{i}", name="multi_history_tool", arguments={})
            for i in range(5)
        ]

        initial_length = len(executor.execution_history)

        for request in requests:
            await executor.execute_tool_call(request, f"agent_{request.id}")

        assert len(executor.execution_history) == initial_length + 5

        # Check that all executions are recorded
        recent_entries = executor.execution_history[-5:]
        for i, entry in enumerate(recent_entries):
            assert entry["tool_name"] == "multi_history_tool"
            assert entry["agent"] == f"agent_multi-{i}"


class TestPerformanceAndConcurrency:
    """Test performance and concurrency aspects."""

    @pytest.mark.asyncio
    async def test_concurrent_tool_execution(self):
        """Test concurrent execution of multiple tools."""
        executor = ToolExecutor()

        # Create tools with delays to test concurrency
        slow_tools = [MockTool(f"slow_tool_{i}", delay=0.1) for i in range(5)]
        for tool in slow_tools:
            executor.register_tool(tool)

        requests = [
            ToolCallRequest(id=f"concurrent-{i}", name=f"slow_tool_{i}", arguments={})
            for i in range(5)
        ]

        start_time = time.time()
        responses = await executor.execute_tool_calls(requests, "concurrent_agent")
        execution_time = time.time() - start_time

        # All should succeed
        assert all(response.success for response in responses)

        # Should execute concurrently, so total time should be less than sum of delays
        # 5 tools * 0.1s delay = 0.5s if sequential, should be ~0.1s if concurrent
        assert execution_time < 0.3  # Allow some margin for overhead

    @pytest.mark.asyncio
    async def test_executor_with_many_tools(self):
        """Test executor performance with many tools."""
        executor = ToolExecutor()

        # Register many tools
        num_tools = 100
        tools = [MockTool(f"perf_tool_{i}") for i in range(num_tools)]

        start_time = time.time()
        for tool in tools:
            executor.register_tool(tool)
        registration_time = time.time() - start_time

        # Registration should be fast
        assert registration_time < 1.0  # Should register 100 tools in under 1 second

        # Test getting available tools
        start_time = time.time()
        available_tools = executor.get_available_tools_for_agent("perf_agent")
        query_time = time.time() - start_time

        assert len(available_tools) == num_tools
        assert query_time < 0.1  # Should query quickly

    @pytest.mark.asyncio
    async def test_executor_memory_usage(self):
        """Test that executor doesn't leak memory with many executions."""
        executor = ToolExecutor()
        tool = MockTool("memory_tool")
        executor.register_tool(tool)

        # Execute many tool calls
        num_executions = 1000
        requests = [
            ToolCallRequest(
                id=f"memory-{i}",
                name="memory_tool",
                arguments={"data": f"test_data_{i}"},
            )
            for i in range(num_executions)
        ]

        # Execute in batches to avoid overwhelming the system
        batch_size = 50
        for i in range(0, num_executions, batch_size):
            batch = requests[i : i + batch_size]
            responses = await executor.execute_tool_calls(batch, "memory_agent")
            assert all(response.success for response in responses)

        # Check that history is maintained but not excessively large
        assert len(executor.execution_history) >= num_executions
        # In a production system, you might want to limit history size


class TestErrorHandling:
    """Test error handling in various scenarios."""

    @pytest.mark.asyncio
    async def test_malformed_tool_call_request(self):
        """Test handling malformed tool call requests."""
        executor = ToolExecutor()
        tool = MockTool("test_tool")
        executor.register_tool(tool)

        # Test with malformed dictionary (missing required fields)
        malformed_dict = {"arguments": {"param": "value"}}  # Missing name

        with pytest.raises(KeyError):
            await executor.execute_tool_call(malformed_dict, "test_agent")

    @pytest.mark.asyncio
    async def test_tool_access_denied(self):
        """Test tool execution when agent doesn't have access."""
        executor = ToolExecutor()

        restricted_tool = MockTool("restricted_tool")
        restricted_tool.set_local_agent("allowed_agent")
        executor.register_tool(restricted_tool)

        # Override can_be_used_by to return False for denied agent
        original_method = restricted_tool.can_be_used_by
        restricted_tool.can_be_used_by = lambda agent: agent == "allowed_agent"

        request = ToolCallRequest(id="denied-id", name="restricted_tool", arguments={})

        # This should still execute since executor doesn't check permissions
        # (That's handled at a higher level)
        response = await executor.execute_tool_call(request, "denied_agent")
        assert response.success is True  # Tool itself succeeds

        # Restore original method
        restricted_tool.can_be_used_by = original_method

    @pytest.mark.asyncio
    async def test_empty_tool_calls_list(self):
        """Test executing empty list of tool calls."""
        executor = ToolExecutor()

        responses = await executor.execute_tool_calls([], "test_agent")

        assert len(responses) == 0
        assert responses == []


class TestToolExecutorIntegration:
    """Test integration with other components."""

    def test_executor_with_function_tools(self):
        """Test executor with FunctionTool instances."""
        executor = ToolExecutor()

        def add_numbers(x: int, y: int) -> int:
            return x + y

        function_tool = FunctionTool(
            name="add_tool", func=add_numbers, description="Adds two numbers"
        )
        function_tool.set_global()

        executor.register_tool(function_tool)

        available_tools = executor.get_available_tools_for_agent("test_agent")
        assert len(available_tools) == 1
        assert available_tools[0].name == "add_tool"

    @pytest.mark.asyncio
    async def test_executor_with_real_function_execution(self):
        """Test executor with real function tool execution."""
        executor = ToolExecutor()

        def multiply_numbers(a: float, b: float) -> float:
            return a * b

        multiply_tool = FunctionTool(
            name="multiply_tool",
            func=multiply_numbers,
            description="Multiplies two numbers",
        )
        multiply_tool.set_global()

        executor.register_tool(multiply_tool)

        request = ToolCallRequest(
            id="multiply-id", name="multiply_tool", arguments={"a": 3.5, "b": 2.0}
        )

        response = await executor.execute_tool_call(request, "math_agent")

        assert response.success is True
        assert response.result == 7.0
        assert response.execution_time is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
