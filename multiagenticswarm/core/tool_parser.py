import json
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger
from .base_tool import ToolCallRequest

logger = get_logger(__name__)


class ToolCallParser:
    """Parse tool calls from agent responses using JSON parsing."""

    @staticmethod
    def extract_tool_calls(response: str) -> List[ToolCallRequest]:
        """
        Extract tool calls from agent response.
        Looks for JSON objects with 'name' and 'args' fields.
        """
        tool_calls = []

        # Try to parse the entire response as JSON first
        try:
            data = json.loads(response)
            if isinstance(data, dict) and "name" in data:
                tool_calls.append(
                    ToolCallRequest.from_dict(
                        {
                            "name": data["name"],
                            "arguments": data.get("args", data.get("arguments", {})),
                        }
                    )
                )
                return tool_calls
        except json.JSONDecodeError:
            pass

        # Use a simpler approach: find all JSON-like objects using regex
        import re

        # Find all potential JSON objects starting with { and potentially ending with }
        # This regex finds JSON objects that might span multiple lines
        json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"

        # Find all matches
        matches = re.finditer(json_pattern, response, re.DOTALL)

        for match in matches:
            json_str = match.group()
            try:
                data = json.loads(json_str)
                if isinstance(data, dict) and "name" in data:
                    tool_calls.append(
                        ToolCallRequest.from_dict(
                            {
                                "name": data["name"],
                                "arguments": data.get(
                                    "args", data.get("arguments", {})
                                ),
                            }
                        )
                    )
            except json.JSONDecodeError:
                logger.debug(f"Failed to parse potential JSON: {json_str[:100]}...")
                continue

        return tool_calls
