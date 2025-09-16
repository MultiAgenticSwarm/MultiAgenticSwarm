from langchain_core.tools import tool, InjectedToolArg
from langgraph.prebuilt import ToolNode, InjectedState
import inspect
import makefun
from typing import Annotated, Optional

from .tool_registry import ToolRegistry
from .tool_permissions import ToolPermissions

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ToolNodeManager:
    def __init__(self, permissions: ToolPermissions, registry: ToolRegistry):
        self.registry = registry
        self.permissions = permissions
        self.tools = {}


    def register_tool(self, tool_id, name, description, category, func,
                      schema=None, output_schema=None, metadata=None,
                      default_permission=None, quota=None):

        # Register Tool
        self.registry.register_tool(tool_id, name, description, category, func,
                                    schema, output_schema, metadata)
        # Set Tool Permissions
        if default_permission:
            self.permissions.set_permission("default", tool_id, status=default_permission, quota=quota)

        # Grab function signature, docstring and name (for lambdas)
        sig = inspect.signature(func)
        doc = func.__doc__ or description or f"Tool {name}"
        func_name = func.__name__ if func.__name__ not in ("<lambda>", "") else name

        # Build a wrapper with the same signature as the passed function
        # TODO: the state is not being injected into the function, also make the registry etc. compatible with the
        #  State schema
        @makefun.with_signature(sig, func_name=func_name)
        def wrapped(*args, currState: Annotated[dict, InjectedState] = None, **kwargs):

            print("State received: ", currState)

            agent_id = kwargs.pop("agent_id", "default")  # optional agent context
            context = kwargs.pop("context", None)

            allowed, reason = self.permissions.check_permission(agent_id, tool_id, context)
            if not allowed:
                self.permissions.log(agent_id, tool_id, "EXECUTE", "DENIED", reason)
                return {"error": reason}

            try:
                result = func(*args, **kwargs)
                self.permissions.log(agent_id, tool_id, "EXECUTE", "SUCCESS", {"args": args, "kwargs": kwargs})
                return {"result": result}
            except Exception as e:
                self.permissions.log(agent_id, tool_id, "EXECUTE", "ERROR", str(e))
                return {"error": str(e)}

        # Apply tool decorator
        wrapped = tool(description=doc)(wrapped)
        wrapped.__doc__ = doc

        self.tools[tool_id] = wrapped


    def get_tool_node(self):
        return ToolNode(self.tools.values())


    def get_tools(self):
        return self.tools.values()
