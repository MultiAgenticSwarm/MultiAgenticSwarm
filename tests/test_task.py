"""
Comprehensive test suite for Task and Collaboration functionality.
"""
import pytest
import asyncio
import uuid
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from multiagenticswarm.core.task import Task, TaskStep, TaskStatus, Collaboration
from multiagenticswarm.core.agent import Agent


class TestTaskStep:
    """Test TaskStep functionality."""
    
    def test_basic_task_step_creation(self):
        """Test creating a basic task step."""
        step = TaskStep(
            agent="TestAgent",
            tool="TestTool",
            input_data="test input",
            context={"key": "value"}
        )
        
        assert step.agent == "TestAgent"
        assert step.tool == "TestTool"
        assert step.input_data == "test input"
        assert step.context == {"key": "value"}
        assert step.condition is None
        assert step.status == TaskStatus.PENDING
        assert step.result is None
        assert step.error is None
    
    def test_task_step_with_agent_object(self):
        """Test creating task step with Agent object."""
        agent = Agent(name="AgentObject")
        step = TaskStep(agent=agent, tool="TestTool")
        
        assert step.agent == "AgentObject"
    
    def test_task_step_with_condition(self):
        """Test creating task step with condition."""
        step = TaskStep(
            agent="ConditionalAgent",
            tool="ConditionalTool",
            condition="context.ready == True"
        )
        
        assert step.condition == "context.ready == True"
    
    def test_task_step_serialization(self):
        """Test TaskStep to_dict method."""
        step = TaskStep(
            agent="SerializeAgent",
            tool="SerializeTool",
            input_data="serialize data",
            context={"serialize": True}
        )
        
        step_dict = step.to_dict()
        
        assert step_dict["agent"] == "SerializeAgent"
        assert step_dict["tool"] == "SerializeTool"
        assert step_dict["input"] == "serialize data"
        assert step_dict["context"] == {"serialize": True}
        assert step_dict["status"] == TaskStatus.PENDING.value
    
    def test_task_step_from_dict(self):
        """Test creating TaskStep from dictionary."""
        step_data = {
            "agent": "DictAgent",
            "tool": "DictTool",
            "input": "dict input",
            "context": {"from": "dict"},
            "condition": "dict.condition",
            "status": "completed",
            "result": {"success": True},
            "error": None
        }
        
        step = TaskStep.from_dict(step_data)
        
        assert step.agent == "DictAgent"
        assert step.tool == "DictTool"
        assert step.input_data == "dict input"
        assert step.context == {"from": "dict"}
        assert step.condition == "dict.condition"


class TestTaskCreation:
    """Test Task creation and initialization."""
    
    def test_basic_task_creation(self):
        """Test creating a basic task."""
        task = Task(name="BasicTask", description="A basic test task")
        
        assert task.name == "BasicTask"
        assert task.description == "A basic test task"
        assert task.parallel is False
        assert task.max_retries == 3
        assert task.timeout is None
        assert len(task.steps) == 0
        assert task.status == TaskStatus.COMPLETED  # Empty task is completed
        assert task.current_step == 0
        assert task.retry_count == 0
        assert task.id is not None
    
    def test_task_with_custom_parameters(self):
        """Test creating task with custom parameters."""
        task = Task(
            name="CustomTask",
            description="Custom task",
            parallel=True,
            max_retries=5,
            timeout=30.0,
            task_id="custom-task-id"
        )
        
        assert task.parallel is True
        assert task.max_retries == 5
        assert task.timeout == 30.0
        assert task.id == "custom-task-id"
    
    def test_task_with_steps_list(self):
        """Test creating task with list of TaskStep objects."""
        steps = [
            TaskStep(agent="Agent1", tool="Tool1", input_data="input1"),
            TaskStep(agent="Agent2", tool="Tool2", input_data="input2")
        ]
        
        task = Task(name="StepsTask", steps=steps)
        
        assert len(task.steps) == 2
        assert task.steps[0].agent == "Agent1"
        assert task.steps[1].agent == "Agent2"
    
    def test_task_with_steps_dicts(self):
        """Test creating task with list of step dictionaries."""
        step_dicts = [
            {"agent": "DictAgent1", "tool": "DictTool1", "input": "dict_input1"},
            {"agent": "DictAgent2", "tool": "DictTool2", "input": "dict_input2"}
        ]
        
        task = Task(name="DictStepsTask", steps=step_dicts)
        
        assert len(task.steps) == 2
        assert task.steps[0].agent == "DictAgent1"
        assert task.steps[1].agent == "DictAgent2"
    
    def test_empty_task_creation(self):
        """Test creating task with no steps."""
        task = Task(name="EmptyTask")
        
        assert len(task.steps) == 0
        assert task.get_next_step() is None
        assert task.is_completed() is True  # Empty task should be considered completed


