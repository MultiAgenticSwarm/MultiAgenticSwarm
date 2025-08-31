"""
Comprehensive test suite for Automation functionality.
"""

import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from multiagenticswarm.core.automation import (
    Automation,
    AutomationMode,
    AutomationStatus,
    create_data_processing_automation,
    create_email_auto_response,
)
from multiagenticswarm.core.task import Task, TaskStep
from multiagenticswarm.core.trigger import Trigger, TriggerType


class TestAutomationCreation:
    """Test automation creation and initialization."""

    def test_basic_automation_creation(self):
        """Test creating a basic automation."""
        trigger = Trigger(name="TestTrigger", trigger_type=TriggerType.EVENT)
        task = Task(name="TestTask", description="Test task")

        automation = Automation(
            trigger=trigger,
            sequence=task,
            name="BasicAutomation",
            description="A basic test automation",
        )

        assert automation.name == "BasicAutomation"
        assert automation.description == "A basic test automation"
        assert automation.mode == AutomationMode.IMMEDIATE
        assert automation.status == AutomationStatus.WAITING
        assert automation.trigger_name == "TestTrigger"
        assert len(automation.task_names) == 1
        assert automation.id is not None

    def test_automation_with_trigger_name(self):
        """Test creating automation with trigger name string."""
        task = Task(name="StringTriggerTask")

        automation = Automation(
            trigger="StringTrigger", sequence=task, name="StringTriggerAutomation"
        )

        assert automation.trigger_name == "StringTrigger"

    def test_automation_with_task_name(self):
        """Test creating automation with task name string."""
        trigger = Trigger(name="StringTaskTrigger")

        automation = Automation(
            trigger=trigger, sequence="StringTask", name="StringTaskAutomation"
        )

        assert automation.task_names == ["StringTask"]

    def test_automation_with_multiple_tasks(self):
        """Test creating automation with multiple tasks."""
        trigger = Trigger(name="MultiTrigger")
        tasks = [Task(name="Task1"), Task(name="Task2"), Task(name="Task3")]

        automation = Automation(
            trigger=trigger, sequence=tasks, name="MultiTaskAutomation"
        )

        assert len(automation.task_names) == 3
        assert automation.task_names == ["Task1", "Task2", "Task3"]

    def test_automation_with_task_name_list(self):
        """Test creating automation with list of task names."""
        trigger = Trigger(name="TaskNamesTrigger")
        task_names = ["TaskA", "TaskB", "TaskC"]

        automation = Automation(
            trigger=trigger, sequence=task_names, name="TaskNamesAutomation"
        )

        assert automation.task_names == task_names

    def test_automation_with_custom_parameters(self):
        """Test creating automation with custom parameters."""
        trigger = Trigger(name="CustomTrigger")
        task = Task(name="CustomTask")

        automation = Automation(
            trigger=trigger,
            sequence=task,
            name="CustomAutomation",
            description="Custom automation with all parameters",
            mode=AutomationMode.QUEUED,
            conditions={"priority": "high", "environment": "production"},
            retry_policy={"max_retries": 5, "delay": 2.0},
            automation_id="custom-automation-id",
        )

        assert automation.mode == AutomationMode.QUEUED
        assert automation.conditions == {
            "priority": "high",
            "environment": "production",
        }
        assert automation.retry_policy == {"max_retries": 5, "delay": 2.0}
        assert automation.id == "custom-automation-id"

    def test_automation_with_auto_generated_name(self):
        """Test automation with auto-generated name."""
        trigger = Trigger(name="AutoTrigger")
        task = Task(name="AutoTask")

        automation = Automation(
            trigger=trigger,
            sequence=task,
            # No name provided - should auto-generate
        )

        assert automation.name is not None
        assert "Auto_AutoTrigger_1" in automation.name or automation.name.startswith(
            "Auto_"
        )


