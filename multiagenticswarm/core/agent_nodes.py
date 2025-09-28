"""
Core agent node implementations for configurable subgraph workflows.

This module provides generic, reusable nodes that can be composed into
custom agent workflows for different task types and specializations.
"""

from typing import Any, Dict, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import json
import time

from ..utils.logger import get_logger

logger = get_logger(__name__)


def input_router_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Categorizes and routes incoming tasks based on content analysis.
    
    This node analyzes the input message to determine task type, complexity,
    and routing decisions for subsequent workflow steps.
    
    Args:
        state: Current agent state containing messages and context
        
    Returns:
        Updated state with routing information and task categorization
    """
    messages = state.get("messages", [])
    if not messages:
        logger.warning("No messages found for routing")
        return state
    
    last_message = messages[-1]
    input_text = last_message.content if hasattr(last_message, 'content') else str(last_message)
    
    # Generic task categorization logic
    task_info = {
        "task_type": _categorize_task(input_text),
        "complexity": _assess_complexity(input_text),
        "requires_planning": len(input_text.split()) > 20,  # Simple heuristic
        "requires_tools": any(keyword in input_text.lower() 
                             for keyword in ["create", "build", "generate", "write", "code"]),
        "routing_timestamp": time.time()
    }
    
    # Update state with routing information
    state["task_info"] = task_info
    state["routing_complete"] = True
    
    logger.debug(f"Task routed as: {task_info['task_type']} (complexity: {task_info['complexity']})")
    
    return state


def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Breaks down complex work into actionable steps and creates execution plan.
    
    This node analyzes the task and creates a structured plan with steps,
    dependencies, and resource requirements.
    
    Args:
        state: Current agent state with task information
        
    Returns:
        Updated state with execution plan and step breakdown
    """
    messages = state.get("messages", [])
    task_info = state.get("task_info", {})
    
    if not messages:
        logger.warning("No messages found for planning")
        return state
    
    last_message = messages[-1]
    input_text = last_message.content if hasattr(last_message, 'content') else str(last_message)
    
    # Create execution plan based on task complexity
    plan = _create_execution_plan(input_text, task_info)
    
    # Update state with plan
    state["execution_plan"] = plan
    state["current_step"] = 0
    state["planning_complete"] = True
    
    # Add planning message to conversation
    planning_message = AIMessage(
        content=f"Planning complete. Created {len(plan['steps'])} steps for execution."
    )
    state["messages"] = messages + [planning_message]
    
    logger.debug(f"Created execution plan with {len(plan['steps'])} steps")
    
    return state


def executor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Performs the core task execution based on the plan.
    
    This node executes the planned steps, handles tool coordination,
    and maintains execution context throughout the process.
    
    Args:
        state: Current agent state with execution plan
        
    Returns:
        Updated state with execution results and progress
    """
    messages = state.get("messages", [])
    execution_plan = state.get("execution_plan", {})
    current_step = state.get("current_step", 0)
    
    if not execution_plan.get("steps"):
        logger.warning("No execution plan found")
        return state
    
    # Execute current step
    steps = execution_plan["steps"]
    if current_step < len(steps):
        step = steps[current_step]
        result = _execute_step(step, state)
        
        # Update execution results
        execution_results = state.get("execution_results", [])
        execution_results.append(result)
        state["execution_results"] = execution_results
        state["current_step"] = current_step + 1
        
        # Add execution message
        execution_message = AIMessage(
            content=f"Completed step {current_step + 1}/{len(steps)}: {step['description']}"
        )
        state["messages"] = messages + [execution_message]
        
        logger.debug(f"Executed step {current_step + 1}/{len(steps)}")
    
    # Mark execution complete if all steps done
    if state["current_step"] >= len(steps):
        state["execution_complete"] = True
    
    return state


def validator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates quality, completeness, and correctness of execution results.
    
    This node performs quality checks, validates against requirements,
    and determines if additional work is needed.
    
    Args:
        state: Current agent state with execution results
        
    Returns:
        Updated state with validation results and quality metrics
    """
    messages = state.get("messages", [])
    execution_results = state.get("execution_results", [])
    execution_plan = state.get("execution_plan", {})
    
    # Perform validation checks
    validation_results = _validate_execution(execution_results, execution_plan, state)
    
    # Update state with validation
    state["validation_results"] = validation_results
    state["validation_complete"] = True
    state["quality_score"] = validation_results.get("quality_score", 0.8)
    
    # Add validation message
    validation_message = AIMessage(
        content=f"Validation complete. Quality score: {validation_results.get('quality_score', 0.8):.2f}"
    )
    state["messages"] = messages + [validation_message]
    
    # Determine if retry is needed
    if validation_results.get("quality_score", 0.8) < 0.7:
        state["needs_retry"] = True
        logger.warning("Validation failed, retry required")
    else:
        state["needs_retry"] = False
        logger.debug("Validation passed")
    
    return state


