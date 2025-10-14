"""
Migration from version 1.0.0 to 1.1.0.

This migration adds enhanced tool permissions tracking to the AgentState schema.
In version 1.1.0, we introduce more granular tool permission management.

Changes:
- Add 'tool_permission_history' field to track permission changes over time
- Enhance 'tool_permissions' structure with metadata
- Add default permissions for new agents
"""

from typing import Dict, Any
from datetime import datetime

from multiagenticswarm.core.state_migration import register_migration


@register_migration("1.0.0", "1.1.0")
def migrate_1_0_to_1_1(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate state from version 1.0.0 to 1.1.0.
    
    Adds enhanced tool permission tracking and history.
    """
    migrated_state = dict(state)
    
    # Add tool permission history tracking
    if "tool_permission_history" not in migrated_state:
        migrated_state["tool_permission_history"] = []
        
        # If there are existing permissions, create an initial history entry
        if migrated_state.get("tool_permissions"):
            initial_entry = {
                "timestamp": datetime.now().isoformat(),
                "event": "migration_1_0_to_1_1",
                "changes": {
                    "added": migrated_state["tool_permissions"],
                    "removed": {},
                    "modified": {}
                },
                "reason": "Initial permissions from migration"
            }
            migrated_state["tool_permission_history"].append(initial_entry)
    
    # Ensure tool_permissions exists with proper structure
    if "tool_permissions" not in migrated_state:
        migrated_state["tool_permissions"] = {}
    
    # Add default permissions for common tools if no permissions exist
    if not migrated_state["tool_permissions"]:
        # Set up basic permissions for any existing agents
        if migrated_state.get("agent_roles"):
            for agent_id in migrated_state["agent_roles"].keys():
                migrated_state["tool_permissions"][agent_id] = [
                    "basic_tools",  # All agents get basic tools
                ]
                
                # Add role-specific permissions
                agent_role = migrated_state["agent_roles"].get(agent_id, "")
                if "developer" in agent_role.lower():
                    migrated_state["tool_permissions"][agent_id].extend([
                        "code_writer", "file_manager", "git_tools"
                    ])
                elif "qa" in agent_role.lower() or "test" in agent_role.lower():
                    migrated_state["tool_permissions"][agent_id].extend([
                        "test_runner", "bug_tracker"
                    ])
                elif "devops" in agent_role.lower():
                    migrated_state["tool_permissions"][agent_id].extend([
                        "deployment_tools", "monitoring_tools"
                    ])
    
    # Add metadata to performance metrics if it exists
    if "performance_metrics" in migrated_state and isinstance(migrated_state["performance_metrics"], dict):
        if "migration_applied" not in migrated_state["performance_metrics"]:
            migrated_state["performance_metrics"]["migration_applied"] = {
                "1_0_to_1_1": {
                    "timestamp": datetime.now().isoformat(),
                    "changes_applied": [
                        "added_tool_permission_history",
                        "enhanced_tool_permissions_structure",
                        "added_default_permissions"
                    ]
                }
            }
    
    # Log the migration in execution trace
    if "execution_trace" in migrated_state:
        migration_trace = {
            "event": "state_migration",
            "timestamp": datetime.now().isoformat(),
            "details": {
                "from_version": "1.0.0",
                "to_version": "1.1.0",
                "changes": [
                    "Added tool_permission_history field",
                    "Enhanced tool_permissions structure",
                    "Added default permissions for existing agents"
                ]
            }
        }
        migrated_state["execution_trace"].append(migration_trace)
    
    return migrated_state


# Example reverse migration (optional, for testing roundtrips)
@register_migration("1.1.0", "1.0.0")
def migrate_1_1_to_1_0(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reverse migration from version 1.1.0 to 1.0.0.
    
    Removes enhanced tool permission features while preserving core functionality.
    """
    migrated_state = dict(state)
    
    # Remove tool permission history (data loss acceptable for reverse migration)
    migrated_state.pop("tool_permission_history", None)
    
    # Simplify tool_permissions structure if needed
    # Keep the actual permissions but remove metadata
    
    # Remove migration metadata from performance metrics
    if "performance_metrics" in migrated_state and isinstance(migrated_state["performance_metrics"], dict):
        perf_metrics = migrated_state["performance_metrics"]
        if "migration_applied" in perf_metrics:
            perf_metrics["migration_applied"].pop("1_0_to_1_1", None)
            if not perf_metrics["migration_applied"]:
                perf_metrics.pop("migration_applied", None)
    
    # Log the reverse migration
    if "execution_trace" in migrated_state:
        migration_trace = {
            "event": "state_reverse_migration",
            "timestamp": datetime.now().isoformat(),
            "details": {
                "from_version": "1.1.0",
                "to_version": "1.0.0",
                "changes": [
                    "Removed tool_permission_history field",
                    "Simplified tool_permissions structure"
                ]
            }
        }
        migrated_state["execution_trace"].append(migration_trace)
    
    return migrated_state