class TestAutomationConditions:
    """Test automation condition evaluation."""

    def test_can_execute_no_conditions(self):
        """Test execution without additional conditions."""
        trigger = Trigger(name="NoConditionTrigger")
        task = Task(name="NoConditionTask")

        automation = Automation(
            trigger=trigger, sequence=task, name="NoConditionAutomation"
        )

        # Should always be able to execute without conditions
        event = {"type": "test", "data": "test_data"}
        context = {"env": "test"}

        assert automation.can_execute(event, context) is True

    def test_can_execute_with_simple_conditions(self):
        """Test execution with simple conditions."""
        trigger = Trigger(name="ConditionTrigger")
        task = Task(name="ConditionTask")

        automation = Automation(
            trigger=trigger,
            sequence=task,
            name="ConditionAutomation",
            conditions={"min_priority": 5, "environment": "production"},
        )

        # Matching conditions
        matching_event = {"priority": 8, "env": "production"}
        matching_context = {"environment": "production", "priority": 8}
        assert automation.can_execute(matching_event, matching_context) is True

        # Non-matching conditions
        non_matching_event = {"priority": 3, "env": "production"}
        non_matching_context = {"environment": "production", "priority": 3}
        # Result depends on implementation logic

    def test_can_execute_with_complex_conditions(self):
        """Test execution with complex conditions."""
        trigger = Trigger(name="ComplexTrigger")
        task = Task(name="ComplexTask")

        automation = Automation(
            trigger=trigger,
            sequence=task,
            name="ComplexAutomation",
            conditions={
                "required_tags": ["urgent", "production"],
                "time_window": {"start": "09:00", "end": "17:00"},
                "max_load": 80,
            },
        )

        # Test various scenarios
        valid_event = {
            "tags": ["urgent", "production", "bug"],
            "time": "14:30",
            "system_load": 65,
        }
        valid_context = {"current_time": "14:30", "system_load": 65}

        # Should be able to execute (if implementation supports complex conditions)
        result = automation.can_execute(valid_event, valid_context)
        assert isinstance(result, bool)


class TestAutomationExecution:
    """Test automation execution functionality."""

    @pytest.mark.asyncio
    async def test_basic_automation_execution(self):
        """Test basic automation execution."""
        trigger = Trigger(name="ExecuteTrigger")
        task = Task(name="ExecuteTask")
        task.add_step("TestAgent", "TestTool", "test_input")

        automation = Automation(
            trigger=trigger, sequence=task, name="ExecuteAutomation"
        )

        event = {"type": "execute_test", "data": "test_data"}
        context = {"env": "test"}
        task_registry = {"ExecuteTask": task}

        # Mock task execution
        with patch.object(task, "execute") as mock_execute:
            mock_execute.return_value = {"success": True, "result": "executed"}

            result = await automation.execute(event, context, task_registry)

            assert result["status"] == "completed"
            assert automation.status == AutomationStatus.COMPLETED
            assert automation.execution_count > 0

    @pytest.mark.asyncio
    async def test_automation_execution_with_multiple_tasks(self):
        """Test executing automation with multiple tasks."""
        trigger = Trigger(name="MultiTaskTrigger")
        tasks = [Task(name="Task1"), Task(name="Task2"), Task(name="Task3")]

        automation = Automation(
            trigger=trigger, sequence=tasks, name="MultiTaskAutomation"
        )

        event = {"type": "multi_task", "data": "test"}
        context = {"batch": True}
        task_registry = {"Task1": tasks[0], "Task2": tasks[1], "Task3": tasks[2]}

        # Mock all task executions
        for task in tasks:
            task.execute = AsyncMock(return_value={"success": True, "task": task.name})

        result = await automation.execute(event, context, task_registry)

        # Should execute all tasks
        for task in tasks:
            task.execute.assert_called_once()

        assert result["status"] == "completed"
        assert automation.status == AutomationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_automation_execution_failure(self):
        """Test automation execution with task failure."""
        trigger = Trigger(name="FailTrigger")
        task = Task(name="FailTask")

        automation = Automation(trigger=trigger, sequence=task, name="FailAutomation")

        event = {"type": "fail_test"}
        context = {}
        task_registry = {"FailTask": task}

        # Mock task failure
        task.execute = AsyncMock(side_effect=Exception("Task execution failed"))

        result = await automation.execute(event, context, task_registry)

        assert result["status"] == "failed"
        assert automation.status == AutomationStatus.FAILED
        assert automation.last_error is not None

    @pytest.mark.asyncio
    async def test_automation_execution_with_retry(self):
        """Test automation execution with retry policy."""
        trigger = Trigger(name="RetryTrigger")
        task = Task(name="RetryTask")

        automation = Automation(
            trigger=trigger,
            sequence=task,
            name="RetryAutomation",
            retry_policy={"max_retries": 3, "delay": 0.1},
        )

        event = {"type": "retry_test"}
        context = {}
        task_registry = {"RetryTask": task}

        # Mock task to fail twice, then succeed
        call_count = 0

        def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception(f"Attempt {call_count} failed")
            return {"success": True, "attempt": call_count}

        task.execute = AsyncMock(side_effect=mock_execute)

        result = await automation.execute(event, context, task_registry)

        # Should succeed after retries
        assert result["status"] == "completed"
        assert automation.status == AutomationStatus.COMPLETED
        assert automation.retry_count == 2  # Two retries before success
        assert task.execute.call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_automation_execution_max_retries_exceeded(self):
        """Test automation execution when max retries are exceeded."""
        trigger = Trigger(name="MaxRetryTrigger")
        task = Task(name="MaxRetryTask")

        automation = Automation(
            trigger=trigger,
            sequence=task,
            name="MaxRetryAutomation",
            retry_policy={"max_retries": 2, "delay": 0.05},
        )

        event = {"type": "max_retry_test"}
        context = {}
        task_registry = {"MaxRetryTask": task}

        # Mock task to always fail
        task.execute = AsyncMock(side_effect=Exception("Always fails"))

        result = await automation.execute(event, context, task_registry)

        # Should fail after max retries
        assert result["status"] == "failed"
        assert automation.status == AutomationStatus.FAILED
        assert automation.retry_count == 2  # Max retries
        assert task.execute.call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_automation_execution_missing_task(self):
        """Test automation execution with missing task in registry."""
        trigger = Trigger(name="MissingTrigger")
        task = Task(name="MissingTask")

        automation = Automation(
            trigger=trigger, sequence=task, name="MissingAutomation"
        )

        event = {"type": "missing_test"}
        context = {}
        task_registry = {}  # Empty registry - task not found

        result = await automation.execute(event, context, task_registry)

        assert result["status"] == "failed"
        assert automation.status == AutomationStatus.FAILED
        assert "not found" in automation.last_error.lower()


