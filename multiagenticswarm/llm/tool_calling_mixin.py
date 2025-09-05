"""
Mixin for standardized tool calling across all LLM providers.
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..core.base_tool import ToolCallRequest, ToolCallResponse
from ..utils.logger import get_logger

logger = get_logger(__name__)


class StandardizedToolCallingMixin(ABC):
    """
    Mixin that provides standardized tool calling capabilities to all LLM providers.
    This ensures consistent behavior regardless of the underlying provider.
    """

    @abstractmethod
    def _convert_tools_to_provider_format(self, tools: List[Dict[str, Any]]) -> Any:
        """
        Convert standardized tool schemas to provider-specific format.
        Each provider must implement this method.
        """
        pass

    @abstractmethod
    def _extract_tool_calls_from_response(self, response: Any) -> List[ToolCallRequest]:
        """
        Extract tool calls from provider-specific response format.
        Each provider must implement this method.
        """
        pass

    @abstractmethod
    def _create_tool_response_message(
        self, tool_responses: List[ToolCallResponse]
    ) -> Dict[str, Any]:
        """
        Create provider-specific tool response message.
        Each provider must implement this method.
        """
        pass

    def prepare_tools_for_llm(self, tools: List[Dict[str, Any]]) -> Any:
        """
        Prepare tools for the LLM in provider-specific format.
        This is called before sending the request to the LLM.
        """
        if not tools:
            return None

        logger.debug(f"Preparing {len(tools)} tools for {self.__class__.__name__}")
        return self._convert_tools_to_provider_format(tools)

    def extract_tool_calls(self, response: Any) -> List[ToolCallRequest]:
        """
        Extract tool calls from LLM response in standardized format.
        """
        try:
            tool_calls = self._extract_tool_calls_from_response(response)
            logger.debug(f"Extracted {len(tool_calls)} tool calls from response")
            return tool_calls
        except Exception as e:
            logger.error(f"Failed to extract tool calls: {e}")
            return []

    def create_tool_response_for_llm(
        self, tool_responses: List[ToolCallResponse]
    ) -> Dict[str, Any]:
        """
        Create tool response message for the LLM in provider-specific format.
        """
        return self._create_tool_response_message(tool_responses)

    def should_continue_conversation(self, response: Any) -> bool:
        """
        Determine if the conversation should continue based on tool calls.
        """
        tool_calls = self.extract_tool_calls(response)
        return len(tool_calls) > 0
