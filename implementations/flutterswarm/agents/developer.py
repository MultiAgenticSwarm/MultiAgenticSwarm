"""
FlutterDeveloperAgent - ALL Flutter knowledge comes from LLM.
No hardcoded Flutter patterns, widgets, or logic.
"""

import json
import logging
from typing import Any, Dict, List, Optional

# Import MAS as the core SDK
import multiagenticswarm as mas

# Import from implementations
from implementations.agentswarm.agents import AbstractDeveloperAgent
from implementations.agentswarm.core.types import (
    AgentRole,
    ExecutionResult,
    TaskContext,
)

# Import directly from MAS utils for logging
from multiagenticswarm.utils.logger import get_logger

# Import tools
from ..tools import DartCLITool, FileSystemTool, FlutterCLITool


class FlutterDeveloperAgent(AbstractDeveloperAgent):
    """
    Flutter developer agent - ALL Flutter knowledge comes from LLM.
    No hardcoded Flutter patterns, widgets, or logic.

    This agent uses LLM for ALL Flutter development decisions:
    - Widget selection and composition
    - State management architecture
    - Navigation patterns
    - Platform-specific implementations
    - Performance optimizations
    """

    def __init__(
        self,
        name: str = "flutter_developer",
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
        self.logger.info(f"Initialized FlutterDeveloperAgent: {name}")

    def _get_specialized_instructions(self) -> str:
        """Flutter-specific instructions - all knowledge comes from LLM"""
        return """You are an expert Flutter developer. Respond ONLY in valid JSON format.

REQUIRED JSON STRUCTURE:
{
  "content": "Your main response content",
  "reasoning": "Your reasoning (optional)",
  "tool_calls": [
    {
      "name": "file_system",
      "arguments": {
        "operation": "write",
        "path": "lib/screens/home_screen.dart",
        "content": "complete file content with no truncation"
      }
    }
  ]
}

CRITICAL FILE CREATION REQUIREMENTS:
1. You MUST use the file_system tool to create ALL files
2. You MUST provide COMPLETE file content - no truncation allowed
3. You MUST create complete, syntactically correct Dart code
4. You MUST include all necessary imports
5. You MUST implement complete widget classes with all required methods
6. NEVER use placeholder comments like "// TODO" or "// Add more code"
7. Every file must be complete and ready to run

FILE SYSTEM TOOL USAGE:
- Use "operation": "mkdir" to create directories
- Use "operation": "write" to create files with complete content
- Always provide the full path from project root
- Include complete file content in the "content" field

FLUTTER EXPERTISE:
- Widget system and state management
- UI/UX implementation
- Navigation and routing
- Data handling and persistence
- Platform-specific code
- Performance optimization
- Testing and debugging

EXAMPLE COMPLETE FILE:
{
  "name": "file_system",
  "arguments": {
    "operation": "write",
    "path": "lib/screens/home_screen.dart",
    "content": "import 'package:flutter/material.dart';\\n\\nclass HomeScreen extends StatefulWidget {\\n  @override\\n  _HomeScreenState createState() => _HomeScreenState();\\n}\\n\\nclass _HomeScreenState extends State<HomeScreen> {\\n  @override\\n  Widget build(BuildContext context) {\\n    return Scaffold(\\n      appBar: AppBar(\\n        title: Text('Home'),\\n      ),\\n      body: Center(\\n        child: Text('Hello World'),\\n      ),\\n    );\\n  }\\n}"
  }
}

MANDATORY: Every response must include tool_calls array with file_system operations to create actual files."""

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

    async def generate_code(
        self, requirements: str, context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Generate code based on requirements"""
        task = f"""
        Generate Flutter code for these requirements:
        {requirements}

        Use your expert Flutter knowledge to:
        1. Choose appropriate widgets and architecture
        2. Follow Flutter best practices
        3. Implement proper state management
        4. Create clean, maintainable code
        5. Include proper error handling
        6. Add comprehensive documentation

        Consider:
        - Material Design principles
        - Performance optimization
        - Platform-specific adaptations
        - Accessibility features
        - Testing requirements
        """

        return await self.execute(task, context)

    async def implement_feature(
        self, feature_description: str, project_context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Implement a complete feature using LLM reasoning"""
        # Simplified prompt focused on the agent's expertise
        implementation_prompt = f"""
        Based on the provided context and requirements, implement the following Flutter feature:

        Feature: {feature_description}

        Project context: {project_context.__dict__ if project_context else 'None'}

        Please use your Flutter expertise to create a complete implementation including:
        1. All necessary files and directories
        2. Complete, compilable Dart code
        3. Proper state management
        4. Responsive UI design
        5. Required dependencies in pubspec.yaml

        Use the file_system tool to create all files with complete content.
        """

        return await self.execute(implementation_prompt, project_context)

    async def refactor_code(
        self,
        code_path: str,
        refactoring_goals: List[str],
        context: Optional[TaskContext] = None,
    ) -> ExecutionResult:
        """Refactor code using LLM analysis and decisions"""
        task = f"""
        Refactor Flutter code at: {code_path}

        Refactoring goals: {refactoring_goals}

        Approach:
        1. Analyze current code structure
        2. Identify improvement opportunities
        3. Apply Flutter best practices
        4. Improve performance and maintainability
        5. Update tests accordingly
        6. Document changes

        Focus on:
        - Code organization and structure
        - Performance optimizations
        - Maintainability improvements
        - Design pattern applications
        - Testing coverage
        """

        return await self.execute(task, context)

    async def debug_issue(
        self,
        issue_description: str,
        error_logs: Optional[List[str]] = None,
        context: Optional[TaskContext] = None,
    ) -> ExecutionResult:
        """Debug and fix issues using LLM analysis"""
        task = f"""
        Debug Flutter issue: {issue_description}

        Error logs: {error_logs or 'None provided'}

        Debug process:
        1. Analyze the issue description and logs
        2. Identify potential root causes
        3. Investigate code paths
        4. Propose solutions
        5. Implement fixes
        6. Test the fixes
        7. Prevent similar issues

        Consider:
        - Flutter-specific debugging techniques
        - Platform-specific issues
        - Performance implications
        - State management problems
        - Widget lifecycle issues
        """

        return await self.execute(task, context)

    async def optimize_performance(
        self, performance_targets: Dict[str, Any], context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Optimize code performance using LLM analysis"""
        task = f"""
        Optimize Flutter performance for targets: {performance_targets}

        Optimization areas:
        1. Widget build optimization
        2. State management efficiency
        3. Memory usage reduction
        4. Animation performance
        5. Network request optimization
        6. Asset loading optimization

        Analysis:
        1. Profile current performance
        2. Identify bottlenecks
        3. Apply Flutter performance best practices
        4. Implement optimizations
        5. Measure improvements
        6. Document changes

        Focus on:
        - Build method optimization
        - Unnecessary rebuilds prevention
        - Memory leak detection
        - Efficient state management
        - Image and asset optimization
        """

        return await self.execute(task, context)

    async def setup_project_structure(self, context: TaskContext) -> ExecutionResult:
        """Agent determines optimal Flutter project structure and sets it up, including running 'flutter create'."""
        self.logger.info("Setting up project structure...")
        try:
            # Check if we're already in a Flutter project
            import os

            pubspec_path = os.path.join(context.project_path, "pubspec.yaml")
            if os.path.exists(pubspec_path):
                self.logger.info(
                    "Flutter project already exists, skipping flutter create"
                )
                create_result = {"success": True, "message": "Project already exists"}
            else:
                # Validate project name
                project_name = (
                    getattr(context, "project_name", None)
                    or getattr(context, "app_name", None)
                    or "my_flutter_app"
                )
                platforms = getattr(context, "platforms", None) or ["ios", "android"]
                # Call flutter_cli.create_project to bootstrap the project
                create_result = await self.flutter_cli.create_project(
                    project_name=project_name, platforms=platforms
                )
                if not create_result.get("success", False):
                    self.logger.error(
                        f"flutter create failed: {create_result.get('error')}"
                    )
                    return ExecutionResult(
                        success=False,
                        error_message=create_result.get("error"),
                        agent_name=self.name,
                        task_id="setup_project_structure",
                    )
            # LLM decides what directories are needed (optional, after flutter create)
            structure_response = await self.llm_provider.execute(
                [
                    {
                        "role": "user",
                        "content": f"What additional directory structure is needed for a Flutter project with requirements: {getattr(context, 'requirements', '')}? Respond with a JSON object containing a 'directories' array.",
                    }
                ]
            )
            # Parse the response to get directory structure
            structure_plan = {"directories": []}  # Default fallback
            try:
                # Use structured JSON response if available
                if hasattr(structure_response, "structured_content"):
                    structure_plan = structure_response.structured_content
                    # Ensure it has the expected structure
                    if "directories" not in structure_plan:
                        structure_plan["directories"] = []
                elif (
                    hasattr(structure_response, "json_response")
                    and structure_response.json_response
                ):
                    structure_plan = structure_response.json_response
                    if "directories" not in structure_plan:
                        structure_plan["directories"] = []
                else:
                    # Fallback to parsing content directly with error handling
                    import json

                    try:
                        structure_plan = json.loads(structure_response.content)
                    except json.JSONDecodeError as e:
                        # Use the parse_json_response function for better error handling
                        from ...llm.providers import parse_json_response

                        structure_plan = parse_json_response(structure_response.content)
            except Exception as e:
                # If parsing fails, use default
                self.logger.warning(f"Failed to parse structure plan: {e}")
                structure_plan = {"directories": []}

            for directory in structure_plan.get("directories", []):
                await self.file_system.create_directory(directory)
            return ExecutionResult(
                success=True,
                agent_name=self.name,
                task_id="setup_project_structure",
                output={
                    "structure_plan": structure_plan,
                    "flutter_create": create_result,
                },
            )
        except Exception as e:
            self.logger.error(f"Project structure setup failed: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e),
                agent_name=self.name,
                task_id="setup_project_structure",
            )

    async def validate_dependencies(
        self, dependencies: List[str], context: TaskContext
    ) -> ExecutionResult:
        """Agent validates Flutter dependencies using LLM knowledge and Dart CLI."""
        self.logger.info(f"Validating dependencies: {dependencies}")
        try:
            validation_response = await self.llm_provider.execute(
                [
                    {
                        "role": "user",
                        "content": f"How should I validate these Flutter dependencies: {dependencies}? What compatibility checks are needed? Respond with JSON containing your analysis and recommendations.",
                    }
                ]
            )
            results = {}
            for dependency in dependencies:
                pub_info = await self.dart_cli.execute("pub", ["deps", dependency])
                compatibility_response = await self.llm_provider.execute(
                    [
                        {
                            "role": "user",
                            "content": f"Is {dependency} compatible? pub info: {pub_info.get('output')}. Respond with JSON containing compatibility assessment.",
                        }
                    ]
                )
                # Use structured JSON response if available
                if hasattr(compatibility_response, "structured_content"):
                    results[dependency] = compatibility_response.structured_content
                elif (
                    hasattr(compatibility_response, "json_response")
                    and compatibility_response.json_response
                ):
                    results[dependency] = compatibility_response.json_response
                else:
                    # Use structured content or parse JSON
                    results[dependency] = (
                        compatibility_response.structured_content
                        if hasattr(compatibility_response, "structured_content")
                        else self._safe_json_parse(compatibility_response.content)
                    )
            return ExecutionResult(success=True, result=results)
        except Exception as e:
            self.logger.error(f"Dependency validation failed: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e),
                agent_name=self.name,
                task_id="validate_dependencies",
            )

    def _safe_json_parse(self, content: str) -> dict:
        """Safely parse JSON content using the enhanced parser."""
        try:
            from multiagenticswarm.llm.providers import parse_json_response

            return parse_json_response(content)
        except Exception as e:
            self.logger.warning(f"Failed to parse JSON content: {e}")
            # Return a proper error structure instead of fallback
            raise ValueError(f"Invalid JSON response: {str(e)}")
