"""
Comprehensive test suite for Tool functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from multiagenticswarm.core.tool import Tool, ToolConfig, ToolScope, create_logger_tool, create_memory_tool
from multiagenticswarm.core.agent import Agent


class TestToolCreation:
    """Test tool creation and initialization."""
    
    def test_basic_tool_creation(self):
        """Test creating tool with minimal parameters."""
        tool = Tool(name="BasicTool")
        
        assert tool.name == "BasicTool"
        assert tool.func is None
        assert tool.description == ""
        assert tool.parameters == {}
        assert tool.scope == ToolScope.LOCAL
        assert tool.id is not None
        assert tool.usage_count == 0
        assert tool.last_used_by is None
    
    def test_full_tool_creation(self):
        """Test creating tool with all parameters."""
        def sample_func(x: int, y: int) -> int:
            return x + y
        
        parameters = {
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"}
            },
            "required": ["x", "y"]
        }
        
        tool = Tool(
            name="FullTool",
            func=sample_func,
            description="Adds two numbers",
            parameters=parameters,
            tool_id="custom-tool-id"
        )
        
        assert tool.name == "FullTool"
        assert tool.func == sample_func
        assert tool.description == "Adds two numbers"
        assert tool.parameters == parameters
        assert tool.id == "custom-tool-id"
    
    def test_tool_from_config(self):
        """Test creating tool from ToolConfig."""
        config = ToolConfig(
            name="ConfigTool",
            description="Tool from config",
            scope=ToolScope.SHARED,
            agents=["Agent1", "Agent2"],
            parameters={"param1": "value1"}
        )
        
        def dummy_func():
            return "result"
        
        tool = Tool.from_config(config, func=dummy_func)
        
        assert tool.name == "ConfigTool"
        assert tool.description == "Tool from config"
        assert tool.scope == ToolScope.SHARED
        assert tool.shared_agents == ["Agent1", "Agent2"]
        assert tool.parameters == {"param1": "value1"}
        assert tool.func == dummy_func


class TestToolSharing:
    """Test tool sharing mechanisms."""
    
    def test_local_tool_sharing(self):
        """Test local tool access control."""
        tool = Tool(name="LocalTool")
        agent1 = Agent(name="Agent1")
        agent2 = Agent(name="Agent2")
        
        # Set tool as local to agent1
        tool.set_local(agent1)
        
        assert tool.scope == ToolScope.LOCAL
        assert tool.local_agent == "Agent1"
        assert tool.shared_agents == []
        assert tool.is_global == False
        
        # Check access
        assert tool.can_be_used_by(agent1) == True
        assert tool.can_be_used_by(agent2) == False
        assert tool.can_be_used_by("Agent1") == True
        assert tool.can_be_used_by("Agent2") == False
    
    def test_shared_tool_sharing(self):
        """Test shared tool access control."""
        tool = Tool(name="SharedTool")
        agent1 = Agent(name="Agent1")
        agent2 = Agent(name="Agent2")
        agent3 = Agent(name="Agent3")
        
        # Set tool as shared between agent1 and agent2
        tool.set_shared(agent1, agent2)
        
        assert tool.scope == ToolScope.SHARED
        assert tool.local_agent is None
        assert set(tool.shared_agents) == {"Agent1", "Agent2"}
        assert tool.is_global == False
        
        # Check access
        assert tool.can_be_used_by(agent1) == True
        assert tool.can_be_used_by(agent2) == True
        assert tool.can_be_used_by(agent3) == False
    
    def test_global_tool_sharing(self):
        """Test global tool access control."""
        tool = Tool(name="GlobalTool")
        agent1 = Agent(name="Agent1")
        agent2 = Agent(name="Agent2")
        agent3 = Agent(name="Agent3")
        
        # Set tool as global
        tool.set_global()
        
        assert tool.scope == ToolScope.GLOBAL
        assert tool.local_agent is None
        assert tool.shared_agents == []
        assert tool.is_global == True
        
        # Check access - all agents should have access
        assert tool.can_be_used_by(agent1) == True
        assert tool.can_be_used_by(agent2) == True
        assert tool.can_be_used_by(agent3) == True
        assert tool.can_be_used_by("AnyAgent") == True
    
    def test_sharing_transitions(self):
        """Test transitioning between sharing modes."""
        tool = Tool(name="TransitionTool")
        agent1 = Agent(name="Agent1")
        agent2 = Agent(name="Agent2")
        
        # Start as local
        tool.set_local(agent1)
        assert tool.scope == ToolScope.LOCAL
        assert tool.can_be_used_by(agent1) == True
        assert tool.can_be_used_by(agent2) == False
        
        # Change to shared
        tool.set_shared(agent1, agent2)
        assert tool.scope == ToolScope.SHARED
        assert tool.local_agent is None
        assert tool.can_be_used_by(agent1) == True
        assert tool.can_be_used_by(agent2) == True
        
        # Change to global
        tool.set_global()
        assert tool.scope == ToolScope.GLOBAL
        assert tool.shared_agents == []
        assert tool.can_be_used_by("AnyAgent") == True
        
        # Back to local
        tool.set_local(agent2)
        assert tool.scope == ToolScope.LOCAL
        assert tool.local_agent == "Agent2"
        assert tool.can_be_used_by(agent1) == False
        assert tool.can_be_used_by(agent2) == True
    
    def test_method_chaining(self):
        """Test that sharing methods return self for chaining."""
        tool = Tool(name="ChainTool")
        agent = Agent(name="Agent")
        
        # Test chaining
        result = tool.set_local(agent)
        assert result == tool
        
        result = tool.set_shared(agent)
        assert result == tool
        
        result = tool.set_global()
        assert result == tool


class TestToolExecution:
    """Test tool execution functionality."""
    
    @pytest.mark.asyncio
    async def test_basic_execution(self):
        """Test basic tool execution."""
        def add(x: int, y: int) -> int:
            return x + y
        
        tool = Tool(name="AddTool", func=add)
        agent = Agent(name="Agent1")
        tool.set_local(agent)
        
        result = await tool.execute(agent, 5, 7)
        
        assert result["success"] == True
        assert result["result"] == 12
        assert result["tool_name"] == "AddTool"
        assert result["agent"] == "Agent1"
        assert tool.usage_count == 1
        assert tool.last_used_by == "Agent1"
        assert "metadata" in result
        assert result["metadata"]["usage_count"] == 1
    
    @pytest.mark.asyncio
    async def test_execution_with_kwargs(self):
        """Test tool execution with keyword arguments."""
        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"
        
        tool = Tool(name="GreetTool", func=greet)
        tool.set_global()
        agent = Agent(name="GreeterAgent")
        
        result = await tool.execute(agent, name="Alice", greeting="Hi")
        
        assert result["success"] == True
        assert result["result"] == "Hi, Alice!"
        
        # Test with default argument
        result2 = await tool.execute(agent, name="Bob")
        assert result2["result"] == "Hello, Bob!"
    
    @pytest.mark.asyncio
    async def test_async_function_execution(self):
        """Test execution of async functions."""
        async def async_fetch(url: str) -> str:
            await asyncio.sleep(0.1)  # Simulate async operation
            return f"Fetched from {url}"
        
        tool = Tool(name="AsyncTool", func=async_fetch)
        tool.set_global()
        agent = Agent(name="AsyncAgent")
        
        result = await tool.execute(agent, "https://example.com")
        
        assert result["success"] == True
        assert result["result"] == "Fetched from https://example.com"
        assert tool.usage_count == 1
    
    @pytest.mark.asyncio
    async def test_execution_permission_denied(self):
        """Test execution when agent doesn't have permission."""
        tool = Tool(name="RestrictedTool", func=lambda: "secret")
        agent1 = Agent(name="Agent1")
        agent2 = Agent(name="Agent2")
        
        # Set tool local to agent1
        tool.set_local(agent1)
        
        # Try to execute with agent2
        result = await tool.execute(agent2)
        
        assert result["success"] == False
        assert "permission" in result["error"].lower()
        assert result["result"] is None
        assert tool.usage_count == 0  # Should not increment on failure
    
    @pytest.mark.asyncio
    async def test_execution_no_function(self):
        """Test execution when tool has no function defined."""
        tool = Tool(name="NoFuncTool")
        agent = Agent(name="Agent")
        tool.set_global()
        
        result = await tool.execute(agent)
        
        assert result["success"] == False
        assert "no function defined" in result["error"].lower()
        assert result["result"] is None
    
    @pytest.mark.asyncio
    async def test_execution_function_error(self):
        """Test execution when function raises an error."""
        def faulty_func():
            raise ValueError("Something went wrong")
        
        tool = Tool(name="FaultyTool", func=faulty_func)
        tool.set_global()
        agent = Agent(name="Agent")
        
        result = await tool.execute(agent)
        
        assert result["success"] == False
        assert "Something went wrong" in result["error"]
        assert result["result"] is None
        assert len(tool.execution_history) == 1
        assert tool.execution_history[0]["success"] == False
    
    @pytest.mark.asyncio
    async def test_execution_history(self):
        """Test that execution history is maintained."""
        call_count = 0
        
        def counter():
            nonlocal call_count
            call_count += 1
            return call_count
        
        tool = Tool(name="CounterTool", func=counter)
        tool.set_global()
        agent1 = Agent(name="Agent1")
        agent2 = Agent(name="Agent2")
        
        # Execute multiple times
        await tool.execute(agent1)
        await tool.execute(agent2)
        await tool.execute(agent1)
        
        assert tool.usage_count == 3
        assert tool.last_used_by == "Agent1"
        assert len(tool.execution_history) == 3
        
        # Check history details
        assert tool.execution_history[0]["agent"] == "Agent1"
        assert tool.execution_history[1]["agent"] == "Agent2"
        assert tool.execution_history[2]["agent"] == "Agent1"
        
        # All should be successful
        assert all(h["success"] for h in tool.execution_history)


