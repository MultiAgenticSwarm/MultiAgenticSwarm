"""
Tests for the state migration system.

This module tests the migration framework, migration functions,
and integration with the state management system.
"""

import pytest
from unittest.mock import patch
from datetime import datetime
from typing import Dict, Any

from multiagenticswarm.core.state_migration import (
    StateVersionError,
    MigrationError,
    MigrationTestError,
    compare_versions,
    is_compatible_version,
    register_migration,
    migrate_state,
    auto_migrate_state,
    create_migration_backup,
    restore_from_backup,
    get_registered_migrations,
    clear_migration_registry,
    create_test_state,
    validate_migration,
    validate_migration_roundtrip,
    benchmark_migration_performance,
    load_migration_scripts,
)
from multiagenticswarm.core.state import create_initial_state, SCHEMA_VERSION


class TestVersionComparison:
    """Test version comparison functionality."""

    def test_compare_versions_equal(self):
        """Test comparing equal versions."""
        assert compare_versions("1.0.0", "1.0.0") == 0
        assert compare_versions("2.1.3", "2.1.3") == 0

    def test_compare_versions_less_than(self):
        """Test comparing when first version is less."""
        assert compare_versions("1.0.0", "1.0.1") == -1
        assert compare_versions("1.0.0", "1.1.0") == -1
        assert compare_versions("1.0.0", "2.0.0") == -1

    def test_compare_versions_greater_than(self):
        """Test comparing when first version is greater."""
        assert compare_versions("1.0.1", "1.0.0") == 1
        assert compare_versions("1.1.0", "1.0.0") == 1
        assert compare_versions("2.0.0", "1.0.0") == 1

    def test_compare_versions_invalid_format(self):
        """Test comparing invalid version formats."""
        with pytest.raises(StateVersionError):
            compare_versions("invalid", "1.0.0")
        
        with pytest.raises(StateVersionError):
            compare_versions("1.0.0", "not.a.version")

    def test_compare_versions_pre_release(self):
        """Test comparing pre-release versions."""
        assert compare_versions("1.0.0-alpha", "1.0.0") == -1
        assert compare_versions("1.0.0", "1.0.0-alpha") == 1
        assert compare_versions("1.0.0-alpha", "1.0.0-beta") == -1

    def test_is_compatible_version(self):
        """Test version compatibility checking."""
        assert is_compatible_version("1.0.0", "1.0.0") is True
        assert is_compatible_version("1.1.0", "1.0.0") is True
        assert is_compatible_version("1.0.0", "1.1.0") is False
        assert is_compatible_version("2.0.0", "1.0.0") is True


class TestMigrationRegistry:
    """Test migration function registry."""

    def setup_method(self):
        """Clear registry before each test."""
        clear_migration_registry()

    def teardown_method(self):
        """Clear registry after each test."""
        clear_migration_registry()

    def test_register_migration_decorator(self):
        """Test registering migrations with decorator."""
        @register_migration("1.0.0", "1.1.0")
        def test_migration(state):
            state["new_field"] = "test_value"
            return state

        migrations = get_registered_migrations()
        assert "1.0.0->1.1.0" in migrations
        assert migrations["1.0.0->1.1.0"] == test_migration

    def test_clear_migration_registry(self):
        """Test clearing the migration registry."""
        @register_migration("1.0.0", "1.1.0")
        def test_migration(state):
            return state

        assert len(get_registered_migrations()) == 1
        clear_migration_registry()
        assert len(get_registered_migrations()) == 0

    def test_get_registered_migrations_copy(self):
        """Test that get_registered_migrations returns a copy."""
        @register_migration("1.0.0", "1.1.0")
        def test_migration(state):
            return state

        migrations1 = get_registered_migrations()
        migrations2 = get_registered_migrations()
        
        # Should be equal but not the same object
        assert migrations1 == migrations2
        assert migrations1 is not migrations2


