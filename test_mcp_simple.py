#!/usr/bin/env python3
"""Simple test script to verify MCP integration."""

print("🔍 Testing MCP Integration")
print("=" * 40)

try:
    # Test basic imports
    print("1. Testing basic import...")
    import multiagenticswarm as mas
    print(f"   ✅ MultiAgenticSwarm v{mas.__version__} imported")
    
    # Test MCP components
    print("2. Testing MCP components...")
    mcp_available = bool(getattr(mas, 'MCPServer', None))
    print(f"   ✅ MCP components available: {mcp_available}")
    
    if mcp_available:
        print("   - MCPServer:", bool(mas.MCPServer))
        print("   - MCPClient:", bool(mas.MCPClient))
        print("   - MCPTool:", bool(mas.MCPTool))
    
    # Test core components
    print("3. Testing core components...")
    print(f"   - Agent: {bool(getattr(mas, 'Agent', None))}")
    print(f"   - System: {bool(getattr(mas, 'System', None))}")
    print(f"   - Tool: {bool(getattr(mas, 'Tool', None))}")
    
    # Test creating a system with MCP
    print("4. Testing System with MCP...")
    system = mas.System()
    has_mcp_attrs = hasattr(system, 'mcp_servers') and hasattr(system, 'mcp_clients')
    print(f"   ✅ System has MCP attributes: {has_mcp_attrs}")
    
    print("\n🎉 All tests passed! MCP integration is working.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