class TestToolSerialization:
    """Test tool serialization and deserialization."""
    
    def test_tool_to_dict(self):
        """Test converting tool to dictionary."""
        def sample_func():
            return "result"
        
        tool = Tool(
            name="SerializeTool",
            func=sample_func,
            description="Test serialization",
            parameters={"param": "value"}
        )
        
        # Set up some state
        tool.set_shared("Agent1", "Agent2")
        tool.usage_count = 5
        tool.last_used_by = "Agent1"
        
        tool_dict = tool.to_dict()
        
        assert tool_dict["name"] == "SerializeTool"
        assert tool_dict["description"] == "Test serialization"
        assert tool_dict["parameters"] == {"param": "value"}
        assert tool_dict["scope"] == "shared"
        assert tool_dict["shared_agents"] == ["Agent1", "Agent2"]
        assert tool_dict["usage_count"] == 5
        assert tool_dict["last_used_by"] == "Agent1"
        assert "id" in tool_dict
    
    def test_tool_from_dict(self):
        """Test creating tool from dictionary."""
        def new_func():
            return "new result"
        
        tool_dict = {
            "id": "test-tool-id",
            "name": "DictTool",
            "description": "From dictionary",
            "parameters": {"type": "object"},
            "scope": "global",
            "is_global": True,
            "usage_count": 10,
            "last_used_by": "SomeAgent"
        }
        
        tool = Tool.from_dict(tool_dict, func=new_func)
        
        assert tool.id == "test-tool-id"
        assert tool.name == "DictTool"
        assert tool.description == "From dictionary"
        assert tool.parameters == {"type": "object"}
        assert tool.scope == ToolScope.GLOBAL
        assert tool.is_global == True
        assert tool.usage_count == 10
        assert tool.last_used_by == "SomeAgent"
        assert tool.func == new_func
    
    def test_serialization_roundtrip(self):
        """Test full serialization roundtrip."""
        def original_func(x: int) -> int:
            return x * 2
        
        original_tool = Tool(
            name="RoundtripTool",
            func=original_func,
            description="Test roundtrip",
            parameters={"x": {"type": "integer"}}
        )
        
        # Set some state
        original_tool.set_shared("A1", "A2", "A3")
        original_tool.usage_count = 7
        original_tool.last_used_by = "A2"
        
        # Serialize and deserialize
        tool_dict = original_tool.to_dict()
        restored_tool = Tool.from_dict(tool_dict, func=original_func)
        
        # Compare attributes
        assert restored_tool.name == original_tool.name
        assert restored_tool.description == original_tool.description
        assert restored_tool.parameters == original_tool.parameters
        assert restored_tool.scope == original_tool.scope
        assert restored_tool.shared_agents == original_tool.shared_agents
        assert restored_tool.usage_count == original_tool.usage_count
        assert restored_tool.last_used_by == original_tool.last_used_by