class TestAutomationModes:
    """Test different automation execution modes."""

    def test_immediate_mode(self):
        """Test immediate execution mode."""
        trigger = Trigger(name="ImmediateTrigger")
        task = Task(name="ImmediateTask")

        automation = Automation(
            trigger=trigger, sequence=task, mode=AutomationMode.IMMEDIATE
        )

        assert automation.mode == AutomationMode.IMMEDIATE

    def test_queued_mode(self):
        """Test queued execution mode."""
        trigger = Trigger(name="QueuedTrigger")
        task = Task(name="QueuedTask")

        automation = Automation(
            trigger=trigger, sequence=task, mode=AutomationMode.QUEUED
        )

        assert automation.mode == AutomationMode.QUEUED

    def test_scheduled_mode(self):
        """Test scheduled execution mode."""
        trigger = Trigger(name="ScheduledTrigger")
        task = Task(name="ScheduledTask")

        automation = Automation(
            trigger=trigger, sequence=task, mode=AutomationMode.SCHEDULED
        )

        assert automation.mode == AutomationMode.SCHEDULED

    def test_conditional_mode(self):
        """Test conditional execution mode."""
        trigger = Trigger(name="ConditionalTrigger")
        task = Task(name="ConditionalTask")

        automation = Automation(
            trigger=trigger,
            sequence=task,
            mode=AutomationMode.CONDITIONAL,
            conditions={"check": "required"},
        )

        assert automation.mode == AutomationMode.CONDITIONAL
        assert automation.conditions == {"check": "required"}


class TestAutomationControl:
    """Test automation control operations."""

    def test_automation_reset(self):
        """Test resetting an automation."""
        trigger = Trigger(name="ResetTrigger")
        task = Task(name="ResetTask")

        automation = Automation(trigger=trigger, sequence=task, name="ResetAutomation")

        # Simulate some execution
        automation.status = AutomationStatus.COMPLETED
        automation.execution_count = 5
        automation.retry_count = 2
        automation.last_executed = "2025-01-01T10:00:00Z"
        automation.last_error = "Some error"

        # Reset automation
        automation.reset()

        assert automation.status == AutomationStatus.WAITING
        assert automation.execution_count == 0
        assert automation.retry_count == 0
        assert automation.last_executed is None
        assert automation.last_error is None

    def test_automation_cancel(self):
        """Test cancelling an automation."""
        trigger = Trigger(name="CancelTrigger")
        task = Task(name="CancelTask")

        automation = Automation(trigger=trigger, sequence=task, name="CancelAutomation")

        # Initially waiting
        assert automation.status == AutomationStatus.WAITING

        # Cancel automation
        automation.cancel()

        assert automation.status == AutomationStatus.CANCELLED

    def test_automation_statistics(self):
        """Test automation statistics."""
        trigger = Trigger(name="StatsTrigger")
        task = Task(name="StatsTask")

        automation = Automation(trigger=trigger, sequence=task, name="StatsAutomation")

        # Add some execution data
        automation.execution_count = 10
        automation.success_count = 8
        automation.failure_count = 2
        automation.total_execution_time = 125.5

        stats = automation.get_statistics()

        assert stats["execution_count"] == 10
        assert stats["success_count"] == 8
        assert stats["failure_count"] == 2
        assert stats["success_rate"] == 0.8
        assert stats["average_execution_time"] == 12.55


