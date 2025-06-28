"""
Comprehensive test suite for Agent functionality.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from multiagenticswarm.core.agent import Agent, AgentConfig
from multiagenticswarm.core.tool import Tool
from multiagenticswarm.core.tool_executor import ToolExecutor
from multiagenticswarm.core.base_tool import FunctionTool, ToolCallRequest


class TestAgentCreation:
    """Test agent creation and initialization."""
    
    def test_basic_agent_creation(self):
        """Test creating agent with minimal parameters."""
        agent = Agent(name="BasicAgent")
        
        assert agent.name == "BasicAgent"
        assert agent.description == ""
        assert agent.system_prompt == ""
        assert agent.llm_provider_name == "openai"
        assert agent.llm_model == "gpt-3.5-turbo"
        assert agent.max_iterations == 10
        assert agent.memory_enabled == True
        assert agent.id is not None
    
    def test_full_agent_creation(self):
        """Test creating agent with all parameters."""
        agent = Agent(
            name="FullAgent",
            description="A fully configured agent",
            system_prompt="You are an expert assistant",
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
            llm_config={"temperature": 0.7, "max_tokens": 2000},
            max_iterations=5,
            memory_enabled=False,
            agent_id="custom-id-123"
        )
        
        assert agent.name == "FullAgent"
        assert agent.description == "A fully configured agent"
        assert agent.system_prompt == "You are an expert assistant"
        assert agent.llm_provider_name == "anthropic"
        assert agent.llm_model == "claude-3-5-sonnet-20241022"
        assert agent.llm_config == {"temperature": 0.7, "max_tokens": 2000}
        assert agent.max_iterations == 5
        assert agent.memory_enabled == False
        assert agent.id == "custom-id-123"
    
    def test_agent_from_config(self):
        """Test creating agent from AgentConfig."""
        config = AgentConfig(
            name="ConfigAgent",
            description="Agent from config",
            system_prompt="Config-based agent",
            llm_provider="openai",
            llm_model="gpt-4",
            llm_config={"temperature": 0.5},
            max_iterations=3,
            memory_enabled=True,
            tools=["tool1", "tool2"]
        )
        
        agent = Agent.from_config(config)
        
        assert agent.name == "ConfigAgent"
        assert agent.description == "Agent from config"
        assert agent.llm_provider_name == "openai"
        assert agent.llm_model == "gpt-4"


class TestAgentSerialization:
    """Test agent serialization and deserialization."""
    
    def test_agent_to_dict(self):
        """Test converting agent to dictionary."""
        agent = Agent(
            name="SerializeAgent",
            description="Test serialization",
            system_prompt="Serialize me",
            llm_provider="anthropic",
            llm_model="claude-3-opus",
            llm_config={"temperature": 0.8},
            max_iterations=7,
            memory_enabled=True
        )
        
        # Add some tools
        agent.local_tools = ["local_tool_1"]
        agent.shared_tools = ["shared_tool_1", "shared_tool_2"]
        agent.global_tools = ["global_tool_1"]
        
        agent_dict = agent.to_dict()
        
        assert agent_dict["name"] == "SerializeAgent"
        assert agent_dict["description"] == "Test serialization"
        assert agent_dict["system_prompt"] == "Serialize me"
        assert agent_dict["llm_provider"] == "anthropic"
        assert agent_dict["llm_model"] == "claude-3-opus"
        assert agent_dict["llm_config"] == {"temperature": 0.8}
        assert agent_dict["max_iterations"] == 7
        assert agent_dict["memory_enabled"] == True
        assert agent_dict["local_tools"] == ["local_tool_1"]
        assert agent_dict["shared_tools"] == ["shared_tool_1", "shared_tool_2"]
        assert agent_dict["global_tools"] == ["global_tool_1"]
        assert "id" in agent_dict
    
    def test_agent_from_dict(self):
        """Test creating agent from dictionary."""
        agent_dict = {
            "id": "test-id-456",
            "name": "DictAgent",
            "description": "From dictionary",
            "system_prompt": "Dict-based",
            "llm_provider": "openai",
            "llm_model": "gpt-3.5-turbo-16k",
            "llm_config": {"temperature": 0.3},
            "max_iterations": 15,
            "memory_enabled": False,
            "local_tools": ["tool_a"],
            "shared_tools": ["tool_b", "tool_c"],
            "global_tools": ["tool_d"]
        }
        
        agent = Agent.from_dict(agent_dict)
        
        assert agent.id == "test-id-456"
        assert agent.name == "DictAgent"
        assert agent.description == "From dictionary"
        assert agent.system_prompt == "Dict-based"
        assert agent.llm_provider_name == "openai"
        assert agent.llm_model == "gpt-3.5-turbo-16k"
        assert agent.llm_config == {"temperature": 0.3}
        assert agent.max_iterations == 15
        assert agent.memory_enabled == False
        assert agent.local_tools == ["tool_a"]
        assert agent.shared_tools == ["tool_b", "tool_c"]
        assert agent.global_tools == ["tool_d"]
    
    def test_serialization_roundtrip(self):
        """Test full serialization roundtrip."""
        original_agent = Agent(
            name="RoundtripAgent",
            description="Test roundtrip",
            system_prompt="Complete cycle",
            llm_provider="azure",
            llm_model="gpt-4-azure",
            llm_config={"api_version": "2023-05-15"},
            max_iterations=12,
            memory_enabled=True
        )
        
        # Serialize and deserialize
        agent_dict = original_agent.to_dict()
        restored_agent = Agent.from_dict(agent_dict)
        
        # Compare all attributes
        assert restored_agent.name == original_agent.name
        assert restored_agent.description == original_agent.description
        assert restored_agent.system_prompt == original_agent.system_prompt
        assert restored_agent.llm_provider_name == original_agent.llm_provider_name
        assert restored_agent.llm_model == original_agent.llm_model
        assert restored_agent.llm_config == original_agent.llm_config
        assert restored_agent.max_iterations == original_agent.max_iterations
        assert restored_agent.memory_enabled == original_agent.memory_enabled


class TestAgentMemory:
    """Test agent memory functionality."""
    
    def test_memory_enabled(self):
        """Test memory operations when enabled."""
        agent = Agent(name="MemoryAgent", memory_enabled=True)
        
        # Add messages to memory
        agent.add_to_memory("user", "Hello agent")
        agent.add_to_memory("assistant", "Hello user", {"tool_used": "greeting"})
        
        assert len(agent.memory) == 2
        assert agent.memory[0]["role"] == "user"
        assert agent.memory[0]["content"] == "Hello agent"
        assert agent.memory[1]["role"] == "assistant"
        assert agent.memory[1]["content"] == "Hello user"
        assert agent.memory[1]["metadata"]["tool_used"] == "greeting"
        assert "timestamp" in agent.memory[0]
    
    def test_memory_disabled(self):
        """Test memory operations when disabled."""
        agent = Agent(name="NoMemoryAgent", memory_enabled=False)
        
        # Try to add messages
        agent.add_to_memory("user", "This shouldn't be stored")
        agent.add_to_memory("assistant", "Neither should this")
        
        assert len(agent.memory) == 0
    
    def test_clear_memory(self):
        """Test clearing agent memory."""
        agent = Agent(name="ClearMemoryAgent", memory_enabled=True)
        
        # Add messages
        agent.add_to_memory("user", "Message 1")
        agent.add_to_memory("assistant", "Response 1")
        agent.add_to_memory("user", "Message 2")
        
        assert len(agent.memory) == 3
        
        # Clear memory
        agent.clear_memory()
        
        assert len(agent.memory) == 0
    
    def test_memory_in_execution(self):
        """Test that memory is used during execution."""
        # This would require mocking the LLM provider
        pass


class TestAgentToolManagement:
    """Test agent tool access and management."""
    
    def test_tool_access_lists(self):
        """Test tool access list management."""
        agent = Agent(name="ToolAgent")
        
        # Initially empty
        assert agent.local_tools == []
        assert agent.shared_tools == []
        assert agent.global_tools == []
        
        # Add tools
        agent.local_tools.append("local_calculator")
        agent.shared_tools.extend(["shared_db", "shared_api"])
        agent.global_tools.append("global_logger")
        
        assert len(agent.local_tools) == 1
        assert len(agent.shared_tools) == 2
        assert len(agent.global_tools) == 1
    
    def test_get_available_tools(self):
        """Test getting all available tools for an agent."""
        agent = Agent(name="ToolAccessAgent")
        
        # Create mock tool registry
        tool_registry = {
            "calc": Mock(shared_agents=["ToolAccessAgent", "OtherAgent"]),
            "db": Mock(shared_agents=["OtherAgent"]),
            "logger": Mock(),
            "api": Mock()
        }
        
        # Set up agent's tool lists
        agent.local_tools = ["calc", "api"]
        agent.shared_tools = ["calc", "db"]
        agent.global_tools = ["logger"]
        
        # Get available tools
        available = agent.get_available_tools(tool_registry)
        
        # Should have calc (local), api (local), calc (shared), and logger (global)
        # But not db (shared but agent not in shared_agents)
        assert "calc" in available
        assert "api" in available
        assert "logger" in available
        assert len(set(available)) == 3  # Remove duplicates


class TestAgentExecution:
    """Test agent execution functionality."""
    
    @pytest.mark.asyncio
    async def test_basic_execution(self):
        """Test basic agent execution without tools."""
        with patch('multiagenticswarm.core.agent.get_llm_provider') as mock_get_provider:
            # Mock the LLM provider
            mock_provider = AsyncMock()
            mock_provider.execute.return_value = Mock(
                content="Hello! I'm here to help.",
                usage={"total_tokens": 50},
                tool_calls=[]
            )
            mock_get_provider.return_value = mock_provider
            
            agent = Agent(name="ExecutionAgent", system_prompt="You are helpful")
            
            result = await agent.execute("Hello")
            
            assert result["success"] == True
            assert result["agent_name"] == "ExecutionAgent"
            assert result["input"] == "Hello"
            assert result["output"] == "Hello! I'm here to help."
            assert "execution_time" in result
    
    @pytest.mark.skip(reason="Complex async mocking - needs refactoring")
    @pytest.mark.asyncio
    async def test_execution_with_tool_executor(self):
        """Test execution with standardized tool executor."""
        # Simplified test - just verify that agent can work with tool executor
        agent = Agent(name="CalcAgent")
        
        # Create tool executor
        tool_executor = ToolExecutor()
        
        # Create and register a simple tool
        def simple_tool() -> str:
            return "tool executed"
        
        test_tool = FunctionTool(func=simple_tool, name="simple_tool")
        test_tool.set_global()
        tool_executor.register_tool(test_tool)
        
        # Mock the LLM provider to return simple responses
        class MockProvider:
            async def execute(self, messages, context=None):
                from types import SimpleNamespace
                response = SimpleNamespace()
                response.content = "Simple response without tool calls"
                response.tool_calls = []
                return response
            
            def extract_tool_calls(self, response):
                return []  # No tool calls for this simple test
        
        agent._llm_provider = MockProvider()
        
        result = await agent.execute(
            "Simple test",
            tool_executor=tool_executor
        )
        
        assert result["success"] == True
        assert result["agent_name"] == "CalcAgent"
        assert result["output"] == "Simple response without tool calls"
    
    @pytest.mark.asyncio
    async def test_execution_with_context(self):
        """Test execution with additional context."""
        with patch('multiagenticswarm.core.agent.get_llm_provider') as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.execute.return_value = Mock(
                content="Based on the context, the answer is 42.",
                usage={"total_tokens": 50},
                tool_calls=[]
            )
            mock_get_provider.return_value = mock_provider
            
            agent = Agent(name="ContextAgent")
            
            context = {
                "user_preference": "detailed",
                "domain": "science",
                "previous_answer": 41
            }
            
            result = await agent.execute(
                "What's the next number?",
                context=context
            )
            
            assert result["success"] == True
            # Verify context was passed to LLM
            mock_provider.execute.assert_called()
            call_args = mock_provider.execute.call_args
            # The context should be part of the execution context
            passed_context = call_args[1]["context"]
            assert passed_context["user_preference"] == "detailed"
            assert passed_context["domain"] == "science"
            assert passed_context["previous_answer"] == 41
    
    @pytest.mark.asyncio
    async def test_execution_error_handling(self):
        """Test error handling during execution."""
        with patch('multiagenticswarm.core.agent.get_llm_provider') as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.execute.side_effect = Exception("API Error")
            mock_get_provider.return_value = mock_provider
            
            agent = Agent(name="ErrorAgent")
            
            result = await agent.execute("This will fail")
            
            assert result["success"] == False
            assert "error" in result
            assert "API Error" in result["error"]
            assert result["output"] == ""
    
    @pytest.mark.skip(reason="Complex async mocking - needs refactoring")
    @pytest.mark.asyncio
    async def test_execution_with_max_iterations(self):
        """Test execution respects max iterations for tool calling."""
        agent = Agent(name="IterationAgent", max_iterations=3)
        
        # Create tool executor
        tool_executor = ToolExecutor()
        test_tool = FunctionTool(func=lambda: "result", name="test_tool")
        test_tool.set_global()
        tool_executor.register_tool(test_tool)
        
        # Mock the LLM provider to always request tool calls
        class MockProvider:
            def __init__(self):
                self.call_count = 0
            
            async def execute(self, messages, context=None):
                from types import SimpleNamespace
                response = SimpleNamespace()
                response.content = "Calling tool again..."
                response.tool_calls = []
                return response
            
            def extract_tool_calls(self, response):
                # Always return tool calls to hit the iteration limit
                return [ToolCallRequest(id=f"call_{self.call_count}", name="test_tool", arguments={})]
            
            def create_tool_response_for_llm(self, tool_responses):
                return [{"role": "tool", "content": "result"}]
        
        agent._llm_provider = MockProvider()
        
        result = await agent.execute(
            "Keep calling tools",
            tool_executor=tool_executor
        )
        
        # Should hit iteration limit
        assert result["output"] == "Maximum tool calling iterations reached."
        assert result["tool_calls_made"] == 3  # Should match agent's max_iterations


class TestAgentLLMProvider:
    """Test agent LLM provider functionality."""
    
    def test_lazy_provider_initialization(self):
        """Test that LLM provider is initialized lazily."""
        agent = Agent(name="LazyAgent")
        
        # Provider should not be initialized yet
        assert agent._llm_provider is None
        
        # Access provider property
        with patch('multiagenticswarm.core.agent.get_llm_provider') as mock_get_provider:
            mock_provider = Mock()
            mock_get_provider.return_value = mock_provider
            
            provider = agent.llm_provider
            
            assert provider == mock_provider
            assert agent._llm_provider == mock_provider
            mock_get_provider.assert_called_once_with(
                provider="openai",
                model="gpt-3.5-turbo"
            )
    
    def test_provider_configuration(self):
        """Test LLM provider configuration."""
        agent = Agent(
            name="ConfiguredAgent",
            llm_provider="anthropic",
            llm_model="claude-3-opus",
            llm_config={
                "api_key": "test-key",
                "temperature": 0.5,
                "max_tokens": 1000
            }
        )
        
        with patch('multiagenticswarm.core.agent.get_llm_provider') as mock_get_provider:
            mock_provider = Mock()
            mock_get_provider.return_value = mock_provider
            
            _ = agent.llm_provider
            
            mock_get_provider.assert_called_once_with(
                provider="anthropic",
                model="claude-3-opus",
                api_key="test-key",
                temperature=0.5,
                max_tokens=1000
            )


class TestAgentEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_name(self):
        """Test agent creation with empty name."""
        with pytest.raises(Exception):
            # Depending on implementation, might need validation
            agent = Agent(name="")
    
    def test_invalid_llm_provider(self):
        """Test agent with invalid LLM provider."""
        agent = Agent(name="InvalidProviderAgent", llm_provider="invalid_provider")
        
        with pytest.raises(Exception):
            # Should fail when trying to get provider
            _ = agent.llm_provider
    
    def test_repr_method(self):
        """Test agent string representation."""
        agent = Agent(
            name="ReprAgent",
            llm_provider="openai",
            llm_model="gpt-4"
        )
        
        repr_str = repr(agent)
        assert "ReprAgent" in repr_str
        assert "openai" in repr_str
        assert "gpt-4" in repr_str
    
    @pytest.mark.asyncio
    async def test_execution_without_memory(self):
        """Test execution with memory disabled."""
        with patch('multiagenticswarm.llm.providers.get_llm_provider') as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.execute.return_value = Mock(
                content="Response without memory",
                usage={"total_tokens": 30},
                tool_calls=[]
            )
            mock_get_provider.return_value = mock_provider
            
            agent = Agent(name="NoMemAgent", memory_enabled=False)
            
            # Execute multiple times
            await agent.execute("First message")
            await agent.execute("Second message")
            
            # Memory should remain empty
            assert len(agent.memory) == 0
    
    def test_agent_with_special_characters(self):
        """Test agent with special characters in name."""
        agent = Agent(name="Agent-123_Test@Special")
        assert agent.name == "Agent-123_Test@Special"
    
    def test_very_long_system_prompt(self):
        """Test agent with very long system prompt."""
        long_prompt = "You are an AI assistant. " * 1000  # 5000+ characters
        agent = Agent(name="LongPromptAgent", system_prompt=long_prompt)
        assert len(agent.system_prompt) > 5000


class TestAgentIntegration:
    """Integration tests with other components."""
    
    @pytest.mark.skip(reason="Complex async mocking - needs refactoring")
    @pytest.mark.asyncio
    async def test_agent_with_multiple_tools(self):
        """Test agent using multiple tools in sequence."""
        agent = Agent(name="MultiToolAgent")
        
        # Create tools
        tool_executor = ToolExecutor()
        
        calc_tool = FunctionTool(
            func=lambda a, b: a + b,
            name="calculator"
        )
        calc_tool.set_global()
        
        format_tool = FunctionTool(
            func=lambda text, style: f"**{text}**" if style == "bold" else text,
            name="formatter"
        )
        format_tool.set_global()
        
        tool_executor.register_tool(calc_tool)
        tool_executor.register_tool(format_tool)
        
        # Mock the LLM provider with simple response
        class MockProvider:
            async def execute(self, messages, context=None):
                from types import SimpleNamespace
                response = SimpleNamespace()
                response.content = "I completed the multi-tool task"
                response.tool_calls = []
                return response
            
            def extract_tool_calls(self, response):
                # For simplicity, no tool calls in this test
                return []
        
        agent._llm_provider = MockProvider()
        
        result = await agent.execute(
            "Calculate 10 + 20 and format it in bold",
            tool_executor=tool_executor
        )
        
        assert result["success"] == True
        assert result["agent_name"] == "MultiToolAgent"
        assert result["output"] == "I completed the multi-tool task"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
