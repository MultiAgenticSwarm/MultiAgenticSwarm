"""
Example: Connecting to an external MCP server as a client.

This example shows how to:
1. Connect to an external MCP server
2. Discover available tools from the server
3. Use external tools within MultiAgenticSwarm agents
4. Create a system that combines local and remote tools

To test this example:
1. First run the mcp_server_example.py to start a local MCP server
2. Then run this script: python examples/mcp_client_example.py
3. Watch as the client connects and uses remote tools
"""

import asyncio
import time
from multiagenticswarm import System, Agent
from multiagenticswarm.core.base_tool import FunctionTool, ToolScope


def create_local_tool():
    """Create a local tool for comparison."""
    
    def greet_user(name: str, greeting: str = "Hello") -> str:
        """
        Greet a user with a personalized message.
        
        Args:
            name: Name of the user to greet
            greeting: Type of greeting (Hello, Hi, Welcome, etc.)
        
        Returns:
            Personalized greeting message
        """
        return f"{greeting}, {name}! Welcome to MultiAgenticSwarm!"
    
    tool = FunctionTool(
        func=greet_user,
        name="local_greeter",
        description="Generate personalized greetings (local tool)",
        parameters={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the user to greet"
                },
                "greeting": {
                    "type": "string",
                    "description": "Type of greeting",
                    "default": "Hello"
                }
            },
            "required": ["name"]
        }
    )
    
    tool.set_global()
    return tool