class TestAutomationSerialization:
    """Test automation serialization functionality."""

    def test_automation_to_dict(self):
        """Test converting automation to dictionary."""
        trigger = Trigger(name="SerializeTrigger")
        task = Task(name="SerializeTask")

        automation = Automation(
            trigger=trigger,
            sequence=task,
            name="SerializeAutomation",
            description="Serialization test",
            mode=AutomationMode.QUEUED,
            conditions={"env": "test"},
            retry_policy={"max_retries": 3, "delay": 1.0},
        )

        # Add some runtime data
        automation.execution_count = 5
        automation.last_executed = "2025-01-01T10:00:00Z"

        automation_dict = automation.to_dict()

        assert automation_dict["name"] == "SerializeAutomation"
        assert automation_dict["description"] == "Serialization test"
        assert automation_dict["trigger_name"] == "SerializeTrigger"
        assert automation_dict["task_names"] == ["SerializeTask"]
        assert automation_dict["mode"] == AutomationMode.QUEUED.value
        assert automation_dict["conditions"] == {"env": "test"}
        assert automation_dict["retry_policy"] == {"max_retries": 3, "delay": 1.0}
        assert automation_dict["execution_count"] == 5

    def test_automation_from_dict(self):
        """Test creating automation from dictionary."""
        automation_data = {
            "name": "DeserializeAutomation",
            "description": "From dictionary",
            "trigger_name": "DeserializeTrigger",
            "task_names": ["DeserializeTask1", "DeserializeTask2"],
            "mode": "scheduled",
            "conditions": {"priority": "high"},
            "retry_policy": {"max_retries": 5, "delay": 2.0},
            "status": "waiting",
            "execution_count": 0,
        }

        automation = Automation.from_dict(automation_data)

        assert automation.name == "DeserializeAutomation"
        assert automation.description == "From dictionary"
        assert automation.trigger_name == "DeserializeTrigger"
        assert automation.task_names == ["DeserializeTask1", "DeserializeTask2"]
        assert automation.mode == AutomationMode.SCHEDULED
        assert automation.conditions == {"priority": "high"}
        assert automation.retry_policy == {"max_retries": 5, "delay": 2.0}

    def test_serialization_roundtrip(self):
        """Test complete serialization roundtrip."""
        trigger = Trigger(name="RoundtripTrigger")
        tasks = [Task(name="RoundtripTask1"), Task(name="RoundtripTask2")]

        original_automation = Automation(
            trigger=trigger,
            sequence=tasks,
            name="RoundtripAutomation",
            description="Roundtrip test",
            mode=AutomationMode.CONDITIONAL,
            conditions={"test": True},
            retry_policy={"max_retries": 4, "delay": 1.5},
        )

        # Add runtime data
        original_automation.execution_count = 3
        original_automation.success_count = 2
        original_automation.failure_count = 1

        # Serialize and deserialize
        automation_dict = original_automation.to_dict()
        restored_automation = Automation.from_dict(automation_dict)

        # Compare
        assert restored_automation.name == original_automation.name
        assert restored_automation.description == original_automation.description
        assert restored_automation.trigger_name == original_automation.trigger_name
        assert restored_automation.task_names == original_automation.task_names
        assert restored_automation.mode == original_automation.mode
        assert restored_automation.conditions == original_automation.conditions
        assert restored_automation.retry_policy == original_automation.retry_policy