class TestStateMigration:
    """Test state migration functionality."""

    def setup_method(self):
        """Setup for each test."""
        clear_migration_registry()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_migration_registry()

    def test_migrate_state_same_version(self):
        """Test migration when state is already at target version."""
        state = create_initial_state()
        result = migrate_state(state, state["state_version"])
        assert result == state

    def test_migrate_state_no_migration_path(self):
        """Test migration when no migration path exists."""
        state = create_initial_state()
        state["state_version"] = "0.5.0"
        
        with pytest.raises(StateVersionError, match="No migration path found"):
            migrate_state(state, "2.0.0")

    def test_migrate_state_success(self):
        """Test successful state migration."""
        @register_migration("1.0.0", "1.1.0")
        def test_migration(state):
            state["new_field"] = "migrated_value"
            return state

        state = create_initial_state()
        state["state_version"] = "1.0.0"
        
        result = migrate_state(state, "1.1.0")
        
        assert result["state_version"] == "1.1.0"
        assert result["new_field"] == "migrated_value"

    def test_migrate_state_migration_failure(self):
        """Test migration failure handling."""
        @register_migration("1.0.0", "1.1.0")
        def failing_migration(state):
            raise ValueError("Migration failed")

        state = create_initial_state()
        state["state_version"] = "1.0.0"
        
        with pytest.raises(MigrationError, match="Migration failed"):
            migrate_state(state, "1.1.0")

    def test_migrate_state_validation_failure(self):
        """Test migration with validation failure."""
        @register_migration("1.0.0", "1.1.0")
        def invalid_migration(state):
            # Create invalid state structure
            state["messages"] = "not_a_list"
            return state

        state = create_initial_state()
        state["state_version"] = "1.0.0"
        
        with pytest.raises(MigrationError, match="validation failed"):
            migrate_state(state, "1.1.0")

    def test_auto_migrate_state(self):
        """Test automatic migration to current schema version."""
        # Since SCHEMA_VERSION is 1.0.0, create migration to a test version
        @register_migration("0.9.0", "1.0.0")
        def test_migration(state):
            state["auto_migrated"] = True
            return state

        state = create_initial_state()
        state["state_version"] = "0.9.0"
        
        result = auto_migrate_state(state)
        
        assert result["state_version"] == SCHEMA_VERSION
        assert result.get("auto_migrated") is True

    def test_auto_migrate_state_same_version(self):
        """Test auto-migration when already at current version."""
        state = create_initial_state()
        result = auto_migrate_state(state)
        assert result == state

    def test_auto_migrate_state_custom_target(self):
        """Test auto-migration to custom target version."""
        @register_migration("1.0.0", "1.5.0")
        def test_migration(state):
            state["custom_target"] = True
            return state

        state = create_initial_state()
        state["state_version"] = "1.0.0"
        
        result = auto_migrate_state(state, "1.5.0")
        
        assert result["state_version"] == "1.5.0"
        assert result.get("custom_target") is True


class TestMigrationBackup:
    """Test migration backup and restore functionality."""

    def test_create_migration_backup(self):
        """Test creating migration backup."""
        state = create_initial_state()
        backup = create_migration_backup(state)
        
        assert "_migration_backup" in backup
        assert backup["_migration_backup"]["original_version"] == state["state_version"]
        assert "timestamp" in backup["_migration_backup"]

    def test_restore_from_backup(self):
        """Test restoring from backup."""
        state = create_initial_state()
        backup = create_migration_backup(state)
        
        # Modify backup to simulate changes
        backup["modified_field"] = "test_value"
        
        restored = restore_from_backup(backup)
        
        assert "_migration_backup" not in restored
        assert restored["modified_field"] == "test_value"
        assert restored["state_version"] == state["state_version"]

    def test_restore_from_backup_no_metadata(self):
        """Test restoring backup without metadata."""
        state = create_initial_state()
        # Create backup without metadata
        backup = dict(state)
        
        restored = restore_from_backup(backup)
        assert restored == state


