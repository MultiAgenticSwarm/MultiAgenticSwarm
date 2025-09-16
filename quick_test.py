"""
Interactive test script - modify and run this to test specific scenarios
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multiagenticswarm.core.tool_permissions import ToolPermissions

def interactive_test():
    print("🧪 Interactive Permission Test")
    print("=" * 40)
    
    # Initialize permissions
    permissions = ToolPermissions()
    
    print(f"✅ Loaded config with roles: {list(permissions.roles.keys())}")
    print()
    
    # Test different scenarios - MODIFY THESE AS NEEDED:
    
    test_cases = [
        # Format: (agent_id, tool_id, context, description)
        ("DataAnalyst", "calculator", None, "DataAnalyst using calculator"),
        ("Assistant", "file_writer", None, "Assistant trying to write files"),
        ("CodeWriter", "file_writer", {"workflow_phase": "planning"}, "CodeWriter writing during planning"),
        ("CodeWriter", "file_writer", {"workflow_phase": "development"}, "CodeWriter writing during development"),
        ("SysAdmin", "system_monitor", None, "SysAdmin monitoring system"),
        ("DataAnalyst", "system_monitor", None, "DataAnalyst trying to monitor (should be denied)"),
    ]
    
    for agent, tool, context, description in test_cases:
        allowed, reason = permissions.check_permission(agent, tool, context)
        status = "✅ ALLOWED" if allowed else "❌ DENIED"
        reason_text = f" - {reason}" if reason else ""
        print(f"{status}: {description}{reason_text}")
    
    print("\n" + "=" * 40)
    print("🎯 Modify the test_cases list above to test your own scenarios!")

if __name__ == "__main__":
    interactive_test()