def tool_coordinator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Advanced tool management and coordination for complex operations.
    
    This node handles sophisticated tool usage patterns, manages tool
    dependencies, and coordinates multi-tool workflows.
    
    Args:
        state: Current agent state with tool requirements
        
    Returns:
        Updated state with tool coordination results
    """
    messages = state.get("messages", [])
    execution_plan = state.get("execution_plan", {})
    task_info = state.get("task_info", {})
    
    # Coordinate tool usage based on plan
    tool_coordination = _coordinate_tools(execution_plan, task_info, state)
    
    # Update state with tool coordination
    state["tool_coordination"] = tool_coordination
    state["available_tools"] = tool_coordination.get("available_tools", [])
    state["tool_permissions"] = tool_coordination.get("permissions", {})
    
    # Add coordination message if tools were configured
    if tool_coordination.get("tools_configured"):
        coord_message = AIMessage(
            content=f"Tool coordination complete. {len(tool_coordination.get('available_tools', []))} tools ready."
        )
        state["messages"] = messages + [coord_message]
        logger.debug(f"Coordinated {len(tool_coordination.get('available_tools', []))} tools")
    
    return state


def output_formatter_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formats and structures the final response for optimal presentation.
    
    This node takes execution results and formats them according to
    output requirements, user preferences, and response standards.
    
    Args:
        state: Current agent state with execution and validation results
        
    Returns:
        Updated state with formatted final output
    """
    messages = state.get("messages", [])
    execution_results = state.get("execution_results", [])
    validation_results = state.get("validation_results", {})
    task_info = state.get("task_info", {})
    
    # Format the final output
    formatted_output = _format_final_output(
        execution_results, validation_results, task_info, state
    )
    
    # Update state with formatted output
    state["formatted_output"] = formatted_output
    state["final_response"] = formatted_output.get("response", "")
    state["output_metadata"] = formatted_output.get("metadata", {})
    
    # Add final response message
    final_message = AIMessage(content=state["final_response"])
    state["messages"] = messages + [final_message]
    
    # Mark workflow complete
    state["workflow_complete"] = True
    
    logger.debug("Output formatting complete")
    
    return state


# Helper functions for node implementations

def _categorize_task(input_text: str) -> str:
    """Categorize task type based on input content."""
    text_lower = input_text.lower()
    
    if any(keyword in text_lower for keyword in ["create", "build", "generate", "make"]):
        return "creation"
    elif any(keyword in text_lower for keyword in ["analyze", "review", "check", "evaluate"]):
        return "analysis"
    elif any(keyword in text_lower for keyword in ["fix", "debug", "solve", "repair"]):
        return "problem_solving"
    elif any(keyword in text_lower for keyword in ["explain", "describe", "what", "how"]):
        return "explanation"
    else:
        return "general"


def _assess_complexity(input_text: str) -> str:
    """Assess task complexity based on various factors."""
    word_count = len(input_text.split())
    
    if word_count < 10:
        return "low"
    elif word_count < 50:
        return "medium"
    else:
        return "high"


