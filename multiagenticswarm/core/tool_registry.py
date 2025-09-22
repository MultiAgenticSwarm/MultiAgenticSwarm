from difflib import get_close_matches

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """Central in-memory registry for tool definitions.

    Responsibilities:
    - Store raw tool metadata (name, description, category, callable, schemas, etc.)
    - Provide discovery via fuzzy matching and optional category filtering
    - Expose retrieval helpers for other components
    """
    def __init__(self):
        self.registry = {}
        logger.debug("Initialized ToolRegistry with empty registry")


    def register_tool(self, tool_id, name, description, category, func,
                      schema=None, output_schema=None, metadata=None):
        """Register raw tool definition in the registry.

        Args:
            tool_id: Unique identifier for the tool
            name: Human-readable name
            description: What the tool does
            category: Logical grouping/category
            func: Callable implementing the tool
            schema: Optional input schema
            output_schema: Optional output schema
            metadata: Arbitrary metadata for the tool
        """
        self.registry[tool_id] = {
            "name": name,
            "description": description,
            "category": category,
            "function": func,
            "schema": schema or {},
            "output_schema": output_schema or {},
            "metadata": metadata or {},
            "available": callable(func)  # simple availability check
        }
        logger.info(
            f"Registered tool '{tool_id}' (name='{name}', category='{category}')",
            extra={"mas_tool": tool_id, "mas_category": category}
        )


    def get_tool(self, tool_id):
        tool = self.registry.get(tool_id)
        logger.debug(
            f"Get tool requested: '{tool_id}' - {'FOUND' if tool else 'NOT FOUND'}",
            extra={"mas_tool": tool_id}
        )
        return tool


    def discover_tool(self, query=None, category=None, top_k=3):
        """
        Discover tools by semantic-like search (fuzzy matching on description/name),
        with optional category filter and availability check.
        """
        results = []
        logger.debug(
            "Discover tool invoked",
            extra={"mas_query": query, "mas_category": category, "mas_top_k": top_k}
        )

        for tool_id, tool in self.registry.items():
            # Skip unavailable tools
            if not tool["available"]:
                continue

            # Category filter
            if category and tool["category"].lower() != category.lower():
                continue

            # Match query (name + description)
            if query:
                # Tokenize name and description into words
                words = tool["name"].split() + tool["description"].split()
                matches = get_close_matches(query, words, n=1, cutoff=0.7)
                if matches:
                    results.append((tool_id, tool))
            else:
                results.append((tool_id, tool))

        if query:
            results = sorted(
                results,
                key=lambda x: x[1]["description"].lower().find(query.lower())
                if query.lower() in x[1]["description"].lower() else float('inf')
            )

        final = results[:top_k]
        logger.debug(
            f"Discovery returning {len(final)} tool(s)",
            extra={"mas_query": query, "mas_category": category}
        )
        return final


    def list_tools(self):
        logger.debug(f"Listing all tools. Count={len(self.registry)}")
        return self.registry
