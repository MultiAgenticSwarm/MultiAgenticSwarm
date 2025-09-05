"""
State Migration System for MultiAgenticSwarm.

This module provides a comprehensive migration system for transforming AgentState objects
from one schema version to another, preserving data during system updates.

Key Features:
- Version tracking and compatibility checking
- Automatic migration on state load
- Migration function registry
- Backup and restore capabilities
- Validation after migration
- Testing utilities for migration development

Usage:
    from multiagenticswarm.core.state_migration import (
        migrate_state,
        auto_migrate_state,
        register_migration
    )
    
    # Register a migration
    @register_migration("1.0.0", "1.1.0")
    def migrate_1_0_to_1_1(state):
        # Add new field with default value
        state["new_field"] = default_value
        return state
    
    # Auto-migrate state to current version
    migrated_state = auto_migrate_state(old_state)
"""

from typing import Any, Dict, List, Callable, Optional, Tuple
from datetime import datetime
import copy
import importlib
import importlib.util
import os
from pathlib import Path

from packaging.version import Version

from ..utils.logger import get_logger

logger = get_logger(__name__)


class StateVersionError(Exception):
    """Raised when state version operations fail."""
    pass


class MigrationError(Exception):
    """Raised when migration operations fail."""
    pass


class MigrationTestError(Exception):
    """Raised when migration testing fails."""
    pass


def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two semantic version strings using the packaging library.

    This implementation uses the well-established packaging.version library
    that handles edge cases, pre-releases, and build metadata more robustly
    than custom implementations.

    Args:
        version1: First version string (e.g., "1.0.0", "2.0.0-alpha.1")
        version2: Second version string (e.g., "1.1.0", "2.0.0-beta.2")

    Returns:
        -1 if version1 < version2
         0 if version1 == version2
         1 if version1 > version2

    Raises:
        StateVersionError: If version format is invalid
    """
    try:
        v1 = Version(version1)
        v2 = Version(version2)

        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1
        else:
            return 0
    except Exception as e:
        raise StateVersionError(f"Invalid version format: {e}") from e


def is_compatible_version(state_version: str, required_version: str) -> bool:
    """
    Check if a state version is compatible with the required version.

    Args:
        state_version: Version of the state
        required_version: Required minimum version

    Returns:
        True if compatible, False otherwise
    """
    try:
        return compare_versions(state_version, required_version) >= 0
    except StateVersionError:
        logger.warning(
            f"Unable to compare versions: {state_version} vs {required_version}"
        )
        return False


# Migration function registry
_MIGRATION_FUNCTIONS: Dict[str, Callable] = {}


def register_migration(from_version: str, to_version: str):
    """
    Decorator to register a migration function.

    Args:
        from_version: Source version
        to_version: Target version

    Example:
        @register_migration("1.0.0", "1.1.0")
        def migrate_1_0_to_1_1(state):
            # Add new field introduced in v1.1.0
            if "tool_permissions" not in state:
                state["tool_permissions"] = {}
            return state
    """

    def decorator(func):
        key = f"{from_version}->{to_version}"
        _MIGRATION_FUNCTIONS[key] = func
        logger.debug(f"Registered migration function: {key}")
        return func

    return decorator


def get_registered_migrations() -> Dict[str, Callable]:
    """
    Get all registered migration functions.

    Returns:
        Dictionary of migration key -> function mappings
    """
    return _MIGRATION_FUNCTIONS.copy()


def clear_migration_registry():
    """
    Clear the migration function registry.
    
    Note: This is mainly for testing purposes.
    """
    global _MIGRATION_FUNCTIONS
    _MIGRATION_FUNCTIONS.clear()
    logger.debug("Migration function registry cleared")


def migrate_state(state: Dict[str, Any], target_version: str) -> Dict[str, Any]:
    """
    Migrate state from its current version to the target version.

    Args:
        state: State dictionary to migrate
        target_version: Target schema version

    Returns:
        Migrated state dictionary

    Raises:
        StateVersionError: If migration is not possible
        MigrationError: If migration execution fails
    """
    current_version = state.get("state_version", "0.0.0")

    if current_version == target_version:
        logger.debug(f"State already at target version {target_version}")
        return state

    logger.info(f"Migrating state from version {current_version} to {target_version}")

    # Find migration path
    migration_path = _find_migration_path(current_version, target_version)
    if not migration_path:
        raise StateVersionError(
            f"No migration path found from {current_version} to {target_version}"
        )

    # Apply migrations step by step
    migrated_state = dict(state)
    for from_ver, to_ver in migration_path:
        migration_key = f"{from_ver}->{to_ver}"
        if migration_key not in _MIGRATION_FUNCTIONS:
            raise StateVersionError(f"Missing migration function: {migration_key}")

        logger.debug(f"Applying migration: {migration_key}")
        try:
            migrated_state = _MIGRATION_FUNCTIONS[migration_key](migrated_state)
            migrated_state["state_version"] = to_ver
            logger.debug(f"Successfully applied migration: {migration_key}")
        except Exception as e:
            raise MigrationError(
                f"Migration failed at {migration_key}: {str(e)}"
            ) from e

    # Validate migrated state using state module validation
    try:
        from .state import validate_state
        validate_state(migrated_state)  # type: ignore
        logger.info(
            f"State migration completed successfully: {current_version} -> {target_version}"
        )
    except ValueError as e:
        raise MigrationError(f"Migrated state validation failed: {str(e)}") from e

    return migrated_state


def _find_migration_path(from_version: str, to_version: str) -> List[Tuple[str, str]]:
    """
    Find a migration path from source to target version.

    This function implements a simple direct migration lookup.
    In the future, it could implement graph search for multi-step migrations.

    Args:
        from_version: Source version
        to_version: Target version

    Returns:
        List of (from_ver, to_ver) tuples representing the migration path
    """
    # For now, implement simple direct migration
    direct_key = f"{from_version}->{to_version}"
    if direct_key in _MIGRATION_FUNCTIONS:
        return [(from_version, to_version)]

    # Future enhancement: implement BFS to find shortest migration path
    # through multiple versions for complex migration chains
    # e.g., 1.0.0 -> 1.1.0 -> 1.2.0 -> 2.0.0

    return []


def create_migration_backup(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a backup of state before migration.

    Args:
        state: State to backup

    Returns:
        Deep copy of the state with backup metadata
    """
    backup = copy.deepcopy(state)
    backup["_migration_backup"] = {
        "timestamp": datetime.now().isoformat(),
        "original_version": state.get("state_version", "unknown"),
    }
    logger.debug(f"Created migration backup for version {backup['_migration_backup']['original_version']}")
    return backup


