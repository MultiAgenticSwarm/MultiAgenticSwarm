"""
Migration scripts directory for MultiAgenticSwarm state schema changes.

This directory contains migration scripts that transform state from one schema version to another.
Each migration script should be named in the format: `v{from_version}_to_v{to_version}.py`

Example:
- `v1_0_0_to_v1_1_0.py` - Migration from version 1.0.0 to 1.1.0
- `v1_1_0_to_v2_0_0.py` - Migration from version 1.1.0 to 2.0.0

Migration scripts should contain a migration function decorated with @register_migration
that transforms the state dictionary according to schema changes.
"""

from ..state_migration import register_migration

__all__ = ["register_migration"]