"""
Model Context Protocol (MCP) integration for MultiAgenticSwarm.

This module provides MCP server and client implementations to enable
standardized tool sharing and interoperability with external systems.
"""

import asyncio
import json
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    from websockets.server import WebSocketServerProtocol

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketServerProtocol = None
    WebSocketClientProtocol = None

try:
    import aiohttp
    from aiohttp import web

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    web = None

from ..utils.logger import get_logger
from .base_tool import BaseTool, ToolCallRequest, ToolCallResponse, ToolScope

logger = get_logger(__name__)


class MCPTransportType(str, Enum):
    """MCP transport types."""

    WEBSOCKET = "websocket"
    HTTP = "http"
    STDIO = "stdio"


@dataclass
class MCPMessage:
    """MCP protocol message format."""

    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"jsonrpc": self.jsonrpc}
        if self.id is not None:
            result["id"] = self.id
        if self.method is not None:
            result["method"] = self.method
        if self.params is not None:
            result["params"] = self.params
        if self.result is not None:
            result["result"] = self.result
        if self.error is not None:
            result["error"] = self.error
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPMessage":
        """Create from dictionary."""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method"),
            params=data.get("params"),
            result=data.get("result"),
            error=data.get("error"),
        )


@dataclass
class MCPCapability:
    """MCP capability description."""

    name: str
    description: str
    version: str = "1.0.0"
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MCPToolDescriptor:
    """MCP tool descriptor following the protocol specification."""

    name: str
    description: str
    inputSchema: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_base_tool(cls, tool: BaseTool) -> "MCPToolDescriptor":
        """Create MCP tool descriptor from BaseTool."""
        return cls(
            name=tool.name,
            description=tool.description,
            inputSchema=tool.parameters,
            metadata={
                "scope": tool.scope.value,
                "tool_id": tool.tool_id,
                "usage_count": tool.usage_count,
            },
        )


class MCPTool(BaseTool):
    """
    Wrapper that adapts external MCP tools to MultiAgenticSwarm's BaseTool interface.

    This allows external MCP tools to be used seamlessly within the MultiAgenticSwarm
    system while maintaining proper scoping and access control.
    """

    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        mcp_client: "MCPClient",
        scope: ToolScope = ToolScope.GLOBAL,  # External tools default to global
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(name, description, parameters, scope)
        self.mcp_client = mcp_client
        self.metadata = metadata or {}
        self.is_external = True

        logger.info(f"Created MCP tool wrapper '{name}' for external tool")

    async def _execute_impl(self, **kwargs) -> Any:
        """Execute the external MCP tool via the client."""
        try:
            # Create tool call request for the external MCP server
            request = ToolCallRequest(
                id=str(uuid.uuid4()), name=self.name, arguments=kwargs
            )

            # Execute via MCP client
            response = await self.mcp_client.call_tool(request)

            if response.success:
                return response.result
            else:
                raise Exception(f"MCP tool execution failed: {response.error}")

        except Exception as e:
            logger.error(f"Error executing MCP tool '{self.name}': {e}")
            raise