class TestTaskStepManagement:
    """Test task step management functionality."""
    
    def test_add_step(self):
        """Test adding steps to a task."""
        task = Task(name="AddStepTask")
        
        task.add_step("Agent1", "Tool1", "input1")
        task.add_step("Agent2", "Tool2", "input2", context={"key": "value"})
        
        assert len(task.steps) == 2
        assert task.steps[0].agent == "Agent1"
        assert task.steps[1].context == {"key": "value"}
    
    def test_add_step_chaining(self):
        """Test that add_step returns self for chaining."""
        task = Task(name="ChainTask")
        
        result = task.add_step("Agent1", "Tool1", "input1")
        
        assert result is task  # Should return self for chaining
        
        # Test chaining
        task.add_step("Agent2", "Tool2", "input2").add_step("Agent3", "Tool3", "input3")
        
        assert len(task.steps) == 3
    
    def test_get_next_step(self):
        """Test getting the next step to execute."""
        task = Task(name="NextStepTask")
        task.add_step("Agent1", "Tool1", "input1")
        task.add_step("Agent2", "Tool2", "input2")
        
        # Should get first step
        next_step = task.get_next_step()
        assert next_step is not None
        assert next_step.agent == "Agent1"
        assert task.current_step == 0
        
        # Mark first step completed and get next
        task.mark_step_completed({"result": "success"})
        next_step = task.get_next_step()
        assert next_step.agent == "Agent2"
        assert task.current_step == 1
        
        # Mark second step completed - no more steps
        task.mark_step_completed({"result": "success"})
        next_step = task.get_next_step()
        assert next_step is None
    
    def test_mark_step_completed(self):
        """Test marking a step as completed."""
        task = Task(name="CompletedStepTask")
        task.add_step("Agent1", "Tool1", "input1")
        
        # Get and mark step completed
        step = task.get_next_step()
        result = {"output": "step result", "metadata": {"time": "10ms"}}
        task.mark_step_completed(result)
        
        assert step.status == TaskStatus.COMPLETED
        assert step.result == result
        assert step.error is None
        assert task.current_step == 1
        assert len(task.results) == 1
        assert task.results[0] == result
    
    def test_mark_step_failed(self):
        """Test marking a step as failed."""
        task = Task(name="FailedStepTask")
        task.add_step("Agent1", "Tool1", "input1")
        
        # Get and mark step failed
        step = task.get_next_step()
        error_msg = "Tool execution failed"
        task.mark_step_failed(error_msg)
        
        assert step.status == TaskStatus.FAILED
        assert step.result is None
        assert step.error == error_msg
        assert task.current_step == 1
    
    def test_reset_task(self):
        """Test resetting a task."""
        task = Task(name="ResetTask")
        task.add_step("Agent1", "Tool1", "input1")
        task.add_step("Agent2", "Tool2", "input2")
        
        # Progress through task
        task.get_next_step()
        task.mark_step_completed({"result": "success"})
        task.get_next_step()
        task.mark_step_failed("error")
        
        # Reset task
        task.reset()
        
        assert task.status == TaskStatus.PENDING
        assert task.current_step == 0
        assert task.retry_count == 0
        assert len(task.results) == 0
        assert len(task.execution_context) == 0
        
        # All steps should be reset
        for step in task.steps:
            assert step.status == TaskStatus.PENDING
            assert step.result is None
            assert step.error is None