class TestToolSchema:
    """Test tool schema generation."""
    
    def test_get_schema(self):
        """Test getting tool schema."""
        parameters = {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The message to process"
                }
            },
            "required": ["message"]
        }
        
        tool = Tool(
            name="MessageTool",
            description="Process messages",
            parameters=parameters
        )
        
        schema = tool.get_schema()
        
        assert schema["name"] == "MessageTool"
        assert schema["description"] == "Process messages"
        assert schema["parameters"] == parameters
        assert schema["scope"] == "local"
        assert schema["usage_count"] == 0
    
    def test_schema_after_usage(self):
        """Test schema includes usage information."""
        tool = Tool(name="UsedTool")
        tool.usage_count = 25
        
        schema = tool.get_schema()
        
        assert schema["usage_count"] == 25


class TestBuiltinTools:
    """Test built-in tool factories."""
    
    def test_create_logger_tool(self):
        """Test creating the built-in logger tool."""
        logger_tool = create_logger_tool()
        
        assert logger_tool.name == "Logger"
        assert logger_tool.is_global == True
        assert logger_tool.scope == ToolScope.GLOBAL
        assert "log messages" in logger_tool.description.lower()
        assert logger_tool.func is not None
        
        # Test the function
        result = logger_tool.func("Test message", "info")
        assert "Logged: Test message" in result
    
    def test_create_memory_tool(self):
        """Test creating the built-in memory tool."""
        memory_tool = create_memory_tool()
        
        assert memory_tool.name == "StoreMemory"
        assert memory_tool.is_global == True
        assert memory_tool.scope == ToolScope.GLOBAL
        assert "store" in memory_tool.description.lower()
        assert memory_tool.func is not None
        
        # Test the function
        result = memory_tool.func("test_key", "test_value")
        assert "Stored 'test_key': test_value" in result
    
    @pytest.mark.asyncio
    async def test_logger_tool_execution(self):
        """Test executing the logger tool."""
        logger_tool = create_logger_tool()
        agent = Agent(name="LoggerUser")
        
        result = await logger_tool.execute(
            agent,
            message="Important event",
            level="warning"
        )
        
        assert result["success"] == True
        assert "Logged: Important event" in result["result"]
    
    @pytest.mark.asyncio
    async def test_memory_tool_execution(self):
        """Test executing the memory tool."""
        memory_tool = create_memory_tool()
        agent = Agent(name="MemoryUser")
        
        # Store a value
        result = await memory_tool.execute(
            agent,
            key="user_preference",
            value="dark_mode"
        )
        
        assert result["success"] == True
        assert "Stored 'user_preference': dark_mode" in result["result"]


class TestToolEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_tool_with_empty_name(self):
        """Test creating tool with empty name."""
        tool = Tool(name="")
        assert tool.name == ""
        # Should still work, though not recommended
    
    def test_tool_with_special_characters(self):
        """Test tool with special characters in name."""
        tool = Tool(name="Tool@#$%_123-Test")
        assert tool.name == "Tool@#$%_123-Test"
    
    def test_tool_repr(self):
        """Test tool string representation."""
        tool = Tool(name="ReprTool")
        tool.set_shared("A1", "A2")
        
        repr_str = repr(tool)
        assert "ReprTool" in repr_str
        assert "shared" in repr_str
    
    @pytest.mark.asyncio
    async def test_execution_with_none_agent(self):
        """Test execution with None as agent."""
        tool = Tool(name="NullAgentTool", func=lambda: "result")
        tool.set_global()
        
        # Using string "None" as agent name
        result = await tool.execute("None")
        assert result["success"] == True
        assert result["agent"] == "None"
    
    def test_tool_without_pydantic(self):
        """Test that tool works without pydantic installed."""
        # This would require mocking the pydantic import
        # For now, just verify the fallback config class works
        from multiagenticswarm.core.tool import ToolConfig
        
        config = ToolConfig(
            name="NoPydanticTool",
            description="Test without pydantic"
        )
        
        assert hasattr(config, 'name')
        assert hasattr(config, 'description')
    
    @pytest.mark.asyncio
    async def test_execution_with_complex_return_types(self):
        """Test tool execution with various return types."""
        # Dictionary return
        dict_tool = Tool(name="DictTool", func=lambda: {"key": "value", "nested": {"a": 1}})
        dict_tool.set_global()
        result = await dict_tool.execute("Agent")
        assert result["success"] == True
        assert isinstance(result["result"], dict)
        
        # List return
        list_tool = Tool(name="ListTool", func=lambda: [1, 2, 3, 4, 5])
        list_tool.set_global()
        result = await list_tool.execute("Agent")
        assert result["success"] == True
        assert isinstance(result["result"], list)
        
        # None return
        none_tool = Tool(name="NoneTool", func=lambda: None)
        none_tool.set_global()
        result = await none_tool.execute("Agent")
        assert result["success"] == True
        assert result["result"] is None
    
    @pytest.mark.asyncio
    async def test_concurrent_executions(self):
        """Test concurrent tool executions."""
        counter = 0
        
        async def slow_increment():
            nonlocal counter
            await asyncio.sleep(0.1)
            counter += 1
            return counter
        
        tool = Tool(name="ConcurrentTool", func=slow_increment)
        tool.set_global()
        
        # Execute concurrently
        results = await asyncio.gather(
            tool.execute("Agent1"),
            tool.execute("Agent2"),
            tool.execute("Agent3")
        )
        
        assert len(results) == 3
        assert all(r["success"] for r in results)
        assert tool.usage_count == 3
        assert counter == 3


