from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, InjectedState
import inspect
import makefun
from typing import Annotated, Optional

from .tool_registry import ToolRegistry
from .tool_permissions import ToolPermissions

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ToolNodeManager:
    """Orchestrates tool registration and exposure to LangGraph as a ToolNode.

    - Wraps raw callables with permission checks and uniform logging
    - Maintains a collection of tool wrappers compatible with LangChain/Graph
    - Provides a single ToolNode for centralized execution
    """
    def __init__(self, permissions: ToolPermissions, registry: ToolRegistry):
        self.registry = registry
        self.permissions = permissions
        self.tools = {}
        logger.debug("Initialized ToolNodeManager with empty tool set")


    def register_tool(self, tool_id, name, description, category, func,
                      schema=None, output_schema=None, metadata=None,
                      default_permission=None, quota=None):

        # Register Tool
        self.registry.register_tool(tool_id, name, description, category, func,
                                    schema, output_schema, metadata)
        logger.info(
            f"ToolNodeManager registering tool wrapper for '{tool_id}'",
            extra={"mas_tool": tool_id, "mas_category": category}
        )
        # Set Tool Permissions
        if default_permission:
            self.permissions.set_permission("default", tool_id, status=default_permission, quota=quota)

        # Grab function signature, docstring and name
        sig = inspect.signature(func)
        params = list(sig.parameters.values())

        new_param = inspect.Parameter(
            "currState",
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=Optional[Annotated[dict, InjectedState]],
            default=None,
        )
        params.append(new_param)
        new_sig = sig.replace(parameters=params)

        doc = func.__doc__ or description or f"Tool {name}"
        func_name = func.__name__ if func.__name__ not in ("<lambda>", "") else name

        # Build a wrapper with the same signature as the passed function
        @makefun.with_signature(new_sig, func_name=func_name)
        def wrapped(*args, currState: Annotated[dict, InjectedState], **kwargs):

            # Log limited state info to avoid leaking large payloads
            state_keys = list(currState.keys()) if isinstance(currState, dict) else None
            logger.debug(
                "Injected state received",
                extra={"mas_context": {"state_keys": state_keys}}
            )

            # Preserve original behavior: agent id comes from injected state
            agent_id = currState.get("current_agent", "default") if isinstance(currState, dict) else "default"
            context = kwargs.pop("context", None)

            allowed, reason = self.permissions.check_permission(agent_id, tool_id, context)
            if not allowed:
                self.permissions.log(agent_id, tool_id, "EXECUTE", "DENIED", reason)
                logger.warning(
                    "Tool execution denied",
                    extra={"mas_tool": tool_id, "mas_agent": agent_id, "mas_reason": reason}
                )
                return {"error": reason}

            try:
                result = func(*args, **kwargs)
                self.permissions.log(agent_id, tool_id, "EXECUTE", "SUCCESS", {"args": str(args), "kwargs": list(kwargs.keys())})
                logger.info(
                    "Tool executed successfully",
                    extra={"mas_tool": tool_id, "mas_agent": agent_id}
                )
                return {"result": result}
            except Exception as e:
                self.permissions.log(agent_id, tool_id, "EXECUTE", "ERROR", str(e))
                logger.error(
                    f"Tool execution error: {e}",
                    extra={"mas_tool": tool_id, "mas_agent": agent_id}
                )
                return {"error": str(e)}

        # Apply tool decorator
        wrapped = tool(description=doc)(wrapped)
        self.tools[tool_id] = wrapped
        logger.debug("Tool wrapper created and stored", extra={"mas_tool": tool_id})


    def get_tool_node(self):
        logger.debug("Providing ToolNode for registered tools", extra={"mas_tools_count": len(self.tools)})
        return ToolNode(self.tools.values())


    def get_tools(self):
        logger.debug("Returning tool collection", extra={"mas_tools_count": len(self.tools)})
        return self.tools.values()