class TestTaskStatus:
    """Test task status management."""
    
    def test_is_completed(self):
        """Test checking if task is completed."""
        task = Task(name="CompletionTask")
        task.add_step("Agent1", "Tool1", "input1")
        task.add_step("Agent2", "Tool2", "input2")
        
        # Initially not completed
        assert task.is_completed() is False
        
        # Complete first step - still not completed
        task.get_next_step()
        task.mark_step_completed({"result": "success"})
        assert task.is_completed() is False
        
        # Complete second step - now completed
        task.get_next_step()
        task.mark_step_completed({"result": "success"})
        assert task.is_completed() is True
        assert task.status == TaskStatus.COMPLETED
    
    def test_is_failed(self):
        """Test checking if task is failed."""
        task = Task(name="FailureTask")
        task.add_step("Agent1", "Tool1", "input1")
        
        # Initially not failed
        assert task.is_failed() is False
        
        # Fail the step
        task.get_next_step()
        task.mark_step_failed("error")
        
        # Should be marked as failed if no retries
        task.status = TaskStatus.FAILED
        assert task.is_failed() is True
    
    def test_can_retry(self):
        """Test checking if task can retry."""
        task = Task(name="RetryTask", max_retries=3)
        
        # Initially can retry
        assert task.can_retry() is True
        
        # Increment retry count
        task.retry_count = 2
        assert task.can_retry() is True
        
        # At max retries
        task.retry_count = 3
        assert task.can_retry() is False
        
        # Beyond max retries
        task.retry_count = 4
        assert task.can_retry() is False
    
    def test_empty_task_completion(self):
        """Test that empty task is considered completed."""
        task = Task(name="EmptyTask")
        
        assert task.is_completed() is True
        assert task.status == TaskStatus.COMPLETED


class TestTaskSerialization:
    """Test task serialization functionality."""
    
    def test_task_to_dict(self):
        """Test converting task to dictionary."""
        task = Task(
            name="SerializableTask",
            description="A task for serialization",
            parallel=True,
            max_retries=5,
            timeout=60.0
        )
        task.add_step("Agent1", "Tool1", "input1")
        task.add_step("Agent2", "Tool2", "input2")
        
        task_dict = task.to_dict()
        
        assert task_dict["name"] == "SerializableTask"
        assert task_dict["description"] == "A task for serialization"
        assert task_dict["parallel"] is True
        assert task_dict["max_retries"] == 5
        assert task_dict["timeout"] == 60.0
        assert len(task_dict["steps"]) == 2
        assert task_dict["status"] == TaskStatus.PENDING.value
    
    def test_task_from_dict(self):
        """Test creating task from dictionary."""
        task_data = {
            "name": "DeserializedTask",
            "description": "From dictionary",
            "parallel": False,
            "max_retries": 2,
            "timeout": 30.0,
            "steps": [
                {"agent": "Agent1", "tool": "Tool1", "input": "input1"},
                {"agent": "Agent2", "tool": "Tool2", "input": "input2"}
            ],
            "status": "pending"
        }
        
        task = Task.from_dict(task_data)
        
        assert task.name == "DeserializedTask"
        assert task.description == "From dictionary"
        assert task.parallel is False
        assert task.max_retries == 2
        assert task.timeout == 30.0
        assert len(task.steps) == 2
        assert task.steps[0].agent == "Agent1"
    
    def test_serialization_roundtrip(self):
        """Test complete serialization roundtrip."""
        original_task = Task(
            name="RoundtripTask",
            description="Test roundtrip serialization",
            parallel=True,
            max_retries=4,
            timeout=45.0
        )
        original_task.add_step("Agent1", "Tool1", "input1", context={"key": "value"})
        original_task.add_step("Agent2", "Tool2", "input2", condition="context.ready")
        
        # Serialize and deserialize
        task_dict = original_task.to_dict()
        restored_task = Task.from_dict(task_dict)
        
        # Compare
        assert restored_task.name == original_task.name
        assert restored_task.description == original_task.description
        assert restored_task.parallel == original_task.parallel
        assert restored_task.max_retries == original_task.max_retries
        assert restored_task.timeout == original_task.timeout
        assert len(restored_task.steps) == len(original_task.steps)