class TestToolIntegration:
    """Integration tests with other components."""
    
    @pytest.mark.asyncio
    async def test_tool_with_agent_context(self):
        """Test tool that uses agent context."""
        def context_aware_tool(agent_name: str, **kwargs) -> str:
            return f"Hello from {agent_name}"
        
        tool = Tool(name="ContextTool", func=context_aware_tool)
        tool.set_global()
        
        agent = Agent(name="ContextAgent")
        
        # The tool receives the agent name through execute
        result = await tool.execute(agent, agent_name="ContextAgent")
        
        assert result["success"] == True
        assert result["result"] == "Hello from ContextAgent"
    
    def test_tool_permission_updates(self):
        """Test that tool permissions update correctly."""
        tool = Tool(name="PermTool")
        agent1 = Agent(name="Agent1") 
        agent2 = Agent(name="Agent2")
        agent3 = Agent(name="Agent3")
        
        # Start with no access
        assert not tool.can_be_used_by(agent1)
        assert not tool.can_be_used_by(agent2)
        assert not tool.can_be_used_by(agent3)
        
        # Give access to agent1
        tool.set_local(agent1)
        assert tool.can_be_used_by(agent1)
        assert not tool.can_be_used_by(agent2)
        assert not tool.can_be_used_by(agent3)
        
        # Share with agent2
        tool.set_shared(agent1, agent2)
        assert tool.can_be_used_by(agent1)
        assert tool.can_be_used_by(agent2)
        assert not tool.can_be_used_by(agent3)
        
        # Make global
        tool.set_global()
        assert tool.can_be_used_by(agent1)
        assert tool.can_be_used_by(agent2)
        assert tool.can_be_used_by(agent3)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
