"""
Trigger system for event-driven automation.
"""

import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class TriggerType(str, Enum):
    """Types of triggers supported."""

    EVENT = "event"  # Event-based triggers
    SCHEDULE = "schedule"  # Time-based triggers
    CONDITION = "condition"  # Condition-based triggers
    WEBHOOK = "webhook"  # HTTP webhook triggers
    MESSAGE = "message"  # Message-based triggers


class TriggerStatus(str, Enum):
    """Trigger status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    TRIGGERED = "triggered"
    ERROR = "error"


class Trigger:
    """
    A trigger defines when an automation should be executed.

    Triggers can be:
    - Event-based: React to specific events
    - Schedule-based: Execute at specific times
    - Condition-based: Execute when conditions are met
    - Webhook-based: React to HTTP requests
    - Message-based: React to messages/notifications
    """

    def __init__(
        self,
        name: str,
        trigger_type: TriggerType = TriggerType.EVENT,
        condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
        condition_string: Optional[str] = None,
        schedule: Optional[str] = None,
        webhook_path: Optional[str] = None,
        description: str = "",
        trigger_id: Optional[str] = None,
    ):
        """
        Initialize a trigger.

        Args:
            name: Unique name for the trigger
            trigger_type: Type of trigger (event, schedule, condition, etc.)
            condition: Callable condition function
            condition_string: String representation of condition for serialization
            schedule: Cron-like schedule string for scheduled triggers
            webhook_path: Path for webhook triggers
            description: Description of the trigger
            trigger_id: Optional custom trigger ID
        """
        self.id = trigger_id or str(uuid.uuid4())
        self.name = name
        self.trigger_type = trigger_type
        self.condition = condition
        self.condition_string = condition_string
        self.schedule = schedule
        self.webhook_path = webhook_path
        self.description = description

        # Runtime state
        self.status = TriggerStatus.ACTIVE
        self.trigger_count = 0
        self.last_triggered: Optional[str] = None
        self.error_count = 0
        self.last_error: Optional[str] = None

        logger.info(f"Created trigger '{name}' of type '{trigger_type.value}'")

    def evaluate(self, event: Dict[str, Any]) -> bool:
        """
        Evaluate if the trigger should fire for the given event.

        Args:
            event: Event data to evaluate

        Returns:
            True if trigger should fire, False otherwise
        """
        if self.status != TriggerStatus.ACTIVE:
            return False

        try:
            if self.trigger_type == TriggerType.EVENT:
                return self._evaluate_event(event)
            elif self.trigger_type == TriggerType.CONDITION:
                return self._evaluate_condition(event)
            elif self.trigger_type == TriggerType.SCHEDULE:
                return self._evaluate_schedule(event)
            elif self.trigger_type == TriggerType.WEBHOOK:
                return self._evaluate_webhook(event)
            elif self.trigger_type == TriggerType.MESSAGE:
                return self._evaluate_message(event)

            return False

        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            self.status = TriggerStatus.ERROR
            logger.error(f"Trigger '{self.name}' evaluation failed: {e}")
            return False

    def _evaluate_event(self, event: Dict[str, Any]) -> bool:
        """Evaluate event-based trigger."""
        if self.condition:
            return self.condition(event)
        elif self.condition_string:
            # Simple string-based condition evaluation
            return self._evaluate_string_condition(event)
        return False

    def _evaluate_condition(self, event: Dict[str, Any]) -> bool:
        """Evaluate condition-based trigger."""
        return self._evaluate_event(event)  # Same logic for now

    def _evaluate_schedule(self, event: Dict[str, Any]) -> bool:
        """Evaluate schedule-based trigger."""
        # This would integrate with a scheduler like APScheduler
        # For now, check if it's a schedule event
        return (
            event.get("type") == "schedule" and event.get("schedule") == self.schedule
        )

    def _evaluate_webhook(self, event: Dict[str, Any]) -> bool:
        """Evaluate webhook-based trigger."""
        return event.get("type") == "webhook" and event.get("path") == self.webhook_path

    def _evaluate_message(self, event: Dict[str, Any]) -> bool:
        """Evaluate message-based trigger."""
        return event.get("type") == "message"

    def _evaluate_string_condition(self, event: Dict[str, Any]) -> bool:
        """Evaluate a string-based condition."""
        if not self.condition_string:
            return False

        try:
            # Simple condition evaluation
            # In production, use a safe expression evaluator
            condition = self.condition_string

            # Replace event.key with event["key"] for evaluation
            for key in event.keys():
                condition = condition.replace(f"event.{key}", f'event["{key}"]')

            # Evaluate the condition (UNSAFE - use safe evaluator in production)
            return eval(condition, {"event": event})

        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logger.warning(
                f"Condition evaluation failed for '{self.condition_string}': {e}"
            )
            return False

    def fire(self, event: Dict[str, Any]) -> None:
        """Mark the trigger as fired."""
        self.trigger_count += 1
        self.last_triggered = logger.name  # Placeholder for timestamp
        self.status = TriggerStatus.TRIGGERED

        logger.info(f"Trigger '{self.name}' fired (count: {self.trigger_count})")

    def reset(self) -> None:
        """Reset trigger to active state."""
        self.status = TriggerStatus.ACTIVE
        self.trigger_count = 0
        self.error_count = 0
        self.last_error = None
        self.last_triggered = None

        logger.debug(f"Reset trigger '{self.name}'")

    def deactivate(self) -> None:
        """Deactivate the trigger."""
        self.status = TriggerStatus.INACTIVE
        logger.debug(f"Deactivated trigger '{self.name}'")

    def activate(self) -> None:
        """Activate the trigger."""
        self.status = TriggerStatus.ACTIVE
        self.last_error = None
        logger.debug(f"Activated trigger '{self.name}'")

    def to_dict(self) -> Dict[str, Any]:
        """Convert trigger to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "trigger_type": self.trigger_type.value,
            "condition_string": self.condition_string,
            "schedule": self.schedule,
            "webhook_path": self.webhook_path,
            "description": self.description,
            "status": self.status.value,
            "trigger_count": self.trigger_count,
            "last_triggered": self.last_triggered,
            "error_count": self.error_count,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Trigger":
        """Create trigger from dictionary representation."""
        trigger = cls(
            name=data["name"],
            trigger_type=TriggerType(data.get("trigger_type", "event")),
            condition_string=data.get("condition_string"),
            schedule=data.get("schedule"),
            webhook_path=data.get("webhook_path"),
            description=data.get("description", ""),
            trigger_id=data.get("id"),
        )

        # Restore runtime state
        if "status" in data:
            trigger.status = TriggerStatus(data["status"])
        trigger.trigger_count = data.get("trigger_count", 0)
        trigger.last_triggered = data.get("last_triggered")
        trigger.error_count = data.get("error_count", 0)
        trigger.last_error = data.get("last_error")

        return trigger

    def __repr__(self) -> str:
        return f"Trigger(name='{self.name}', type='{self.trigger_type.value.upper()}', status='{self.status.value}')"


# Built-in trigger factories
def create_email_trigger(name: str = "EmailReceived") -> Trigger:
    """Create a trigger for email events."""
    return Trigger(
        name=name,
        trigger_type=TriggerType.EVENT,
        condition_string="event.type == 'email'",
        description="Triggers when an email is received",
    )


def create_time_trigger(name: str, schedule: str) -> Trigger:
    """Create a scheduled trigger."""
    return Trigger(
        name=name,
        trigger_type=TriggerType.SCHEDULE,
        schedule=schedule,
        description=f"Triggers on schedule: {schedule}",
    )


def create_webhook_trigger(name: str, path: str) -> Trigger:
    """Create a webhook trigger."""
    return Trigger(
        name=name,
        trigger_type=TriggerType.WEBHOOK,
        webhook_path=path,
        description=f"Triggers on webhook: {path}",
    )


def create_condition_trigger(name: str, condition: str) -> Trigger:
    """Create a condition-based trigger."""
    return Trigger(
        name=name,
        trigger_type=TriggerType.CONDITION,
        condition_string=condition,
        description=f"Triggers when: {condition}",
    )
