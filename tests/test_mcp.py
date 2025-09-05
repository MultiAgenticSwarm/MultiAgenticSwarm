"""
Tests for MCP (Model Context Protocol) integration.
"""

import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Import the MCP components
try:
    from multiagenticswarm.core.base_tool import (
        BaseTool,
        ToolCallRequest,
        ToolCallResponse,
        ToolScope,
    )
    from multiagenticswarm.core.mcp_integration import (
        MCPCapability,
        MCPClient,
        MCPMessage,
        MCPServer,
        MCPTool,
        MCPToolDescriptor,
        MCPTransportType,
    )
    from multiagenticswarm.core.system import System

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


# Skip all tests if MCP components are not available
pytestmark = pytest.mark.skipif(
    not MCP_AVAILABLE, reason="MCP integration not available"
)


class TestTool(BaseTool):
    """Test tool for MCP testing."""

    def __init__(self, name: str = "test_tool"):
        super().__init__(
            name=name,
            description="A test tool for MCP integration",
            parameters={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Message to process"}
                },
                "required": ["message"],
            },
            scope=ToolScope.GLOBAL,
        )

    async def _execute_impl(self, message: str = "Hello") -> str:
        return f"Processed: {message}"


class TestMCPMessage:
    """Test MCPMessage class."""

    def test_message_creation(self):
        """Test creating MCP messages."""
        msg = MCPMessage(id="test-123", method="test/method", params={"key": "value"})

        assert msg.jsonrpc == "2.0"
        assert msg.id == "test-123"
        assert msg.method == "test/method"
        assert msg.params == {"key": "value"}

    def test_message_to_dict(self):
        """Test converting message to dictionary."""
        msg = MCPMessage(id="test-123", method="test/method", params={"key": "value"})

        data = msg.to_dict()
        expected = {
            "jsonrpc": "2.0",
            "id": "test-123",
            "method": "test/method",
            "params": {"key": "value"},
        }
        assert data == expected

    def test_message_from_dict(self):
        """Test creating message from dictionary."""
        data = {
            "jsonrpc": "2.0",
            "id": "test-123",
            "method": "test/method",
            "params": {"key": "value"},
        }

        msg = MCPMessage.from_dict(data)
        assert msg.jsonrpc == "2.0"
        assert msg.id == "test-123"
        assert msg.method == "test/method"
        assert msg.params == {"key": "value"}


class TestMCPToolDescriptor:
    """Test MCPToolDescriptor class."""

    def test_from_base_tool(self):
        """Test creating descriptor from BaseTool."""
        tool = TestTool("test_tool")
        descriptor = MCPToolDescriptor.from_base_tool(tool)

        assert descriptor.name == "test_tool"
        assert descriptor.description == "A test tool for MCP integration"
        assert descriptor.inputSchema["type"] == "object"
        assert "message" in descriptor.inputSchema["properties"]
        assert descriptor.metadata["scope"] == "global"