class MCPServer:
    """
    MCP Server that exposes MultiAgenticSwarm tools via the Model Context Protocol.

    This allows external MCP clients to discover and use tools from the
    MultiAgenticSwarm system.
    """

    def __init__(
        self,
        name: str = "MultiAgenticSwarm",
        version: str = "1.0.0",
        host: str = "localhost",
        port: int = 8765,
        transport: MCPTransportType = MCPTransportType.WEBSOCKET,
    ):
        self.name = name
        self.version = version
        self.host = host
        self.port = port
        self.transport = transport

        # Tool registry - only tools that should be exposed via MCP
        self.exposed_tools: Dict[str, BaseTool] = {}

        # Client connections
        self.clients: Dict[str, Any] = {}

        # Server state
        self.running = False
        self.server = None

        logger.info(
            f"Created MCP server '{name}' on {host}:{port} using {transport.value}"
        )

    def expose_tool(self, tool: BaseTool, force_global: bool = False) -> None:
        """
        Expose a tool via MCP protocol.

        Args:
            tool: Tool to expose
            force_global: If True, expose the tool even if it's not global scope
        """
        # Only expose global tools by default, unless forced
        if not tool.is_global and not force_global:
            logger.warning(
                f"Tool '{tool.name}' is not global scope, not exposing via MCP. Use force_global=True to override."
            )
            return

        self.exposed_tools[tool.name] = tool
        logger.info(f"Exposed tool '{tool.name}' via MCP server")

    def expose_tools(self, tools: List[BaseTool], force_global: bool = False) -> None:
        """Expose multiple tools via MCP protocol."""
        for tool in tools:
            self.expose_tool(tool, force_global)

    def remove_tool(self, tool_name: str) -> bool:
        """Remove a tool from MCP exposure."""
        if tool_name in self.exposed_tools:
            del self.exposed_tools[tool_name]
            logger.info(f"Removed tool '{tool_name}' from MCP exposure")
            return True
        return False

    def get_capabilities(self) -> List[MCPCapability]:
        """Get server capabilities."""
        return [
            MCPCapability(
                name="tools",
                description="Tool discovery and execution",
                version="1.0.0",
            )
        ]

    def get_tool_descriptors(self) -> List[MCPToolDescriptor]:
        """Get MCP tool descriptors for all exposed tools."""
        descriptors = []
        for tool in self.exposed_tools.values():
            descriptor = MCPToolDescriptor.from_base_tool(tool)
            descriptors.append(descriptor)
        return descriptors

    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request."""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": True}},
            "serverInfo": {"name": self.name, "version": self.version},
        }

    async def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request."""
        tools = []
        for descriptor in self.get_tool_descriptors():
            tools.append(
                {
                    "name": descriptor.name,
                    "description": descriptor.description,
                    "inputSchema": descriptor.inputSchema,
                }
            )

        return {"tools": tools}

    async def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        try:
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name not in self.exposed_tools:
                raise ValueError(f"Tool '{tool_name}' not found")

            tool = self.exposed_tools[tool_name]

            # Create tool call request
            request = ToolCallRequest(
                id=str(uuid.uuid4()), name=tool_name, arguments=arguments
            )

            # Execute tool (use "mcp_client" as agent name)
            response = await tool.execute(request, "mcp_client")

            if response.success:
                return {
                    "content": [{"type": "text", "text": str(response.result)}],
                    "isError": False,
                }
            else:
                return {
                    "content": [{"type": "text", "text": f"Error: {response.error}"}],
                    "isError": True,
                }

        except Exception as e:
            logger.error(f"Error handling tools/call: {e}")
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True,
            }

    async def handle_message(self, message: MCPMessage, client_id: str) -> MCPMessage:
        """Handle incoming MCP message."""
        try:
            if message.method == "initialize":
                result = await self.handle_initialize(message.params or {})
                return MCPMessage(id=message.id, result=result)

            elif message.method == "tools/list":
                result = await self.handle_tools_list(message.params or {})
                return MCPMessage(id=message.id, result=result)

            elif message.method == "tools/call":
                result = await self.handle_tools_call(message.params or {})
                return MCPMessage(id=message.id, result=result)

            else:
                return MCPMessage(
                    id=message.id,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {message.method}",
                    },
                )

        except Exception as e:
            logger.error(f"Error handling MCP message: {e}")
            return MCPMessage(
                id=message.id,
                error={"code": -32603, "message": f"Internal error: {str(e)}"},
            )

    async def start_websocket_server(self) -> None:
        """Start WebSocket server."""
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError(
                "websockets library not available. Install with: pip install websockets"
            )

        async def handle_client(websocket, path):
            client_id = str(uuid.uuid4())
            self.clients[client_id] = websocket
            logger.info(f"MCP client connected: {client_id}")

            try:
                async for message_str in websocket:
                    try:
                        message_data = json.loads(message_str)
                        message = MCPMessage.from_dict(message_data)

                        response = await self.handle_message(message, client_id)
                        response_str = json.dumps(response.to_dict())
                        await websocket.send(response_str)

                    except json.JSONDecodeError as e:
                        error_response = MCPMessage(
                            error={"code": -32700, "message": "Parse error"}
                        )
                        await websocket.send(json.dumps(error_response.to_dict()))

            except Exception as e:
                logger.error(f"Error handling MCP client {client_id}: {e}")
            finally:
                if client_id in self.clients:
                    del self.clients[client_id]
                logger.info(f"MCP client disconnected: {client_id}")

        import websockets

        self.server = await websockets.serve(handle_client, self.host, self.port)
        logger.info(f"MCP WebSocket server started on ws://{self.host}:{self.port}")

    async def start_http_server(self) -> None:
        """Start HTTP server."""
        if not AIOHTTP_AVAILABLE:
            raise ImportError(
                "aiohttp library not available. Install with: pip install aiohttp"
            )

        async def handle_http_request(request):
            try:
                data = await request.json()
                message = MCPMessage.from_dict(data)

                response = await self.handle_message(message, "http_client")
                return web.json_response(response.to_dict())

            except Exception as e:
                error_response = MCPMessage(
                    error={"code": -32603, "message": f"Internal error: {str(e)}"}
                )
                return web.json_response(error_response.to_dict(), status=500)

        app = web.Application()
        app.router.add_post("/mcp", handle_http_request)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        self.server = runner
        logger.info(f"MCP HTTP server started on http://{self.host}:{self.port}/mcp")

    async def start(self) -> None:
        """Start the MCP server."""
        if self.running:
            logger.warning("MCP server is already running")
            return

        try:
            if self.transport == MCPTransportType.WEBSOCKET:
                await self.start_websocket_server()
            elif self.transport == MCPTransportType.HTTP:
                await self.start_http_server()
            else:
                raise ValueError(f"Unsupported transport type: {self.transport}")

            self.running = True
            logger.info(f"MCP server '{self.name}' started successfully")

        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise

    async def stop(self) -> None:
        """Stop the MCP server."""
        if not self.running:
            return

        try:
            if self.server:
                if self.transport == MCPTransportType.WEBSOCKET:
                    self.server.close()
                    await self.server.wait_closed()
                elif self.transport == MCPTransportType.HTTP:
                    await self.server.cleanup()

            self.running = False
            self.clients.clear()
            logger.info(f"MCP server '{self.name}' stopped")

        except Exception as e:
            logger.error(f"Error stopping MCP server: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get server status."""
        return {
            "name": self.name,
            "version": self.version,
            "running": self.running,
            "transport": self.transport.value,
            "host": self.host,
            "port": self.port,
            "exposed_tools": len(self.exposed_tools),
            "connected_clients": len(self.clients),
        }


class MCPClient:
    """
    MCP Client that connects to external MCP servers to access their tools.

    This allows MultiAgenticSwarm to use tools from external MCP servers.
    """

    def __init__(
        self,
        server_url: str,
        name: str = "MultiAgenticSwarm-Client",
        transport: MCPTransportType = MCPTransportType.WEBSOCKET,
    ):
        self.server_url = server_url
        self.name = name
        self.transport = transport

        # Connection state
        self.connected = False
        self.connection = None
        self.session = None

        # Remote server info
        self.server_info: Optional[Dict[str, Any]] = None
        self.server_capabilities: Optional[Dict[str, Any]] = None
        self.available_tools: Dict[str, Dict[str, Any]] = {}

        logger.info(f"Created MCP client for {server_url} using {transport.value}")

    async def connect(self) -> None:
        """Connect to the MCP server."""
        if self.connected:
            logger.warning("MCP client is already connected")
            return

        try:
            if self.transport == MCPTransportType.WEBSOCKET:
                await self._connect_websocket()
            elif self.transport == MCPTransportType.HTTP:
                await self._connect_http()
            else:
                raise ValueError(f"Unsupported transport type: {self.transport}")

            # Initialize connection
            await self._initialize()

            # Discover available tools
            await self._discover_tools()

            self.connected = True
            logger.info(f"Connected to MCP server at {self.server_url}")

        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise

    async def _connect_websocket(self) -> None:
        """Connect via WebSocket."""
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError(
                "websockets library not available. Install with: pip install websockets"
            )

        import websockets

        self.connection = await websockets.connect(self.server_url)

    async def _connect_http(self) -> None:
        """Connect via HTTP."""
        if not AIOHTTP_AVAILABLE:
            raise ImportError(
                "aiohttp library not available. Install with: pip install aiohttp"
            )

        import aiohttp

        self.session = aiohttp.ClientSession()

    async def _initialize(self) -> None:
        """Initialize MCP connection."""
        message = MCPMessage(
            id=str(uuid.uuid4()),
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": self.name, "version": "1.0.0"},
            },
        )

        response = await self._send_message(message)

        if response.error:
            raise Exception(f"MCP initialization failed: {response.error}")

        self.server_info = response.result.get("serverInfo", {})
        self.server_capabilities = response.result.get("capabilities", {})

        logger.info(f"Initialized MCP connection with server: {self.server_info}")

    async def _discover_tools(self) -> None:
        """Discover available tools from the server."""
        message = MCPMessage(id=str(uuid.uuid4()), method="tools/list", params={})

        response = await self._send_message(message)

        if response.error:
            logger.warning(f"Failed to discover tools: {response.error}")
            return

        tools = response.result.get("tools", [])
        self.available_tools = {tool["name"]: tool for tool in tools}

        logger.info(f"Discovered {len(self.available_tools)} tools from MCP server")

    async def _send_message(self, message: MCPMessage) -> MCPMessage:
        """Send message to MCP server and wait for response."""
        try:
            if self.transport == MCPTransportType.WEBSOCKET:
                return await self._send_websocket_message(message)
            elif self.transport == MCPTransportType.HTTP:
                return await self._send_http_message(message)
            else:
                raise ValueError(f"Unsupported transport type: {self.transport}")

        except Exception as e:
            logger.error(f"Error sending MCP message: {e}")
            raise

    async def _send_websocket_message(self, message: MCPMessage) -> MCPMessage:
        """Send message via WebSocket."""
        if not self.connection:
            raise Exception("WebSocket connection not established")

        message_str = json.dumps(message.to_dict())
        await self.connection.send(message_str)

        response_str = await self.connection.recv()
        response_data = json.loads(response_str)

        return MCPMessage.from_dict(response_data)

    async def _send_http_message(self, message: MCPMessage) -> MCPMessage:
        """Send message via HTTP."""
        if not self.session:
            raise Exception("HTTP session not established")

        async with self.session.post(
            self.server_url, json=message.to_dict()
        ) as response:
            response_data = await response.json()
            return MCPMessage.from_dict(response_data)

    async def call_tool(self, request: ToolCallRequest) -> ToolCallResponse:
        """Call a tool on the remote MCP server."""
        if not self.connected:
            raise Exception("Not connected to MCP server")

        if request.name not in self.available_tools:
            raise ValueError(f"Tool '{request.name}' not available on MCP server")

        message = MCPMessage(
            id=str(uuid.uuid4()),
            method="tools/call",
            params={"name": request.name, "arguments": request.arguments},
        )

        start_time = time.time()

        try:
            response = await self._send_message(message)
            execution_time = time.time() - start_time

            if response.error:
                return ToolCallResponse(
                    id=request.id,
                    name=request.name,
                    result=None,
                    success=False,
                    error=response.error.get("message", "Unknown error"),
                    execution_time=execution_time,
                )

            # Extract result from MCP response
            result_content = response.result.get("content", [])
            if result_content and len(result_content) > 0:
                result = result_content[0].get("text", "")
            else:
                result = response.result

            is_error = response.result.get("isError", False)

            return ToolCallResponse(
                id=request.id,
                name=request.name,
                result=result,
                success=not is_error,
                error=result if is_error else None,
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return ToolCallResponse(
                id=request.id,
                name=request.name,
                result=None,
                success=False,
                error=str(e),
                execution_time=execution_time,
            )

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.available_tools.keys())

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific tool."""
        return self.available_tools.get(tool_name)

    def create_mcp_tools(self, scope: ToolScope = ToolScope.GLOBAL) -> List[MCPTool]:
        """Create MCPTool wrappers for all available tools."""
        tools = []

        for tool_name, tool_info in self.available_tools.items():
            mcp_tool = MCPTool(
                name=tool_name,
                description=tool_info.get("description", ""),
                parameters=tool_info.get("inputSchema", {}),
                mcp_client=self,
                scope=scope,
                metadata=tool_info,
            )
            tools.append(mcp_tool)

        return tools

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if not self.connected:
            return

        try:
            if self.transport == MCPTransportType.WEBSOCKET and self.connection:
                await self.connection.close()
            elif self.transport == MCPTransportType.HTTP and self.session:
                await self.session.close()

            self.connected = False
            self.connection = None
            self.session = None

            logger.info(f"Disconnected from MCP server at {self.server_url}")

        except Exception as e:
            logger.error(f"Error disconnecting from MCP server: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get client status."""
        return {
            "server_url": self.server_url,
            "name": self.name,
            "transport": self.transport.value,
            "connected": self.connected,
            "server_info": self.server_info,
            "available_tools": len(self.available_tools),
        }
