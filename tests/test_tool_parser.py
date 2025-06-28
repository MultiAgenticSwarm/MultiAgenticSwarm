"""
Comprehensive test suite for ToolCallParser functionality.
"""
import pytest
import json
from unittest.mock import Mock, patch

from multiagenticswarm.core.tool_parser import ToolCallParser
from multiagenticswarm.core.base_tool import ToolCallRequest


class TestToolCallParserBasics:
    """Test basic ToolCallParser functionality."""
    
    def test_extract_simple_json_tool_call(self):
        """Test extracting a simple JSON tool call."""
        response = '{"name": "test_tool", "args": {"param1": "value1", "param2": 42}}'
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 1
        call = tool_calls[0]
        assert call.name == "test_tool"
        assert call.arguments == {"param1": "value1", "param2": 42}
        assert call.id is not None
    
    def test_extract_tool_call_with_arguments_key(self):
        """Test extracting tool call with 'arguments' instead of 'args'."""
        response = '{"name": "argument_tool", "arguments": {"x": 10, "y": 20}}'
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 1
        call = tool_calls[0]
        assert call.name == "argument_tool"
        assert call.arguments == {"x": 10, "y": 20}
    
    def test_extract_tool_call_no_arguments(self):
        """Test extracting tool call without arguments."""
        response = '{"name": "no_args_tool"}'
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 1
        call = tool_calls[0]
        assert call.name == "no_args_tool"
        assert call.arguments == {}
    
    def test_extract_empty_response(self):
        """Test extracting from empty response."""
        response = ""
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 0
    
    def test_extract_non_json_response(self):
        """Test extracting from non-JSON response."""
        response = "This is just a regular text response with no tool calls."
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 0
    
    def test_extract_malformed_json(self):
        """Test extracting from malformed JSON."""
        response = '{"name": "malformed_tool", "args": {"param": "value"'  # Missing closing braces
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 0  # Should handle gracefully


class TestMultipleToolCalls:
    """Test parsing multiple tool calls from a single response."""
    
    def test_extract_multiple_json_objects(self):
        """Test extracting multiple JSON tool calls."""
        response = '''
        {"name": "tool1", "args": {"param": "value1"}}
        {"name": "tool2", "args": {"param": "value2"}}
        {"name": "tool3", "args": {"param": "value3"}}
        '''
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 3
        assert tool_calls[0].name == "tool1"
        assert tool_calls[1].name == "tool2"
        assert tool_calls[2].name == "tool3"
        assert tool_calls[0].arguments == {"param": "value1"}
        assert tool_calls[1].arguments == {"param": "value2"}
        assert tool_calls[2].arguments == {"param": "value3"}
    
    def test_extract_mixed_with_text(self):
        """Test extracting tool calls mixed with regular text."""
        response = '''
        I need to call some tools to help you.
        
        {"name": "search_tool", "args": {"query": "python tutorial"}}
        
        Let me also check the weather:
        
        {"name": "weather_tool", "args": {"location": "New York"}}
        
        That should give us the information we need.
        '''
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 2
        assert tool_calls[0].name == "search_tool"
        assert tool_calls[0].arguments == {"query": "python tutorial"}
        assert tool_calls[1].name == "weather_tool"
        assert tool_calls[1].arguments == {"location": "New York"}
    
    def test_extract_nested_json_structures(self):
        """Test extracting tool calls with nested JSON arguments."""
        response = '''
        {
            "name": "complex_tool",
            "args": {
                "config": {
                    "setting1": "value1",
                    "setting2": {
                        "nested": "data"
                    }
                },
                "array_param": [1, 2, 3],
                "simple_param": "simple_value"
            }
        }
        '''
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 1
        call = tool_calls[0]
        assert call.name == "complex_tool"
        
        expected_args = {
            "config": {
                "setting1": "value1",
                "setting2": {
                    "nested": "data"
                }
            },
            "array_param": [1, 2, 3],
            "simple_param": "simple_value"
        }
        assert call.arguments == expected_args
    
    def test_extract_with_incomplete_json(self):
        """Test extracting when some JSON objects are incomplete."""
        response = '''
        {"name": "good_tool", "args": {"param": "value"}}
        {"name": "incomplete_tool", "args": {"param": "value"
        {"name": "another_good_tool", "args": {"param": "value2"}}
        '''
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        # Should extract the complete ones and skip the incomplete
        assert len(tool_calls) == 2
        assert tool_calls[0].name == "good_tool"
        assert tool_calls[1].name == "another_good_tool"