def restore_from_backup(backup: Dict[str, Any]) -> Dict[str, Any]:
    """
    Restore state from a migration backup.

    Args:
        backup: Backup state dictionary

    Returns:
        Restored state without backup metadata
    """
    restored = copy.deepcopy(backup)
    backup_info = restored.pop("_migration_backup", None)
    if backup_info:
        logger.info(f"Restored state from backup created at {backup_info['timestamp']}")
    else:
        logger.warning("No backup metadata found in restore operation")
    return restored


def auto_migrate_state(state: Dict[str, Any], target_version: Optional[str] = None) -> Dict[str, Any]:
    """
    Automatically migrate state to the current or specified schema version.

    Args:
        state: State to migrate
        target_version: Target version (defaults to current schema version)

    Returns:
        Migrated state

    Raises:
        StateVersionError: If automatic migration fails
        MigrationError: If migration execution fails
    """
    if target_version is None:
        from .state import SCHEMA_VERSION
        target_version = SCHEMA_VERSION

    current_version = state.get("state_version", "0.0.0")

    if current_version == target_version:
        logger.debug(f"State already at target version {target_version}")
        return state

    # Create backup before migration
    backup = create_migration_backup(state)

    try:
        migrated_state = migrate_state(state, target_version)
        logger.info(f"Auto-migration successful: {current_version} -> {target_version}")
        return migrated_state
    except (StateVersionError, MigrationError) as e:
        logger.error(f"Auto-migration failed: {e}")
        logger.info("State left unchanged due to migration failure")
        raise


