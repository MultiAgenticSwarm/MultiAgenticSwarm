"""
Custom state reducers for MultiAgenticSwarm.

This module provides custom reducers that define how to merge state updates
when multiple agents or processes modify the state concurrently. These reducers
work alongside LangGraph's built-in reducers like add_messages.

Reducers ensure consistent and predictable state merging behavior while
preserving important historical information and resolving conflicts intelligently.
"""

from typing import Any, Dict, List, Optional, Union
from collections.abc import Callable
from datetime import datetime, timezone
import copy
import uuid

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ReducerError(Exception):
    """Raised when reducer operations fail."""
    pass


class ConflictResolutionStrategy:
    """Defines strategies for resolving conflicts in state merging."""
    
    LAST_WRITE_WINS = "last_write_wins"
    MOST_RESTRICTIVE = "most_restrictive"
    MOST_PERMISSIVE = "most_permissive"
    TIMESTAMP_BASED = "timestamp_based"
    MERGE_UNION = "merge_union"
    MERGE_INTERSECTION = "merge_intersection"
    MONOTONIC_INCREASE = "monotonic_increase"
    KEEP_BOTH = "keep_both"


def safe_reducer(reducer_func: Callable) -> Callable:
    """
    Decorator to add error handling and logging to reducer functions.
    
    Args:
        reducer_func: The reducer function to wrap
        
    Returns:
        Wrapped reducer function with error handling
    """
    def wrapped_reducer(*args, **kwargs):
        func_name = reducer_func.__name__
        try:
            logger.debug(f"Executing reducer: {func_name}")
            start_time = datetime.now()
            result = reducer_func(*args, **kwargs)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.debug(f"Reducer {func_name} completed in {duration:.4f}s")
            return result
        except Exception as e:
            error_id = str(uuid.uuid4())[:8]
            logger.error(
                f"Reducer {func_name} failed (ID: {error_id}): {str(e)}"
            )
            # For critical reducers, we might want to raise the error
            # For non-critical ones, we could return a safe default
            raise ReducerError(f"Reducer {func_name} failed (ID: {error_id}): {str(e)}") from e
    
    return wrapped_reducer


