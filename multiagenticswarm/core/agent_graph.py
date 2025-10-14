"""
Agent subgraph builder for configurable workflow construction.

This module provides functionality to build custom agent subgraphs
with configurable node sequences and workflow patterns.
"""

from typing import Any, Dict, List, Optional, Callable
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage

from .agent_nodes import (
    input_router_node,
    planner_node,
    executor_node,
    validator_node,
    tool_coordinator_node,
    output_formatter_node
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


def build_agent_subgraph(
    config: Dict[str, Any],
    state_schema: type
) -> StateGraph:
    """
    Build a configurable agent subgraph based on workflow configuration.
    
    Args:
        config: Configuration dictionary specifying enabled nodes and workflow
        state_schema: TypedDict schema for state management
        
    Returns:
        Compiled StateGraph ready for execution
    """
    logger.debug(f"Building agent subgraph with config: {config}")
    
    graph = StateGraph(state_schema)
    
    # Get node configuration
    workflow_type = config.get("workflow_type", "default")
    node_config = _get_node_configuration(workflow_type, config)
    
    # Add enabled nodes
    added_nodes = []
    
    if node_config.get("enable_input_router", True):
        graph.add_node("input_router", input_router_node)
        added_nodes.append("input_router")
    
    if node_config.get("enable_planner", True):
        graph.add_node("planner", planner_node)
        added_nodes.append("planner")
    
    if node_config.get("enable_executor", True):
        graph.add_node("executor", executor_node)
        added_nodes.append("executor")
    
    if node_config.get("enable_validator", False):
        graph.add_node("validator", validator_node)
        added_nodes.append("validator")
    
    if node_config.get("enable_tool_coordinator", False):
        graph.add_node("tool_coordinator", tool_coordinator_node)
        added_nodes.append("tool_coordinator")
    
    if node_config.get("enable_output_formatter", True):
        graph.add_node("output_formatter", output_formatter_node)
        added_nodes.append("output_formatter")
    
    # Configure node sequence and edges
    _configure_workflow_edges(graph, added_nodes, workflow_type, config)
    
    # Set entry point
    if added_nodes:
        graph.set_entry_point(added_nodes[0])
    
    logger.debug(f"Built subgraph with nodes: {added_nodes}")
    
    return graph.compile()


def _get_node_configuration(workflow_type: str, config: Dict[str, Any]) -> Dict[str, bool]:
    """
    Get node enable/disable configuration based on workflow type.
    
    Args:
        workflow_type: Type of workflow (default, planning, reactive, validation)
        config: Base configuration dictionary
        
    Returns:
        Dictionary with node enable flags
    """
    # Default configuration
    node_config = {
        "enable_input_router": True,
        "enable_planner": True,
        "enable_executor": True,
        "enable_validator": False,
        "enable_tool_coordinator": False,
        "enable_output_formatter": True
    }
    
    # Workflow-specific overrides
    if workflow_type == "planning":
        node_config.update({
            "enable_planner": True,
            "enable_validator": True,
            "enable_tool_coordinator": True
        })
    elif workflow_type == "reactive":
        node_config.update({
            "enable_planner": False,
            "enable_input_router": False,
            "enable_executor": True,
            "enable_tool_coordinator": True
        })
    elif workflow_type == "validation":
        node_config.update({
            "enable_validator": True,
            "enable_output_formatter": True
        })
    elif workflow_type == "simple":
        node_config.update({
            "enable_input_router": False,
            "enable_planner": False,
            "enable_validator": False,
            "enable_tool_coordinator": False
        })
    
    # Apply explicit config overrides
    for key, value in config.items():
        if key.startswith("enable_") and isinstance(value, bool):
            node_config[key] = value
    
    return node_config


def _configure_workflow_edges(
    graph: StateGraph,
    nodes: List[str],
    workflow_type: str,
    config: Dict[str, Any]
) -> None:
    """
    Configure edges between nodes based on workflow type and configuration.
    
    Args:
        graph: StateGraph to configure
        nodes: List of added node names
        workflow_type: Type of workflow
        config: Configuration dictionary
    """
    if not nodes:
        return
    
    # Get custom sequence if specified
    custom_sequence = config.get("node_sequence")
    if custom_sequence:
        _add_sequential_edges(graph, custom_sequence)
        return
    
    # Default workflow patterns
    if workflow_type == "planning":
        _configure_planning_workflow(graph, nodes)
    elif workflow_type == "reactive":
        _configure_reactive_workflow(graph, nodes)
    elif workflow_type == "validation":
        _configure_validation_workflow(graph, nodes)
    else:
        # Default sequential flow
        _configure_default_workflow(graph, nodes)


def _configure_default_workflow(graph: StateGraph, nodes: List[str]) -> None:
    """Configure default sequential workflow."""
    # Define preferred sequence
    preferred_sequence = [
        "input_router", "planner", "tool_coordinator", 
        "executor", "validator", "output_formatter"
    ]
    
    # Filter to only included nodes in preferred order
    ordered_nodes = [node for node in preferred_sequence if node in nodes]
    
    # Add any remaining nodes not in preferred sequence
    remaining_nodes = [node for node in nodes if node not in ordered_nodes]
    ordered_nodes.extend(remaining_nodes)
    
    _add_sequential_edges(graph, ordered_nodes)


def _configure_planning_workflow(graph: StateGraph, nodes: List[str]) -> None:
    """Configure planning-focused workflow with validation loops."""
    # Planning workflow: router → planner → tool_coordinator → executor → validator → formatter
    sequence = []
    
    for preferred in ["input_router", "planner", "tool_coordinator", "executor", "validator", "output_formatter"]:
        if preferred in nodes:
            sequence.append(preferred)
    
    _add_sequential_edges(graph, sequence)
    
    # Add validation loop if both validator and executor exist
    if "validator" in nodes and "executor" in nodes:
        # Add conditional edge for retry (placeholder for future implementation)
        pass


def _configure_reactive_workflow(graph: StateGraph, nodes: List[str]) -> None:
    """Configure reactive workflow optimized for quick responses."""
    # Reactive workflow: tool_coordinator → executor → formatter (minimal planning)
    sequence = []
    
    for preferred in ["tool_coordinator", "executor", "output_formatter"]:
        if preferred in nodes:
            sequence.append(preferred)
    
    # Add any other nodes at the beginning
    other_nodes = [node for node in nodes if node not in sequence]
    sequence = other_nodes + sequence
    
    _add_sequential_edges(graph, sequence)


def _configure_validation_workflow(graph: StateGraph, nodes: List[str]) -> None:
    """Configure validation-heavy workflow for quality assurance."""
    # Validation workflow: router → planner → executor → validator → formatter
    sequence = []
    
    for preferred in ["input_router", "planner", "executor", "validator", "output_formatter"]:
        if preferred in nodes:
            sequence.append(preferred)
    
    # Add tool coordinator before executor if present
    if "tool_coordinator" in nodes and "tool_coordinator" not in sequence:
        executor_idx = sequence.index("executor") if "executor" in sequence else len(sequence)
        sequence.insert(executor_idx, "tool_coordinator")
    
    _add_sequential_edges(graph, sequence)


def _add_sequential_edges(graph: StateGraph, sequence: List[str]) -> None:
    """Add sequential edges between nodes in the given order."""
    for i in range(len(sequence) - 1):
        graph.add_edge(sequence[i], sequence[i + 1])
    
    # Connect last node to END
    if sequence:
        graph.add_edge(sequence[-1], END)


def get_available_workflow_types() -> List[str]:
    """
    Get list of available workflow types.
    
    Returns:
        List of supported workflow type names
    """
    return ["default", "planning", "reactive", "validation", "simple"]


def get_workflow_description(workflow_type: str) -> str:
    """
    Get description of a workflow type.
    
    Args:
        workflow_type: Workflow type name
        
    Returns:
        Human-readable description of the workflow
    """
    descriptions = {
        "default": "Balanced workflow with planning, execution, and formatting",
        "planning": "Planning-focused workflow with validation loops and tool coordination",
        "reactive": "Quick response workflow with minimal planning overhead", 
        "validation": "Quality-focused workflow with comprehensive validation steps",
        "simple": "Minimal workflow with just execution and output formatting"
    }
    
    return descriptions.get(workflow_type, "Custom workflow configuration")


def validate_workflow_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize workflow configuration.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Validated and normalized configuration
    """
    validated_config = config.copy()
    
    # Ensure workflow_type is valid
    workflow_type = validated_config.get("workflow_type", "default")
    if workflow_type not in get_available_workflow_types():
        logger.warning(f"Unknown workflow type '{workflow_type}', using 'default'")
        validated_config["workflow_type"] = "default"
    
    # Validate node sequence if provided
    node_sequence = validated_config.get("node_sequence")
    if node_sequence:
        valid_nodes = {
            "input_router", "planner", "executor", "validator", 
            "tool_coordinator", "output_formatter"
        }
        invalid_nodes = [node for node in node_sequence if node not in valid_nodes]
        if invalid_nodes:
            logger.warning(f"Invalid nodes in sequence: {invalid_nodes}")
            validated_config["node_sequence"] = [
                node for node in node_sequence if node in valid_nodes
            ]
    
    return validated_config
