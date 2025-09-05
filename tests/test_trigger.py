"""
Comprehensive test suite for Trigger functionality.
"""

import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from multiagenticswarm.core.trigger import (
    Trigger,
    TriggerStatus,
    TriggerType,
    create_condition_trigger,
    create_email_trigger,
    create_time_trigger,
    create_webhook_trigger,
)


class TestTriggerCreation:
    """Test trigger creation and initialization."""

    def test_basic_trigger_creation(self):
        """Test creating a basic trigger."""
        trigger = Trigger(
            name="BasicTrigger",
            trigger_type=TriggerType.EVENT,
            description="A basic test trigger",
        )

        assert trigger.name == "BasicTrigger"
        assert trigger.trigger_type == TriggerType.EVENT
        assert trigger.description == "A basic test trigger"
        assert trigger.status == TriggerStatus.ACTIVE
        assert trigger.trigger_count == 0
        assert trigger.last_triggered is None
        assert trigger.error_count == 0
        assert trigger.id is not None

    def test_trigger_with_condition_function(self):
        """Test creating trigger with condition function."""

        def test_condition(event):
            return event.get("type") == "test_event"

        trigger = Trigger(
            name="FunctionTrigger",
            trigger_type=TriggerType.CONDITION,
            condition=test_condition,
            description="Trigger with function condition",
        )

        assert trigger.condition == test_condition
        assert trigger.condition_string is None

    def test_trigger_with_condition_string(self):
        """Test creating trigger with condition string."""
        condition_str = "event.priority == 'high' and event.status == 'ready'"

        trigger = Trigger(
            name="StringTrigger",
            trigger_type=TriggerType.CONDITION,
            condition_string=condition_str,
            description="Trigger with string condition",
        )

        assert trigger.condition_string == condition_str
        assert trigger.condition is None

    def test_trigger_with_schedule(self):
        """Test creating scheduled trigger."""
        schedule = "0 9 * * *"  # Daily at 9 AM

        trigger = Trigger(
            name="ScheduledTrigger",
            trigger_type=TriggerType.SCHEDULE,
            schedule=schedule,
            description="Scheduled trigger",
        )

        assert trigger.schedule == schedule
        assert trigger.trigger_type == TriggerType.SCHEDULE

    def test_trigger_with_webhook(self):
        """Test creating webhook trigger."""
        webhook_path = "/api/webhook/test"

        trigger = Trigger(
            name="WebhookTrigger",
            trigger_type=TriggerType.WEBHOOK,
            webhook_path=webhook_path,
            description="Webhook trigger",
        )

        assert trigger.webhook_path == webhook_path
        assert trigger.trigger_type == TriggerType.WEBHOOK

    def test_trigger_with_custom_id(self):
        """Test creating trigger with custom ID."""
        custom_id = "custom-trigger-id-123"

        trigger = Trigger(name="CustomIdTrigger", trigger_id=custom_id)

        assert trigger.id == custom_id