def _create_execution_plan(input_text: str, task_info: Dict[str, Any]) -> Dict[str, Any]:
    """Create a structured execution plan for the task."""
    complexity = task_info.get("complexity", "medium")
    task_type = task_info.get("task_type", "general")
    
    # Generate steps based on complexity and type
    if complexity == "low":
        steps = [
            {"id": 1, "description": "Analyze requirements", "type": "analysis"},
            {"id": 2, "description": "Execute task", "type": "execution"}
        ]
    elif complexity == "medium":
        steps = [
            {"id": 1, "description": "Analyze requirements", "type": "analysis"},
            {"id": 2, "description": "Plan approach", "type": "planning"},
            {"id": 3, "description": "Execute task", "type": "execution"},
            {"id": 4, "description": "Review results", "type": "review"}
        ]
    else:  # high complexity
        steps = [
            {"id": 1, "description": "Deep analysis of requirements", "type": "analysis"},
            {"id": 2, "description": "Break down into subtasks", "type": "decomposition"},
            {"id": 3, "description": "Plan detailed approach", "type": "planning"},
            {"id": 4, "description": "Execute primary task", "type": "execution"},
            {"id": 5, "description": "Validate and refine", "type": "validation"},
            {"id": 6, "description": "Finalize results", "type": "finalization"}
        ]
    
    return {
        "steps": steps,
        "total_steps": len(steps),
        "estimated_duration": len(steps) * 30,  # 30 seconds per step estimate
        "complexity": complexity,
        "task_type": task_type
    }


def _execute_step(step: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single step of the plan."""
    start_time = time.time()
    
    # Simulate step execution based on type
    step_type = step.get("type", "general")
    
    result = {
        "step_id": step["id"],
        "description": step["description"],
        "type": step_type,
        "status": "completed",
        "execution_time": time.time() - start_time,
        "output": f"Step {step['id']} completed successfully"
    }
    
    return result


def _validate_execution(execution_results: List[Dict], execution_plan: Dict, state: Dict[str, Any]) -> Dict[str, Any]:
    """Validate execution results against plan and quality standards."""
    total_steps = len(execution_results)
    expected_steps = execution_plan.get("total_steps", 0)
    
    # Calculate quality score based on completion and success
    completion_rate = total_steps / max(expected_steps, 1)
    success_rate = sum(1 for result in execution_results if result.get("status") == "completed") / max(total_steps, 1)
    
    quality_score = (completion_rate + success_rate) / 2
    
    return {
        "quality_score": quality_score,
        "completion_rate": completion_rate,
        "success_rate": success_rate,
        "total_steps_executed": total_steps,
        "expected_steps": expected_steps,
        "validation_passed": quality_score >= 0.7
    }


def _coordinate_tools(execution_plan: Dict, task_info: Dict, state: Dict[str, Any]) -> Dict[str, Any]:
    """Coordinate tool usage for the execution plan."""
    requires_tools = task_info.get("requires_tools", False)
    
    if not requires_tools:
        return {"tools_configured": False, "available_tools": []}
    
    # Configure tools based on task requirements
    available_tools = ["generic_tool", "text_processor", "file_handler"]
    
    return {
        "tools_configured": True,
        "available_tools": available_tools,
        "permissions": {"read": True, "write": True, "execute": False},
        "coordination_complete": True
    }


def _format_final_output(execution_results: List[Dict], validation_results: Dict, 
                        task_info: Dict, state: Dict[str, Any]) -> Dict[str, Any]:
    """Format the final output based on execution and validation results."""
    # Create a structured response
    response_parts = []
    
    # Add execution summary
    if execution_results:
        response_parts.append("Task execution completed successfully.")
        response_parts.append(f"Completed {len(execution_results)} steps.")
    
    # Add quality information
    quality_score = validation_results.get("quality_score", 0.8)
    if quality_score >= 0.8:
        response_parts.append("High quality results achieved.")
    elif quality_score >= 0.6:
        response_parts.append("Good quality results achieved.")
    else:
        response_parts.append("Basic quality results achieved.")
    
    final_response = " ".join(response_parts)
    
    return {
        "response": final_response,
        "metadata": {
            "execution_steps": len(execution_results),
            "quality_score": quality_score,
            "task_type": task_info.get("task_type", "general"),
            "completion_time": time.time()
        }
    }
