"""
Custom state reducers for MultiAgenticSwarm.

This module provides custom reducers that define how to merge state updates
when multiple agents or processes modify the state concurrently. These reducers
work alongside LangGraph's built-in reducers like add_messages.

Reducers ensure consistent and predictable state merging behavior while
preserving important historical information and resolving conflicts intelligently.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
import copy

from ..utils.logger import get_logger

logger = get_logger(__name__)


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
    """
    merged = copy.deepcopy(current) if current else {}
    
    if not update:
        return merged
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    for agent_id, output in update.items():
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
            
            # Move current to history and set new current
            if "current" in existing:
                # Add current to history if it's different from new output
                if existing["current"] != output:
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
            if len(existing["history"]) > max_history:
                existing["history"] = existing["history"][-max_history:]
    
    logger.debug(f"Merged agent outputs for {len(update)} agents")
    return merged


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
    """
    merged = copy.deepcopy(current) if current else {}
    
    if not update:
        return merged
    
    for task_id, new_progress in update.items():
        # Validate progress value
        if not isinstance(new_progress, (int, float)):
            logger.warning(f"Invalid progress value for task {task_id}: {new_progress}")
            continue
            
        # Clamp progress to valid range [0, 100]
        new_progress = max(0.0, min(100.0, float(new_progress)))
        
        if task_id not in merged:
            # New task progress
            merged[task_id] = new_progress
        else:
            # Update existing task progress
            current_progress = merged[task_id]
            
            # Ensure monotonic progress (no going backwards)
            if new_progress >= current_progress:
                merged[task_id] = new_progress
            else:
                logger.warning(
                    f"Progress regression detected for task {task_id}: "
                    f"{current_progress}% -> {new_progress}%. Keeping higher value."
                )
                # Keep the higher progress value
                merged[task_id] = max(current_progress, new_progress)
    
    logger.debug(f"Aggregated progress for {len(update)} tasks")
    return merged


def resolve_permissions(
    current: Dict[str, List[str]], 
    update: Dict[str, List[str]]
) -> Dict[str, List[str]]:
    """
    Resolve tool permission updates with security-first conflict resolution.
    
    This reducer merges permission updates while applying security-first rules:
    - Most restrictive permission wins in conflicts
    - Maintains audit trail of permission changes
    - Prevents privilege escalation
    
    Args:
        current: Current tool_permissions state
        update: New permissions to merge
        
    Returns:
        Merged permissions with security-first resolution
    """
    merged = copy.deepcopy(current) if current else {}
    
    if not update:
        return merged
    
    for agent_id, new_permissions in update.items():
        if not isinstance(new_permissions, list):
            logger.warning(f"Invalid permissions format for agent {agent_id}: {new_permissions}")
            continue
        
        # Normalize permissions list
        new_permissions = [str(perm).strip() for perm in new_permissions if perm]
        new_permissions = list(set(new_permissions))  # Remove duplicates
        
        if agent_id not in merged:
            # New agent permissions
            merged[agent_id] = new_permissions
        else:
            # Merge with existing permissions
            current_permissions = set(merged[agent_id])
            new_permission_set = set(new_permissions)
            
            # Security-first merge: intersection (most restrictive)
            # Only permissions that are in BOTH current and new are granted
            intersection = current_permissions.intersection(new_permission_set)
            
            # However, if new permissions is empty, it means revoke all
            if not new_permissions:
                merged[agent_id] = []
                logger.info(f"All permissions revoked for agent {agent_id}")
            elif not intersection and (current_permissions or new_permission_set):
                # If no intersection but both have permissions, it's a conflict
                # Apply most restrictive (empty set)
                logger.warning(
                    f"Permission conflict for agent {agent_id}: "
                    f"current={sorted(current_permissions)}, "
                    f"new={sorted(new_permission_set)}. Applying most restrictive."
                )
                merged[agent_id] = []
            else:
                merged[agent_id] = sorted(list(intersection))
    
    logger.debug(f"Resolved permissions for {len(update)} agents")
    return merged


def merge_tool_results(current: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge tool execution results, preserving history and handling duplicates.
    
    Args:
        current: Current tool_results state
        update: New tool results to merge
        
    Returns:
        Merged tool results with deduplication
    """
    merged = copy.deepcopy(current) if current else {}
    
    if not update:
        return merged
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    for tool_call_id, result in update.items():
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
            
            # If result is different, it might be a retry
            if existing.get("result") != result:
                # Store previous result in history
                if "history" not in existing:
                    existing["history"] = []
                
                existing["history"].append({
                    "result": existing["result"],
                    "timestamp": existing.get("timestamp"),
                    "attempt": existing.get("attempts", 1)
                })
                
                # Update with new result
                existing["result"] = result
                existing["timestamp"] = timestamp
                existing["attempts"] = existing.get("attempts", 1) + 1
    
    logger.debug(f"Merged tool results for {len(update)} tool calls")
    return merged