class TestJSONParsingEdgeCases:
    """Test edge cases in JSON parsing."""
    
    def test_extract_with_extra_whitespace(self):
        """Test extracting tool calls with extra whitespace."""
        response = '''
        
        
        {
            "name"   :   "whitespace_tool"  ,
            "args"   :   {
                "param1"  :  "value1"  ,
                "param2"  :  42
            }
        }
        
        
        '''
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 1
        call = tool_calls[0]
        assert call.name == "whitespace_tool"
        assert call.arguments == {"param1": "value1", "param2": 42}
    
    def test_extract_with_json_in_strings(self):
        """Test handling JSON-like content within strings."""
        response = '''
        {
            "name": "string_tool",
            "args": {
                "json_string": "{\\"nested\\": \\"json\\"}",
                "description": "This tool handles JSON strings"
            }
        }
        '''
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 1
        call = tool_calls[0]
        assert call.name == "string_tool"
        assert call.arguments["json_string"] == '{"nested": "json"}'
        assert call.arguments["description"] == "This tool handles JSON strings"
    
    def test_extract_with_special_characters(self):
        """Test extracting tool calls with special characters."""
        response = '''
        {
            "name": "special_chars_tool",
            "args": {
                "unicode": "Hello 🌍",
                "symbols": "!@#$%^&*()_+-=[]{}|;:,.<>?",
                "newlines": "Line 1\\nLine 2\\nLine 3",
                "quotes": "He said \\"Hello\\" to me"
            }
        }
        '''
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 1
        call = tool_calls[0]
        assert call.name == "special_chars_tool"
        assert "🌍" in call.arguments["unicode"]
        assert call.arguments["symbols"] == "!@#$%^&*()_+-=[]{}|;:,.<>?"
        assert "Line 1\nLine 2\nLine 3" in call.arguments["newlines"]
    
    def test_extract_with_numbers_and_booleans(self):
        """Test extracting tool calls with various data types."""
        response = '''
        {
            "name": "types_tool",
            "args": {
                "integer": 42,
                "float": 3.14159,
                "boolean_true": true,
                "boolean_false": false,
                "null_value": null,
                "array": [1, "two", 3.0, true, null],
                "object": {"nested": "value"}
            }
        }
        '''
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 1
        call = tool_calls[0]
        args = call.arguments
        
        assert args["integer"] == 42
        assert args["float"] == 3.14159
        assert args["boolean_true"] is True
        assert args["boolean_false"] is False
        assert args["null_value"] is None
        assert args["array"] == [1, "two", 3.0, True, None]
        assert args["object"] == {"nested": "value"}