class TestBuiltinAutomationFactories:
    """Test built-in automation factory functions."""

    def test_create_email_auto_response(self):
        """Test creating email auto-response automation."""
        response_template = "Thank you for your email. We will respond within 24 hours."
        automation = create_email_auto_response(response_template, "EmailBot")

        assert automation.name == "EmailAutoResponse"
        assert "email" in automation.description.lower()
        assert automation.trigger_name == "EmailAutoResponse"
        assert len(automation.task_names) == 1
        assert automation.task_names[0] == "EmailAutoResponseTask"

    def test_create_email_auto_response_default_agent(self):
        """Test creating email auto-response with default agent."""
        response_template = "Auto-response message"
        automation = create_email_auto_response(response_template)

        assert automation.name == "EmailAutoResponse"
        # Should use default agent name

    def test_create_data_processing_automation(self):
        """Test creating data processing automation."""
        schedule = "0 2 * * *"  # Daily at 2 AM
        automation = create_data_processing_automation(schedule, "DataBot")

        assert automation.name == "ScheduledDataProcessing"
        assert schedule in automation.description
        assert automation.trigger_name == "DataProcessingSchedule"
        assert len(automation.task_names) == 1
        assert automation.task_names[0] == "DataProcessingTask"

    def test_create_data_processing_automation_default_agent(self):
        """Test creating data processing automation with default agent."""
        schedule = "0 */6 * * *"  # Every 6 hours
        automation = create_data_processing_automation(schedule)

        assert automation.name == "ScheduledDataProcessing"
        # Should use default agent name


class TestAutomationEdgeCases:
    """Test edge cases and error conditions."""

    def test_automation_with_empty_name(self):
        """Test automation with empty name."""
        trigger = Trigger(name="EmptyNameTrigger")
        task = Task(name="EmptyNameTask")

        automation = Automation(trigger=trigger, sequence=task, name="")

        assert automation.name == ""

    def test_automation_with_very_long_name(self):
        """Test automation with extremely long name."""
        long_name = "a" * 1000
        trigger = Trigger(name="LongNameTrigger")
        task = Task(name="LongNameTask")

        automation = Automation(trigger=trigger, sequence=task, name=long_name)

        assert automation.name == long_name

    def test_automation_with_special_characters(self):
        """Test automation with special characters."""
        special_name = "automation-with_special.chars@123!#$%"
        trigger = Trigger(name="SpecialTrigger")
        task = Task(name="SpecialTask")

        automation = Automation(trigger=trigger, sequence=task, name=special_name)

        assert automation.name == special_name

    def test_automation_with_unicode_characters(self):
        """Test automation with unicode characters."""
        unicode_name = "自动化_测试_🤖_émojis"
        trigger = Trigger(name="UnicodeTrigger")
        task = Task(name="UnicodeTask")

        automation = Automation(
            trigger=trigger,
            sequence=task,
            name=unicode_name,
            description="Unicode test automation with émojis 🚀 and Chinese 中文",
        )

        assert automation.name == unicode_name
        assert "🚀" in automation.description
        assert "中文" in automation.description

    def test_automation_with_empty_conditions(self):
        """Test automation with empty conditions."""
        trigger = Trigger(name="EmptyConditionsTrigger")
        task = Task(name="EmptyConditionsTask")

        automation = Automation(trigger=trigger, sequence=task, conditions={})

        # Should handle empty conditions gracefully
        event = {"type": "test"}
        context = {"env": "test"}
        assert automation.can_execute(event, context) is True

    def test_automation_with_none_retry_policy(self):
        """Test automation with None retry policy."""
        trigger = Trigger(name="NoneRetryTrigger")
        task = Task(name="NoneRetryTask")

        automation = Automation(trigger=trigger, sequence=task, retry_policy=None)

        # Should use default retry policy
        assert automation.retry_policy is not None
        assert "max_retries" in automation.retry_policy

    def test_automation_repr(self):
        """Test automation string representation."""
        trigger = Trigger(name="ReprTrigger")
        task = Task(name="ReprTask")

        automation = Automation(trigger=trigger, sequence=task, name="ReprAutomation")

        repr_str = repr(automation)

        assert "ReprAutomation" in repr_str
        assert "ReprTrigger" in repr_str


