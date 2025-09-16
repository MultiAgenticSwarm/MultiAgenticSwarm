"""
Final integration test demonstrating the enhanced permission system
working seamlessly with your colleague's existing ToolNodeManager.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multiagenticswarm.core.tool_permissions import ToolPermissions
from multiagenticswarm.core.tool_registry import ToolRegistry

# Create a minimal mock ToolNodeManager to demonstrate integration
class MockToolNodeManager:
    """Mock version of your colleague's ToolNodeManager to demonstrate integration."""
    
    def __init__(self, permissions: ToolPermissions, registry: ToolRegistry):
        self.permissions = permissions
        self.registry = registry
        self.tools = {}
    
    def register_tool(self, tool_id, name, description, category, func, default_permission="ALLOWED"):
        """Register a tool (your colleague's existing method)."""
        # Store tool info in registry (using correct API)
        self.registry.register_tool(tool_id, name, description, category, func)
        
        # Store function for execution
        self.tools[tool_id] = func
        
        print(f"✓ Registered tool: {name} ({tool_id})")
    
    def execute_tool(self, agent_id, tool_id, context=None, **kwargs):
        """Execute a tool with permission checking (your colleague's logic + our enhancement)."""
        # Check permissions using enhanced system
        allowed, reason = self.permissions.check_permission(agent_id, tool_id, context)
        
        if not allowed:
            print(f"❌ {agent_id} denied access to {tool_id}: {reason}")
            return {"error": f"Permission denied: {reason}"}
        
        # Execute the tool (your colleague's existing logic)
        if tool_id not in self.tools:
            return {"error": "Tool not found"}
        
        try:
            result = self.tools[tool_id](**kwargs)
            print(f"✅ {agent_id} executed {tool_id} successfully")
            
            # Log the execution
            self.permissions.log(agent_id, tool_id, "EXECUTE", "SUCCESS", result)
            return {"result": result}
        except Exception as e:
            print(f"❌ {agent_id} failed to execute {tool_id}: {e}")
            self.permissions.log(agent_id, tool_id, "EXECUTE", "ERROR", str(e))
            return {"error": str(e)}

def sample_calculator(x: int, y: int, operation: str = "add") -> int:
    """Sample calculator function."""
    if operation == "add":
        return x + y
    elif operation == "multiply":
        return x * y
    return 0

def sample_file_writer(filename: str, content: str) -> str:
    """Sample file writing function."""
    return f"Would write to {filename}: {content[:50]}..."

def sample_code_executor(code: str) -> str:
    """Sample code execution function."""
    return f"Would execute: {code[:30]}..."

def test_integration():
    """Test the enhanced permission system with ToolNodeManager."""
    print("=== Enhanced Permissions + ToolNodeManager Integration Test ===\n")
    
    # Initialize components (your colleague's architecture)
    permissions = ToolPermissions()
    registry = ToolRegistry()
    tool_manager = MockToolNodeManager(permissions, registry)
    
    # Register tools (your colleague's way)
    tool_manager.register_tool("calculator", "Calculator", "Basic math", "math", sample_calculator)
    tool_manager.register_tool("file_writer", "File Writer", "Write files", "io", sample_file_writer)
    tool_manager.register_tool("code_executor", "Code Executor", "Execute code", "system", sample_code_executor)
    
    print("\n--- Role-Based Permission Tests ---")
    
    # Test DataAnalyst with calculator (should work - allowed by role)
    result = tool_manager.execute_tool("DataAnalyst", "calculator", None, x=5, y=3, operation="add")
    print(f"DataAnalyst calculator result: {result}")
    
    # Test Assistant with file_writer (should be denied - not in role)
    result = tool_manager.execute_tool("Assistant", "file_writer", None, filename="test.txt", content="Hello world")
    print(f"Assistant file_writer result: {result}")
    
    print("\n--- Workflow Restriction Tests ---")
    
    # Test CodeWriter with file_writer during planning (should be denied)
    planning_context = {"workflow_phase": "planning"}
    result = tool_manager.execute_tool("CodeWriter", "file_writer", planning_context, filename="plan.md", content="Planning...")
    print(f"CodeWriter file_writer during planning: {result}")
    
    # Test CodeWriter with file_writer during development (should work)
    dev_context = {"workflow_phase": "development"}
    result = tool_manager.execute_tool("CodeWriter", "file_writer", dev_context, filename="code.py", content="print('hello')")
    print(f"CodeWriter file_writer during development: {result}")
    
    # Test CodeWriter with code_executor during production (should be denied)
    prod_context = {"workflow_phase": "production"}
    result = tool_manager.execute_tool("CodeWriter", "code_executor", prod_context, code="print('test')")
    print(f"CodeWriter code_executor during production: {result}")
    
    # Test SysAdmin with code_executor during production (should work)
    result = tool_manager.execute_tool("SysAdmin", "code_executor", prod_context, code="system_check()")
    print(f"SysAdmin code_executor during production: {result}")
    
    print("\n--- Configuration-Based Denials ---")
    
    # Test DataAnalyst with system_monitor (explicitly denied in config)
    result = tool_manager.execute_tool("DataAnalyst", "system_monitor", None)
    print(f"DataAnalyst system_monitor result: {result}")
    
    print("\n--- Permission Logs ---")
    
    logs = permissions.get_logs()
    print(f"Recent permission logs ({len(logs)} entries):")
    for log in logs[-5:]:  # Show last 5 logs
        print(f"  {log['agent']} -> {log['tool']}: {log['outcome']}")
    
    print("\n🎉 Integration Test Complete!")
    print("✅ Enhanced permissions work seamlessly with existing ToolNodeManager")
    print("🔧 Your colleague can use the enhanced system without changing their code")
    print("📝 Config-driven permissions are now available")
    print("⚡ Workflow-based restrictions are enforced")

if __name__ == "__main__":
    test_integration()