class TestTriggerEvaluation:
    """Test trigger evaluation functionality."""

    def test_evaluate_event_trigger_with_function(self):
        """Test evaluating event trigger with function condition."""

        def event_condition(event):
            return (
                event.get("type") == "user_login" and event.get("user_id") is not None
            )

        trigger = Trigger(
            name="LoginTrigger",
            trigger_type=TriggerType.EVENT,
            condition=event_condition,
        )

        # Test matching event
        matching_event = {
            "type": "user_login",
            "user_id": "12345",
            "timestamp": "2025-01-01T10:00:00Z",
        }
        assert trigger.evaluate(matching_event) is True

        # Test non-matching event (wrong type)
        non_matching_event = {"type": "user_logout", "user_id": "12345"}
        assert trigger.evaluate(non_matching_event) is False

        # Test non-matching event (missing user_id)
        incomplete_event = {"type": "user_login", "timestamp": "2025-01-01T10:00:00Z"}
        assert trigger.evaluate(incomplete_event) is False

    def test_evaluate_event_trigger_with_string(self):
        """Test evaluating event trigger with string condition."""
        trigger = Trigger(
            name="StringConditionTrigger",
            trigger_type=TriggerType.EVENT,
            condition_string="event.get('priority', 'normal') == 'high'",
        )

        # Test matching event
        high_priority_event = {"priority": "high", "message": "urgent task"}
        assert trigger.evaluate(high_priority_event) is True

        # Test non-matching event
        normal_priority_event = {"priority": "normal", "message": "regular task"}
        assert trigger.evaluate(normal_priority_event) is False

        # Test event without priority (should default to 'normal')
        no_priority_event = {"message": "task without priority"}
        assert trigger.evaluate(no_priority_event) is False

    def test_evaluate_condition_trigger(self):
        """Test evaluating condition-based trigger."""

        def complex_condition(event):
            # Trigger when temperature > 30 and humidity > 80
            return event.get("temperature", 0) > 30 and event.get("humidity", 0) > 80

        trigger = Trigger(
            name="WeatherTrigger",
            trigger_type=TriggerType.CONDITION,
            condition=complex_condition,
        )

        # Test triggering condition
        hot_humid_event = {"temperature": 35, "humidity": 85, "location": "Miami"}
        assert trigger.evaluate(hot_humid_event) is True

        # Test non-triggering conditions
        cool_dry_event = {"temperature": 20, "humidity": 40, "location": "Seattle"}
        assert trigger.evaluate(cool_dry_event) is False

        hot_dry_event = {"temperature": 35, "humidity": 30, "location": "Phoenix"}
        assert trigger.evaluate(hot_dry_event) is False

    def test_evaluate_schedule_trigger(self):
        """Test evaluating schedule-based trigger."""
        trigger = Trigger(
            name="ScheduleTrigger",
            trigger_type=TriggerType.SCHEDULE,
            schedule="0 9 * * *",  # Daily at 9 AM
        )

        # Mock time-based evaluation
        with patch.object(trigger, "_evaluate_schedule") as mock_schedule:
            mock_schedule.return_value = True

            time_event = {"type": "schedule_check", "time": "09:00"}
            assert trigger.evaluate(time_event) is True

            mock_schedule.assert_called_once_with(time_event)

    def test_evaluate_webhook_trigger(self):
        """Test evaluating webhook-based trigger."""
        trigger = Trigger(
            name="WebhookTrigger",
            trigger_type=TriggerType.WEBHOOK,
            webhook_path="/api/webhook/deploy",
        )

        # Test matching webhook event
        webhook_event = {
            "type": "webhook",
            "path": "/api/webhook/deploy",
            "method": "POST",
            "data": {"action": "deploy", "branch": "main"},
        }

        with patch.object(trigger, "_evaluate_webhook") as mock_webhook:
            mock_webhook.return_value = True
            assert trigger.evaluate(webhook_event) is True
            mock_webhook.assert_called_once_with(webhook_event)

    def test_evaluate_message_trigger(self):
        """Test evaluating message-based trigger."""
        trigger = Trigger(
            name="MessageTrigger",
            trigger_type=TriggerType.MESSAGE,
            condition_string="'urgent' in event.get('content', '').lower()",
        )

        # Test matching message
        urgent_message = {
            "type": "message",
            "content": "URGENT: Server is down!",
            "sender": "monitoring@company.com",
        }

        with patch.object(trigger, "_evaluate_message") as mock_message:
            mock_message.return_value = True
            assert trigger.evaluate(urgent_message) is True

    def test_evaluate_inactive_trigger(self):
        """Test that inactive triggers don't evaluate."""
        trigger = Trigger(
            name="InactiveTrigger",
            condition_string="True",  # Would always trigger if active
        )

        trigger.deactivate()

        any_event = {"type": "test", "data": "anything"}
        assert trigger.evaluate(any_event) is False
        assert trigger.status == TriggerStatus.INACTIVE

    def test_evaluate_with_exception(self):
        """Test trigger evaluation with exceptions."""

        def failing_condition(event):
            raise ValueError("Condition evaluation failed")

        trigger = Trigger(name="FailingTrigger", condition=failing_condition)

        test_event = {"type": "test"}
        result = trigger.evaluate(test_event)

        assert result is False
        assert trigger.error_count > 0
        assert trigger.last_error is not None
        assert "Condition evaluation failed" in trigger.last_error