class TestMigrationUtilities:
    """Test migration testing utilities."""

    def setup_method(self):
        """Setup for each test."""
        clear_migration_registry()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_migration_registry()

    def test_create_test_state(self):
        """Test creating test state."""
        test_state = create_test_state("0.9.0", current_task="test_migration")
        
        assert test_state["state_version"] == "0.9.0"
        assert test_state["current_task"] == "test_migration"
        assert "execution_trace" in test_state
        assert len(test_state["execution_trace"]) > 0

    def test_validate_migration_success(self):
        """Test successful migration validation."""
        @register_migration("1.0.0", "1.1.0")
        def test_migration(state):
            state["validated_field"] = "validated_value"
            return state

        result = validate_migration(
            "1.0.0", "1.1.0", 
            expected_changes={"validated_field": "validated_value"}
        )
        
        assert result is True

    def test_validate_migration_version_error(self):
        """Test migration validation with missing migration function."""
        # No migration function registered, so validation should fail
        with pytest.raises(MigrationTestError, match="Migration validation failed"):
            validate_migration("1.0.0", "1.1.0")

    def test_validate_migration_expected_changes_error(self):
        """Test migration validation with unexpected changes."""
        @register_migration("1.0.0", "1.1.0")
        def test_migration(state):
            state["unexpected_field"] = "unexpected_value"
            return state

        with pytest.raises(MigrationTestError, match="did not produce expected change"):
            validate_migration(
                "1.0.0", "1.1.0", 
                expected_changes={"expected_field": "expected_value"}
            )

    def test_test_migration_roundtrip(self):
        """Test migration roundtrip functionality."""
        @register_migration("1.0.0", "1.1.0")
        def forward_migration(state):
            state["temp_field"] = "temp_value"
            return state

        @register_migration("1.1.0", "1.0.0")
        def reverse_migration(state):
            state.pop("temp_field", None)
            return state

        original_state = create_test_state("1.0.0")
        
        result = validate_migration_roundtrip(original_state, "1.1.0")
        assert result is True

    def test_test_migration_roundtrip_data_loss(self):
        """Test roundtrip failure due to data loss."""
        @register_migration("1.0.0", "1.1.0")
        def forward_migration(state):
            state["temp_field"] = "temp_value"
            return state

        @register_migration("1.1.0", "1.0.0")
        def bad_reverse_migration(state):
            # Lose data - corrupt messages
            state["messages"] = []
            return state

        original_state = create_test_state("1.0.0")
        # Add a message to test data loss
        from langchain_core.messages import HumanMessage
        original_state["messages"] = [HumanMessage(content="test message")]
        
        with pytest.raises(MigrationTestError, match="Data was not preserved"):
            validate_migration_roundtrip(original_state, "1.1.0")

    def test_benchmark_migration_performance(self):
        """Test migration performance benchmarking."""
        @register_migration("1.0.0", "1.1.0")
        def simple_migration(state):
            state["benchmark_field"] = "benchmark_value"
            return state

        test_state = create_test_state("1.0.0")
        
        metrics = benchmark_migration_performance(test_state, "1.1.0", iterations=5)
        
        assert "avg_time" in metrics
        assert "min_time" in metrics
        assert "max_time" in metrics
        assert "total_time" in metrics
        assert metrics["iterations"] == 5
        assert metrics["avg_time"] > 0


class TestMigrationScriptLoading:
    """Test dynamic loading of migration scripts."""

    def setup_method(self):
        """Setup for each test."""
        clear_migration_registry()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_migration_registry()

    def test_load_migration_scripts_nonexistent_dir(self):
        """Test loading from non-existent directory."""
        result = load_migration_scripts("/nonexistent/path")
        assert result == 0

    def test_load_migration_scripts_empty_dir(self, tmp_path):
        """Test loading from empty directory."""
        result = load_migration_scripts(str(tmp_path))
        assert result == 0

    @patch('multiagenticswarm.core.state_migration.logger')
    def test_load_migration_scripts_invalid_file(self, mock_logger, tmp_path):
        """Test loading with invalid migration file."""
        # Create an invalid Python file
        invalid_file = tmp_path / "v1_0_0_to_v1_1_0.py"
        invalid_file.write_text("invalid python syntax !!!")
        
        result = load_migration_scripts(str(tmp_path))
        assert result == 0
        mock_logger.error.assert_called_once()


class TestIntegration:
    """Test integration with the state system."""

    def test_integration_with_state_module(self):
        """Test that migration integrates properly with state module."""
        from multiagenticswarm.core.state import (
            StateVersionError as StateModuleVersionError,
            auto_migrate_state as state_auto_migrate
        )
        
        # These should be the same functions
        assert StateVersionError == StateModuleVersionError
        assert auto_migrate_state == state_auto_migrate

    def test_migration_preserves_state_structure(self):
        """Test that migration preserves valid state structure."""
        @register_migration("1.0.0", "1.1.0")
        def structure_preserving_migration(state):
            # Only add new optional fields
            if "new_optional_field" not in state:
                state["new_optional_field"] = "default_value"
            return state

        # Create a full valid state
        original_state = create_initial_state(
            collaboration_prompt="Test collaboration",
            initial_message="Hello world"
        )
        original_state["state_version"] = "1.0.0"
        
        # Add some realistic data
        original_state["current_task"] = "Integration test"
        original_state["agent_outputs"] = {"test_agent": "test_output"}
        
        migrated_state = migrate_state(original_state, "1.1.0")
        
        # Verify migration succeeded and structure is preserved
        assert migrated_state["state_version"] == "1.1.0"
        assert migrated_state["current_task"] == "Integration test"
        assert migrated_state["agent_outputs"]["test_agent"] == "test_output"
        assert migrated_state["new_optional_field"] == "default_value"
        
        # Verify state is still valid
        from multiagenticswarm.core.state import validate_state
        assert validate_state(migrated_state) is True