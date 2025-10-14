"""
Comprehensive test suite for configurable LangGraph-based Agent functionality.
"""

import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool

from multiagenticswarm.core.agent import Agent, AgentConfig
from multiagenticswarm.core.state import AgentState
from multiagenticswarm.core.agent_builder import (
    AgentWorkflowConfig, create_planning_agent_config, create_reactive_agent_config,
    create_validation_agent_config, create_simple_agent_config
)


class TestAgentSubgraphCreation:
    """Test agent creation and configurable subgraph initialization."""
    
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
        assert agent._compiled_subgraph is None  # Lazy initialization
        assert agent.workflow_config is not None
        assert agent.workflow_config.workflow_type == "default"
    
    def test_agent_with_tools(self):
        """Test creating agent with tools."""
        @tool
        def test_tool(query: str) -> str:
            """Test tool for agent."""
            return f"Result for: {query}"
        
        agent = Agent(
            name="ToolAgent",
            tools=[test_tool],
            system_prompt="You have access to tools",
            workflow_type="reactive"
        )
        
        assert len(agent.tools) == 1
        assert agent.tools[0] == test_tool
        assert agent.workflow_config.workflow_type == "reactive"
    
    def test_agent_from_config(self):
        """Test creating agent from AgentConfig."""
        config = AgentConfig(
            name="ConfigAgent",
            description="Agent from config",
            system_prompt="Config-based agent",
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
            llm_config={"temperature": 0.5},
            max_iterations=5,
            tools=["tool1", "tool2"],
            workflow_type="planning",
            enable_validator=True
        )
        
        agent = Agent.from_config(config)
        
        assert agent.name == "ConfigAgent"
        assert agent.description == "Agent from config"
        assert agent.llm_provider_name == "anthropic"
        assert agent.llm_model == "claude-3-5-sonnet-20241022"
        assert agent.max_iterations == 5
        assert agent.workflow_config.workflow_type == "planning"
        assert agent.workflow_config.enable_validator == True

    def test_agent_with_workflow_config(self):
        """Test creating agent with pre-built workflow configuration."""
        workflow_config = create_planning_agent_config()
        
        agent = Agent(
            name="PlanningAgent",
            workflow_config=workflow_config
        )
        
        assert agent.workflow_config.workflow_type == "planning"
        assert agent.workflow_config.enable_planner == True
        assert agent.workflow_config.enable_validator == True
        assert agent.workflow_config.enable_tool_coordinator == True


class TestAgentSubgraphCompilation:
    """Test agent subgraph compilation and structure."""
    
    @patch('multiagenticswarm.core.agent.build_agent_subgraph')
    @patch('multiagenticswarm.core.agent.get_llm_provider')
    def test_subgraph_compilation(self, mock_get_provider, mock_build_subgraph):
        """Test that agent compiles into proper configurable subgraph."""
        # Mock dependencies
        mock_llm = Mock()
        mock_get_provider.return_value = mock_llm
        mock_compiled_graph = Mock()
        mock_build_subgraph.return_value = mock_compiled_graph
        
        agent = Agent(name="CompileAgent", workflow_type="planning")
        
        # Get compiled subgraph
        subgraph = agent.get_compiled_subgraph()
        
        # Verify compilation was called
        mock_build_subgraph.assert_called_once()
        assert subgraph is not None
        assert agent._compiled_subgraph is not None
    
    @patch('multiagenticswarm.core.agent.build_agent_subgraph')
    @patch('multiagenticswarm.core.agent.get_llm_provider')
    def test_subgraph_lazy_compilation(self, mock_get_provider, mock_build_subgraph):
        """Test that subgraph is compiled lazily."""
        mock_llm = Mock()
        mock_get_provider.return_value = mock_llm
        mock_compiled_graph = Mock()
        mock_build_subgraph.return_value = mock_compiled_graph
        
        agent = Agent(name="LazyAgent")
        
        # Initially no compiled subgraph
        assert agent._compiled_subgraph is None
        
        # First access triggers compilation
        subgraph1 = agent.get_compiled_subgraph()
        assert agent._compiled_subgraph is not None
        
        # Second access returns same instance
        subgraph2 = agent.get_compiled_subgraph()
        assert subgraph1 is subgraph2
    
    def test_workflow_configuration_validation(self):
        """Test workflow configuration validation and setup."""
        agent = Agent(
            name="WorkflowAgent",
            workflow_type="planning",
            enable_validator=True,
            enable_tool_coordinator=False
        )
        
        # Verify workflow configuration
        assert agent.workflow_config.workflow_type == "planning"
        assert agent.workflow_config.enable_validator == True
        assert agent.workflow_config.enable_tool_coordinator == False