class TestTriggerFiring:
    """Test trigger firing functionality."""

    def test_trigger_fire(self):
        """Test firing a trigger."""
        trigger = Trigger(name="FireTrigger")

        test_event = {"type": "test_fire", "data": "test_data"}

        # Initially no triggers
        assert trigger.trigger_count == 0
        assert trigger.last_triggered is None

        # Fire the trigger
        trigger.fire(test_event)

        # Should update statistics
        assert trigger.trigger_count == 1
        assert trigger.last_triggered is not None
        assert trigger.status == TriggerStatus.TRIGGERED

    def test_multiple_trigger_fires(self):
        """Test firing trigger multiple times."""
        trigger = Trigger(name="MultipleFires")

        events = [
            {"type": "event1", "data": "data1"},
            {"type": "event2", "data": "data2"},
            {"type": "event3", "data": "data3"},
        ]

        for event in events:
            trigger.fire(event)

        assert trigger.trigger_count == 3
        assert trigger.status == TriggerStatus.TRIGGERED

    def test_trigger_reset(self):
        """Test resetting a trigger."""
        trigger = Trigger(name="ResetTrigger")

        # Fire trigger several times
        for i in range(5):
            trigger.fire({"event": f"test_{i}"})

        # Add some errors
        trigger.error_count = 3
        trigger.last_error = "Some error"

        # Reset trigger
        trigger.reset()

        assert trigger.status == TriggerStatus.ACTIVE
        assert trigger.trigger_count == 0
        assert trigger.last_triggered is None
        assert trigger.error_count == 0
        assert trigger.last_error is None

    def test_trigger_activate_deactivate(self):
        """Test activating and deactivating triggers."""
        trigger = Trigger(name="ActivateDeactivateTrigger")

        # Initially active
        assert trigger.status == TriggerStatus.ACTIVE

        # Deactivate
        trigger.deactivate()
        assert trigger.status == TriggerStatus.INACTIVE

        # Activate again
        trigger.activate()
        assert trigger.status == TriggerStatus.ACTIVE


class TestTriggerSerialization:
    """Test trigger serialization functionality."""

    def test_trigger_to_dict(self):
        """Test converting trigger to dictionary."""
        trigger = Trigger(
            name="SerializeTrigger",
            trigger_type=TriggerType.EVENT,
            condition_string="event.type == 'serialize'",
            description="Serialization test trigger",
        )

        # Fire trigger to add some data
        trigger.fire({"type": "serialize", "test": True})

        trigger_dict = trigger.to_dict()

        assert trigger_dict["name"] == "SerializeTrigger"
        assert trigger_dict["trigger_type"] == TriggerType.EVENT.value
        assert trigger_dict["condition_string"] == "event.type == 'serialize'"
        assert trigger_dict["description"] == "Serialization test trigger"
        assert trigger_dict["status"] == TriggerStatus.TRIGGERED.value
        assert trigger_dict["trigger_count"] == 1
        assert trigger_dict["last_triggered"] is not None

    def test_trigger_from_dict(self):
        """Test creating trigger from dictionary."""
        trigger_data = {
            "name": "DeserializeTrigger",
            "trigger_type": "condition",
            "condition_string": "event.ready == True",
            "description": "Deserialized trigger",
            "status": "active",
            "trigger_count": 0,
            "error_count": 0,
        }

        trigger = Trigger.from_dict(trigger_data)

        assert trigger.name == "DeserializeTrigger"
        assert trigger.trigger_type == TriggerType.CONDITION
        assert trigger.condition_string == "event.ready == True"
        assert trigger.description == "Deserialized trigger"
        assert trigger.status == TriggerStatus.ACTIVE

    def test_serialization_roundtrip(self):
        """Test complete serialization roundtrip."""
        original_trigger = Trigger(
            name="RoundtripTrigger",
            trigger_type=TriggerType.WEBHOOK,
            webhook_path="/api/test",
            description="Roundtrip test",
        )

        # Add some runtime data
        original_trigger.fire({"webhook": "test"})
        original_trigger.error_count = 2
        original_trigger.last_error = "Test error"

        # Serialize and deserialize
        trigger_dict = original_trigger.to_dict()
        restored_trigger = Trigger.from_dict(trigger_dict)

        # Compare
        assert restored_trigger.name == original_trigger.name
        assert restored_trigger.trigger_type == original_trigger.trigger_type
        assert restored_trigger.webhook_path == original_trigger.webhook_path
        assert restored_trigger.description == original_trigger.description
        assert restored_trigger.trigger_count == original_trigger.trigger_count
        assert restored_trigger.error_count == original_trigger.error_count


