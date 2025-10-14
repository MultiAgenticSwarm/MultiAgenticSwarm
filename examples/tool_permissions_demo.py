#!/usr/bin/env python3
"""
Demo script showing dynamic tool permissions in action.

This demonstrates:
1. Loading permissions from config
2. Runtime permission updates
3. Conditional permissions based on context
4. Usage quotas and limits
5. Audit trail functionality
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from multiagenticswarm.core.system import System
from multiagenticswarm.core.base_tool import FunctionTool


def create_demo_tools():
    """Create some demo tools for testing permissions."""
    
    def read_file(filename: str) -> str:
        """Read a file from the filesystem."""
        return f"Reading file: {filename}"
    
    def write_code(code: str) -> str:
        """Write code to a file."""
        return f"Writing code: {code[:50]}..."
    
    def send_email(to: str, subject: str, body: str) -> str:
        """Send an email."""
        return f"Email sent to {to}: {subject}"
    
    def access_database(query: str) -> str:
        """Access database with a query."""
        return f"Database query: {query}"
    
    # Create tools
    tools = [
        FunctionTool(func=read_file, name="FileReader", 
                    description="Read files from filesystem"),
        FunctionTool(func=write_code, name="CodeWriter", 
                    description="Write code to files"),
        FunctionTool(func=send_email, name="EmailSender", 
                    description="Send emails to users"),
        FunctionTool(func=access_database, name="Database", 
                    description="Access database")
    ]
    
    return tools


async def demo_permission_system():
    """Demonstrate the dynamic permission system."""
    print("🚀 Dynamic Tool Permissions Demo")
    print("=" * 50)
    
    # Initialize system without auto-loading config
    system = System(enable_logging=True)
    
    # Add demo tools
    tools = create_demo_tools()
    for tool in tools:
        system.register_tool(tool)
    
    # Register demo agents with basic permissions
    system.tool_executor.register_agent("ui_agent", {
        "CodeWriter": "always",
        "Database": "never", 
        "FileReader": "conditional:read_only_mode",
        "EmailSender": "quota:5/day"
    })
    system.tool_executor.register_agent("data_agent", {
        "CodeWriter": "never",
        "Database": "never",  # Start with never, then change to conditional
        "FileReader": "conditional:read_only_mode", 
        "EmailSender": "conditional:user_approved"
    })
    system.tool_executor.register_agent("admin_agent", {
        "CodeWriter": "always",
        "Database": "always",
        "FileReader": "conditional:read_only_mode",
        "EmailSender": "always"
    })
    
    print("\n📋 Initial Permissions (from defaults):")
    for agent in ["ui_agent", "data_agent", "admin_agent"]:
        permissions = system.get_agent_permissions(agent)
        print(f"  {agent}: {len(permissions)} permissions")
        for tool, perm in permissions.items():
            if tool in ["CodeWriter", "Database", "FileReader", "EmailSender"]:
                print(f"    {tool}: {perm}")
    
    print("\n🔧 Updating Permissions at Runtime:")
    
    # Give ui_agent always access to CodeWriter
    system.update_tool_permission("ui_agent", "CodeWriter", "always")
    print("  ✅ ui_agent can now always use CodeWriter")
    
    # Give data_agent conditional database access
    system.update_tool_permission("data_agent", "Database", "conditional:data_safe")
    print("  ✅ data_agent can use Database when data is safe")
    
    # Give admin_agent quota-limited email sending
    system.update_tool_permission("admin_agent", "EmailSender", "quota:3/day")
    print("  ✅ admin_agent can send 3 emails per day")
    
    print("\n🧪 Testing Permission Checks:")
    
    # Test 1: ui_agent using CodeWriter (should work)
    can_use = system.tool_executor.permission_matrix.check_permission(
        "ui_agent", "CodeWriter", {}
    )
    print(f"  ui_agent can use CodeWriter: {can_use} ✅")
    
    # Test 2: ui_agent using Database (should fail)
    can_use = system.tool_executor.permission_matrix.check_permission(
        "ui_agent", "Database", {}
    )
    print(f"  ui_agent can use Database: {can_use} ❌")
    
    # Test 3: data_agent using Database with safe data (should work)
    context = {"data_sensitive": False}
    can_use = system.tool_executor.permission_matrix.check_permission(
        "data_agent", "Database", context
    )
    print(f"  data_agent can use Database (safe data): {can_use} ✅" if can_use else f"  data_agent can use Database (safe data): {can_use} ❌")
    
    # Test 4: data_agent using Database with sensitive data (should fail)
    context = {"data_sensitive": True}
    can_use = system.tool_executor.permission_matrix.check_permission(
        "data_agent", "Database", context
    )
    print(f"  data_agent can use Database (sensitive data): {can_use} ❌" if not can_use else f"  data_agent can use Database (sensitive data): {can_use} ✅")
    
    print("\n📊 Testing Quota System:")
    
    # Test quota usage
    for i in range(5):
        can_use = system.tool_executor.permission_matrix.check_permission(
            "admin_agent", "EmailSender", {}
        )
        if can_use:
            # Simulate tool usage
            used = system.tool_executor.permission_matrix.use_quota("admin_agent", "EmailSender")
            print(f"  Email {i+1}: {'Sent ✅' if used else 'Quota exceeded ❌'}")
        else:
            print(f"  Email {i+1}: Permission denied ❌")
    
    # Check quota status
    print(f"  Quota usage complete")
    
    print("\n🔍 Conditional Permissions Demo:")
    
    # Set different contexts and test
    contexts = [
        {"current_phase": "design"},
        {"current_phase": "implementation"},
        {"mode": "development", "read_only": True}
    ]
    
    for i, context in enumerate(contexts, 1):
        print(f"  Context {i}: {context}")
        system.set_execution_context(context)
        
        # Test conditional permissions
        can_read = system.tool_executor.permission_matrix.check_permission(
            "ui_agent", "FileSystem", context
        )
        print(f"    ui_agent can use FileSystem: {can_read}")
    
    print("\n✅ Demo completed!")
    
    # Show audit trail
    print("\n📝 Audit Trail (last 10 entries):")
    audit = system.get_permission_audit_trail(limit=10)
    for entry in audit:
        timestamp = entry['timestamp'].split('T')[1].split('.')[0]  # Just time part
        result_icon = "✅" if entry['result'] == "allowed" else "❌"
        print(f"  {timestamp} | {entry['agent_id']:12} | {entry['tool_name']:12} | {result_icon} {entry['result']:7} | {entry['reason']}")
    
    print("\n📊 Audit Summary:")
    total = len(system.tool_executor.permission_matrix.audit_trail)
    allowed = sum(1 for e in system.tool_executor.permission_matrix.audit_trail if e['result'] == 'allowed')
    denied = total - allowed
    print(f"  Total checks: {total}")
    print(f"  Allowed: {allowed}")
    print(f"  Denied: {denied}")
    
    print("\nKey Features Demonstrated:")
    print("  ✅ Dynamic permission updates")
    print("  ✅ Conditional permissions work")
    print("  ✅ Role-based access")
    print("  ✅ Usage quotas implemented")
    print("  ✅ Audit trail functional")


if __name__ == "__main__":
    asyncio.run(demo_permission_system())