class TestCollaboration:
    """Test Collaboration functionality."""
    
    def test_basic_collaboration_creation(self):
        """Test creating a basic collaboration."""
        agents = ["Agent1", "Agent2", "Agent3"]
        collaboration = Collaboration(
            name="BasicCollaboration",
            agents=agents,
            pattern="sequential"
        )
        
        assert collaboration.name == "BasicCollaboration"
        assert collaboration.agents == agents
        assert collaboration.pattern == "sequential"
        assert collaboration.shared_context == {}
        assert collaboration.handoff_rules == {}
        assert collaboration.id is not None
    
    def test_collaboration_with_agent_objects(self):
        """Test creating collaboration with Agent objects."""
        agents = [
            Agent(name="CollabAgent1"),
            Agent(name="CollabAgent2")
        ]
        
        collaboration = Collaboration(
            name="ObjectCollaboration",
            agents=agents
        )
        
        # Should convert to agent names
        assert collaboration.agents == ["CollabAgent1", "CollabAgent2"]
    
    def test_collaboration_with_handoff_rules(self):
        """Test collaboration with handoff rules."""
        handoff_rules = {
            "Agent1": ["Agent2", "Agent3"],
            "Agent2": ["Agent3"],
            "Agent3": ["Agent1"]
        }
        
        collaboration = Collaboration(
            name="HandoffCollaboration",
            agents=["Agent1", "Agent2", "Agent3"],
            pattern="custom",
            handoff_rules=handoff_rules
        )
        
        assert collaboration.handoff_rules == handoff_rules
    
    def test_collaboration_with_shared_context(self):
        """Test collaboration with shared context."""
        shared_context = {
            "project_id": "proj_123",
            "workspace": "main",
            "priority": "high"
        }
        
        collaboration = Collaboration(
            name="ContextCollaboration",
            agents=["Agent1", "Agent2"],
            shared_context=shared_context
        )
        
        assert collaboration.shared_context == shared_context
    
    def test_get_next_agent_sequential(self):
        """Test getting next agent in sequential pattern."""
        collaboration = Collaboration(
            name="SequentialCollab",
            agents=["Agent1", "Agent2", "Agent3"],
            pattern="sequential"
        )
        
        # Sequential should follow order
        next_agent = collaboration.get_next_agent("Agent1", {})
        assert next_agent == "Agent2"
        
        next_agent = collaboration.get_next_agent("Agent2", {})
        assert next_agent == "Agent3"
        
        next_agent = collaboration.get_next_agent("Agent3", {})
        assert next_agent is None  # End of sequence
    
    def test_get_next_agent_round_robin(self):
        """Test getting next agent in round-robin pattern."""
        collaboration = Collaboration(
            name="RoundRobinCollab",
            agents=["Agent1", "Agent2", "Agent3"],
            pattern="round_robin"
        )
        
        # Round robin should cycle
        next_agent = collaboration.get_next_agent("Agent1", {})
        assert next_agent == "Agent2"
        
        next_agent = collaboration.get_next_agent("Agent2", {})
        assert next_agent == "Agent3"
        
        next_agent = collaboration.get_next_agent("Agent3", {})
        assert next_agent == "Agent1"  # Back to start
    
    def test_get_next_agent_custom_handoff(self):
        """Test getting next agent with custom handoff rules."""
        handoff_rules = {
            "Agent1": ["Agent2", "Agent3"],
            "Agent2": ["Agent3"],
            "Agent3": ["Agent1"]
        }
        
        collaboration = Collaboration(
            name="CustomHandoffCollab",
            agents=["Agent1", "Agent2", "Agent3"],
            pattern="custom",
            handoff_rules=handoff_rules
        )
        
        # Should follow handoff rules
        # Agent1 can go to Agent2 or Agent3, should pick first
        next_agent = collaboration.get_next_agent("Agent1", {})
        assert next_agent == "Agent2"
        
        # Agent2 can only go to Agent3
        next_agent = collaboration.get_next_agent("Agent2", {})
        assert next_agent == "Agent3"
        
        # Agent3 can go to Agent1
        next_agent = collaboration.get_next_agent("Agent3", {})
        assert next_agent == "Agent1"
    
    def test_add_execution_record(self):
        """Test adding execution records."""
        collaboration = Collaboration(
            name="RecordCollab",
            agents=["Agent1", "Agent2"]
        )
        
        collaboration.add_execution_record("Agent1", "process_data", {"result": "processed"})
        collaboration.add_execution_record("Agent2", "analyze_data", {"result": "analyzed"})
        
        assert len(collaboration.execution_history) == 2
        assert collaboration.execution_history[0]["agent"] == "Agent1"
        assert collaboration.execution_history[0]["action"] == "process_data"
        assert collaboration.execution_history[1]["agent"] == "Agent2"
    
    def test_collaboration_serialization(self):
        """Test collaboration serialization."""
        collaboration = Collaboration(
            name="SerializeCollab",
            agents=["Agent1", "Agent2"],
            pattern="sequential",
            shared_context={"key": "value"},
            handoff_rules={"Agent1": ["Agent2"]}
        )
        
        # Add execution record
        collaboration.add_execution_record("Agent1", "test_action", "test_result")
        
        collab_dict = collaboration.to_dict()
        
        assert collab_dict["name"] == "SerializeCollab"
        assert collab_dict["agents"] == ["Agent1", "Agent2"]
        assert collab_dict["pattern"] == "sequential"
        assert collab_dict["shared_context"] == {"key": "value"}
        assert collab_dict["handoff_rules"] == {"Agent1": ["Agent2"]}
        assert len(collab_dict["execution_history"]) == 1
    
    def test_collaboration_from_dict(self):
        """Test creating collaboration from dictionary."""
        collab_data = {
            "name": "DictCollab",
            "agents": ["DictAgent1", "DictAgent2"],
            "pattern": "round_robin",
            "shared_context": {"from": "dict"},
            "handoff_rules": {"DictAgent1": ["DictAgent2"]}
        }
        
        collaboration = Collaboration.from_dict(collab_data)
        
        assert collaboration.name == "DictCollab"
        assert collaboration.agents == ["DictAgent1", "DictAgent2"]
        assert collaboration.pattern == "round_robin"
        assert collaboration.shared_context == {"from": "dict"}
        assert collaboration.handoff_rules == {"DictAgent1": ["DictAgent2"]}


class TestTaskEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_task_with_duplicate_step_agents(self):
        """Test task with same agent used in multiple steps."""
        task = Task(name="DuplicateAgentTask")
        task.add_step("SameAgent", "Tool1", "input1")
        task.add_step("SameAgent", "Tool2", "input2")
        task.add_step("SameAgent", "Tool3", "input3")
        
        assert len(task.steps) == 3
        assert all(step.agent == "SameAgent" for step in task.steps)
    
    def test_task_with_very_long_name(self):
        """Test task with extremely long name."""
        long_name = "a" * 1000
        task = Task(name=long_name)
        
        assert task.name == long_name
    
    def test_task_with_special_characters(self):
        """Test task with special characters in name and description."""
        task = Task(
            name="Special-Task_123@#$%",
            description="Task with émojis 🚀 and special chars: <>?/\\|"
        )
        
        assert "🚀" in task.description
        assert "@#$%" in task.name
    
    def test_task_with_zero_max_retries(self):
        """Test task with zero max retries."""
        task = Task(name="NoRetryTask", max_retries=0)
        
        assert task.max_retries == 0
        assert task.can_retry() is False
    
    def test_task_with_negative_timeout(self):
        """Test task with negative timeout."""
        task = Task(name="NegativeTimeoutTask", timeout=-10.0)
        
        assert task.timeout == -10.0  # Should accept negative values
    
    def test_collaboration_with_single_agent(self):
        """Test collaboration with only one agent."""
        collaboration = Collaboration(
            name="SingleAgentCollab",
            agents=["OnlyAgent"],
            pattern="sequential"
        )
        
        # Should handle single agent gracefully
        next_agent = collaboration.get_next_agent("OnlyAgent", {})
        assert next_agent is None  # No next agent
    
    def test_collaboration_with_empty_agents(self):
        """Test collaboration with empty agent list."""
        collaboration = Collaboration(
            name="EmptyAgentsCollab",
            agents=[],
            pattern="sequential"
        )
        
        # Should handle empty list gracefully
        next_agent = collaboration.get_next_agent("AnyAgent", {})
        assert next_agent is None
    
    def test_collaboration_with_unknown_pattern(self):
        """Test collaboration with unknown pattern."""
        collaboration = Collaboration(
            name="UnknownPatternCollab",
            agents=["Agent1", "Agent2"],
            pattern="unknown_pattern"
        )
        
        # Should handle unknown pattern gracefully
        next_agent = collaboration.get_next_agent("Agent1", {})
        # Implementation should handle this gracefully