class TestBraceCountingLogic:
    """Test the brace counting logic used in parsing."""
    
    def test_nested_braces_simple(self):
        """Test parsing with simple nested braces."""
        response = '''
        {
            "name": "nested_tool",
            "args": {
                "config": {
                    "level": 2
                }
            }
        }
        '''
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 1
        assert tool_calls[0].name == "nested_tool"
        assert tool_calls[0].arguments["config"]["level"] == 2
    
    def test_deeply_nested_braces(self):
        """Test parsing with deeply nested braces."""
        response = '''
        {
            "name": "deep_nested_tool",
            "args": {
                "level1": {
                    "level2": {
                        "level3": {
                            "level4": {
                                "deep_value": "found"
                            }
                        }
                    }
                }
            }
        }
        '''
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 1
        call = tool_calls[0]
        assert call.name == "deep_nested_tool"
        deep_value = call.arguments["level1"]["level2"]["level3"]["level4"]["deep_value"]
        assert deep_value == "found"
    
    def test_unbalanced_braces_in_string(self):
        """Test handling unbalanced braces within string values."""
        response = '''
        {
            "name": "brace_string_tool",
            "args": {
                "unbalanced": "This string has { unbalanced } braces",
                "code_snippet": "if (x > 0) { return x; }"
            }
        }
        '''
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 1
        call = tool_calls[0]
        assert "{ unbalanced }" in call.arguments["unbalanced"]
        assert "{ return x; }" in call.arguments["code_snippet"]
    
    def test_mixed_brackets_and_braces(self):
        """Test parsing with mixed brackets and braces."""
        response = '''
        {
            "name": "mixed_brackets_tool",
            "args": {
                "array_of_objects": [
                    {"item": 1},
                    {"item": 2},
                    {"item": 3}
                ],
                "object_with_arrays": {
                    "numbers": [1, 2, 3],
                    "strings": ["a", "b", "c"]
                }
            }
        }
        '''
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 1
        call = tool_calls[0]
        
        array_of_objects = call.arguments["array_of_objects"]
        assert len(array_of_objects) == 3
        assert array_of_objects[0]["item"] == 1
        
        object_with_arrays = call.arguments["object_with_arrays"]
        assert object_with_arrays["numbers"] == [1, 2, 3]
        assert object_with_arrays["strings"] == ["a", "b", "c"]


class TestErrorHandling:
    """Test error handling in various scenarios."""
    
    def test_extract_with_invalid_json_characters(self):
        """Test handling completely invalid JSON."""
        response = '''
        {name: invalid_json, args: {param: value}}
        '''
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        # Should handle gracefully and return empty list
        assert len(tool_calls) == 0
    
    def test_extract_with_only_braces(self):
        """Test handling response with only braces."""
        response = "{{{}}}}"
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 0
    
    def test_extract_with_mixed_valid_invalid(self):
        """Test handling mix of valid and invalid JSON."""
        response = '''
        {"name": "valid_tool", "args": {"param": "value"}}
        {invalid json here}
        {"name": "another_valid_tool", "args": {"param2": "value2"}}
        '''
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        # Should extract only the valid ones
        assert len(tool_calls) == 2
        assert tool_calls[0].name == "valid_tool"
        assert tool_calls[1].name == "another_valid_tool"
    
    def test_extract_with_extremely_long_response(self):
        """Test handling extremely long responses."""
        # Create a very long response with tool calls
        long_text = "This is a very long text. " * 1000
        response = f'''
        {long_text}
        {{"name": "buried_tool", "args": {{"param": "value"}}}}
        {long_text}
        '''
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 1
        assert tool_calls[0].name == "buried_tool"
    
    @patch('multiagenticswarm.core.tool_parser.logger')
    def test_logging_on_parse_failure(self, mock_logger):
        """Test that parsing failures are logged."""
        response = '''
        {"name": "good_tool", "args": {"param": "value"}}
        {this is invalid json}
        '''
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        # Should extract the good one
        assert len(tool_calls) == 1
        assert tool_calls[0].name == "good_tool"
        
        # Should have logged the parsing failure
        mock_logger.debug.assert_called()


