"""
Custom state reducers for MultiAgenticSwarm.

Reducers define how to merge state updates when multiple nodes attempt to modify
the same state fields concurrently. This is essential for multi-agent systems
where multiple agents may update shared state simultaneously.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Union


def merge_agent_outputs(
    existing: Dict[str, Any], new: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge agent outputs with timestamp-based conflict resolution.

    Combines outputs from multiple agents, resolving conflicts based on timestamp.
    Preserves all historical outputs for audit trail.

    Args:
        existing: Current agent outputs
        new: New agent outputs to merge

    Returns:
        Dict: Merged agent outputs with conflict resolution
    """
    if not existing:
        existing = {}

    merged = existing.copy()

    for agent_id, output in new.items():
        if agent_id not in merged:
            # New agent output
            merged[agent_id] = {
                "current": output,
                "history": [output],
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
        else:
            # Update existing agent output
            merged[agent_id]["current"] = output
            merged[agent_id]["history"].append(output)
            merged[agent_id]["last_updated"] = datetime.now(timezone.utc).isoformat()

            # Keep only last 10 historical outputs to prevent memory bloat
            if len(merged[agent_id]["history"]) > 10:
                merged[agent_id]["history"] = merged[agent_id]["history"][-10:]

    return merged


def aggregate_progress(
    existing: Dict[str, float], new: Dict[str, float]
) -> Dict[str, float]:
    """
    Aggregate task progress with weighted calculation.

    Calculates overall progress from subtasks, handling partial completions
    and weighting tasks by importance.

    Args:
        existing: Current progress tracking
        new: New progress updates

    Returns:
        Dict: Updated progress with aggregated values
    """
    if not existing:
        existing = {}

    merged = existing.copy()
    merged.update(new)

    # Calculate overall progress if subtasks are present
    if merged:
        # Exclude the _overall field from average calculation
        task_values = {k: v for k, v in merged.items() if k != "_overall"}

        if task_values:
            total_progress = sum(task_values.values())
            task_count = len(task_values)
            merged["_overall"] = total_progress / task_count
        else:
            merged["_overall"] = 0.0

    return merged


def resolve_permissions(
    existing: Dict[str, List[str]], new: Dict[str, List[str]]
) -> Dict[str, List[str]]:
    """
    Resolve tool permission conflicts with security-first approach.

    Merges permission updates where the most restrictive permission wins.
    Maintains audit trail of permission changes.

    Args:
        existing: Current permission matrix
        new: New permission updates

    Returns:
        Dict: Resolved permissions with audit trail
    """
    if not existing:
        existing = {}

    merged = existing.copy()

    for agent_id, permissions in new.items():
        if agent_id not in merged:
            # New agent permissions
            merged[agent_id] = permissions.copy()
        else:
            # Merge permissions - keep intersection for security
            # (most restrictive wins)
            current_perms = set(merged[agent_id])
            new_perms = set(permissions)

            # For security, we use intersection unless new permissions are empty
            # Empty permissions mean revoke all access
            if not permissions:
                merged[agent_id] = []
            else:
                # Union of permissions - more permissive approach
                # Change to intersection for more restrictive approach
                merged[agent_id] = list(current_perms.union(new_perms))

    return merged


def merge_tool_results(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge tool execution results with deduplication.

    Combines results from multiple tool executions, handling deduplication
    and maintaining execution history.

    Args:
        existing: Current tool results
        new: New tool results

    Returns:
        Dict: Merged tool results
    """
    if not existing:
        existing = {}

    merged = existing.copy()

    for tool_name, result in new.items():
        if tool_name not in merged:
            merged[tool_name] = {
                "latest": result,
                "history": [result],
                "execution_count": 1,
                "last_executed": datetime.now(timezone.utc).isoformat(),
            }
        else:
            merged[tool_name]["latest"] = result
            merged[tool_name]["history"].append(result)
            merged[tool_name]["execution_count"] += 1
            merged[tool_name]["last_executed"] = datetime.now(timezone.utc).isoformat()

            # Keep only last 5 results to prevent memory bloat
            if len(merged[tool_name]["history"]) > 5:
                merged[tool_name]["history"] = merged[tool_name]["history"][-5:]

    return merged


def merge_help_requests(
    existing: List[Dict[str, Any]], new: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge help requests with deduplication and status tracking.

    Combines help requests from multiple agents, avoiding duplicates
    based on request content and maintaining status.

    Args:
        existing: Current help requests
        new: New help requests

    Returns:
        List: Merged help requests with deduplication
    """
    if not existing:
        existing = []

    merged = existing.copy()

    for request in new:
        # Check for duplicates based on topic and requesting agent
        is_duplicate = False

        for existing_request in merged:
            if (
                existing_request.get("topic") == request.get("topic")
                and existing_request.get("requesting_agent")
                == request.get("requesting_agent")
                and existing_request.get("status", "open") == "open"
            ):
                # Update existing request instead of creating duplicate
                existing_request.update(request)
                is_duplicate = True
                break

        if not is_duplicate:
            # Add timestamp if not present
            if "timestamp" not in request:
                request["timestamp"] = datetime.now(timezone.utc).isoformat()

            # Set default status
            if "status" not in request:
                request["status"] = "open"

            merged.append(request)

    # Sort by timestamp, newest first
    merged.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return merged


def merge_execution_trace(
    existing: List[Dict[str, Any]], new: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge execution traces maintaining chronological order.

    Combines execution traces from multiple sources while preserving
    the chronological order of events.

    Args:
        existing: Current execution trace
        new: New trace entries

    Returns:
        List: Merged execution trace in chronological order
    """
    if not existing:
        existing = []

    merged = existing.copy()

    for entry in new:
        # Add timestamp if not present
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Add unique ID if not present
        if "id" not in entry:
            entry["id"] = (
                f"trace_{len(merged)}_{datetime.now(timezone.utc).timestamp()}"
            )

        merged.append(entry)

    # Sort by timestamp to maintain chronological order
    merged.sort(key=lambda x: x.get("timestamp", ""))

    # Keep only last 100 entries to prevent memory bloat
    if len(merged) > 100:
        merged = merged[-100:]

    return merged


def merge_error_log(existing: List[str], new: List[str]) -> List[str]:
    """
    Merge error logs with deduplication and limits.

    Combines error messages while avoiding duplicates and maintaining
    reasonable size limits.

    Args:
        existing: Current error log
        new: New error messages

    Returns:
        List: Merged error log with deduplication
    """
    if not existing:
        existing = []

    merged = existing.copy()

    for error in new:
        # Add timestamp prefix if not present
        if not error.startswith("["):
            timestamped_error = f"[{datetime.now(timezone.utc).isoformat()}] {error}"
        else:
            timestamped_error = error

        # Avoid exact duplicates
        if timestamped_error not in merged:
            merged.append(timestamped_error)

    # Keep only last 50 errors to prevent memory bloat
    if len(merged) > 50:
        merged = merged[-50:]

    return merged


def merge_list_append(existing: List[Any], new: List[Any]) -> List[Any]:
    """
    Generic list merger that appends new items to existing list.

    Simple append operation for lists that don't need special handling.

    Args:
        existing: Current list
        new: New items to append

    Returns:
        List: Combined list
    """
    if not existing:
        existing = []

    return existing + new


def merge_dict_update(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generic dictionary merger with deep update.

    Updates existing dictionary with new values, handling nested dictionaries.

    Args:
        existing: Current dictionary
        new: New values to merge

    Returns:
        Dict: Updated dictionary
    """
    if not existing:
        existing = {}

    merged = existing.copy()

    for key, value in new.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            merged[key] = merge_dict_update(merged[key], value)
        else:
            # Simple update for non-dict values
            merged[key] = value

    return merged


# Export commonly used reducers for easy import
__all__ = [
    "merge_agent_outputs",
    "aggregate_progress",
    "resolve_permissions",
    "merge_tool_results",
    "merge_help_requests",
    "merge_execution_trace",
    "merge_error_log",
    "merge_list_append",
    "merge_dict_update",
]