class TestTaskPerformance:
    """Test task performance characteristics."""
    
    def test_task_with_many_steps(self):
        """Test task with large number of steps."""
        task = Task(name="ManyStepsTask")
        
        # Add many steps
        num_steps = 1000
        for i in range(num_steps):
            task.add_step(f"Agent{i}", f"Tool{i}", f"input{i}")
        
        assert len(task.steps) == num_steps
        
        # Should be able to iterate through all steps efficiently
        step_count = 0
        while task.get_next_step() is not None:
            task.mark_step_completed({"result": f"result{step_count}"})
            step_count += 1
        
        assert step_count == num_steps
        assert task.is_completed() is True
    
    def test_collaboration_execution_history_size(self):
        """Test collaboration with large execution history."""
        collaboration = Collaboration(
            name="LargeHistoryCollab",
            agents=["Agent1", "Agent2"]
        )
        
        # Add many execution records
        num_records = 10000
        for i in range(num_records):
            collaboration.add_execution_record(
                f"Agent{i % 2 + 1}",
                f"action_{i}",
                f"result_{i}"
            )
        
        assert len(collaboration.execution_history) == num_records
        
        # Serialization should still work
        collab_dict = collaboration.to_dict()
        assert len(collab_dict["execution_history"]) == num_records


class TestTaskIntegration:
    """Test task integration with other components."""
    
    def test_task_with_agent_objects_in_steps(self):
        """Test task steps that reference Agent objects."""
        agent1 = Agent(name="IntegrationAgent1")
        agent2 = Agent(name="IntegrationAgent2")
        
        task = Task(name="IntegrationTask")
        task.add_step(agent1, "Tool1", "input1")
        task.add_step(agent2, "Tool2", "input2")
        
        assert task.steps[0].agent == "IntegrationAgent1"
        assert task.steps[1].agent == "IntegrationAgent2"
    
    def test_task_context_sharing_between_steps(self):
        """Test context sharing between task steps."""
        task = Task(name="ContextSharingTask")
        task.add_step("Agent1", "Tool1", "input1")
        task.add_step("Agent2", "Tool2", "input2")
        
        # Execute first step and add context
        step1 = task.get_next_step()
        result1 = {"output": "step1_result", "shared_data": "important_data"}
        task.mark_step_completed(result1)
        
        # Context should be available for next step
        task.execution_context["from_step1"] = result1["shared_data"]
        
        step2 = task.get_next_step()
        assert "from_step1" in task.execution_context
        assert task.execution_context["from_step1"] == "important_data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
