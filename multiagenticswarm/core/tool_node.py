import inspect
from typing import Annotated, Optional, Any, Dict, Callable

import makefun
from langchain_core.tools import tool, InjectedToolArg
from langgraph.prebuilt import ToolNode, InjectedState

from .tool_registry import ToolRegistry
from .tool_permissions import ToolPermissions
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ToolNodeManager:
    def __init__(self, permissions: ToolPermissions, registry: ToolRegistry) -> None:
        self.registry = registry
        self.permissions = permissions
        self.tools: Dict[str, Any] = {}

    def register_tool(
        self, 
        tool_id: str, 
        name: str, 
        description: str, 
        category: str, 
        func: Callable,
        schema: Optional[Dict[str, Any]] = None, 
        output_schema: Optional[Dict[str, Any]] = None, 
        metadata: Optional[Dict[str, Any]] = None,
        default_permission: Optional[str] = None, 
        quota: Optional[Dict[str, Any]] = None
    ) -> None:

        self.registry.register_tool(tool_id, name, description, category, func,
                                    schema, output_schema, metadata)
        if default_permission:
            self.permissions.set_permission("default", tool_id, status=default_permission, quota=quota)

        sig = inspect.signature(func)
        doc = func.__doc__ or description or f"Tool {name}"
        func_name = func.__name__ if func.__name__ not in ("<lambda>", "") else name

        # TODO: the state is not being injected into the function, also make the registry etc. compatible with the
        #  State schema
        @makefun.with_signature(sig, func_name=func_name)
        def wrapped(*args, currState: Annotated[dict, InjectedState] = None, **kwargs):

            logger.debug('State received: %s', currState)

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

        wrapped = tool(description=doc)(wrapped)
        wrapped.__doc__ = doc

        self.tools[tool_id] = wrapped


    def get_tool_node(self) -> ToolNode:
        return ToolNode(self.tools.values())

    def get_tools(self) -> Any:
        return self.tools.values()
