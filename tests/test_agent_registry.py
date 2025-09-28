"""
Tests for the agent registry system.
"""

import pytest
import time
from unittest.mock import Mock, patch
from multiagenticswarm.core.agent import Agent
from multiagenticswarm.core.agent_registry import AgentRegistry, get_registry, register_agent, find_agent_for_task
from multiagenticswarm.core.agent_manifest import AgentStatus, HealthStatus


class TestAgentRegistry:
    """Test cases for AgentRegistry class."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Reset singleton for clean tests
        AgentRegistry.reset_instance()
        self.registry = AgentRegistry.get_instance()
        
        # Create test agents
        self.agent1 = Agent(
            name="test_agent_1",
            description="Test agent for text processing",
            system_prompt="You are a text processing assistant."
        )
        
        self.agent2 = Agent(
            name="test_agent_2", 
            description="Test agent for data analysis",
            system_prompt="You are a data analysis assistant."
        )
        
        self.agent3 = Agent(
            name="test_agent_3",
            description="Test agent for code generation",
            system_prompt="You are a code generation assistant."
        )
    
    def test_registry_singleton(self):
        """Test that registry follows singleton pattern."""
        registry1 = AgentRegistry.get_instance()
        registry2 = AgentRegistry.get_instance()
        assert registry1 is registry2
        assert registry1 is self.registry
    
    def test_register_agent_basic(self):
        """Test basic agent registration."""
        agent_id = self.registry.register_agent(
            self.agent1, 
            capabilities=["text_processing", "summarization"]
        )
        
        assert agent_id is not None
        assert self.agent1.registry_id == agent_id
        assert agent_id in self.registry.list_agents()
        
        # Check agent can be retrieved
        retrieved_agent = self.registry.get_agent(agent_id)
        assert retrieved_agent is self.agent1
        
        # Check manifest
        manifest = self.registry.get_manifest(agent_id)
        assert manifest is not None
        assert manifest.name == "test_agent_1"
        assert "text_processing" in manifest.capabilities
        assert "summarization" in manifest.capabilities
    
    def test_register_agent_with_custom_id(self):
        """Test agent registration with custom ID."""
        custom_id = "custom_agent_123"
        agent_id = self.registry.register_agent(
            self.agent1,
            capabilities=["text_processing"],
            custom_id=custom_id
        )
        
        assert agent_id == custom_id
        assert self.agent1.registry_id == custom_id
    
    def test_register_agent_duplicate_id_fails(self):
        """Test that registering with duplicate custom ID fails."""
        custom_id = "duplicate_id"
        
        # First registration should succeed
        self.registry.register_agent(
            self.agent1,
            capabilities=["text_processing"],
            custom_id=custom_id
        )
        
        # Second registration with same ID should fail
        with pytest.raises(ValueError, match="Agent ID .* already exists"):
            self.registry.register_agent(
                self.agent2,
                capabilities=["data_analysis"],
                custom_id=custom_id
            )
    
    def test_register_agent_validation(self):
        """Test agent registration validation."""
        # None agent should fail
        with pytest.raises(ValueError, match="Agent cannot be None"):
            self.registry.register_agent(None, capabilities=["test"])
        
        # Empty capabilities should fail
        with pytest.raises(ValueError, match="must have at least one capability"):
            self.registry.register_agent(self.agent1, capabilities=[])
        
        # None capabilities should fail
        with pytest.raises(ValueError, match="must have at least one capability"):
            self.registry.register_agent(self.agent1, capabilities=None)
    
    def test_find_agents_by_capability(self):
        """Test finding agents by single capability."""
        # Register agents with different capabilities
        id1 = self.registry.register_agent(self.agent1, capabilities=["text_processing", "summarization"])
        id2 = self.registry.register_agent(self.agent2, capabilities=["data_analysis", "visualization"]) 
        id3 = self.registry.register_agent(self.agent3, capabilities=["text_processing", "code_generation"])
        
        # Find agents with text_processing capability
        text_agents = self.registry.find_agents_by_capability("text_processing")
        assert set(text_agents) == {id1, id3}
        
        # Find agents with data_analysis capability
        data_agents = self.registry.find_agents_by_capability("data_analysis")
        assert data_agents == [id2]
        
        # Find agents with non-existent capability
        none_agents = self.registry.find_agents_by_capability("non_existent")
        assert none_agents == []
    
    def test_find_agents_by_capabilities_match_all(self):
        """Test finding agents by multiple capabilities (match all)."""
        # Register agents with overlapping capabilities
        id1 = self.registry.register_agent(self.agent1, capabilities=["text_processing", "summarization", "analysis"])
        id2 = self.registry.register_agent(self.agent2, capabilities=["data_analysis", "visualization"])
        id3 = self.registry.register_agent(self.agent3, capabilities=["text_processing", "analysis", "code_generation"])
        
        # Find agents that have both text_processing AND analysis
        matching_agents = self.registry.find_agents_by_capabilities(
            ["text_processing", "analysis"], 
            match_all=True
        )
        assert set(matching_agents) == {id1, id3}
        
        # Find agents that have all three capabilities (should be only id1)
        matching_agents = self.registry.find_agents_by_capabilities(
            ["text_processing", "analysis", "summarization"],
            match_all=True
        )
        assert matching_agents == [id1]
        
        # Find agents with impossible combination
        matching_agents = self.registry.find_agents_by_capabilities(
            ["text_processing", "data_analysis"],
            match_all=True
        )
        assert matching_agents == []
    
    def test_find_agents_by_capabilities_match_any(self):
        """Test finding agents by multiple capabilities (match any)."""
        # Register agents
        id1 = self.registry.register_agent(self.agent1, capabilities=["text_processing"])
        id2 = self.registry.register_agent(self.agent2, capabilities=["data_analysis"])
        id3 = self.registry.register_agent(self.agent3, capabilities=["code_generation"])
        
        # Find agents that have text_processing OR data_analysis
        matching_agents = self.registry.find_agents_by_capabilities(
            ["text_processing", "data_analysis"],
            match_all=False
        )
        assert set(matching_agents) == {id1, id2}
        
        # Find agents that have any of the three capabilities
        matching_agents = self.registry.find_agents_by_capabilities(
            ["text_processing", "data_analysis", "code_generation"],
            match_all=False
        )
        assert set(matching_agents) == {id1, id2, id3}
    
    def test_get_agent_for_task_basic(self):
        """Test smart agent selection for tasks."""
        # Register agents with different capabilities
        id1 = self.registry.register_agent(
            self.agent1, 
            capabilities=["text_processing", "summarization"],
            requirements=["text_tool"]
        )
        id2 = self.registry.register_agent(
            self.agent2, 
            capabilities=["data_analysis", "visualization"],
            requirements=["data_tool"]
        )
        
        # Find agent for text processing task
        agent = self.registry.get_agent_for_task(["text_processing"])
        assert agent is self.agent1
        
        # Find agent for data analysis task
        agent = self.registry.get_agent_for_task(["data_analysis"])
        assert agent is self.agent2
        
        # Find agent for non-existent capability
        agent = self.registry.get_agent_for_task(["non_existent"])
        assert agent is None
    
    def test_get_agent_for_task_with_requirements(self):
        """Test agent selection with tool requirements."""
        # Register agent with requirements
        id1 = self.registry.register_agent(
            self.agent1,
            capabilities=["text_processing"],
            requirements=["text_tool", "file_tool"]
        )
        
        # Should find agent when all requirements are met
        agent = self.registry.get_agent_for_task(
            ["text_processing"],
            available_tools=["text_tool", "file_tool", "other_tool"]
        )
        assert agent is self.agent1
        
        # Should not find agent when requirements are not met
        agent = self.registry.get_agent_for_task(
            ["text_processing"],
            available_tools=["text_tool"]  # missing file_tool
        )
        assert agent is None
    
    def test_get_agent_for_task_with_preferences(self):
        """Test agent selection with preferred capabilities."""
        # Register agents with different capability sets
        id1 = self.registry.register_agent(self.agent1, capabilities=["text_processing"])
        id2 = self.registry.register_agent(self.agent2, capabilities=["text_processing", "summarization"])
        
        # Without preferences, either agent could be selected
        agent = self.registry.get_agent_for_task(["text_processing"])
        assert agent in [self.agent1, self.agent2]
        
        # With preference for summarization, agent2 should be selected
        agent = self.registry.get_agent_for_task(
            ["text_processing"],
            preferred_capabilities=["summarization"]
        )
        assert agent is self.agent2
    
    def test_update_agent_status(self):
        """Test updating agent status and health."""
        id1 = self.registry.register_agent(self.agent1, capabilities=["text_processing"])
        
        # Update status
        success = self.registry.update_agent_status(id1, "maintenance", "degraded")
        assert success is True
        
        manifest = self.registry.get_manifest(id1)
        assert manifest.status == "maintenance"
        assert manifest.health == "degraded"
        
        # Update non-existent agent should fail
        success = self.registry.update_agent_status("non_existent", "active")
        assert success is False
    
    def test_record_agent_execution(self):
        """Test recording agent execution metrics."""
        id1 = self.registry.register_agent(self.agent1, capabilities=["text_processing"])
        
        # Record successful execution
        success = self.registry.record_agent_execution(id1, success=True, execution_time=1.5)
        assert success is True
        
        manifest = self.registry.get_manifest(id1)
        assert manifest.metrics.total_executions == 1
        assert manifest.metrics.successful_executions == 1
        assert manifest.metrics.failed_executions == 0
        assert manifest.metrics.success_rate == 1.0
        
        # Record failed execution
        self.registry.record_agent_execution(id1, success=False, execution_time=0.8)
        
        manifest = self.registry.get_manifest(id1)
        assert manifest.metrics.total_executions == 2
        assert manifest.metrics.successful_executions == 1
        assert manifest.metrics.failed_executions == 1
        assert manifest.metrics.success_rate == 0.5
        
        # Record for non-existent agent should fail
        success = self.registry.record_agent_execution("non_existent", True, 1.0)
        assert success is False
    
    def test_remove_agent(self):
        """Test removing agents from registry."""
        id1 = self.registry.register_agent(self.agent1, capabilities=["text_processing", "summarization"])
        
        # Verify agent is registered
        assert self.registry.get_agent(id1) is self.agent1
        assert id1 in self.registry.find_agents_by_capability("text_processing")
        
        # Remove agent
        success = self.registry.remove_agent(id1)
        assert success is True
        
        # Verify agent is removed
        assert self.registry.get_agent(id1) is None
        assert id1 not in self.registry.list_agents()
        assert id1 not in self.registry.find_agents_by_capability("text_processing")
        
        # Remove non-existent agent should fail
        success = self.registry.remove_agent("non_existent")
        assert success is False
    
    def test_list_agents_with_filter(self):
        """Test listing agents with status filter."""
        id1 = self.registry.register_agent(self.agent1, capabilities=["text_processing"])
        id2 = self.registry.register_agent(self.agent2, capabilities=["data_analysis"])
        
        # Set different statuses
        self.registry.update_agent_status(id1, "maintenance")
        
        # List all agents
        all_agents = self.registry.list_agents()
        assert set(all_agents) == {id1, id2}
        
        # List only active agents
        active_agents = self.registry.list_agents(status_filter="active")
        assert active_agents == [id2]
        
        # List only maintenance agents
        maintenance_agents = self.registry.list_agents(status_filter="maintenance")
        assert maintenance_agents == [id1]
    
    def test_registry_stats(self):
        """Test registry statistics collection."""
        # Empty registry stats
        stats = self.registry.get_registry_stats()
        assert stats["total_agents"] == 0
        assert stats["active_agents"] == 0
        
        # Register some agents
        id1 = self.registry.register_agent(self.agent1, capabilities=["text_processing", "summarization"])
        id2 = self.registry.register_agent(self.agent2, capabilities=["data_analysis"])
        
        # Set one agent to maintenance
        self.registry.update_agent_status(id1, "maintenance")
        
        # Record some executions for metrics
        self.registry.record_agent_execution(id1, True, 1.0)
        self.registry.record_agent_execution(id2, True, 2.0)
        
        stats = self.registry.get_registry_stats()
        assert stats["total_agents"] == 2
        assert stats["active_agents"] == 1
        assert stats["inactive_agents"] == 1
        assert stats["total_capabilities"] == 3  # text_processing, summarization, data_analysis
        assert "text_processing" in stats["capabilities"]
        assert stats["average_success_rate"] == 1.0
        assert stats["average_execution_time"] == 1.5
    
    def test_export_registry(self):
        """Test registry export functionality."""
        # Register agents
        id1 = self.registry.register_agent(self.agent1, capabilities=["text_processing"])
        id2 = self.registry.register_agent(self.agent2, capabilities=["data_analysis"])
        
        # Export registry
        registry_data = self.registry.export_registry()
        
        assert "agents" in registry_data
        assert "capability_index" in registry_data
        assert "exported_at" in registry_data
        
        assert id1 in registry_data["agents"]
        assert id2 in registry_data["agents"]
        
        assert "text_processing" in registry_data["capability_index"]
        assert "data_analysis" in registry_data["capability_index"]
        assert id1 in registry_data["capability_index"]["text_processing"]
        assert id2 in registry_data["capability_index"]["data_analysis"]
    
    def test_clear_registry(self):
        """Test clearing registry."""
        # Register some agents
        self.registry.register_agent(self.agent1, capabilities=["text_processing"])
        self.registry.register_agent(self.agent2, capabilities=["data_analysis"])
        
        # Verify agents are registered
        assert len(self.registry.list_agents()) == 2
        
        # Clear registry
        self.registry.clear_registry()
        
        # Verify registry is empty
        assert len(self.registry.list_agents()) == 0
        stats = self.registry.get_registry_stats()
        assert stats["total_agents"] == 0
        assert stats["total_capabilities"] == 0
    
    def test_inactive_agents_excluded_from_discovery(self):
        """Test that inactive agents are excluded from discovery by default."""
        id1 = self.registry.register_agent(self.agent1, capabilities=["text_processing"])
        id2 = self.registry.register_agent(self.agent2, capabilities=["text_processing"])
        
        # Set one agent to inactive
        self.registry.update_agent_status(id1, "inactive")
        
        # Find agents by capability (should exclude inactive)
        active_agents = self.registry.find_agents_by_capability("text_processing")
        assert id1 not in active_agents
        assert id2 in active_agents
        
        # Find agents including inactive
        all_agents = self.registry.find_agents_by_capability("text_processing", include_inactive=True)
        assert id1 in all_agents
        assert id2 in all_agents
        
        # Get agent for task should not return inactive agent
        agent = self.registry.get_agent_for_task(["text_processing"])
        assert agent is self.agent2  # Should get the active one


class TestRegistryConvenienceFunctions:
    """Test convenience functions."""
    
    def setup_method(self):
        """Setup for each test."""
        AgentRegistry.reset_instance()
        self.agent = Agent(name="test_agent", description="Test agent")
    
    def test_get_registry(self):
        """Test get_registry convenience function."""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2
        assert isinstance(registry1, AgentRegistry)
    
    def test_register_agent_convenience(self):
        """Test register_agent convenience function."""
        agent_id = register_agent(self.agent, ["test_capability"])
        
        registry = get_registry()
        assert registry.get_agent(agent_id) is self.agent
    
    def test_find_agent_for_task_convenience(self):
        """Test find_agent_for_task convenience function."""
        register_agent(self.agent, ["test_capability"])
        
        found_agent = find_agent_for_task(["test_capability"])
        assert found_agent is self.agent
        
        # Test with non-existent capability
        not_found = find_agent_for_task(["non_existent"])
        assert not_found is None


class TestRegistryIntegration:
    """Test registry integration with Agent class."""
    
    def setup_method(self):
        """Setup for each test."""
        AgentRegistry.reset_instance()
        self.registry = AgentRegistry.get_instance()
    
    def test_agent_registry_id_set(self):
        """Test that registry_id is set on agent when registered."""
        agent = Agent(name="test_agent", description="Test agent")
        
        # Initially no registry ID
        assert agent.registry_id is None
        
        # Register agent
        agent_id = self.registry.register_agent(agent, ["test_capability"])
        
        # Registry ID should be set
        assert agent.registry_id == agent_id
    
    def test_agent_works_without_registry(self):
        """Test that agents work normally without registry integration."""
        agent = Agent(name="test_agent", description="Test agent")
        
        # Agent should work normally without being registered
        assert agent.name == "test_agent"
        assert agent.registry_id is None
        
        # All normal agent operations should work
        agent.add_to_memory("user", "test message")
        assert len(agent.memory) == 1
