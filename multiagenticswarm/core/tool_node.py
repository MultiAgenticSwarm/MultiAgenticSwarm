from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
import functools

from .tool_registry import ToolRegistry
from .tool_permissions import ToolPermissions

from ..utils.logger import get_logger

logger = get_logger(__name__)


"""
    This will be the exposed class that will return the ToolNode and handle registry, permissions using the specific
    class implementation
"""

class ToolNodeManager:
    def __init__(self, permissions: ToolPermissions, registry: ToolRegistry):
        self.registry = registry
        self.permissions = permissions
        self.tools = {}  # wrapped functions


    def register_tool(self, tool_id, name, description, category, func,
                      schema=None, output_schema=None, metadata=None,
                      default_permission=None, quota=None):

        # Register raw definition
        self.registry.register_tool(tool_id, name, description, category, func,
                                    schema, output_schema, metadata)

        # Optionally set default permission
        if default_permission:
            self.permissions.set_permission("default", tool_id, status=default_permission, quota=quota)

        # TODO: the tools should be compatible with the LangGraph system and the agent should be exposed to proper
        #  tool args as defined in the tool function signature, also need to manage the function name to be close to
        #  the original function name as it is also a part of the tool schema.
        # Wrap function with checks
        @functools.wraps(func)
        @tool(description=description)
        def wrapped(*args, **kwargs):
            # allowed, reason = self.permissions.check_permission(agent_id, tool_id, context)
            #
            # if not allowed:
            #     self.permissions.log(agent_id, tool_id, "EXECUTE", "DENIED", reason)
            #     return {"error": reason}
            #
            # ok, quota_reason = self.permissions._check_quota(agent_id, tool_id)
            # if not ok:
            #     self.permissions.log(agent_id, tool_id, "EXECUTE", "DENIED", quota_reason)
            #     return {"error": quota_reason}

            try:
                logger.info("tool name", func.__name__)
                logger.info("tool description", func.__doc__)

                result = func(*args, **kwargs)
                # self.permissions.log(agent_id, tool_id, "EXECUTE", "SUCCESS", {"args": args, "kwargs": kwargs})
                return {"result": result}

            except Exception as e:
                # self.permissions.log(agent_id, tool_id, "EXECUTE", "ERROR", str(e))
                return {"error": str(e)}

        # Store wrapped function
        self.tools[tool_id] = wrapped


    # This will be the API accessed by the agent to access to all the tools with proper validation happening and stuff
    def get_tool_node(self):
        return ToolNode(self.tools.values())

    def get_tools(self):
        return self.tools.values()