class TestAgentWorkflowConfigurations:
    """Test different agent workflow configurations."""
    
    def test_preset_workflow_configs(self):
        """Test preset workflow configurations."""
        # Planning agent
        planning_agent = Agent(name="PlanningAgent", workflow_config=create_planning_agent_config())
        assert planning_agent.workflow_config.workflow_type == "planning"
        assert planning_agent.workflow_config.enable_validator == True
        
        # Reactive agent
        reactive_agent = Agent(name="ReactiveAgent", workflow_config=create_reactive_agent_config())
        assert reactive_agent.workflow_config.workflow_type == "reactive"
        assert reactive_agent.workflow_config.enable_planner == False
        
        # Validation agent
        validation_agent = Agent(name="ValidationAgent", workflow_config=create_validation_agent_config())
        assert validation_agent.workflow_config.workflow_type == "validation"
        assert validation_agent.workflow_config.enable_validator == True
        
        # Simple agent
        simple_agent = Agent(name="SimpleAgent", workflow_config=create_simple_agent_config())
        assert simple_agent.workflow_config.workflow_type == "simple"
        assert simple_agent.workflow_config.enable_planner == False
    
    def test_custom_node_sequence(self):
        """Test custom node sequence configuration."""
        custom_sequence = ["input_router", "executor", "output_formatter"]
        agent = Agent(
            name="CustomAgent",
            workflow_type="custom",
            node_sequence=custom_sequence
        )
        
        assert agent.workflow_config.node_sequence == custom_sequence


class TestAgentNodeExecution:
    """Test agent execution as LangGraph node."""
    
    def test_agent_call_interface(self):
        """Test agent __call__ method interface."""
        agent = Agent(name="CallableAgent")
        
        # Create mock state
        test_state = {
            "messages": [HumanMessage(content="Test message")],
            "agent_outputs": {},
            "subgraph_states": {},
            "parent_graph_id": "test-parent-123",
            "current_agent": "",
            "execution_metadata": {}
        }
        
        # Mock the subgraph execution
        with patch.object(agent, 'get_compiled_subgraph') as mock_get_subgraph:
            mock_subgraph = Mock()
            mock_subgraph.stream.return_value = [
                {"output_formatter": {
                    "messages": [
                        HumanMessage(content="Test message"),
                        AIMessage(content="Test response")
                    ],
                    "agent_name": "CallableAgent",
                    "parent_graph_id": "test-parent-123",
                    "execution_context": {},
                    "final_response": "Test response",
                    "workflow_complete": True,
                    "tool_outputs": []
                }}
            ]
            mock_get_subgraph.return_value = mock_subgraph
            
            # Execute agent as callable
            result = agent(test_state)
            
            # Verify result structure
            assert "subgraph_states" in result
            assert "agent_outputs" in result
            assert "current_agent" in result
            assert "messages" in result
            
            assert result["current_agent"] == "CallableAgent"
            assert "CallableAgent" in result["agent_outputs"]
            assert result["agent_outputs"]["CallableAgent"]["success"] == True
    
    def test_agent_execution_error_handling(self):
        """Test error handling in agent execution."""
        agent = Agent(name="ErrorAgent")
        
        test_state = {
            "messages": [HumanMessage(content="Test message")],
            "agent_outputs": {},
            "subgraph_states": {},
            "parent_graph_id": "test-parent",
            "current_agent": "",
            "execution_metadata": {}
        }
        
        # Mock subgraph to raise exception
        with patch.object(agent, 'get_compiled_subgraph') as mock_get_subgraph:
            mock_subgraph = Mock()
            mock_subgraph.stream.side_effect = Exception("Subgraph execution failed")
            mock_get_subgraph.return_value = mock_subgraph
            
            result = agent(test_state)
            
            # Verify error handling
            assert "agent_outputs" in result
            assert "ErrorAgent" in result["agent_outputs"]
            assert result["agent_outputs"]["ErrorAgent"]["success"] == False
            assert "error" in result["agent_outputs"]["ErrorAgent"]
            assert "Subgraph execution failed" in result["agent_outputs"]["ErrorAgent"]["error"]
    
    def test_subgraph_state_management(self):
        """Test that agent maintains subgraph state in parent state."""
        agent = Agent(name="StateAgent")
        
        initial_state = {
            "messages": [HumanMessage(content="Hello")],
            "agent_outputs": {},
            "subgraph_states": {"OtherAgent": {"messages": []}},
            "parent_graph_id": "parent-123",
            "current_agent": "",
            "execution_metadata": {}
        }
        
        with patch.object(agent, 'get_compiled_subgraph') as mock_get_subgraph:
            mock_final_state = {
                "messages": [
                    HumanMessage(content="Hello"),
                    AIMessage(content="Hi there!")
                ],
                "agent_name": "StateAgent",
                "parent_graph_id": "parent-123",
                "execution_context": {},
                "tool_outputs": []
            }
            
            mock_subgraph = Mock()
            mock_subgraph.stream.return_value = [{"agent": mock_final_state}]
            mock_get_subgraph.return_value = mock_subgraph
            
            result = agent(initial_state)
            
            # Verify state preservation
            assert "StateAgent" in result["subgraph_states"]
            assert "OtherAgent" in result["subgraph_states"]  # Should preserve existing
            assert result["subgraph_states"]["StateAgent"] == mock_final_state