def load_migration_scripts(migrations_dir: Optional[str] = None) -> int:
    """
    Dynamically load migration scripts from the migrations directory.

    Args:
        migrations_dir: Path to migrations directory (defaults to core/migrations)

    Returns:
        Number of migration scripts loaded

    Raises:
        ImportError: If migration script loading fails
    """
    if migrations_dir is None:
        # Default to the migrations directory relative to this file
        migrations_dir = str(Path(__file__).parent / "migrations")

    if not os.path.exists(migrations_dir):
        logger.warning(f"Migrations directory not found: {migrations_dir}")
        return 0

    scripts_loaded = 0
    migrations_path = Path(migrations_dir)
    
    # Get all Python files in migrations directory
    for migration_file in migrations_path.glob("v*.py"):
        if migration_file.name.startswith("v") and migration_file.name.endswith(".py"):
            module_name = migration_file.stem
            try:
                # Import migration module
                spec = importlib.util.spec_from_file_location(
                    f"migrations.{module_name}", migration_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    scripts_loaded += 1
                    logger.debug(f"Loaded migration script: {module_name}")
            except Exception as e:
                logger.error(f"Failed to load migration script {migration_file}: {e}")

    logger.info(f"Loaded {scripts_loaded} migration scripts from {migrations_dir}")
    return scripts_loaded


# ========== Migration Testing Utilities ==========


def create_test_state(version: str, **kwargs) -> Dict[str, Any]:
    """
    Create a test state for migration testing.

    Args:
        version: State version to create
        **kwargs: Additional state fields to set

    Returns:
        Test state dictionary
    """
    from .state import create_initial_state

    test_state = create_initial_state(**kwargs)
    test_state["state_version"] = version
    
    # Add some test data
    test_state.update({
        "current_task": "test_task",
        "messages": [],
        "agent_outputs": {"test_agent": "test_output"},
        "tool_calls": [],
        "execution_trace": [
            {
                "event": "test_state_created",
                "timestamp": datetime.now().isoformat(),
                "details": f"Test state created with version {version}",
            }
        ]
    })
    
    # Override with any provided kwargs
    test_state.update(kwargs)
    
    logger.debug(f"Created test state with version {version}")
    return test_state


def validate_migration(
    from_version: str,
    to_version: str,
    test_data: Optional[Dict[str, Any]] = None,
    expected_changes: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Validate that a migration works correctly.

    Args:
        from_version: Source version to test
        to_version: Target version to test
        test_data: Custom test data (defaults to generated test state)
        expected_changes: Expected changes after migration

    Returns:
        True if migration validates successfully

    Raises:
        MigrationTestError: If migration validation fails
    """
    if test_data is None:
        test_data = create_test_state(from_version)

    try:
        # Perform migration
        migrated_state = migrate_state(test_data, to_version)

        # Basic validation
        if migrated_state.get("state_version") != to_version:
            raise MigrationTestError(
                f"Migration did not update version correctly. Expected {to_version}, got {migrated_state.get('state_version')}"
            )

        # Check expected changes if provided
        if expected_changes:
            for field, expected_value in expected_changes.items():
                if migrated_state.get(field) != expected_value:
                    raise MigrationTestError(
                        f"Migration did not produce expected change for field '{field}'. Expected {expected_value}, got {migrated_state.get(field)}"
                    )

        # Validate final state structure
        from .state import validate_state
        validate_state(migrated_state)

        logger.info(f"Migration validation successful: {from_version} -> {to_version}")
        return True

    except Exception as e:
        raise MigrationTestError(f"Migration validation failed: {str(e)}") from e


def validate_migration_roundtrip(
    original_state: Dict[str, Any],
    intermediate_version: str
) -> bool:
    """
    Test migration roundtrip to ensure data preservation.

    Note: This requires reverse migration functions to be available.

    Args:
        original_state: Original state to test with
        intermediate_version: Intermediate version to migrate to and back

    Returns:
        True if roundtrip preserves data

    Raises:
        MigrationTestError: If roundtrip test fails
    """
    original_version = original_state.get("state_version")
    
    try:
        # Forward migration
        forward_migrated = migrate_state(original_state, intermediate_version)
        
        # Backward migration
        backward_migrated = migrate_state(forward_migrated, original_version)
        
        # Compare essential data (excluding metadata that might change)
        essential_fields = [
            "messages", "current_task", "agent_outputs", "tool_calls",
            "tool_results", "agent_roles", "collaboration_prompt"
        ]
        
        for field in essential_fields:
            if field in original_state:
                if original_state[field] != backward_migrated.get(field):
                    raise MigrationTestError(
                        f"Roundtrip failed for field '{field}'. Data was not preserved."
                    )
        
        logger.info(f"Migration roundtrip successful: {original_version} -> {intermediate_version} -> {original_version}")
        return True
        
    except Exception as e:
        raise MigrationTestError(f"Migration roundtrip test failed: {str(e)}") from e


def benchmark_migration_performance(
    state: Dict[str, Any], 
    target_version: str, 
    iterations: int = 100
) -> Dict[str, float]:
    """
    Benchmark migration performance.

    Args:
        state: Test state to migrate
        target_version: Target version for migration
        iterations: Number of iterations to run

    Returns:
        Performance metrics dictionary
    """
    import time
    
    times = []
    memory_usage = []
    
    for _ in range(iterations):
        start_time = time.perf_counter()
        
        # Clone state for each iteration
        test_state = copy.deepcopy(state)
        
        # Perform migration
        migrate_state(test_state, target_version)
        
        end_time = time.perf_counter()
        times.append(end_time - start_time)
    
    metrics = {
        "avg_time": sum(times) / len(times),
        "min_time": min(times),
        "max_time": max(times),
        "total_time": sum(times),
        "iterations": iterations
    }
    
    logger.info(f"Migration benchmark results: avg={metrics['avg_time']:.4f}s, min={metrics['min_time']:.4f}s, max={metrics['max_time']:.4f}s")
    return metrics


# Auto-load migration scripts when module is imported
try:
    load_migration_scripts()
except Exception as e:
    logger.warning(f"Failed to auto-load migration scripts: {e}")