async def demonstrate_tool_usage(system: System, agent: Agent):
    """Demonstrate using both local and remote tools."""
    
    print(f"\n🤖 Testing agent '{agent.name}' with mixed tools...")
    
    # Test local tool
    print(f"\n1. Testing local tool:")
    try:
        result = await system.execute_agent(
            agent_name=agent.name,
            input_text="Use the local_greeter tool to greet 'Alice' with a 'Welcome' greeting.",
            context={"test": "local_tool"}
        )
        print(f"   Result: {result.get('result', {}).get('output', 'No output')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test remote tool (data processor)
    print(f"\n2. Testing remote tool (data_processor):")
    try:
        result = await system.execute_agent(
            agent_name=agent.name,
            input_text="Use the data_processor tool to convert 'Hello World' to uppercase.",
            context={"test": "remote_tool"}
        )
        print(f"   Result: {result.get('result', {}).get('output', 'No output')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test remote tool (calculator)
    print(f"\n3. Testing remote tool (calculator):")
    try:
        result = await system.execute_agent(
            agent_name=agent.name,
            input_text="Use the calculator tool to compute 15 * 7 + 23.",
            context={"test": "remote_calculator"}
        )
        print(f"   Result: {result.get('result', {}).get('output', 'No output')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test combining tools
    print(f"\n4. Testing combined workflow:")
    try:
        result = await system.execute_agent(
            agent_name=agent.name,
            input_text="First greet 'Bob' using the local_greeter, then use data_processor to make the greeting uppercase, and finally use Logger to log the result.",
            context={"test": "combined_workflow"}
        )
        print(f"   Result: {result.get('result', {}).get('output', 'No output')}")
    except Exception as e:
        print(f"   Error: {e}")


async def main():
    """Main function to demonstrate MCP client setup."""
    
    print("🔧 Setting up MultiAgenticSwarm system...")
    
    # Create system
    system = System(enable_logging=True, verbose=True)
    
    # Add a local tool
    local_tool = create_local_tool()
    system.tool_executor.register_tool(local_tool)
    
    # Create an agent
    agent = Agent(
        name="MixedToolAgent",
        description="Agent that can use both local and remote tools",
        system_prompt="You are a helpful agent that can use various tools to assist users. Always use the appropriate tools to complete tasks.",
        llm_provider="openai",
        llm_model="gpt-3.5-turbo"
    )
    system.register_agent(agent)
    
    print(f"✅ System initialized with {len(system.tool_executor.get_all_tools())} local tools")
    
    print(f"\n🌐 Connecting to external MCP server...")
    
    try:
        # Connect to MCP server (assumes mcp_server_example.py is running)
        mcp_client = await system.connect_mcp_client(
            name="external-server",
            server_url="ws://localhost:8765",
            transport="websocket",
            register_tools=True,
            tool_scope="global"
        )
        
        print(f"✅ Connected to MCP server")
        
        # Get client status
        status = mcp_client.get_status()
        print(f"   Server URL: {status['server_url']}")
        print(f"   Connected: {status['connected']}")
        print(f"   Available remote tools: {status['available_tools']}")
        
        # List available remote tools
        remote_tools = mcp_client.get_available_tools()
        print(f"\n🔧 Remote tools discovered:")
        for tool_name in remote_tools:
            tool_info = mcp_client.get_tool_info(tool_name)
            print(f"   - {tool_name}: {tool_info.get('description', 'No description')}")
        
        # Show all tools now available in the system
        all_tools = system.tool_executor.get_all_tools()
        print(f"\n📋 All tools now available ({len(all_tools)} total):")
        for tool in all_tools:
            tool_type = "remote" if hasattr(tool, 'is_external') and tool.is_external else "local"
            print(f"   - {tool.name}: {tool.description} ({tool_type})")
        
        # Demonstrate tool usage
        await demonstrate_tool_usage(system, agent)
        
        # Show MCP status
        mcp_status = system.get_mcp_status()
        print(f"\n📊 MCP Integration Status:")
        print(f"   Servers: {mcp_status['total_servers']}")
        print(f"   Clients: {mcp_status['total_clients']}")
        for client_name, client_status in mcp_status['clients'].items():
            print(f"   - {client_name}: {client_status['available_tools']} tools available")
        
    except ImportError as e:
        print(f"❌ MCP client not available: {e}")
        print(f"   Install dependencies: pip install websockets aiohttp")
        return
    
    except ConnectionError as e:
        print(f"❌ Could not connect to MCP server: {e}")
        print(f"   Make sure the MCP server is running:")
        print(f"   python examples/mcp_server_example.py")
        return
    
    except Exception as e:
        print(f"❌ Error connecting to MCP server: {e}")
        print(f"   Make sure the MCP server is running on ws://localhost:8765")
        return
    
    finally:
        print(f"\n🛑 Disconnecting from MCP server...")
        try:
            await system.disconnect_mcp_client("external-server")
            print(f"✅ Disconnected from MCP server")
        except Exception as e:
            print(f"⚠️  Error disconnecting: {e}")
        
        print(f"\n🎉 MCP client example completed!")


async def test_connection():
    """Test if MCP server is available before running the main example."""
    
    print("🔍 Testing connection to MCP server...")
    
    try:
        from multiagenticswarm.core.mcp_integration import MCPClient, MCPTransportType
        
        # Create a test client
        test_client = MCPClient("ws://localhost:8765", transport=MCPTransportType.WEBSOCKET)
        
        # Try to connect
        await test_client.connect()
        
        print("✅ MCP server is available!")
        
        # Disconnect test client
        await test_client.disconnect()
        
        return True
        
    except Exception as e:
        print(f"❌ MCP server not available: {e}")
        print(f"\n💡 To fix this:")
        print(f"   1. Open another terminal")
        print(f"   2. Run: python examples/mcp_server_example.py")
        print(f"   3. Wait for 'MCP Server is running' message")
        print(f"   4. Then run this example again")
        return False


if __name__ == "__main__":
    # Check if MCP is available
    try:
        from multiagenticswarm.core.mcp_integration import MCPClient
        print("🔍 Starting MCP Client Example")
        print("=" * 50)
        
        # Test connection first
        if asyncio.run(test_connection()):
            # Run main example
            asyncio.run(main())
        else:
            print("\n❌ Cannot proceed without MCP server running")
            
    except ImportError:
        print("❌ MCP integration not available")
        print("   This example requires websockets and aiohttp:")
        print("   pip install websockets aiohttp")
