"""
Agent builder for constructing configured agent instances with custom workflows.

This module provides high-level interfaces for building agents with
specific workflow patterns and configurations.
"""

from typing import Any, Dict, List, Optional
from ..utils.logger import get_logger
from .agent_graph import get_available_workflow_types, validate_workflow_config

logger = get_logger(__name__)


class AgentWorkflowConfig:
    """
    Configuration class for agent workflow settings.
    
    This class provides a structured way to configure agent workflows
    with validation and preset management.
    """
    
    def __init__(
        self,
        workflow_type: str = "default",
        enable_input_router: bool = True,
        enable_planner: bool = True,
        enable_executor: bool = True,
        enable_validator: bool = False,
        enable_tool_coordinator: bool = False,
        enable_output_formatter: bool = True,
        node_sequence: Optional[List[str]] = None,
        max_iterations: int = 10,
        **kwargs
    ):
        """
        Initialize workflow configuration.
        
        Args:
            workflow_type: Type of workflow pattern to use
            enable_input_router: Whether to enable input routing node
            enable_planner: Whether to enable planning node
            enable_executor: Whether to enable execution node
            enable_validator: Whether to enable validation node
            enable_tool_coordinator: Whether to enable tool coordination node
            enable_output_formatter: Whether to enable output formatting node
            node_sequence: Custom sequence of nodes (overrides workflow_type)
            max_iterations: Maximum iterations for complex workflows
            **kwargs: Additional configuration parameters
        """
        self.workflow_type = workflow_type
        self.enable_input_router = enable_input_router
        self.enable_planner = enable_planner
        self.enable_executor = enable_executor
        self.enable_validator = enable_validator
        self.enable_tool_coordinator = enable_tool_coordinator
        self.enable_output_formatter = enable_output_formatter
        self.node_sequence = node_sequence
        self.max_iterations = max_iterations
        
        # Store additional configuration
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        # Validate configuration
        self._validate()
    
    def _validate(self) -> None:
        """Validate configuration parameters."""
        if self.workflow_type not in get_available_workflow_types():
            logger.warning(f"Unknown workflow type '{self.workflow_type}', using 'default'")
            self.workflow_type = "default"
        
        if self.max_iterations < 1:
            logger.warning("max_iterations must be >= 1, setting to 1")
            self.max_iterations = 1
        
        if self.node_sequence:
            valid_nodes = {
                "input_router", "planner", "executor", "validator",
                "tool_coordinator", "output_formatter"
            }
            invalid_nodes = [node for node in self.node_sequence if node not in valid_nodes]
            if invalid_nodes:
                logger.warning(f"Invalid nodes in sequence: {invalid_nodes}")
                self.node_sequence = [node for node in self.node_sequence if node in valid_nodes]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "workflow_type": self.workflow_type,
            "enable_input_router": self.enable_input_router,
            "enable_planner": self.enable_planner,
            "enable_executor": self.enable_executor,
            "enable_validator": self.enable_validator,
            "enable_tool_coordinator": self.enable_tool_coordinator,
            "enable_output_formatter": self.enable_output_formatter,
            "node_sequence": self.node_sequence,
            "max_iterations": self.max_iterations
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "AgentWorkflowConfig":
        """Create configuration from dictionary."""
        return cls(**config_dict)


def create_planning_agent_config() -> AgentWorkflowConfig:
    """
    Create configuration for a planning-focused agent.
    
    This agent excels at breaking down complex tasks into manageable steps
    with comprehensive validation and tool coordination.
    
    Returns:
        Configured AgentWorkflowConfig for planning workflows
    """
    return AgentWorkflowConfig(
        workflow_type="planning",
        enable_input_router=True,
        enable_planner=True,
        enable_executor=True,
        enable_validator=True,
        enable_tool_coordinator=True,
        enable_output_formatter=True,
        max_iterations=15
    )


def create_reactive_agent_config() -> AgentWorkflowConfig:
    """
    Create configuration for a reactive agent.
    
    This agent is optimized for quick responses with minimal planning overhead,
    ideal for interactive scenarios and rapid iterations.
    
    Returns:
        Configured AgentWorkflowConfig for reactive workflows
    """
    return AgentWorkflowConfig(
        workflow_type="reactive",
        enable_input_router=False,
        enable_planner=False,
        enable_executor=True,
        enable_validator=False,
        enable_tool_coordinator=True,
        enable_output_formatter=True,
        max_iterations=5
    )


def create_validation_agent_config() -> AgentWorkflowConfig:
    """
    Create configuration for a validation-focused agent.
    
    This agent emphasizes quality assurance with comprehensive validation
    steps and quality checking at multiple stages.
    
    Returns:
        Configured AgentWorkflowConfig for validation workflows
    """
    return AgentWorkflowConfig(
        workflow_type="validation",
        enable_input_router=True,
        enable_planner=True,
        enable_executor=True,
        enable_validator=True,
        enable_tool_coordinator=False,
        enable_output_formatter=True,
        max_iterations=12
    )


