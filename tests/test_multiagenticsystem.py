"""
Test suite for multiagenticswarm package.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from multiagenticswarm import Agent, Tool, Task, System


class TestAgent:
    """Test Agent functionality."""
    
    def test_agent_creation(self):
        """Test basic agent creation."""
        agent = Agent(
            name="TestAgent",
            description="A test agent",
            system_prompt="You are a test agent",
            llm_provider="openai",
            llm_model="gpt-3.5-turbo"
        )
        
        assert agent.name == "TestAgent"
        assert agent.description == "A test agent"
        assert agent.llm_provider_name == "openai"
        assert agent.llm_model == "gpt-3.5-turbo"
    
    def test_agent_serialization(self):
        """Test agent to/from dict conversion."""
        agent = Agent(
            name="SerializationTest",
            description="Test serialization",
            llm_provider="anthropic",
            llm_model="claude-3.5-sonnet"
        )
        
        # Convert to dict and back
        agent_dict = agent.to_dict()
        restored_agent = Agent.from_dict(agent_dict)
        
        assert restored_agent.name == agent.name
        assert restored_agent.description == agent.description
        assert restored_agent.llm_provider_name == agent.llm_provider_name
        assert restored_agent.llm_model == agent.llm_model
    
    @pytest.mark.asyncio
    async def test_agent_execution(self):
        """Test agent execution."""
        with patch('multiagenticswarm.core.agent.get_llm_provider') as mock_get_provider:
            # Create a mock provider
            mock_provider = Mock()
            async def mock_execute(messages, **kwargs):
                return Mock(content="Hello! I'm doing well, thank you for asking.", tool_calls=[])
            mock_provider.execute = AsyncMock(side_effect=mock_execute)
            mock_provider.extract_tool_calls.return_value = []  # No tool calls
            mock_get_provider.return_value = mock_provider
            
            # Create an empty tool executor for the agent
            from multiagenticswarm.core.tool_executor import ToolExecutor
            tool_executor = ToolExecutor()
            
            agent = Agent(
                name="ExecutionTest",
                system_prompt="You are a helpful assistant"
            )
            
            result = await agent.execute(
                "Hello, how are you?",
                tool_executor=tool_executor
            )
            
            assert result["success"] == True
            assert result["agent_name"] == "ExecutionTest"
            assert "output" in result


class TestTool:
    """Test Tool functionality."""
    
    def test_tool_creation(self):
        """Test basic tool creation."""
        def sample_func(x: int) -> int:
            return x * 2
        
        tool = Tool(
            name="TestTool",
            func=sample_func,
            description="A test tool"
        )
        
        assert tool.name == "TestTool"
        assert tool.description == "A test tool"
        assert tool.func == sample_func
    
    def test_tool_sharing_local(self):
        """Test local tool sharing."""
        agent = Agent("TestAgent")
        tool = Tool("LocalTool")
        
        tool.set_local(agent)
        
        assert tool.can_be_used_by(agent)
        assert tool.local_agent == agent.name
    
    def test_tool_sharing_shared(self):
        """Test shared tool sharing."""
        agent1 = Agent("Agent1")
        agent2 = Agent("Agent2")
        agent3 = Agent("Agent3")
        
        tool = Tool("SharedTool")
        tool.set_shared(agent1, agent2)
        
        assert tool.can_be_used_by(agent1)
        assert tool.can_be_used_by(agent2)
        assert not tool.can_be_used_by(agent3)
    
    def test_tool_sharing_global(self):
        """Test global tool sharing."""
        agent1 = Agent("Agent1")
        agent2 = Agent("Agent2")
        
        tool = Tool("GlobalTool")
        tool.set_global()
        
        assert tool.can_be_used_by(agent1)
        assert tool.can_be_used_by(agent2)
        assert tool.is_global == True
    
    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """Test tool execution."""
        def multiply(x: int, y: int) -> int:
            return x * y
        
        tool = Tool("Multiplier", func=multiply)
        agent = Agent("TestAgent")
        tool.set_local(agent)
        
        result = await tool.execute(agent, 5, 3)
        
        assert result["success"] == True
        assert result["result"] == 15
        assert result["agent"] == "TestAgent"


class TestTask:
    """Test Task functionality."""
    
    def test_task_creation(self):
        """Test basic task creation."""
        task = Task(
            name="TestTask",
            description="A test task"
        )
        
        assert task.name == "TestTask"
        assert task.description == "A test task"
        assert len(task.steps) == 0
    
    def test_task_with_steps(self):
        """Test task creation with steps."""
        steps = [
            {"agent": "Agent1", "tool": "Tool1", "input": "test input 1"},
            {"agent": "Agent2", "tool": "Tool2", "input": "test input 2"}
        ]
        
        task = Task("StepTask", steps=steps)
        
        assert len(task.steps) == 2
        assert task.steps[0].agent == "Agent1"
        assert task.steps[1].agent == "Agent2"
    
    def test_task_step_management(self):
        """Test task step management."""
        task = Task("ManagementTest")
        
        task.add_step("Agent1", "Tool1", "input1")
        task.add_step("Agent2", "Tool2", "input2")
        
        assert len(task.steps) == 2
        
        # Test step progression
        next_step = task.get_next_step()
        assert next_step.agent == "Agent1"
        
        task.mark_step_completed({"result": "success"})
        assert task.current_step == 1
        
        next_step = task.get_next_step()
        assert next_step.agent == "Agent2"


class TestSystem:
    """Test System functionality."""
    
    def test_system_creation(self):
        """Test basic system creation."""
        system = System()
        
        status = system.get_system_status()
        assert status["running"] == False
        assert status["agents"] == 0
        assert status["tools"] >= 2  # Built-in tools
    
    def test_agent_registration(self):
        """Test agent registration."""
        system = System()
        agent = Agent("TestAgent")
        
        system.register_agent(agent)
        
        assert "TestAgent" in system.agents
        assert system.get_agent("TestAgent") == agent
        assert "TestAgent" in system.list_agents()
    
    def test_tool_registration(self):
        """Test tool registration."""
        system = System()
        tool = Tool("TestTool")
        
        system.register_tool(tool)
        
        assert "TestTool" in system.tools
        assert system.get_tool("TestTool") == tool
        assert "TestTool" in system.list_tools()
    
    def test_task_registration(self):
        """Test task registration."""
        system = System()
        task = Task("TestTask")
        
        system.register_task(task)
        
        assert "TestTask" in system.tasks
        assert system.get_task("TestTask") == task
        assert "TestTask" in system.list_tasks()
    
    def test_tool_access_integration(self):
        """Test tool access through system."""
        system = System()
        
        # Create agents and tools
        agent1 = Agent("Agent1")
        agent2 = Agent("Agent2")
        
        local_tool = Tool("LocalTool")
        local_tool.set_local(agent1)
        
        shared_tool = Tool("SharedTool") 
        shared_tool.set_shared(agent1, agent2)
        
        global_tool = Tool("GlobalTool")
        global_tool.set_global()
        
        # Register everything
        system.register_agents(agent1, agent2)
        system.register_tools(local_tool, shared_tool, global_tool)
        
        # Check tool access
        agent1_tools = agent1.get_available_tools(system.tools)
        agent2_tools = agent2.get_available_tools(system.tools)
        
        # Agent1 should have access to local, shared, and global tools
        assert "LocalTool" in agent1_tools
        assert "SharedTool" in agent1_tools  
        assert "GlobalTool" in agent1_tools
        
        # Agent2 should have access to shared and global tools only
        assert "LocalTool" not in agent2_tools
        assert "SharedTool" in agent2_tools
        assert "GlobalTool" in agent2_tools
    
    @pytest.mark.asyncio
    async def test_system_execution(self):
        """Test system execution capabilities."""
        with patch('multiagenticswarm.core.agent.get_llm_provider') as mock_get_provider:
            # Create a mock provider
            mock_provider = Mock()
            async def mock_execute(messages, **kwargs):
                return Mock(content="Hello! I'm a helpful assistant.", tool_calls=[])
            mock_provider.execute = AsyncMock(side_effect=mock_execute)
            mock_provider.extract_tool_calls.return_value = []  # No tool calls
            mock_get_provider.return_value = mock_provider
            
            system = System()
            
            # Create a simple agent
            agent = Agent("ExecutionAgent", system_prompt="You are helpful")
            system.register_agent(agent)
            
            # Test agent execution through system
            result = await system.execute_agent(
                "ExecutionAgent",
                "Hello world",
                {"test": True}
            )
            
            assert result["success"] == True
            assert result["agent_name"] == "ExecutionAgent"


class TestIntegration:
    """Integration tests for the complete system."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test a complete workflow from start to finish."""
        with patch('multiagenticswarm.core.agent.get_llm_provider') as mock_get_provider:
            # Create a mock provider
            mock_provider = Mock()
            async def mock_execute(messages, **kwargs):
                return Mock(content="Task completed successfully", tool_calls=[])
            mock_provider.execute = AsyncMock(side_effect=mock_execute)
            mock_provider.extract_tool_calls.return_value = []  # No tool calls
            mock_get_provider.return_value = mock_provider
            
            system = System()
            
            # Create agents
            analyst = Agent("DataAnalyst", system_prompt="Analyze data")
            executor = Agent("ActionExecutor", system_prompt="Execute actions")
            
            # Create tools
            def fetch_data(query: str) -> dict:
                return {"data": f"fetched for {query}"}
            
            def process_data(data: dict) -> dict:
                return {"processed": data}
            
            fetcher = Tool("DataFetcher", func=fetch_data)
            fetcher.set_local(analyst)
            
            processor = Tool("DataProcessor", func=process_data)
            processor.set_shared(analyst, executor)
            
            # Create task
            task = Task("AnalysisWorkflow")
            task.add_step("DataAnalyst", "DataFetcher", "get sales data")
            task.add_step("ActionExecutor", "DataProcessor", "process results")
            
            # Register everything
            system.register_agents(analyst, executor)
            system.register_tools(fetcher, processor)
            system.register_task(task)
            
            # Verify system state
            status = system.get_system_status()
            assert status["agents"] == 2
            assert status["tools"] >= 4  # 2 custom + 2 built-in
            assert status["tasks"] == 1
            
            # Test task execution
            result = await system.execute_task("AnalysisWorkflow")
            assert result["success"] == True
            assert result["task_name"] == "AnalysisWorkflow"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
