"""
Example: Creating and running an MCP server to expose MultiAgenticSwarm tools.

This example shows how to:
1. Create a MultiAgenticSwarm system with tools
2. Set up an MCP server to expose tools
3. Start the server to make tools available to external MCP clients

To test this example:
1. Run this script: python examples/mcp_server_example.py
2. Connect to the server using an MCP client on ws://localhost:8765
3. Use the 'data_processor' and 'Logger' tools via the MCP protocol
"""

import asyncio
import time
from multiagenticswarm import System
from multiagenticswarm.core.base_tool import FunctionTool, ToolScope


def create_data_processor_tool():
    """Create a sample data processing tool."""
    
    def process_data(data: str, operation: str = "uppercase") -> str:
        """
        Process data with specified operation.
        
        Args:
            data: Input data to process
            operation: Operation to perform (uppercase, lowercase, reverse, length)
        
        Returns:
            Processed data result
        """
        if operation == "uppercase":
            return data.upper()
        elif operation == "lowercase":
            return data.lower()
        elif operation == "reverse":
            return data[::-1]
        elif operation == "length":
            return f"Length: {len(data)}"
        else:
            return f"Unknown operation: {operation}"
    
    # Create tool with proper parameter schema
    tool = FunctionTool(
        func=process_data,
        name="data_processor",
        description="Process text data with various operations",
        parameters={
            "type": "object",
            "properties": {
                "data": {
                    "type": "string",
                    "description": "Input data to process"
                },
                "operation": {
                    "type": "string",
                    "enum": ["uppercase", "lowercase", "reverse", "length"],
                    "description": "Operation to perform on the data",
                    "default": "uppercase"
                }
            },
            "required": ["data"]
        }
    )
    
    # Set as global tool so it can be exposed via MCP
    tool.set_global()
    return tool


def create_calculator_tool():
    """Create a sample calculator tool."""
    
    def calculate(expression: str) -> str:
        """
        Safely evaluate mathematical expressions.
        
        Args:
            expression: Mathematical expression to evaluate (e.g., "2 + 3 * 4")
        
        Returns:
            Calculation result or error message
        """
        try:
            # Basic safety check - only allow numbers, operators, parentheses, and spaces
            allowed_chars = set("0123456789+-*/()%. ")
            if not all(c in allowed_chars for c in expression):
                return "Error: Invalid characters in expression"
            
            # Evaluate the expression
            result = eval(expression)
            return f"Result: {result}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    tool = FunctionTool(
        func=calculate,
        name="calculator",
        description="Safely evaluate mathematical expressions",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    )
    
    tool.set_global()
    return tool


async def main():
    """Main function to demonstrate MCP server setup."""
    
    print("🔧 Setting up MultiAgenticSwarm system...")
    
    # Create system
    system = System(enable_logging=True, verbose=True)
    
    # Create and register custom tools
    data_tool = create_data_processor_tool()
    calc_tool = create_calculator_tool()
    
    system.tool_executor.register_tool(data_tool)
    system.tool_executor.register_tool(calc_tool)
    
    print(f"✅ Registered {len(system.tool_executor.get_all_tools())} tools")
    
    # List available tools
    all_tools = system.tool_executor.get_all_tools()
    print("\n📋 Available tools:")
    for tool in all_tools:
        print(f"  - {tool.name}: {tool.description} (scope: {tool.scope.value})")
    
    print("\n🌐 Setting up MCP server...")
    
    try:
        # Register MCP server
        mcp_server = system.register_mcp_server(
            name="MultiAgenticSwarm-Server",
            host="localhost",
            port=8765,
            transport="websocket",
            expose_global_tools=True  # Expose all global tools
        )
        
        # Get server status
        status = mcp_server.get_status()
        print(f"✅ MCP Server created:")
        print(f"   Name: {status['name']}")
        print(f"   Address: ws://{status['host']}:{status['port']}")
        print(f"   Transport: {status['transport']}")
        print(f"   Exposed tools: {status['exposed_tools']}")
        
        # List exposed tools
        descriptors = mcp_server.get_tool_descriptors()
        print(f"\n🔧 Exposed tools via MCP:")
        for desc in descriptors:
            print(f"   - {desc.name}: {desc.description}")
        
        print(f"\n🚀 Starting MCP server...")
        
        # Start the server
        await system.start_mcp_server("MultiAgenticSwarm-Server")
        
        print(f"✅ MCP Server is running on ws://localhost:8765")
        print(f"\n💡 To test the server:")
        print(f"   1. Use an MCP client to connect to ws://localhost:8765")
        print(f"   2. Send 'initialize' request to establish connection")
        print(f"   3. Send 'tools/list' request to see available tools")
        print(f"   4. Send 'tools/call' requests to execute tools")
        print(f"\n📖 Example tool calls:")
        print(f"   - data_processor: {{\"name\": \"data_processor\", \"arguments\": {{\"data\": \"hello world\", \"operation\": \"uppercase\"}}}}")
        print(f"   - calculator: {{\"name\": \"calculator\", \"arguments\": {{\"expression\": \"2 + 3 * 4\"}}}}")
        print(f"   - Logger: {{\"name\": \"Logger\", \"arguments\": {{\"message\": \"Test log message\", \"level\": \"info\"}}}}")
        
        print(f"\n⏰ Server will run for 60 seconds, then shutdown...")
        print(f"   (Press Ctrl+C to stop early)")
        
        try:
            # Keep server running for demonstration
            await asyncio.sleep(60)
        except KeyboardInterrupt:
            print(f"\n⚠️  Interrupted by user")
        
    except ImportError as e:
        print(f"❌ MCP server not available: {e}")
        print(f"   Install dependencies: pip install websockets aiohttp")
        return
    
    except Exception as e:
        print(f"❌ Error setting up MCP server: {e}")
        return
    
    finally:
        print(f"\n🛑 Shutting down MCP server...")
        try:
            await system.stop_mcp_server("MultiAgenticSwarm-Server")
            print(f"✅ MCP server stopped")
        except Exception as e:
            print(f"⚠️  Error stopping server: {e}")
        
        print(f"\n🎉 MCP server example completed!")


if __name__ == "__main__":
    # Check if MCP is available
    try:
        from multiagenticswarm.core.mcp_integration import MCPServer
        print("🔍 Starting MCP Server Example")
        print("=" * 50)
        asyncio.run(main())
    except ImportError:
        print("❌ MCP integration not available")
        print("   This example requires websockets and aiohttp:")
        print("   pip install websockets aiohttp")