def merge_memory_layers(current: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge memory layer updates with intelligent conflict resolution.
    
    Args:
        current: Current memory state
        update: New memory updates
        
    Returns:
        Merged memory with timestamp-based conflict resolution
    """
    merged = copy.deepcopy(current) if current else {}
    
    if not update:
        return merged
    
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
            
            # Simple last-write-wins with metadata
            existing["value"] = value
            existing["last_updated"] = timestamp
            existing["update_count"] = existing.get("update_count", 0) + 1
    
    logger.debug(f"Merged memory updates for {len(update)} keys")
    return merged


def merge_communication_messages(
    current: List[Dict[str, Any]], 
    update: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge inter-agent communication messages, preserving order and deduplicating.
    
    Args:
        current: Current message list
        update: New messages to add
        
    Returns:
        Merged message list with deduplication
    """
    merged = copy.deepcopy(current) if current else []
    
    if not update:
        return merged
    
    # Create set of existing message IDs for deduplication
    existing_ids = set()
    for msg in merged:
        if "id" in msg:
            existing_ids.add(msg["id"])
    
    # Add new messages if they don't already exist
    for msg in update:
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
    merged.sort(key=lambda x: x.get("timestamp", ""))
    
    # Limit message history to prevent memory bloat
    max_messages = 1000
    if len(merged) > max_messages:
        merged = merged[-max_messages:]
        logger.debug(f"Trimmed message history to {max_messages} messages")
    
    logger.debug(f"Merged {len(update)} new messages")
    return merged


def merge_execution_trace(
    current: List[Dict[str, Any]], 
    update: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge execution trace entries, maintaining chronological order.
    
    Args:
        current: Current trace entries
        update: New trace entries to add
        
    Returns:
        Merged trace with chronological ordering
    """
    merged = copy.deepcopy(current) if current else []
    
    if not update:
        return merged
    
    # Add new trace entries
    for entry in update:
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        merged.append(entry)
    
    # Sort by timestamp
    merged.sort(key=lambda x: x.get("timestamp", ""))
    
    # Limit trace size
    max_trace_entries = 5000
    if len(merged) > max_trace_entries:
        merged = merged[-max_trace_entries:]
        logger.debug(f"Trimmed execution trace to {max_trace_entries} entries")
    
    logger.debug(f"Merged {len(update)} trace entries")
    return merged


# Reducer registry for easy lookup
REDUCERS = {
    "agent_outputs": merge_agent_outputs,
    "task_progress": aggregate_progress,
    "tool_permissions": resolve_permissions,
    "tool_results": merge_tool_results,
    "tool_calls": merge_communication_messages,  # Tool calls are lists that should be merged
    "short_term_memory": merge_memory_layers,
    "working_memory": merge_memory_layers,
    "shared_memory": merge_memory_layers,
    "agent_messages": merge_communication_messages,
    "help_requests": merge_communication_messages,
    "broadcast_messages": merge_communication_messages,
    "pending_responses": merge_communication_messages,
    "execution_trace": merge_execution_trace,
    "error_log": merge_execution_trace,
}


def apply_reducer(field_name: str, current: Any, update: Any) -> Any:
    """
    Apply the appropriate reducer for a specific field.
    
    Args:
        field_name: Name of the state field
        current: Current value
        update: Update value
        
    Returns:
        Merged value using appropriate reducer
    """
    if field_name in REDUCERS:
        return REDUCERS[field_name](current, update)
    else:
        # Default behavior: last write wins
        logger.debug(f"No custom reducer for field '{field_name}', using last-write-wins")
        return update if update is not None else current


def merge_states(base_state: Dict[str, Any], state_updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple state updates into a base state using appropriate reducers.
    
    Args:
        base_state: Base state to merge into
        state_updates: Updates to apply
        
    Returns:
        Merged state with all updates applied
    """
    merged = copy.deepcopy(base_state)
    
    for field, update_value in state_updates.items():
        if field in merged:
            current_value = merged[field]
            merged[field] = apply_reducer(field, current_value, update_value)
        else:
            merged[field] = update_value
    
    logger.debug(f"Merged state updates for {len(state_updates)} fields")
    return merged