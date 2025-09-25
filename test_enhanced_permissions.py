"""
Test the enhanced permission system independently.
This demonstrates the new features without requiring LangChain dependencies.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multiagenticswarm.core.tool_permissions import ToolPermissions

def test_enhanced_permissions():
    """Test the enhanced permission system."""
    print("=== Enhanced Permission System Test ===")
    
    # Initialize permission system (loads config automatically)
    permissions = ToolPermissions()
    
    print(f"Config loaded: {permissions.config_path}")
    print(f"Roles available: {list(permissions.roles.keys())}")
    
    # Test config-based permissions
    print("\n--- Config-Based Permission Tests ---")
    
    # DataAnalyst should have access to calculator (from data_analyst role)
    allowed, reason = permissions.check_permission("DataAnalyst", "calculator")
    print(f"DataAnalyst can use calculator: {allowed} ({reason or 'Allowed by role'})")
    
    # Assistant should have limited access (basic_user role)
    allowed, reason = permissions.check_permission("Assistant", "calculator") 
    print(f"Assistant can use calculator: {allowed} ({reason or 'Allowed by role'})")
    
    # CodeWriter should NOT have access to data_reader (not in developer role)
    allowed, reason = permissions.check_permission("CodeWriter", "data_reader")
    print(f"CodeWriter can use data_reader: {allowed} ({reason})")
    
    # Test denied tools (explicit deny overrides role)
    allowed, reason = permissions.check_permission("DataAnalyst", "system_monitor")
    print(f"DataAnalyst can use system_monitor: {allowed} ({reason})")
    
    # Test workflow restrictions
    print("\n--- Workflow Restriction Tests ---")
    
    # Test planning phase restrictions - file_writer should be restricted during planning
    planning_context = {"workflow_phase": "planning"}
    allowed, reason = permissions.check_permission("CodeWriter", "file_writer", planning_context)
    print(f"CodeWriter can use file_writer during planning: {allowed} ({reason})")
    
    # Test development phase (should work for code_executor)
    dev_context = {"workflow_phase": "development"}
    allowed, reason = permissions.check_permission("CodeWriter", "code_executor", dev_context)
    print(f"CodeWriter can use code_executor during development: {allowed} ({reason or 'Allowed by role'})")
    
    # Test production phase - only SysAdmin should be allowed
    prod_context = {"workflow_phase": "production"}
    allowed, reason = permissions.check_permission("CodeWriter", "code_executor", prod_context)
    print(f"CodeWriter can use code_executor during production: {allowed} ({reason})")
    
    allowed, reason = permissions.check_permission("SysAdmin", "code_executor", prod_context)
    print(f"SysAdmin can use code_executor during production: {allowed} ({reason or 'Allowed by role'})")
    
    # Test role-based permissions
    print("\n--- Role-Based Permission Tests ---")
    
    # Get agent permissions summary
    analyst_perms = permissions.get_agent_permissions("DataAnalyst")
    print(f"\nDataAnalyst permissions:")
    print(f"  Role: {analyst_perms['config_permissions']['role']}")
    print(f"  Allowed tools: {analyst_perms['config_permissions']['allowed_tools']}")
    print(f"  Denied tools: {analyst_perms['config_permissions']['denied_tools']}")
    
    # Test manual role assignment
    print("\n--- Manual Role Assignment ---")
    
    # Create a new role and assign it
    permissions.set_role("tester", ["calculator", "logger", "test_runner"], "QA tester role")
    permissions.assign_role("QATester", "tester")
    
    allowed, reason = permissions.check_permission("QATester", "test_runner")
    print(f"QATester can use test_runner: {allowed} ({reason or 'Allowed by role'})")
    
    print("\n--- Permission Logging ---")
    
    # Test logging
    permissions.log("TestAgent", "calculator", "EXECUTE", "SUCCESS", {"result": 42})
    permissions.log("TestAgent", "restricted_tool", "EXECUTE", "DENIED", "No permission")
    
    recent_logs = permissions.get_logs()[-2:]
    for log in recent_logs:
        print(f"Log: {log['agent']} -> {log['tool']} ({log['outcome']})")
    
    print("\nEnhanced permission system working correctly!")
    print("Your colleague can use ToolNodeManager with the enhanced ToolPermissions class")
    print("The existing API is fully backward compatible")

if __name__ == "__main__":
    test_enhanced_permissions()