class TestMCPServer:
    """Test MCPServer class."""

    def test_server_creation(self):
        """Test creating MCP server."""
        server = MCPServer(
            name="test-server",
            host="localhost",
            port=8765,
            transport=MCPTransportType.WEBSOCKET,
        )

        assert server.name == "test-server"
        assert server.host == "localhost"
        assert server.port == 8765
        assert server.transport == MCPTransportType.WEBSOCKET
        assert not server.running
        assert len(server.exposed_tools) == 0

    def test_expose_tool(self):
        """Test exposing tools via MCP server."""
        server = MCPServer()
        tool = TestTool("test_tool")
        tool.set_global()  # Make sure tool is global

        server.expose_tool(tool)
        assert "test_tool" in server.exposed_tools
        assert server.exposed_tools["test_tool"] == tool

    def test_expose_non_global_tool(self):
        """Test exposing non-global tool (should be warned but not exposed)."""
        server = MCPServer()
        tool = TestTool("local_tool")
        tool.set_local("test_agent")

        # Should not expose local tool without force_global
        server.expose_tool(tool)
        assert "local_tool" not in server.exposed_tools

        # Should expose with force_global=True
        server.expose_tool(tool, force_global=True)
        assert "local_tool" in server.exposed_tools

    def test_get_capabilities(self):
        """Test getting server capabilities."""
        server = MCPServer()
        capabilities = server.get_capabilities()

        assert len(capabilities) == 1
        assert capabilities[0].name == "tools"
        assert capabilities[0].description == "Tool discovery and execution"

    def test_get_tool_descriptors(self):
        """Test getting tool descriptors."""
        server = MCPServer()
        tool = TestTool("test_tool")
        tool.set_global()  # Make sure tool is global
        server.expose_tool(tool)

        descriptors = server.get_tool_descriptors()
        assert len(descriptors) == 1
        assert descriptors[0].name == "test_tool"

    @pytest.mark.asyncio
    async def test_handle_initialize(self):
        """Test handling initialize request."""
        server = MCPServer()
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        }

        result = await server.handle_initialize(params)

        assert result["protocolVersion"] == "2024-11-05"
        assert "capabilities" in result
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == server.name

    @pytest.mark.asyncio
    async def test_handle_tools_list(self):
        """Test handling tools/list request."""
        server = MCPServer()
        tool = TestTool("test_tool")
        tool.set_global()  # Make sure tool is global
        server.expose_tool(tool)

        result = await server.handle_tools_list({})

        assert "tools" in result
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "test_tool"
        assert result["tools"][0]["description"] == "A test tool for MCP integration"

    @pytest.mark.asyncio
    async def test_handle_tools_call(self):
        """Test handling tools/call request."""
        server = MCPServer()
        tool = TestTool("test_tool")
        tool.set_global()  # Make sure tool is global
        server.expose_tool(tool)

        params = {"name": "test_tool", "arguments": {"message": "test message"}}

        result = await server.handle_tools_call(params)

        assert "content" in result
        assert result["isError"] is False
        assert "Processed: test message" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_handle_tools_call_unknown_tool(self):
        """Test handling tools/call request for unknown tool."""
        server = MCPServer()

        params = {"name": "unknown_tool", "arguments": {}}

        result = await server.handle_tools_call(params)

        assert "content" in result
        assert result["isError"] is True
        assert "not found" in result["content"][0]["text"]

    def test_get_status(self):
        """Test getting server status."""
        server = MCPServer(name="test-server", host="localhost", port=8765)
        tool = TestTool("test_tool")
        tool.set_global()  # Make sure tool is global
        server.expose_tool(tool)

        status = server.get_status()

        assert status["name"] == "test-server"
        assert status["host"] == "localhost"
        assert status["port"] == 8765
        assert status["running"] is False
        assert status["exposed_tools"] == 1
        assert status["connected_clients"] == 0


class TestMCPClient:
    """Test MCPClient class."""

    def test_client_creation(self):
        """Test creating MCP client."""
        client = MCPClient(
            server_url="ws://localhost:8765",
            name="test-client",
            transport=MCPTransportType.WEBSOCKET,
        )

        assert client.server_url == "ws://localhost:8765"
        assert client.name == "test-client"
        assert client.transport == MCPTransportType.WEBSOCKET
        assert not client.connected
        assert len(client.available_tools) == 0

    def test_get_available_tools(self):
        """Test getting available tool names."""
        client = MCPClient("ws://localhost:8765")
        client.available_tools = {
            "tool1": {"name": "tool1", "description": "Tool 1"},
            "tool2": {"name": "tool2", "description": "Tool 2"},
        }

        tools = client.get_available_tools()
        assert tools == ["tool1", "tool2"]

    def test_get_tool_info(self):
        """Test getting tool information."""
        client = MCPClient("ws://localhost:8765")
        tool_info = {"name": "tool1", "description": "Tool 1", "inputSchema": {}}
        client.available_tools = {"tool1": tool_info}

        info = client.get_tool_info("tool1")
        assert info == tool_info

        info = client.get_tool_info("unknown")
        assert info is None

    def test_create_mcp_tools(self):
        """Test creating MCPTool wrappers."""
        client = MCPClient("ws://localhost:8765")
        client.available_tools = {
            "tool1": {
                "name": "tool1",
                "description": "Tool 1",
                "inputSchema": {"type": "object", "properties": {}},
            }
        }

        mcp_tools = client.create_mcp_tools(ToolScope.GLOBAL)

        assert len(mcp_tools) == 1
        assert isinstance(mcp_tools[0], MCPTool)
        assert mcp_tools[0].name == "tool1"
        assert mcp_tools[0].scope == ToolScope.GLOBAL

    def test_get_status(self):
        """Test getting client status."""
        client = MCPClient("ws://localhost:8765", name="test-client")
        client.available_tools = {"tool1": {}}

        status = client.get_status()

        assert status["server_url"] == "ws://localhost:8765"
        assert status["name"] == "test-client"
        assert status["connected"] is False
        assert status["available_tools"] == 1


