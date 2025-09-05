"""
Migration template for schema changes.

This is a template showing best practices for migration scripts.
Copy this file and modify it for your specific migration needs.

Migration Naming Convention:
- File: v{from_major}_{from_minor}_{from_patch}_to_v{to_major}_{to_minor}_{to_patch}.py
- Function: migrate_{from_major}_{from_minor}_to_{to_major}_{to_minor}

Best Practices:
1. Always preserve data when possible
2. Provide default values for new fields
3. Log all changes in execution_trace
4. Handle edge cases and malformed data
5. Test with real data before deploying
6. Consider reverse migrations for testing
"""

from typing import Dict, Any
from datetime import datetime

from multiagenticswarm.core.state_migration import register_migration


# Template migration function - replace versions and logic as needed
@register_migration("1.1.0", "1.2.0")
def migrate_1_1_to_1_2(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migration template from version 1.1.0 to 1.2.0.
    
    Replace this docstring with actual changes being made.
    Example: "Add enhanced memory management and agent state isolation."
    """
    migrated_state = dict(state)
    
    # === STEP 1: Add new fields ===
    # Add new fields with sensible defaults
    if "new_field" not in migrated_state:
        migrated_state["new_field"] = "default_value"
    
    # === STEP 2: Transform existing fields ===
    # Example: Convert field format or structure
    if "old_format_field" in migrated_state:
        # Transform to new format
        old_value = migrated_state["old_format_field"]
        if isinstance(old_value, str):
            # Convert string to dict format
            migrated_state["new_format_field"] = {
                "value": old_value,
                "metadata": {"converted_from": "string"}
            }
        else:
            # Handle unexpected format gracefully
            migrated_state["new_format_field"] = {
                "value": str(old_value),
                "metadata": {"converted_from": type(old_value).__name__}
            }
        
        # Optionally remove old field or keep for compatibility
        # migrated_state.pop("old_format_field")
    
    # === STEP 3: Handle data validation and cleanup ===
    # Validate and clean up existing data
    if "tool_permissions" in migrated_state:
        # Ensure all agent IDs are strings
        clean_permissions = {}
        for agent_id, permissions in migrated_state["tool_permissions"].items():
            clean_agent_id = str(agent_id)
            if isinstance(permissions, list):
                clean_permissions[clean_agent_id] = permissions
            else:
                # Handle malformed data
                clean_permissions[clean_agent_id] = []
        migrated_state["tool_permissions"] = clean_permissions
    
    # === STEP 4: Update metadata and tracking ===
    # Update performance metrics
    if "performance_metrics" in migrated_state:
        perf_metrics = migrated_state["performance_metrics"]
        if "migration_applied" not in perf_metrics:
            perf_metrics["migration_applied"] = {}
        
        perf_metrics["migration_applied"]["1_1_to_1_2"] = {
            "timestamp": datetime.now().isoformat(),
            "changes_applied": [
                "added_new_field",
                "transformed_old_format_field",
                "cleaned_tool_permissions"
            ]
        }
    
    # === STEP 5: Log migration in execution trace ===
    if "execution_trace" in migrated_state:
        migration_trace = {
            "event": "state_migration",
            "timestamp": datetime.now().isoformat(),
            "details": {
                "from_version": "1.1.0",
                "to_version": "1.2.0",
                "changes": [
                    "Added new_field with default value",
                    "Transformed old_format_field to new_format_field",
                    "Cleaned and validated tool_permissions"
                ]
            }
        }
        migrated_state["execution_trace"].append(migration_trace)
    
    return migrated_state


# Optional reverse migration for testing
@register_migration("1.2.0", "1.1.0")  
def migrate_1_2_to_1_1(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reverse migration from version 1.2.0 to 1.1.0.
    
    Note: Reverse migrations may involve data loss and should be used
    primarily for testing migration roundtrips.
    """
    migrated_state = dict(state)
    
    # Remove fields added in 1.2.0
    migrated_state.pop("new_field", None)
    
    # Attempt to restore old format if possible
    if "new_format_field" in migrated_state:
        new_format_data = migrated_state["new_format_field"]
        if isinstance(new_format_data, dict) and "value" in new_format_data:
            # Try to restore original format
            migrated_state["old_format_field"] = new_format_data["value"]
        migrated_state.pop("new_format_field", None)
    
    # Clean up migration metadata
    if "performance_metrics" in migrated_state:
        perf_metrics = migrated_state["performance_metrics"]
        if "migration_applied" in perf_metrics:
            perf_metrics["migration_applied"].pop("1_1_to_1_2", None)
    
    # Log reverse migration
    if "execution_trace" in migrated_state:
        migration_trace = {
            "event": "state_reverse_migration",
            "timestamp": datetime.now().isoformat(),
            "details": {
                "from_version": "1.2.0", 
                "to_version": "1.1.0",
                "changes": [
                    "Removed new_field",
                    "Restored old_format_field from new_format_field"
                ]
            }
        }
        migrated_state["execution_trace"].append(migration_trace)
    
    return migrated_state


# Example of handling breaking changes
@register_migration("1.2.0", "2.0.0")
def migrate_1_2_to_2_0(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Major version migration from 1.2.0 to 2.0.0.
    
    Breaking changes:
    - Restructure agent_outputs format
    - Remove deprecated fields
    - Update message format
    """
    migrated_state = dict(state)
    
    # === BREAKING CHANGE 1: Restructure agent_outputs ===
    if "agent_outputs" in migrated_state:
        old_outputs = migrated_state["agent_outputs"]
        new_outputs = {}
        
        for agent_id, output_data in old_outputs.items():
            # Convert to new structured format
            new_outputs[agent_id] = {
                "latest_output": output_data,
                "output_history": [output_data] if output_data else [],
                "metadata": {
                    "migrated_from": "1.2.0",
                    "original_format": "simple"
                }
            }
        
        migrated_state["agent_outputs"] = new_outputs
    
    # === BREAKING CHANGE 2: Remove deprecated fields ===
    deprecated_fields = ["old_deprecated_field", "legacy_config"]
    for field in deprecated_fields:
        if field in migrated_state:
            # Optionally preserve data in migration backup
            if "_migration_backup" not in migrated_state:
                migrated_state["_migration_backup"] = {}
            migrated_state["_migration_backup"][field] = migrated_state.pop(field)
    
    # === BREAKING CHANGE 3: Update message format (if needed) ===
    # This would depend on actual LangChain message format changes
    
    # Update version-specific metadata
    migrated_state["major_version_migration"] = {
        "from_version": "1.2.0",
        "to_version": "2.0.0", 
        "timestamp": datetime.now().isoformat(),
        "breaking_changes": [
            "restructured_agent_outputs",
            "removed_deprecated_fields"
        ]
    }
    
    # Log major migration
    if "execution_trace" in migrated_state:
        migration_trace = {
            "event": "major_version_migration",
            "timestamp": datetime.now().isoformat(),
            "details": {
                "from_version": "1.2.0",
                "to_version": "2.0.0",
                "breaking_changes": True,
                "changes": [
                    "Restructured agent_outputs to new format with history",
                    "Removed deprecated fields (backed up)",
                    "Added major_version_migration metadata"
                ]
            }
        }
        migrated_state["execution_trace"].append(migration_trace)
    
    return migrated_state