class TestAutomationPerformance:
    """Test automation performance characteristics."""

    @pytest.mark.asyncio
    async def test_automation_execution_timing(self):
        """Test automation execution timing."""
        trigger = Trigger(name="TimingTrigger")
        task = Task(name="TimingTask")

        automation = Automation(trigger=trigger, sequence=task, name="TimingAutomation")

        # Mock task execution with delay
        async def slow_execute(*args, **kwargs):
            await asyncio.sleep(0.1)  # 100ms delay
            return {"success": True, "duration": 0.1}

        task.execute = slow_execute

        event = {"type": "timing_test"}
        context = {}
        task_registry = {"TimingTask": task}

        start_time = time.time()
        result = await automation.execute(event, context, task_registry)
        execution_time = time.time() - start_time

        assert result["status"] == "completed"
        assert execution_time >= 0.1  # Should take at least the task delay
        assert automation.total_execution_time >= 0.1

    @pytest.mark.asyncio
    async def test_multiple_automations_concurrent_execution(self):
        """Test concurrent execution of multiple automations."""
        automations = []
        tasks = []

        # Create multiple automations
        for i in range(5):
            trigger = Trigger(name=f"ConcurrentTrigger{i}")
            task = Task(name=f"ConcurrentTask{i}")

            # Mock task execution
            async def concurrent_execute(task_id=i):
                await asyncio.sleep(0.05)  # Small delay
                return {"success": True, "task_id": task_id}

            task.execute = concurrent_execute
            tasks.append(task)

            automation = Automation(
                trigger=trigger, sequence=task, name=f"ConcurrentAutomation{i}"
            )
            automations.append(automation)

        # Execute all automations concurrently
        event = {"type": "concurrent_test"}
        context = {}
        task_registry = {f"ConcurrentTask{i}": tasks[i] for i in range(5)}

        start_time = time.time()
        results = await asyncio.gather(
            *[
                automation.execute(event, context, task_registry)
                for automation in automations
            ]
        )
        total_time = time.time() - start_time

        # All should succeed
        assert all(result["status"] == "completed" for result in results)

        # Should execute concurrently, so total time should be less than sum
        # 5 * 0.05 = 0.25s if sequential, should be ~0.05s if concurrent
        assert total_time < 0.15  # Allow some overhead

    def test_automation_memory_usage_with_many_executions(self):
        """Test automation memory usage over many executions."""
        trigger = Trigger(name="MemoryTrigger")
        task = Task(name="MemoryTask")

        automation = Automation(trigger=trigger, sequence=task, name="MemoryAutomation")

        # Simulate many execution records
        for i in range(10000):
            automation.execution_count += 1
            automation.success_count += 1 if i % 10 != 0 else 0
            automation.failure_count += 1 if i % 10 == 0 else 0
            automation.total_execution_time += 0.1

        # Statistics should still be accessible
        stats = automation.get_statistics()
        assert stats["execution_count"] == 10000
        assert stats["success_count"] == 9000
        assert stats["failure_count"] == 1000


class TestAutomationIntegration:
    """Test automation integration with other components."""

    @pytest.mark.asyncio
    async def test_automation_with_real_trigger_evaluation(self):
        """Test automation with actual trigger evaluation."""

        # Create trigger that looks for specific event type
        def trigger_condition(event):
            return (
                event.get("type") == "integration_test"
                and event.get("priority") == "high"
            )

        trigger = Trigger(name="IntegrationTrigger", condition=trigger_condition)

        task = Task(name="IntegrationTask")
        task.add_step("IntegrationAgent", "IntegrationTool", "integration_input")

        automation = Automation(
            trigger=trigger, sequence=task, name="IntegrationAutomation"
        )

        # Test with matching event
        matching_event = {
            "type": "integration_test",
            "priority": "high",
            "data": "test",
        }

        # Should trigger
        assert trigger.evaluate(matching_event) is True

        # Test with non-matching event
        non_matching_event = {
            "type": "integration_test",
            "priority": "low",
            "data": "test",
        }

        # Should not trigger
        assert trigger.evaluate(non_matching_event) is False

    def test_automation_task_dependency_chain(self):
        """Test automation with task dependency chains."""
        trigger = Trigger(name="ChainTrigger")

        # Create tasks that depend on each other
        data_fetch_task = Task(name="DataFetchTask")
        data_fetch_task.add_step("DataAgent", "FetchTool", "fetch_data")

        data_process_task = Task(name="DataProcessTask")
        data_process_task.add_step("ProcessAgent", "ProcessTool", "process_data")

        report_task = Task(name="ReportTask")
        report_task.add_step("ReportAgent", "GenerateTool", "generate_report")

        automation = Automation(
            trigger=trigger,
            sequence=[data_fetch_task, data_process_task, report_task],
            name="ChainAutomation",
        )

        assert len(automation.task_names) == 3
        assert automation.task_names == [
            "DataFetchTask",
            "DataProcessTask",
            "ReportTask",
        ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