@safe_reducer
def merge_agent_outputs(current: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge agent outputs, preserving historical outputs and resolving conflicts.
    
    This reducer combines outputs from multiple agents, maintaining a complete
    history of all outputs while ensuring the most recent output for each agent
    is easily accessible.
    
    Args:
        current: Current agent_outputs state
        update: New agent_outputs to merge
        
    Returns:
        Merged agent_outputs with historical preservation
        
    Raises:
        ReducerError: If merge operation fails
    """
    if current is None and update is None:
        return {}
    
    merged = copy.deepcopy(current) if current else {}
    
    if not update:
        return merged
    
    if not isinstance(update, dict):
        raise ReducerError(f"Update must be a dictionary, got {type(update).__name__}")
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    for agent_id, output in update.items():
        if not isinstance(agent_id, str):
            logger.warning(f"Agent ID should be string, got {type(agent_id).__name__}: {agent_id}")
            agent_id = str(agent_id)
        
        if agent_id not in merged:
            # First output from this agent
            merged[agent_id] = {
                "current": output,
                "history": [
                    {
                        "output": output,
                        "timestamp": timestamp,
                        "version": 1
                    }
                ],
                "last_updated": timestamp,
                "total_outputs": 1
            }
        else:
            # Update existing agent output
            existing = merged[agent_id]
            
            # Ensure existing has proper structure
            if not isinstance(existing, dict):
                logger.warning(f"Converting invalid agent output structure for {agent_id}")
                existing = {"current": existing, "history": [], "total_outputs": 1}
                merged[agent_id] = existing
            
            # Move current to history and set new current
            if "current" in existing:
                # Add current to history if it's different from new output
                if existing["current"] != output:
                    if "history" not in existing:
                        existing["history"] = []
                    
                    existing["history"].append({
                        "output": existing["current"],
                        "timestamp": existing.get("last_updated", timestamp),
                        "version": existing.get("total_outputs", 0)
                    })
            
            # Update with new output
            existing["current"] = output
            existing["last_updated"] = timestamp
            existing["total_outputs"] = existing.get("total_outputs", 0) + 1
            
            # Limit history size to prevent memory bloat
            max_history = 50
            if len(existing.get("history", [])) > max_history:
                existing["history"] = existing["history"][-max_history:]
                logger.debug(f"Trimmed history for agent {agent_id} to {max_history} entries")
    
    logger.debug(f"Merged agent outputs for {len(update)} agents")
    return merged


@safe_reducer
def aggregate_progress(current: Dict[str, float], update: Dict[str, float]) -> Dict[str, float]:
    """
    Aggregate task progress, ensuring monotonic progress and handling conflicts.
    
    This reducer merges progress updates while ensuring that progress values
    are monotonically increasing (tasks don't go backwards) and handles
    concurrent updates intelligently.
    
    Args:
        current: Current task_progress state
        update: New progress values to merge
        
    Returns:
        Merged progress with conflict resolution
        
    Raises:
        ReducerError: If merge operation fails
    """
    if current is None and update is None:
        return {}
    
    merged = copy.deepcopy(current) if current else {}
    
    if not update:
        return merged
    
    if not isinstance(update, dict):
        raise ReducerError(f"Update must be a dictionary, got {type(update).__name__}")
    
    warnings = []
    
    for task_id, new_progress in update.items():
        try:
            # Validate progress value
            if not isinstance(new_progress, (int, float)):
                warnings.append(f"Invalid progress value for task {task_id}: {new_progress} (type: {type(new_progress).__name__})")
                continue
                
            # Clamp progress to valid range [0, 100]
            clamped_progress = max(0.0, min(100.0, float(new_progress)))
            if clamped_progress != new_progress:
                warnings.append(f"Progress for task {task_id} clamped from {new_progress} to {clamped_progress}")
            
            if task_id not in merged:
                # New task progress
                merged[task_id] = clamped_progress
            else:
                # Update existing task progress
                current_progress = merged[task_id]
                
                # Ensure current_progress is a number
                if not isinstance(current_progress, (int, float)):
                    warnings.append(f"Current progress for task {task_id} is invalid: {current_progress}, resetting to 0")
                    current_progress = 0.0
                
                # Ensure monotonic progress (no going backwards)
                if clamped_progress >= current_progress:
                    merged[task_id] = clamped_progress
                else:
                    warnings.append(
                        f"Progress regression detected for task {task_id}: "
                        f"{current_progress}% -> {clamped_progress}%. Keeping higher value."
                    )
                    # Keep the higher progress value
                    merged[task_id] = max(current_progress, clamped_progress)
        
        except Exception as e:
            warnings.append(f"Error processing progress for task {task_id}: {str(e)}")
            continue
    
    # Log warnings
    for warning in warnings:
        logger.warning(warning)
    
    logger.debug(f"Aggregated progress for {len(update)} tasks")
    return merged


@safe_reducer
def resolve_permissions(
    current: Dict[str, List[str]], 
    update: Dict[str, List[str]],
    strategy: str = ConflictResolutionStrategy.MOST_RESTRICTIVE
) -> Dict[str, List[str]]:
    """
    Resolve tool permission updates with configurable conflict resolution.
    
    This reducer merges permission updates while applying configurable security rules:
    - Most restrictive: intersection of permissions (default)
    - Most permissive: union of permissions
    - Last write wins: update completely replaces current
    
    Args:
        current: Current tool_permissions state
        update: New permissions to merge
        strategy: Conflict resolution strategy
        
    Returns:
        Merged permissions with configured resolution
        
    Raises:
        ReducerError: If merge operation fails
    """
    if current is None and update is None:
        return {}
    
    merged = copy.deepcopy(current) if current else {}
    
    if not update:
        return merged
    
    if not isinstance(update, dict):
        raise ReducerError(f"Update must be a dictionary, got {type(update).__name__}")
    
    warnings = []
    
    for agent_id, new_permissions in update.items():
        try:
            if not isinstance(agent_id, str):
                warnings.append(f"Agent ID should be string, got {type(agent_id).__name__}: {agent_id}")
                agent_id = str(agent_id)
            
            if not isinstance(new_permissions, list):
                warnings.append(f"Invalid permissions format for agent {agent_id}: {new_permissions}")
                continue
            
            # Normalize permissions list
            normalized_permissions = []
            for perm in new_permissions:
                if perm and isinstance(perm, str):
                    normalized_permissions.append(perm.strip())
                else:
                    warnings.append(f"Invalid permission '{perm}' for agent {agent_id}")
            
            normalized_permissions = list(set(normalized_permissions))  # Remove duplicates
            
            if agent_id not in merged:
                # New agent permissions
                merged[agent_id] = normalized_permissions
            else:
                # Merge with existing permissions based on strategy
                current_permissions = set(merged[agent_id])
                new_permission_set = set(normalized_permissions)
                
                if strategy == ConflictResolutionStrategy.MOST_RESTRICTIVE:
                    # Security-first merge: intersection
                    if not normalized_permissions:
                        # Empty list means revoke all
                        merged[agent_id] = []
                        logger.info(f"All permissions revoked for agent {agent_id}")
                    else:
                        intersection = current_permissions.intersection(new_permission_set)
                        if not intersection and (current_permissions or new_permission_set):
                            logger.warning(
                                f"Permission conflict for agent {agent_id}: "
                                f"current={sorted(current_permissions)}, "
                                f"new={sorted(new_permission_set)}. Applying most restrictive (no permissions)."
                            )
                            merged[agent_id] = []
                        else:
                            merged[agent_id] = sorted(list(intersection))
                
                elif strategy == ConflictResolutionStrategy.MOST_PERMISSIVE:
                    # Union of permissions
                    union = current_permissions.union(new_permission_set)
                    merged[agent_id] = sorted(list(union))
                
                elif strategy == ConflictResolutionStrategy.LAST_WRITE_WINS:
                    # Update completely replaces current
                    merged[agent_id] = normalized_permissions
                
                else:
                    raise ReducerError(f"Unknown conflict resolution strategy: {strategy}")
        
        except Exception as e:
            warnings.append(f"Error processing permissions for agent {agent_id}: {str(e)}")
            continue
    
    # Log warnings
    for warning in warnings:
        logger.warning(warning)
    
    logger.debug(f"Resolved permissions for {len(update)} agents using strategy: {strategy}")
    return merged


@safe_reducer
def merge_tool_results(current: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge tool execution results, preserving history and handling duplicates.
    
    Args:
        current: Current tool_results state
        update: New tool results to merge
        
    Returns:
        Merged tool results with deduplication and history
        
    Raises:
        ReducerError: If merge operation fails
    """
    if current is None and update is None:
        return {}
    
    merged = copy.deepcopy(current) if current else {}
    
    if not update:
        return merged
    
    if not isinstance(update, dict):
        raise ReducerError(f"Update must be a dictionary, got {type(update).__name__}")
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    for tool_call_id, result in update.items():
        if not isinstance(tool_call_id, str):
            logger.warning(f"Tool call ID should be string, got {type(tool_call_id).__name__}: {tool_call_id}")
            tool_call_id = str(tool_call_id)
        
        if tool_call_id not in merged:
            # New tool result
            merged[tool_call_id] = {
                "result": result,
                "timestamp": timestamp,
                "attempts": 1
            }
        else:
            # Update existing result (retry case)
            existing = merged[tool_call_id]
            
            # Ensure existing has proper structure
            if not isinstance(existing, dict):
                logger.warning(f"Converting invalid tool result structure for {tool_call_id}")
                existing = {"result": existing, "attempts": 1}
                merged[tool_call_id] = existing
            
            # If result is different, it might be a retry
            if existing.get("result") != result:
                # Store previous result in history
                if "history" not in existing:
                    existing["history"] = []
                
                existing["history"].append({
                    "result": existing.get("result"),
                    "timestamp": existing.get("timestamp"),
                    "attempt": existing.get("attempts", 1)
                })
                
                # Update with new result
                existing["result"] = result
                existing["timestamp"] = timestamp
                existing["attempts"] = existing.get("attempts", 1) + 1
                
                # Limit history size
                max_history = 10
                if len(existing["history"]) > max_history:
                    existing["history"] = existing["history"][-max_history:]
    
    logger.debug(f"Merged tool results for {len(update)} tool calls")
    return merged


@safe_reducer
def merge_memory_layers(current: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge memory layer updates with intelligent conflict resolution.
    
    Args:
        current: Current memory state
        update: New memory updates
        
    Returns:
        Merged memory with timestamp-based conflict resolution
        
    Raises:
        ReducerError: If merge operation fails
    """
    if current is None and update is None:
        return {}
    
    merged = copy.deepcopy(current) if current else {}
    
    if not update:
        return merged
    
    if not isinstance(update, dict):
        raise ReducerError(f"Update must be a dictionary, got {type(update).__name__}")
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    for key, value in update.items():
        if key not in merged:
            # New memory entry
            merged[key] = {
                "value": value,
                "last_updated": timestamp,
                "update_count": 1
            }
        else:
            # Update existing memory
            existing = merged[key]
            
            # Ensure existing has proper structure
            if not isinstance(existing, dict):
                logger.debug(f"Converting simple memory value to structured format for key: {key}")
                existing = {"value": existing, "update_count": 1}
                merged[key] = existing
            
            # Simple last-write-wins with metadata
            existing["value"] = value
            existing["last_updated"] = timestamp
            existing["update_count"] = existing.get("update_count", 0) + 1
    
    logger.debug(f"Merged memory updates for {len(update)} keys")
    return merged


@safe_reducer
def merge_communication_messages(
    current: List[Dict[str, Any]], 
    update: List[Dict[str, Any]],
    max_messages: int = 1000
) -> List[Dict[str, Any]]:
    """
    Merge inter-agent communication messages, preserving order and deduplicating.
    
    Args:
        current: Current message list
        update: New messages to add
        max_messages: Maximum number of messages to keep
        
    Returns:
        Merged message list with deduplication and size limits
        
    Raises:
        ReducerError: If merge operation fails
    """
    if current is None and update is None:
        return []
    
    merged = copy.deepcopy(current) if current else []
    
    # Handle explicit empty list update - this clears the list
    if update is not None and len(update) == 0:
        return []
    
    if not update:
        return merged
    
    if not isinstance(update, list):
        raise ReducerError(f"Update must be a list, got {type(update).__name__}")
    
    if not isinstance(merged, list):
        logger.warning("Current messages is not a list, resetting to empty list")
        merged = []
    
    # Create set of existing message IDs for deduplication
    existing_ids = set()
    for msg in merged:
        if isinstance(msg, dict) and "id" in msg:
            existing_ids.add(msg["id"])
    
    # Add new messages if they don't already exist
    for msg in update:
        if not isinstance(msg, dict):
            logger.warning(f"Skipping invalid message (not a dict): {msg}")
            continue
        
        msg_id = msg.get("id")
        if msg_id and msg_id in existing_ids:
            logger.debug(f"Skipping duplicate message with ID: {msg_id}")
            continue
        
        # Add timestamp if not present
        if "timestamp" not in msg:
            msg["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        merged.append(msg)
        if msg_id:
            existing_ids.add(msg_id)
    
    # Sort by timestamp to maintain chronological order
    try:
        merged.sort(key=lambda x: x.get("timestamp", ""))
    except Exception as e:
        logger.warning(f"Failed to sort messages by timestamp: {e}")
    
    # Limit message history to prevent memory bloat
    if len(merged) > max_messages:
        merged = merged[-max_messages:]
        logger.debug(f"Trimmed message history to {max_messages} messages")
    
    logger.debug(f"Merged {len(update)} new messages")
    return merged


@safe_reducer
def merge_execution_trace(
    current: List[Dict[str, Any]], 
    update: List[Dict[str, Any]],
    max_entries: int = 5000
) -> List[Dict[str, Any]]:
    """
    Merge execution trace entries, maintaining chronological order.
    
    Args:
        current: Current trace entries
        update: New trace entries to add
        max_entries: Maximum number of trace entries to keep
        
    Returns:
        Merged trace with chronological ordering and size limits
        
    Raises:
        ReducerError: If merge operation fails
    """
    if current is None and update is None:
        return []
    
    merged = copy.deepcopy(current) if current else []
    
    if not update:
        return merged
    
    if not isinstance(update, list):
        raise ReducerError(f"Update must be a list, got {type(update).__name__}")
    
    if not isinstance(merged, list):
        logger.warning("Current trace is not a list, resetting to empty list")
        merged = []
    
    # Add new trace entries
    for entry in update:
        if not isinstance(entry, dict):
            logger.warning(f"Skipping invalid trace entry (not a dict): {entry}")
            continue
        
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        merged.append(entry)
    
    # Sort by timestamp
    try:
        merged.sort(key=lambda x: x.get("timestamp", ""))
    except Exception as e:
        logger.warning(f"Failed to sort trace entries by timestamp: {e}")
    
    # Limit trace size
    if len(merged) > max_entries:
        merged = merged[-max_entries:]
        logger.debug(f"Trimmed execution trace to {max_entries} entries")
    
    logger.debug(f"Merged {len(update)} trace entries")
    return merged


# Enhanced reducer registry with metadata
REDUCERS = {
    "agent_outputs": {
        "function": merge_agent_outputs,
        "description": "Merges agent outputs with history preservation",
        "strategy": ConflictResolutionStrategy.TIMESTAMP_BASED
    },
    "task_progress": {
        "function": aggregate_progress,
        "description": "Aggregates task progress with monotonic guarantees",
        "strategy": ConflictResolutionStrategy.MONOTONIC_INCREASE
    },
    "tool_permissions": {
        "function": resolve_permissions,
        "description": "Resolves tool permissions with security-first approach",
        "strategy": ConflictResolutionStrategy.MOST_RESTRICTIVE
    },
    "tool_results": {
        "function": merge_tool_results,
        "description": "Merges tool results with retry handling",
        "strategy": ConflictResolutionStrategy.KEEP_BOTH
    },
    "tool_calls": {
        "function": merge_communication_messages,
        "description": "Merges tool call lists with deduplication",
        "strategy": ConflictResolutionStrategy.MERGE_UNION
    },
    "short_term_memory": {
        "function": merge_memory_layers,
        "description": "Merges short-term memory with timestamps",
        "strategy": ConflictResolutionStrategy.LAST_WRITE_WINS
    },
    "working_memory": {
        "function": merge_memory_layers,
        "description": "Merges working memory with timestamps",
        "strategy": ConflictResolutionStrategy.LAST_WRITE_WINS
    },
    "shared_memory": {
        "function": merge_memory_layers,
        "description": "Merges shared memory with timestamps",
        "strategy": ConflictResolutionStrategy.LAST_WRITE_WINS
    },
    "agent_messages": {
        "function": merge_communication_messages,
        "description": "Merges agent messages with deduplication",
        "strategy": ConflictResolutionStrategy.MERGE_UNION
    },
    "help_requests": {
        "function": merge_communication_messages,
        "description": "Merges help requests with deduplication",
        "strategy": ConflictResolutionStrategy.MERGE_UNION
    },
    "broadcast_messages": {
        "function": merge_communication_messages,
        "description": "Merges broadcast messages with deduplication",
        "strategy": ConflictResolutionStrategy.MERGE_UNION
    },
    "pending_responses": {
        "function": merge_communication_messages,
        "description": "Merges pending responses with deduplication",
        "strategy": ConflictResolutionStrategy.MERGE_UNION
    },
    "execution_trace": {
        "function": merge_execution_trace,
        "description": "Merges execution trace with chronological ordering",
        "strategy": ConflictResolutionStrategy.MERGE_UNION
    },
    "error_log": {
        "function": merge_execution_trace,
        "description": "Merges error logs with chronological ordering",
        "strategy": ConflictResolutionStrategy.MERGE_UNION
    },
}


def get_reducer_info(field_name: str) -> Dict[str, Any]:
    """
    Get information about a reducer for a specific field.
    
    Args:
        field_name: Name of the state field
        
    Returns:
        Dictionary with reducer information
    """
    if field_name in REDUCERS:
        return REDUCERS[field_name].copy()
    else:
        return {
            "function": None,
            "description": "Last-write-wins (no custom reducer)",
            "strategy": ConflictResolutionStrategy.LAST_WRITE_WINS
        }


@safe_reducer
def apply_reducer(field_name: str, current: Any, update: Any, **kwargs) -> Any:
    """
    Apply the appropriate reducer for a specific field.
    
    Args:
        field_name: Name of the state field
        current: Current value
        update: Update value
        **kwargs: Additional arguments passed to the reducer
        
    Returns:
        Merged value using appropriate reducer
        
    Raises:
        ReducerError: If reducer application fails
    """
    if field_name in REDUCERS:
        reducer_info = REDUCERS[field_name]
        reducer_func = reducer_info["function"]
        
        # Pass additional kwargs to reducer if it supports them
        try:
            import inspect
            sig = inspect.signature(reducer_func)
            if len(sig.parameters) > 2:  # More than just current and update
                return reducer_func(current, update, **kwargs)
            else:
                return reducer_func(current, update)
        except Exception as e:
            logger.error(f"Failed to apply reducer for field '{field_name}': {str(e)}")
            raise ReducerError(f"Reducer application failed for field '{field_name}': {str(e)}") from e
    else:
        # Default behavior: last write wins (including None values)
        logger.debug(f"No custom reducer for field '{field_name}', using last-write-wins")
        return update


@safe_reducer
def merge_states(base_state: Dict[str, Any], state_updates: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """
    Merge multiple state updates into a base state using appropriate reducers.
    
    Args:
        base_state: Base state to merge into
        state_updates: Updates to apply
        **kwargs: Additional arguments passed to reducers
        
    Returns:
        Merged state with all updates applied
        
    Raises:
        ReducerError: If state merging fails
    """
    if not isinstance(base_state, dict):
        raise ReducerError(f"Base state must be a dictionary, got {type(base_state).__name__}")
    
    if not isinstance(state_updates, dict):
        raise ReducerError(f"State updates must be a dictionary, got {type(state_updates).__name__}")
    
    merged = copy.deepcopy(base_state)
    errors = []
    
    for field, update_value in state_updates.items():
        try:
            if field in merged:
                current_value = merged[field]
                merged[field] = apply_reducer(field, current_value, update_value, **kwargs)
            else:
                merged[field] = update_value
        except ReducerError as e:
            errors.append(f"Field '{field}': {str(e)}")
        except Exception as e:
            errors.append(f"Field '{field}': Unexpected error - {str(e)}")
    
    if errors:
        error_msg = f"State merge completed with errors:\n" + "\n".join(f"  - {error}" for error in errors)
        logger.error(error_msg)
        # Continue with partial merge, but log the errors
    
    logger.debug(f"Merged state updates for {len(state_updates)} fields")
    return merged


def validate_reducer_performance(field_name: str, data_size: int, iterations: int = 100) -> Dict[str, float]:
    """
    Validate reducer performance with test data.
    
    Args:
        field_name: Name of the field to test
        data_size: Size of test data
        iterations: Number of test iterations
        
    Returns:
        Performance metrics dictionary
    """
    import time
    import random
    
    if field_name not in REDUCERS:
        return {"error": "No reducer found for field"}
    
    reducer_func = REDUCERS[field_name]["function"]
    
    # Generate test data based on field type
    def generate_test_data(size: int):
        if field_name in ["agent_outputs", "tool_results", "tool_permissions"]:
            return {f"item_{i}": {"data": f"value_{i}"} for i in range(size)}
        elif field_name in ["task_progress"]:
            return {f"task_{i}": random.uniform(0, 100) for i in range(size)}
        elif field_name in ["agent_messages", "execution_trace", "tool_calls"]:
            return [{"id": f"msg_{i}", "data": f"content_{i}"} for i in range(size)]
        else:
            return {f"key_{i}": f"value_{i}" for i in range(size)}
    
    current_data = generate_test_data(data_size)
    update_data = generate_test_data(data_size // 2)
    
    # Perform timing tests
    times = []
    for _ in range(iterations):
        start_time = time.perf_counter()
        try:
            result = reducer_func(current_data, update_data)
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        except Exception as e:
            logger.warning(f"Performance test failed for {field_name}: {e}")
            return {"error": str(e)}
    
    return {
        "field": field_name,
        "data_size": data_size,
        "iterations": iterations,
        "avg_time": sum(times) / len(times),
        "min_time": min(times),
        "max_time": max(times),
        "total_time": sum(times)
    }