class TestMCPTool:
    """Test MCPTool class."""

    def test_mcp_tool_creation(self):
        """Test creating MCP tool."""
        mock_client = Mock()
        tool = MCPTool(
            name="external_tool",
            description="External tool via MCP",
            parameters={"type": "object", "properties": {}},
            mcp_client=mock_client,
            scope=ToolScope.GLOBAL,
        )

        assert tool.name == "external_tool"
        assert tool.description == "External tool via MCP"
        assert tool.scope == ToolScope.GLOBAL
        assert tool.is_external is True
        assert tool.mcp_client == mock_client

    @pytest.mark.asyncio
    async def test_mcp_tool_execute(self):
        """Test executing MCP tool."""
        mock_client = Mock()
        mock_client.call_tool = AsyncMock()
        mock_client.call_tool.return_value = ToolCallResponse(
            id="test-123", name="external_tool", result="External result", success=True
        )

        tool = MCPTool(
            name="external_tool",
            description="External tool",
            parameters={},
            mcp_client=mock_client,
        )

        result = await tool._execute_impl(message="test")

        assert result == "External result"
        mock_client.call_tool.assert_called_once()

        # Check the call arguments
        call_args = mock_client.call_tool.call_args[0][0]
        assert call_args.name == "external_tool"
        assert call_args.arguments == {"message": "test"}

    @pytest.mark.asyncio
    async def test_mcp_tool_execute_error(self):
        """Test executing MCP tool with error."""
        mock_client = Mock()
        mock_client.call_tool = AsyncMock()
        mock_client.call_tool.return_value = ToolCallResponse(
            id="test-123",
            name="external_tool",
            result=None,
            success=False,
            error="External error",
        )

        tool = MCPTool(
            name="external_tool",
            description="External tool",
            parameters={},
            mcp_client=mock_client,
        )

        with pytest.raises(Exception) as exc_info:
            await tool._execute_impl(message="test")

        assert "External error" in str(exc_info.value)


class TestSystemMCPIntegration:
    """Test MCP integration with System class."""

    def test_system_mcp_initialization(self):
        """Test that System initializes MCP components."""
        system = System()

        assert hasattr(system, "mcp_servers")
        assert hasattr(system, "mcp_clients")
        assert len(system.mcp_servers) == 0
        assert len(system.mcp_clients) == 0

    def test_register_mcp_server(self):
        """Test registering MCP server with System."""
        system = System()

        # Add a global tool first
        from multiagenticswarm.core.base_tool import FunctionTool

        def test_func(message: str) -> str:
            return f"Result: {message}"

        tool = FunctionTool(test_func, name="test_function")
        tool.set_global()
        system.tool_executor.register_tool(tool)

        # Register MCP server
        server = system.register_mcp_server(
            name="test-server", host="localhost", port=8765, transport="websocket"
        )

        assert "test-server" in system.mcp_servers
        assert system.mcp_servers["test-server"] == server
        assert server.name == "test-server"
        assert server.host == "localhost"
        assert server.port == 8765

    def test_get_mcp_status(self):
        """Test getting MCP status from System."""
        system = System()

        status = system.get_mcp_status()

        assert "servers" in status
        assert "clients" in status
        assert status["total_servers"] == 0
        assert status["total_clients"] == 0

    def test_list_mcp_components(self):
        """Test listing MCP components."""
        system = System()

        assert system.list_mcp_servers() == []
        assert system.list_mcp_clients() == []


@pytest.mark.integration
class TestMCPIntegration:
    """Integration tests for MCP components."""

    @pytest.mark.asyncio
    async def test_mcp_server_client_integration(self):
        """Test integration between MCP server and client."""
        # This test would require actual networking and is more complex
        # For now, we'll test the message flow

        # Create server
        server = MCPServer(name="integration-server")
        tool = TestTool("integration_tool")
        tool.set_global()  # Make sure tool is global
        server.expose_tool(tool)

        # Test message handling
        init_message = MCPMessage(
            id="init-1",
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client"},
            },
        )

        response = await server.handle_message(init_message, "test-client")
        assert response.id == "init-1"
        assert response.result is not None
        assert "serverInfo" in response.result

        # Test tools list
        list_message = MCPMessage(id="list-1", method="tools/list", params={})

        response = await server.handle_message(list_message, "test-client")
        assert response.id == "list-1"
        assert "tools" in response.result
        assert len(response.result["tools"]) == 1

        # Test tool call
        call_message = MCPMessage(
            id="call-1",
            method="tools/call",
            params={
                "name": "integration_tool",
                "arguments": {"message": "integration test"},
            },
        )

        response = await server.handle_message(call_message, "test-client")
        assert response.id == "call-1"
        assert response.result["isError"] is False
        assert "Processed: integration test" in response.result["content"][0]["text"]


if __name__ == "__main__":
    pytest.main([__file__])
