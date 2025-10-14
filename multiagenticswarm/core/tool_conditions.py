"""Conditions system for evaluating conditional tool permissions."""

from typing import Dict, Any

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ToolConditions:
    """Evaluates conditional permissions based on runtime context."""
    
    def __init__(self):
        """Initialize the conditions system."""
        logger.info("Tool conditions system initialized")
    
    def evaluate_condition(self, condition_name: str, context: Dict[str, Any]) -> bool:
        """
        Evaluate a named condition against runtime context.
        
        Args:
            condition_name: Condition identifier
            context: Runtime context dictionary
            
        Returns:
            True if condition is met, False otherwise
        """
        if not context:
            return False
        
        if condition_name == "development_mode":
            return context.get("mode") == "development"
        elif condition_name == "read_only_mode":
            return context.get("read_only", False)
        elif condition_name == "design_phase":
            return context.get("current_phase") == "design"
        elif condition_name == "data_safe":
            return not context.get("data_sensitive", True)
        elif condition_name == "user_approved":
            return context.get("user_approval", False)
        
        return False
    
    def load_from_config(self, config: Dict[str, Any]):
        """Process conditions from configuration."""
        conditions_config = config.get("conditions", {})
        if conditions_config:
            logger.info(f"Processed {len(conditions_config)} custom conditions from config")


_conditions_instance = None


def get_conditions() -> ToolConditions:
    """Get the singleton conditions instance."""
    global _conditions_instance
    if _conditions_instance is None:
        _conditions_instance = ToolConditions()
    return _conditions_instance
