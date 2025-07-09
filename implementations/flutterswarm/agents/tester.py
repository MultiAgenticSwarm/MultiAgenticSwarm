"""
FlutterTesterAgent - ALL testing knowledge comes from LLM.
No hardcoded testing patterns or frameworks.
"""

import json
import logging
from typing import Any, Dict, List, Optional

# Import MAS as the core SDK
import multiagenticswarm as mas
from implementations.agentswarm.agents import AbstractTesterAgent
from implementations.agentswarm.core.types import ExecutionResult, TaskContext

# Import directly from MAS utils for logging
from multiagenticswarm.utils.logger import get_logger

from ..tools import DartCLITool, FileSystemTool, FlutterCLITool


class FlutterTesterAgent(AbstractTesterAgent):
    """
    Flutter tester agent - ALL testing knowledge comes from LLM.
    No hardcoded testing patterns - all knowledge comes from LLM.
    """

    def __init__(
        self,
        name: str = "flutter_tester",
        working_directory: str = ".",
        flutter_cli=None,
        dart_cli=None,
        file_system=None,
        **kwargs,
    ):
        self.working_directory = working_directory

        # Use shared tool instances if provided
        self.flutter_cli = (
            flutter_cli
            if flutter_cli is not None
            else FlutterCLITool(working_directory)
        )
        self.dart_cli = (
            dart_cli if dart_cli is not None else DartCLITool(working_directory)
        )
        self.file_system = (
            file_system
            if file_system is not None
            else FileSystemTool(working_directory)
        )

        # Initialize with proper MAS integration
        super().__init__(
            name=name,
            system=kwargs.get("system"),
            llm_provider=kwargs.get("llm_provider", "openai"),
            llm_model=kwargs.get("llm_model", "gpt-4"),
            **{
                k: v
                for k, v in kwargs.items()
                if k not in ["system", "llm_provider", "llm_model"]
            },
        )

        self.logger = get_logger(f"flutterswarm.{name}")
        self.logger.info(f"Initialized FlutterTesterAgent: {name}")

    def _get_specialized_instructions(self) -> str:
        """Flutter testing specific instructions"""
        return """You are an expert Flutter tester. You MUST return all responses in valid JSON format.

REQUIRED JSON FORMAT:
{
  "content": "Your main testing work or analysis",
  "reasoning": "Brief explanation of testing approach",
  "tool_calls": [
    {
      "name": "file_system",
      "arguments": {
        "operation": "write",
        "path": "test/widget/my_widget_test.dart",
        "content": "complete test file content"
      }
    }
  ]
}

CRITICAL TEST FILE CREATION REQUIREMENTS:
1. You MUST use the file_system tool to create ALL test files
2. You MUST provide COMPLETE test implementations - no truncation
3. You MUST create complete, syntactically correct Dart test code
4. You MUST include all necessary imports
5. You MUST implement complete test functions with all required assertions
6. NEVER use placeholder comments like "// TODO" or "// Add more tests"
7. Every test file must be complete and ready to run

FILE SYSTEM TOOL USAGE:
- Use "operation": "mkdir" to create test directories
- Use "operation": "write" to create files with complete content
- Always provide the full path from project root
- Include complete test implementation in the "content" field

FLUTTER TESTING EXPERTISE:
- flutter_test package and WidgetTester for widget testing
- Unit testing for business logic and models
- Integration testing for full app flows
- Mockito for mocking dependencies
- Test organization and structure
- Performance and accessibility testing

EXAMPLE COMPLETE TEST FILE:
{
  "name": "file_system",
  "arguments": {
    "operation": "write",
    "path": "test/widget/home_screen_test.dart",
    "content": "import 'package:flutter/material.dart';\\nimport 'package:flutter_test/flutter_test.dart';\\nimport 'package:myapp/screens/home_screen.dart';\\n\\nvoid main() {\\n  group('HomeScreen Tests', () {\\n    testWidgets('should display app title', (WidgetTester tester) async {\\n      await tester.pumpWidget(\\n        MaterialApp(\\n          home: HomeScreen(),\\n        ),\\n      );\\n\\n      expect(find.text('Home'), findsOneWidget);\\n      expect(find.byType(AppBar), findsOneWidget);\\n    });\\n\\n    testWidgets('should navigate when button pressed', (WidgetTester tester) async {\\n      await tester.pumpWidget(\\n        MaterialApp(\\n          home: HomeScreen(),\\n        ),\\n      );\\n\\n      await tester.tap(find.byType(ElevatedButton));\\n      await tester.pumpAndSettle();\\n\\n      expect(find.text('Hello World'), findsOneWidget);\\n    });\\n  });\\n}"
  }
}

MANDATORY: Every response must include tool_calls array with file_system operations to create actual test files."""

    def _get_tools(self) -> List[Dict[str, Any]]:
        """Get tools for this agent - properly formatted for function calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "flutter_cli",
                    "description": "Execute Flutter CLI commands",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The Flutter command to execute",
                            },
                            "args": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Command arguments",
                            },
                        },
                        "required": ["command"],
                    },
                },
                "func": self.flutter_cli.execute,
                "scope": "local",
            },
            {
                "type": "function",
                "function": {
                    "name": "dart_cli",
                    "description": "Execute Dart CLI commands",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The Dart command to execute",
                            },
                            "args": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Command arguments",
                            },
                        },
                        "required": ["command"],
                    },
                },
                "func": self.dart_cli.execute,
                "scope": "local",
            },
            {
                "type": "function",
                "function": {
                    "name": "file_system",
                    "description": "Create, read, write, and manage files and directories. MUST be used to create all files and directories.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "operation": {
                                "type": "string",
                                "enum": [
                                    "read",
                                    "write",
                                    "list",
                                    "mkdir",
                                    "exists",
                                    "delete",
                                    "copy",
                                    "move",
                                ],
                                "description": "The file system operation to perform",
                            },
                            "path": {
                                "type": "string",
                                "description": "The path to the file or directory",
                            },
                            "content": {
                                "type": "string",
                                "description": "The content to write to the file (for write operations)",
                            },
                            "encoding": {
                                "type": "string",
                                "description": "File encoding (default: utf-8)",
                            },
                            "create_dirs": {
                                "type": "boolean",
                                "description": "Whether to create parent directories (default: true)",
                            },
                        },
                        "required": ["operation", "path"],
                    },
                },
                "func": self.file_system.execute,
                "scope": "local",
            },
        ]

    async def create_test_plan(
        self, requirements: str, context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Create a comprehensive test plan using LLM analysis"""
        task = f"""
        Create a comprehensive test plan for Flutter application with these requirements:
        {requirements}

        Include:
        1. Unit tests for business logic
        2. Widget tests for UI components
        3. Integration tests for full flows
        4. Performance tests
        5. Accessibility tests
        6. Platform-specific tests

        For each test category, specify:
        - Test scenarios
        - Test data needed
        - Expected outcomes
        - Test priority
        - Implementation approach
        """

        return await self.execute(task, context)

    async def write_tests(
        self, context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Write tests for the given code using LLM decisions"""
        # Extract test parameters from context
        code_path = getattr(context, "project_path", "./lib")
        test_types = getattr(context, "metadata", {}).get(
            "test_types", ["unit", "widget", "integration"]
        )

        task = f"""
        Write comprehensive Flutter tests for the code at: {code_path}

        Test types to implement: {test_types}

        For each test type:
        1. Analyze the code structure
        2. Identify test scenarios
        3. Create test files with proper organization
        4. Write clear, maintainable test code
        5. Include edge cases and error scenarios
        6. Use appropriate Flutter testing patterns

        Follow Flutter testing best practices:
        - Use flutter_test package
        - Implement proper test fixtures
        - Use meaningful test descriptions
        - Include setup and teardown when needed
        - Mock external dependencies
        """

        return await self.execute(task, context)

    async def run_tests(
        self, test_suite: str, context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Run tests and analyze results using LLM"""
        task = f"""
        Run Flutter tests for: {test_suite}

        1. Execute the test suite using flutter test
        2. Analyze test results
        3. Identify failures and their causes
        4. Provide debugging suggestions
        5. Generate test coverage report
        6. Recommend improvements

        Return:
        - Test execution summary
        - Detailed failure analysis
        - Coverage metrics
        - Performance insights
        - Next steps for fixes
        """

        return await self.execute(task, context)

    async def analyze_test_results(
        self, test_results: Dict[str, Any], context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Analyze test results and provide insights"""
        task = f"""
        Analyze Flutter test results: {test_results}

        Provide:
        1. Overall test health assessment
        2. Failure pattern analysis
        3. Performance bottleneck identification
        4. Coverage gap analysis
        5. Flaky test detection
        6. Recommendations for improvement

        Focus on:
        - Test stability and reliability
        - Performance implications
        - Code coverage gaps
        - Test maintenance needs
        - CI/CD pipeline impact
        """

        return await self.execute(task, context)

    async def generate_test_data(
        self, data_requirements: Dict[str, Any], context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Generate test data using LLM"""
        task = f"""
        Generate test data for Flutter application: {data_requirements}

        Create:
        1. Realistic test fixtures
        2. Mock API responses
        3. Sample user inputs
        4. Edge case data
        5. Performance test data
        6. Error condition data

        Ensure data is:
        - Comprehensive and realistic
        - Covers all test scenarios
        - Maintains data consistency
        - Includes edge cases
        - Properly structured for Flutter tests
        """

        return await self.execute(task, context)

    async def create_integration_tests(self, context: TaskContext) -> ExecutionResult:
        """Agent creates comprehensive Flutter integration tests using LLM and tools."""
        self.logger.info("Creating integration tests...")
        try:
            # LLM decides test strategy
            test_strategy_response = await self.llm_provider.generate_response(
                f"Design a comprehensive test strategy for Flutter app: {context.project_path}"
            )
            test_strategy = (
                test_strategy_response.structured_content
                if hasattr(test_strategy_response, "structured_content")
                else self._safe_json_parse(test_strategy_response.content)
            )

            results = []
            for test_type in test_strategy.get("test_types", []):
                test_code_response = await self.llm_provider.generate_response(
                    f"Generate {test_type} test code for Flutter app at {context.project_path}"
                )
                test_code = (
                    test_code_response.structured_content
                    if hasattr(test_code_response, "structured_content")
                    else self._safe_json_parse(test_code_response.content)
                )
                file_path = f"test/{test_type}_test.dart"
                await self.file_system.create_file(file_path, test_code)
                results.append(file_path)
            # Run tests
            test_results = await self.flutter_cli.execute("test", ["--coverage"])
            analysis_response = await self.llm_provider.generate_response(
                f"Analyze Flutter test results: {test_results.get('output')}"
            )
            analysis = (
                analysis_response.structured_content
                if hasattr(analysis_response, "structured_content")
                else self._safe_json_parse(analysis_response.content)
            )
            return ExecutionResult(
                success=True,
                result={
                    "test_files": results,
                    "test_results": test_results.get("output"),
                    "analysis": analysis,
                },
            )
        except Exception as e:
            self.logger.error(f"Integration test creation failed: {e}")
            return ExecutionResult(success=False, error=str(e))

    # Helper methods
    def _extract_test_files_from_response(self, response: str) -> List[Dict[str, str]]:
        """Extract test files from LLM response"""
        files = []

        lines = response.split("\n")
        current_file = None
        current_content = []

        for line in lines:
            if line.strip().startswith("TEST_FILE:") or line.strip().startswith(
                "test/"
            ):
                if current_file:
                    files.append(
                        {"path": current_file, "content": "\n".join(current_content)}
                    )

                current_file = (
                    line.split(":", 1)[1].strip() if ":" in line else line.strip()
                )
                current_content = []
            elif current_file and line.strip():
                current_content.append(line)

        if current_file:
            files.append({"path": current_file, "content": "\n".join(current_content)})

        return files

    def _safe_json_parse(self, content: str) -> dict:
        """Safely parse JSON content using the enhanced parser."""
        try:
            from ...llm.providers import parse_json_response

            return parse_json_response(content)
        except Exception as e:
            self.logger.warning(f"Failed to parse JSON content: {e}")
            # Return a proper error structure instead of fallback
            raise ValueError(f"Invalid JSON response: {str(e)}")