class TestBuiltinTriggerFactories:
    """Test built-in trigger factory functions."""

    def test_create_email_trigger(self):
        """Test creating email trigger."""
        trigger = create_email_trigger("EmailNotification")

        assert trigger.name == "EmailNotification"
        assert trigger.trigger_type == TriggerType.EVENT
        assert trigger.condition_string == "event.type == 'email'"
        assert "email" in trigger.description.lower()

    def test_create_email_trigger_default_name(self):
        """Test creating email trigger with default name."""
        trigger = create_email_trigger()

        assert trigger.name == "EmailReceived"
        assert trigger.trigger_type == TriggerType.EVENT

    def test_create_time_trigger(self):
        """Test creating time-based trigger."""
        schedule = "0 */2 * * *"  # Every 2 hours
        trigger = create_time_trigger("BiHourlyTrigger", schedule)

        assert trigger.name == "BiHourlyTrigger"
        assert trigger.trigger_type == TriggerType.SCHEDULE
        assert trigger.schedule == schedule
        assert schedule in trigger.description

    def test_create_webhook_trigger(self):
        """Test creating webhook trigger."""
        path = "/api/webhooks/github"
        trigger = create_webhook_trigger("GitHubWebhook", path)

        assert trigger.name == "GitHubWebhook"
        assert trigger.trigger_type == TriggerType.WEBHOOK
        assert trigger.webhook_path == path
        assert path in trigger.description

    def test_create_condition_trigger(self):
        """Test creating condition trigger."""
        condition = "event.temperature > 25 and event.humidity < 60"
        trigger = create_condition_trigger("WeatherCondition", condition)

        assert trigger.name == "WeatherCondition"
        assert trigger.trigger_type == TriggerType.CONDITION
        assert trigger.condition_string == condition
        assert condition in trigger.description


class TestStringConditionEvaluation:
    """Test string condition evaluation functionality."""

    def test_simple_string_conditions(self):
        """Test simple string condition evaluation."""
        trigger = Trigger(
            name="SimpleStringTrigger",
            condition_string="event.get('status') == 'ready'",
        )

        ready_event = {"status": "ready", "data": "test"}
        not_ready_event = {"status": "pending", "data": "test"}

        assert trigger.evaluate(ready_event) is True
        assert trigger.evaluate(not_ready_event) is False

    def test_complex_string_conditions(self):
        """Test complex string condition evaluation."""
        condition = (
            "event.get('priority', 'normal') == 'high' and "
            "event.get('category') in ['urgent', 'critical'] and "
            "len(event.get('message', '')) > 10"
        )

        trigger = Trigger(name="ComplexStringTrigger", condition_string=condition)

        # Matching event
        matching_event = {
            "priority": "high",
            "category": "urgent",
            "message": "This is a long urgent message that needs attention",
        }
        assert trigger.evaluate(matching_event) is True

        # Non-matching events
        wrong_priority = {
            "priority": "normal",
            "category": "urgent",
            "message": "This is a long message",
        }
        assert trigger.evaluate(wrong_priority) is False

        wrong_category = {
            "priority": "high",
            "category": "info",
            "message": "This is a long message",
        }
        assert trigger.evaluate(wrong_category) is False

        short_message = {"priority": "high", "category": "urgent", "message": "Short"}
        assert trigger.evaluate(short_message) is False

    def test_string_condition_with_functions(self):
        """Test string conditions that use functions."""
        condition = (
            "'error' in event.get('message', '').lower() or "
            "event.get('error_code', 0) > 0"
        )

        trigger = Trigger(name="ErrorDetectionTrigger", condition_string=condition)

        # Test with error in message
        error_message_event = {"message": "An ERROR occurred in processing"}
        assert trigger.evaluate(error_message_event) is True

        # Test with error code
        error_code_event = {"error_code": 500, "message": "Server issue"}
        assert trigger.evaluate(error_code_event) is True

        # Test without errors
        normal_event = {"message": "Processing completed successfully", "error_code": 0}
        assert trigger.evaluate(normal_event) is False

    def test_string_condition_evaluation_error(self):
        """Test handling errors in string condition evaluation."""
        # Invalid condition that will cause evaluation error
        trigger = Trigger(
            name="InvalidConditionTrigger",
            condition_string="event.nonexistent.attribute == 'value'",
        )

        test_event = {"valid": "data"}
        result = trigger.evaluate(test_event)

        # Should handle error gracefully
        assert result is False
        assert trigger.error_count > 0
        assert trigger.last_error is not None


