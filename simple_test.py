"""
Super simple one-liner tests - just run and see results
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multiagenticswarm.core.tool_permissions import ToolPermissions

# Initialize once
permissions = ToolPermissions()

print("🔍 Quick Permission Checks:")
print("-" * 30)

# Test basic permissions
result = permissions.check_permission("DataAnalyst", "calculator")
print(f"DataAnalyst + calculator: {result}")

result = permissions.check_permission("Assistant", "file_writer") 
print(f"Assistant + file_writer: {result}")

# Test workflow restrictions
context = {"workflow_phase": "planning"}
result = permissions.check_permission("CodeWriter", "file_writer", context)
print(f"CodeWriter + file_writer (planning): {result}")

context = {"workflow_phase": "development"}
result = permissions.check_permission("CodeWriter", "file_writer", context)
print(f"CodeWriter + file_writer (development): {result}")

# Test denied permissions
result = permissions.check_permission("DataAnalyst", "system_monitor")
print(f"DataAnalyst + system_monitor: {result}")

print("\n✅ All tests complete!")