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

        self.logger = mas.get_logger(f"flutterswarm.{name}")
        self.logger.info(f"Initialized FlutterTesterAgent: {name}")

    def _get_specialized_instructions(self) -> str:
        """Flutter testing specific instructions"""
        return """You are an expert Flutter tester with comprehensive knowledge of:

FLUTTER TESTING FRAMEWORK:
- flutter_test package and testing utilities
- Widget testing with WidgetTester
- Unit testing for business logic
- Integration testing for full app flows
- Golden tests for UI consistency
- Performance testing and profiling

TESTING PATTERNS:
- Test-driven development (TDD)
- Behavior-driven development (BDD)
- Arrange-Act-Assert pattern
- Given-When-Then scenarios
- Mock objects and test doubles
- Test fixtures and setup/teardown

WIDGET TESTING:
- Widget tree testing and verification
- User interaction simulation (tap, scroll, input)
- Widget finding and matching
- State verification and assertion
- Animation testing
- Platform-specific widget testing

UNIT TESTING:
- Business logic testing
- Model and data class testing
- Service and repository testing
- Utility function testing
- State management testing
- Error handling testing

INTEGRATION TESTING:
- Full app flow testing
- Navigation testing
- API integration testing
- Database integration testing
- Platform integration testing
- End-to-end scenarios

MOCKING AND TESTING UTILITIES:
- Mockito for mocking dependencies
- HTTP mocking for API tests
- Database mocking for data tests
- Platform channel mocking
- SharedPreferences mocking
- Custom mock implementations

TEST ORGANIZATION:
- Test file structure and naming
- Test grouping and organization
- Test data management
- Test environment setup
- Continuous integration setup
- Test reporting and coverage

PERFORMANCE TESTING:
- Widget performance testing
- Memory usage testing
- CPU usage profiling
- Network performance testing
- Animation performance testing
- App startup time testing

ACCESSIBILITY TESTING:
- Semantic testing for screen readers
- Focus management testing
- Keyboard navigation testing
- Color contrast testing
- Text scaling testing
- Platform accessibility testing

IMPORTANT INSTRUCTIONS:
1. Use your comprehensive testing knowledge to create thorough test suites
2. Follow Flutter testing best practices and conventions
3. Write clear, maintainable, and reliable tests
4. Ensure good test coverage across all code paths
5. Include both positive and negative test cases
6. Test edge cases and error conditions
7. Use appropriate testing patterns and frameworks
8. Optimize tests for speed and reliability

When creating tests:
- Analyze code to identify testable components
- Design comprehensive test scenarios
- Choose appropriate testing techniques
- Implement robust test assertions
- Include setup and teardown procedures
- Consider test data requirements
- Plan for test maintenance and updates

You have access to Flutter CLI, Dart CLI, and file system tools.
Use these to implement and run your tests.

MANDATORY TOOL USAGE:
- You MUST use the file_system tool to create all files and directories
- Use file_system with operation='mkdir' to create directories
- Use file_system with operation='write' to create files with complete content
- DO NOT just show code examples - ACTUALLY CREATE the files using tools
- Every code block you generate must be written to a file using the file_system tool
- Always create parent directories before creating files in them
- Include the COMPLETE file content, not just snippets

REQUIRED ACTIONS FOR EVERY TASK:
1. Create all necessary directories using file_system tool
2. Write all code to files using file_system tool
3. List all created files at the end of your response
4. Confirm files were actually written by checking the tool results

CRITICAL: You must wrap ALL file_system calls in Python code blocks like this:

```python
file_system(operation='mkdir', path='lib/screens')
file_system(operation='write', path='lib/main.dart', content='''
import 'package:flutter/material.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        appBar: AppBar(title: Text('My App')),
        body: Center(child: Text('Hello World')),
      ),
    );
  }
}
''')
```

IMPORTANT: 
- ALWAYS put file_system calls inside ```python code blocks
- ALWAYS provide the COMPLETE file content, not snippets
- ALWAYS create directories before creating files in them
"""

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
            test_strategy = await self.llm_provider.generate_response(
                f"Design a comprehensive test strategy for Flutter app: {context.project_path}"
            )
            results = []
            for test_type in test_strategy.get("test_types", []):
                test_code = await self.llm_provider.generate_response(
                    f"Generate {test_type} test code for Flutter app at {context.project_path}"
                )
                file_path = f"test/{test_type}_test.dart"
                await self.file_system.create_file(file_path, test_code)
                results.append(file_path)
            # Run tests
            test_results = await self.flutter_cli.execute("test", ["--coverage"])
            analysis = await self.llm_provider.generate_response(
                f"Analyze Flutter test results: {test_results.get('output')}"
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