class TestBackwardCompatibility:
    """Test backward compatibility with legacy execute() method."""
    
    def test_legacy_execute_method(self):
        """Test that legacy execute() method still works."""
        agent = Agent(name="LegacyAgent")
        
        # Mock the new __call__ method
        def mock_call(state):
            return {
                "agent_outputs": {
                    "LegacyAgent": {
                        "output": "Legacy response",
                        "execution_time": 0.1,
                        "success": True
                    }
                },
                "current_agent": "LegacyAgent",
                "messages": [AIMessage(content="Legacy response")]
            }
        
        agent.__call__ = mock_call
        
        # Test legacy interface
        result = agent.execute("Legacy test input")
        
        # Verify legacy format
        assert result["agent_id"] == agent.id
        assert result["agent_name"] == "LegacyAgent"
        assert result["input"] == "Legacy test input"
        assert result["output"] == "Legacy response"
        assert result["execution_time"] == 0.1
        assert result["success"] == True
    
    def test_legacy_execute_with_context(self):
        """Test legacy execute with context parameter."""
        agent = Agent(name="ContextAgent")
        
        def mock_call(state):
            # Should receive context in execution_metadata
            context_data = state.get("execution_metadata", {})
            return {
                "agent_outputs": {
                    "ContextAgent": {
                        "output": f"Context received: {context_data.get('key', 'none')}",
                        "execution_time": 0.1,
                        "success": True
                    }
                }
            }
        
        agent.__call__ = mock_call
        
        result = agent.execute("Test", context={"key": "value"})
        
        assert "Context received: value" in result["output"]


class TestAgentNodeFactory:
    """Test agent node factory method."""
    
    def test_create_subgraph_node_runner(self):
        """Test factory method for creating node runner function."""
        agent = Agent(name="FactoryAgent")
        
        # Get node runner function
        node_runner = agent.create_subgraph_node_runner()
        
        # Verify it's callable
        assert callable(node_runner)
        
        # Test execution through node runner
        test_state = {
            "messages": [HumanMessage(content="Factory test")],
            "agent_outputs": {},
            "subgraph_states": {},
            "parent_graph_id": "factory-parent",
            "current_agent": "",
            "execution_metadata": {}
        }
        
        # Mock agent __call__
        def mock_call(state):
            return {"current_agent": "FactoryAgent"}
        
        agent.__call__ = mock_call
        
        result = node_runner(test_state)
        assert result["current_agent"] == "FactoryAgent"