def create_simple_agent_config() -> AgentWorkflowConfig:
    """
    Create configuration for a simple agent.
    
    This agent has minimal overhead with just execution and formatting,
    suitable for straightforward tasks and lightweight operations.
    
    Returns:
        Configured AgentWorkflowConfig for simple workflows
    """
    return AgentWorkflowConfig(
        workflow_type="simple",
        enable_input_router=False,
        enable_planner=False,
        enable_executor=True,
        enable_validator=False,
        enable_tool_coordinator=False,
        enable_output_formatter=True,
        max_iterations=3
    )


def create_custom_agent_config(
    enabled_nodes: List[str],
    node_sequence: Optional[List[str]] = None,
    max_iterations: int = 10
) -> AgentWorkflowConfig:
    """
    Create a custom agent configuration with specific nodes enabled.
    
    Args:
        enabled_nodes: List of node names to enable
        node_sequence: Optional custom sequence for node execution
        max_iterations: Maximum iterations for the workflow
        
    Returns:
        Configured AgentWorkflowConfig for custom workflow
    """
    # Start with all nodes disabled
    config_args = {
        "workflow_type": "custom",
        "enable_input_router": False,
        "enable_planner": False,
        "enable_executor": False,
        "enable_validator": False,
        "enable_tool_coordinator": False,
        "enable_output_formatter": False,
        "max_iterations": max_iterations
    }
    
    # Enable specified nodes
    for node in enabled_nodes:
        enable_key = f"enable_{node}"
        if enable_key in config_args:
            config_args[enable_key] = True
    
    # Set custom sequence if provided
    if node_sequence:
        config_args["node_sequence"] = node_sequence
    
    return AgentWorkflowConfig(**config_args)


class AgentBuilder:
    """
    Builder class for constructing agents with specific workflow configurations.
    
    This class provides a fluent interface for building agents with
    various workflow patterns and customizations.
    """
    
    def __init__(self):
        """Initialize the agent builder."""
        self._config = AgentWorkflowConfig()
    
    def with_workflow_type(self, workflow_type: str) -> "AgentBuilder":
        """Set the workflow type."""
        self._config.workflow_type = workflow_type
        return self
    
    def enable_node(self, node_name: str) -> "AgentBuilder":
        """Enable a specific node."""
        enable_attr = f"enable_{node_name}"
        if hasattr(self._config, enable_attr):
            setattr(self._config, enable_attr, True)
        return self
    
    def disable_node(self, node_name: str) -> "AgentBuilder":
        """Disable a specific node."""
        enable_attr = f"enable_{node_name}"
        if hasattr(self._config, enable_attr):
            setattr(self._config, enable_attr, False)
        return self
    
    def with_node_sequence(self, sequence: List[str]) -> "AgentBuilder":
        """Set custom node sequence."""
        self._config.node_sequence = sequence
        return self
    
    def with_max_iterations(self, max_iterations: int) -> "AgentBuilder":
        """Set maximum iterations."""
        self._config.max_iterations = max_iterations
        return self
    
    def build_config(self) -> AgentWorkflowConfig:
        """Build and return the workflow configuration."""
        return self._config


def get_preset_configs() -> Dict[str, AgentWorkflowConfig]:
    """
    Get dictionary of all preset configurations.
    
    Returns:
        Dictionary mapping preset names to configurations
    """
    return {
        "planning": create_planning_agent_config(),
        "reactive": create_reactive_agent_config(),
        "validation": create_validation_agent_config(),
        "simple": create_simple_agent_config()
    }


def describe_workflow_config(config: AgentWorkflowConfig) -> str:
    """
    Generate a human-readable description of a workflow configuration.
    
    Args:
        config: Workflow configuration to describe
        
    Returns:
        Human-readable description string
    """
    enabled_nodes = []
    
    if config.enable_input_router:
        enabled_nodes.append("Input Router")
    if config.enable_planner:
        enabled_nodes.append("Planner")
    if config.enable_tool_coordinator:
        enabled_nodes.append("Tool Coordinator")
    if config.enable_executor:
        enabled_nodes.append("Executor")
    if config.enable_validator:
        enabled_nodes.append("Validator")
    if config.enable_output_formatter:
        enabled_nodes.append("Output Formatter")
    
    node_list = " → ".join(enabled_nodes) if enabled_nodes else "No nodes enabled"
    
    description = f"Workflow Type: {config.workflow_type.title()}\n"
    description += f"Node Sequence: {node_list}\n"
    description += f"Max Iterations: {config.max_iterations}\n"
    
    if config.node_sequence:
        custom_sequence = " → ".join([node.replace("_", " ").title() for node in config.node_sequence])
        description += f"Custom Sequence: {custom_sequence}\n"
    
    return description
