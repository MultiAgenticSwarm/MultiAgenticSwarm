
# TODO: improve the registry system
class ToolRegistry:
    def __init__(self):
        self.registry = {}

    def register_tool(self, tool_id, name, description, category, func,
                      schema=None, output_schema=None, metadata=None):
        """Register raw tool definition"""
        self.registry[tool_id] = {
            "name": name,
            "description": description,
            "category": category,
            "function": func,
            "schema": schema or {},
            "output_schema": output_schema or {},
            "metadata": metadata or {}
        }

    def get_tool(self, tool_id):
        return self.registry.get(tool_id)

    def list_tools(self):
        return self.registry