class TestAgentSerialization:
    """Test agent serialization with new subgraph architecture."""
    
    def test_agent_to_dict_with_tools(self):
        """Test serializing agent with tools and workflow config."""
        @tool
        def sample_tool(text: str) -> str:
            """A sample tool for testing serialization."""
            return f"Processed: {text}"
        
        agent = Agent(
            name="SerializeAgent",
            description="Test serialization",
            tools=[sample_tool],
            system_prompt="You have tools available",
            workflow_type="planning",
            enable_validator=True
        )
        
        agent_dict = agent.to_dict()
        
        assert agent_dict["name"] == "SerializeAgent"
        assert agent_dict["description"] == "Test serialization"
        assert len(agent_dict["tools"]) == 1  # Tools are serialized as strings
        assert "workflow_config" in agent_dict
        assert agent_dict["workflow_config"]["workflow_type"] == "planning"
        assert agent_dict["workflow_config"]["enable_validator"] == True
    
    def test_agent_from_dict_restoration(self):
        """Test restoring agent from dictionary with workflow config."""
        agent_dict = {
            "id": "test-restore-id",
            "name": "RestoreAgent",
            "description": "Restored from dict",
            "system_prompt": "Restored agent",
            "llm_provider": "anthropic",
            "llm_model": "claude-3-opus",
            "llm_config": {"temperature": 0.7},
            "max_iterations": 8,
            "memory_enabled": True,
            "tools": [],  # Tools need proper deserialization in full implementation
            "workflow_config": {
                "workflow_type": "validation",
                "enable_validator": True,
                "enable_planner": True,
                "max_iterations": 8
            }
        }
        
        agent = Agent.from_dict(agent_dict)
        
        assert agent.id == "test-restore-id"
        assert agent.name == "RestoreAgent"
        assert agent.description == "Restored from dict"
        assert agent.llm_provider_name == "anthropic"
        assert agent.llm_model == "claude-3-opus"
        assert agent.workflow_config.workflow_type == "validation"
        assert agent.workflow_config.enable_validator == True


class TestAgentLLMIntegration:
    """Test agent integration with LLM providers."""
    
    @patch('multiagenticswarm.core.agent.get_llm_provider')
    def test_llm_provider_lazy_loading(self, mock_get_provider):
        """Test LLM provider is loaded lazily."""
        mock_llm = Mock()
        mock_get_provider.return_value = mock_llm
        
        agent = Agent(
            name="LLMAgent",
            llm_provider="anthropic",
            llm_model="claude-3-opus",
            llm_config={"temperature": 0.5}
        )
        
        # Provider not loaded initially
        assert agent._llm_provider is None
        
        # Access triggers loading
        provider = agent.llm_provider
        
        assert provider == mock_llm
        assert agent._llm_provider == mock_llm
        mock_get_provider.assert_called_once_with(
            provider="anthropic",
            model="claude-3-opus",
            temperature=0.5
        )


class TestAgentStreaming:
    """Test agent streaming capabilities."""
    
    def test_subgraph_streaming_support(self):
        """Test that agent supports streaming from subgraph."""
        agent = Agent(name="StreamAgent")
        
        test_state = {
            "messages": [HumanMessage(content="Stream test")],
            "agent_outputs": {},
            "subgraph_states": {},
            "parent_graph_id": "stream-parent",
            "current_agent": "",
            "execution_metadata": {}
        }
        
        # Mock streaming subgraph
        stream_chunks = [
            {"agent": {"messages": [HumanMessage(content="Stream test")], "partial": True}},
            {"agent": {"messages": [HumanMessage(content="Stream test"), AIMessage(content="Partial response")]}},
            {"agent": {"messages": [HumanMessage(content="Stream test"), AIMessage(content="Final response")], 
                      "agent_name": "StreamAgent", "parent_graph_id": "stream-parent", 
                      "execution_context": {}, "tool_outputs": []}}
        ]
        
        with patch.object(agent, 'get_compiled_subgraph') as mock_get_subgraph:
            mock_subgraph = Mock()
            mock_subgraph.stream.return_value = iter(stream_chunks)
            mock_get_subgraph.return_value = mock_subgraph
            
            result = agent(test_state)
            
            # Should use final chunk
            assert result["agent_outputs"]["StreamAgent"]["output"] == "Final response"
            assert result["current_agent"] == "StreamAgent"


class TestAgentEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_name_validation(self):
        """Test agent creation with empty name."""
        with pytest.raises(ValueError, match="Agent name cannot be empty"):
            Agent(name="")
        
        with pytest.raises(ValueError, match="Agent name cannot be empty"):
            Agent(name="   ")  # Whitespace only
    
    def test_agent_repr(self):
        """Test agent string representation."""
        agent = Agent(
            name="ReprAgent",
            llm_provider="anthropic",
            llm_model="claude-3-opus"
        )
        
        repr_str = repr(agent)
        assert "ReprAgent" in repr_str
        assert "anthropic" in repr_str
        assert "claude-3-opus" in repr_str
        assert "workflow='default'" in repr_str
    
    def test_empty_subgraph_response(self):
        """Test handling of empty subgraph response."""
        agent = Agent(name="EmptyAgent")
        
        test_state = {
            "messages": [HumanMessage(content="Test")],
            "agent_outputs": {},
            "subgraph_states": {},
            "parent_graph_id": "empty-parent",
            "current_agent": "",
            "execution_metadata": {}
        }
        
        # Mock subgraph that returns empty results
        with patch.object(agent, 'get_compiled_subgraph') as mock_get_subgraph:
            mock_subgraph = Mock()
            mock_subgraph.stream.return_value = []  # Empty stream
            mock_get_subgraph.return_value = mock_subgraph
            
            result = agent(test_state)
            
            # Should handle empty response with error
            assert "agent_outputs" in result
            assert result["agent_outputs"]["EmptyAgent"]["success"] == False
            assert "error" in result["agent_outputs"]["EmptyAgent"]

    def test_agent_call_with_none_state(self):
        """Test agent.__call__ with None state."""
        agent = Agent(name="TestAgent")
        
        with pytest.raises(ValueError, match="State cannot be None"):
            agent(None)

    def test_langgraph_not_available_error(self):
        """Test behavior when LangGraph is not available."""
        agent = Agent(name="TestAgent")
        
        # Mock LANGGRAPH_AVAILABLE as False
        with patch('multiagenticswarm.core.agent.LANGGRAPH_AVAILABLE', False):
            with pytest.raises(ImportError, match="LangGraph not available"):
                agent._create_agent_subgraph()
            
            with pytest.raises(ImportError, match="LangGraph not available"):
                state = {
                    "messages": [HumanMessage(content="Test")],
                    "agent_outputs": {},
                    "subgraph_states": {},
                    "parent_graph_id": "test-123",
                    "current_agent": "TestAgent",
                    "execution_metadata": {}
                }
                agent(state)


class TestAgentStateSchema:
    """Test agent state schema validation."""
    
    def test_agent_state_schema(self):
        """Test AgentState TypedDict structure."""
        # This is more of a documentation test
        # In practice, TypedDict provides runtime type hints
        
        state = {
            "messages": [HumanMessage(content="Test")],
            "agent_outputs": {"agent1": {"output": "result"}},
            "subgraph_states": {"agent1": {"messages": []}},
            "parent_graph_id": "parent-123",
            "current_agent": "agent1",
            "execution_metadata": {"key": "value"}
        }
        
        # Verify all required keys are present
        required_keys = ["messages", "agent_outputs", "subgraph_states", 
                        "parent_graph_id", "current_agent", "execution_metadata"]
        
        for key in required_keys:
            assert key in state
    
    def test_agent_subgraph_state_schema(self):
        """Test AgentSubgraphState TypedDict structure."""
        subgraph_state = {
            "messages": [HumanMessage(content="Test")],
            "agent_name": "TestAgent",
            "parent_graph_id": "parent-123",
            "execution_context": {"temperature": 0.5},
            "tool_outputs": [{"tool": "result"}]
        }
        
        required_keys = ["messages", "agent_name", "parent_graph_id", 
                        "execution_context", "tool_outputs"]
        
        for key in required_keys:
            assert key in subgraph_state


if __name__ == "__main__":
    pytest.main([__file__, "-v"])