class TestToolCallRequestIntegration:
    """Test integration with ToolCallRequest objects."""
    
    def test_tool_call_request_creation(self):
        """Test that extracted calls create proper ToolCallRequest objects."""
        response = '{"name": "integration_tool", "args": {"x": 10, "y": 20}}'
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 1
        call = tool_calls[0]
        
        # Should be a ToolCallRequest instance
        assert isinstance(call, ToolCallRequest)
        assert hasattr(call, 'id')
        assert hasattr(call, 'name')
        assert hasattr(call, 'arguments')
        
        # Properties should be correct
        assert call.name == "integration_tool"
        assert call.arguments == {"x": 10, "y": 20}
        assert call.id is not None
    
    def test_multiple_tool_calls_unique_ids(self):
        """Test that multiple tool calls get unique IDs."""
        response = '''
        {"name": "tool1", "args": {"param": "value1"}}
        {"name": "tool2", "args": {"param": "value2"}}
        {"name": "tool3", "args": {"param": "value3"}}
        '''
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 3
        
        # All IDs should be unique
        ids = [call.id for call in tool_calls]
        assert len(set(ids)) == 3  # All unique
        
        # All should be non-empty strings
        assert all(isinstance(id_val, str) and len(id_val) > 0 for id_val in ids)


class TestRealWorldScenarios:
    """Test real-world scenarios and common LLM response patterns."""
    
    def test_chatgpt_style_response(self):
        """Test parsing ChatGPT-style tool call responses."""
        response = '''
        I'll help you with that calculation. Let me use the calculator tool.
        
        {"name": "calculator", "args": {"operation": "add", "a": 15, "b": 27}}
        
        The result of adding 15 and 27 is 42.
        '''
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 1
        call = tool_calls[0]
        assert call.name == "calculator"
        assert call.arguments == {"operation": "add", "a": 15, "b": 27}
    
    def test_claude_style_response(self):
        """Test parsing Claude-style tool call responses."""
        response = '''
        I need to search for information and then process the results.
        
        {"name": "web_search", "arguments": {"query": "python asyncio tutorial", "max_results": 5}}
        
        Now let me analyze the search results:
        
        {"name": "text_analyzer", "arguments": {"text": "search results here", "analysis_type": "summarize"}}
        '''
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 2
        assert tool_calls[0].name == "web_search"
        assert tool_calls[0].arguments["query"] == "python asyncio tutorial"
        assert tool_calls[1].name == "text_analyzer"
        assert tool_calls[1].arguments["analysis_type"] == "summarize"
    
    def test_function_calling_format(self):
        """Test parsing function calling format responses."""
        response = '''
        {
            "name": "get_weather",
            "arguments": {
                "location": "San Francisco, CA",
                "unit": "celsius",
                "include_forecast": true
            }
        }
        '''
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 1
        call = tool_calls[0]
        assert call.name == "get_weather"
        assert call.arguments["location"] == "San Francisco, CA"
        assert call.arguments["unit"] == "celsius"
        assert call.arguments["include_forecast"] is True
    
    def test_complex_workflow_response(self):
        """Test parsing complex multi-step workflow responses."""
        response = '''
        I'll help you process this data through several steps:
        
        Step 1: Load the data
        {"name": "data_loader", "args": {"source": "database", "table": "users", "limit": 1000}}
        
        Step 2: Clean the data
        {"name": "data_cleaner", "args": {"remove_nulls": true, "standardize_format": true}}
        
        Step 3: Analyze the data
        {"name": "data_analyzer", "args": {"analysis_type": "statistical_summary", "generate_plots": true}}
        
        Step 4: Generate report
        {"name": "report_generator", "args": {"format": "pdf", "include_charts": true, "title": "User Data Analysis"}}
        
        This workflow will give you a comprehensive analysis of your user data.
        '''
        
        tool_calls = ToolCallParser.extract_tool_calls(response)
        
        assert len(tool_calls) == 4
        
        # Verify each step
        expected_tools = ["data_loader", "data_cleaner", "data_analyzer", "report_generator"]
        actual_tools = [call.name for call in tool_calls]
        assert actual_tools == expected_tools
        
        # Verify some specific arguments
        assert tool_calls[0].arguments["source"] == "database"
        assert tool_calls[1].arguments["remove_nulls"] is True
        assert tool_calls[2].arguments["analysis_type"] == "statistical_summary"
        assert tool_calls[3].arguments["format"] == "pdf"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