class TestTriggerEdgeCases:
    """Test edge cases and error conditions."""

    def test_trigger_with_empty_name(self):
        """Test trigger with empty name."""
        trigger = Trigger(name="")

        assert trigger.name == ""
        assert trigger.id is not None

    def test_trigger_with_very_long_name(self):
        """Test trigger with extremely long name."""
        long_name = "a" * 1000
        trigger = Trigger(name=long_name)

        assert trigger.name == long_name

    def test_trigger_with_special_characters(self):
        """Test trigger with special characters."""
        special_name = "trigger-with_special.chars@123!#$%"
        trigger = Trigger(name=special_name)

        assert trigger.name == special_name

    def test_trigger_with_unicode_characters(self):
        """Test trigger with unicode characters."""
        unicode_name = "触发器_测试_🚀_émojis"
        trigger = Trigger(
            name=unicode_name,
            description="Unicode test trigger with émojis 🎯 and Chinese 中文",
        )

        assert trigger.name == unicode_name
        assert "🎯" in trigger.description
        assert "中文" in trigger.description

    def test_trigger_with_none_condition(self):
        """Test trigger with None condition."""
        trigger = Trigger(
            name="NoneConditionTrigger", condition=None, condition_string=None
        )

        # Should handle None conditions gracefully
        test_event = {"type": "test"}
        result = trigger.evaluate(test_event)

        # Result depends on implementation, but should not crash
        assert isinstance(result, bool)

    def test_trigger_with_both_function_and_string_condition(self):
        """Test trigger with both function and string conditions."""

        def test_condition(event):
            return event.get("function_check") is True

        trigger = Trigger(
            name="BothConditionsTrigger",
            condition=test_condition,
            condition_string="event.get('string_check') == True",
        )

        # Should prioritize function condition over string
        function_match_event = {"function_check": True, "string_check": False}
        string_match_event = {"function_check": False, "string_check": True}

        # Implementation dependent - test that it handles both gracefully
        result1 = trigger.evaluate(function_match_event)
        result2 = trigger.evaluate(string_match_event)

        assert isinstance(result1, bool)
        assert isinstance(result2, bool)

    def test_trigger_repr(self):
        """Test trigger string representation."""
        trigger = Trigger(
            name="ReprTrigger",
            trigger_type=TriggerType.EVENT,
            description="Test representation",
        )

        repr_str = repr(trigger)

        assert "ReprTrigger" in repr_str
        assert "EVENT" in repr_str


class TestTriggerPerformance:
    """Test trigger performance characteristics."""

    def test_trigger_evaluation_performance(self):
        """Test trigger evaluation with many events."""

        def simple_condition(event):
            return event.get("id", 0) % 2 == 0  # Even IDs

        trigger = Trigger(name="PerformanceTrigger", condition=simple_condition)

        # Test with many events
        num_events = 10000
        matching_count = 0

        start_time = time.time()
        for i in range(num_events):
            event = {"id": i, "data": f"event_{i}"}
            if trigger.evaluate(event):
                matching_count += 1
        evaluation_time = time.time() - start_time

        # Should evaluate quickly
        assert evaluation_time < 1.0  # Should complete in under 1 second
        assert matching_count == num_events // 2  # Half should match (even IDs)

    def test_complex_condition_performance(self):
        """Test performance of complex conditions."""
        complex_condition = (
            "event.get('priority', 0) > 5 and "
            "len(event.get('tags', [])) > 2 and "
            "any(tag.startswith('urgent') for tag in event.get('tags', [])) and "
            "event.get('timestamp', 0) > 1000000000"
        )

        trigger = Trigger(
            name="ComplexPerformanceTrigger", condition_string=complex_condition
        )

        # Test with complex events
        complex_events = [
            {
                "priority": 8,
                "tags": ["urgent_bug", "production", "critical"],
                "timestamp": 1609459200,
                "data": "complex data " * 100,  # Long data
            }
            for _ in range(1000)
        ]

        start_time = time.time()
        matching_count = sum(1 for event in complex_events if trigger.evaluate(event))
        evaluation_time = time.time() - start_time

        # Should still evaluate reasonably quickly
        assert evaluation_time < 2.0
        assert matching_count == len(complex_events)  # All should match


class TestTriggerIntegration:
    """Test trigger integration with other components."""

    def test_trigger_with_real_time_events(self):
        """Test trigger with timestamp-based events."""

        def recent_event_condition(event):
            event_time = event.get("timestamp", 0)
            current_time = time.time()
            return (current_time - event_time) < 60  # Within last minute

        trigger = Trigger(name="RecentEventTrigger", condition=recent_event_condition)

        # Recent event
        recent_event = {"type": "test", "timestamp": time.time() - 30}
        assert trigger.evaluate(recent_event) is True

        # Old event
        old_event = {"type": "test", "timestamp": time.time() - 120}
        assert trigger.evaluate(old_event) is False

    def test_trigger_state_persistence(self):
        """Test that trigger state is maintained across evaluations."""
        trigger = Trigger(name="StatefulTrigger")

        # Fire trigger multiple times
        events = [
            {"id": 1, "type": "test"},
            {"id": 2, "type": "test"},
            {"id": 3, "type": "test"},
        ]

        for event in events:
            trigger.fire(event)

        # State should be maintained
        assert trigger.trigger_count == 3
        assert trigger.status == TriggerStatus.TRIGGERED

        # Reset and verify state change
        trigger.reset()
        assert trigger.trigger_count == 0
        assert trigger.status == TriggerStatus.ACTIVE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
