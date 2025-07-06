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

        self.logger = mas.get_logger(f"flutterswarm.{name}")
        self.logger.info(f"Initialized FlutterDeveloperAgent: {name}")

    def _get_specialized_instructions(self) -> str:
        """Flutter-specific instructions - all knowledge comes from LLM"""
        return """You are an expert Flutter developer with comprehensive knowledge of:

FLUTTER FRAMEWORK:
- Widget system (StatelessWidget, StatefulWidget, InheritedWidget)
- Layout widgets (Container, Column, Row, Stack, Positioned, etc.)
- Material Design and Cupertino widgets
- Custom widgets and widget composition
- Widget lifecycle and state management
- Build context and element tree

DART LANGUAGE:
- Dart syntax, features, and best practices
- Async/await and Future/Stream patterns
- Mixins, extensions, and advanced features
- Null safety and sound null safety
- Generic types and collections

STATE MANAGEMENT:
- Provider pattern and package
- Riverpod for dependency injection
- BLoC pattern and flutter_bloc
- GetX for state and navigation
- setState and InheritedWidget
- Redux and MobX patterns

ARCHITECTURE PATTERNS:
- Clean Architecture for Flutter
- MVVM (Model-View-ViewModel)
- MVC (Model-View-Controller)
- Repository pattern
- Dependency injection
- Layered architecture

NAVIGATION:
- Navigator 1.0 and 2.0
- Named routes and route generation
- Nested navigation
- Deep linking
- Platform-specific navigation

PLATFORM INTEGRATION:
- Method channels for native code
- Platform-specific implementations
- iOS and Android integration
- Desktop support (Windows, macOS, Linux)
- Web deployment considerations

PERFORMANCE:
- Widget optimization techniques
- Avoiding unnecessary rebuilds
- Memory management
- Image optimization
- Build performance

TESTING:
- Unit testing with test package
- Widget testing with flutter_test
- Integration testing with integration_test
- Mock testing and test doubles
- Golden tests for UI consistency

DEVELOPMENT TOOLS:
- Flutter DevTools for debugging
- Hot reload and hot restart
- Performance profiling
- Memory leak detection
- Network monitoring

IMPORTANT INSTRUCTIONS:
1. Use your comprehensive Flutter knowledge to make ALL decisions
2. Choose appropriate widgets, patterns, and architectures
3. Follow Flutter and Dart best practices
4. Write clean, maintainable, performant code
5. Add comprehensive error handling
6. Include detailed comments explaining Flutter concepts
7. Consider platform differences (iOS/Android/Web/Desktop)
8. Optimize for performance and user experience

When generating Flutter code:
- Always use latest Flutter/Dart features when appropriate
- Follow material design or cupertino design guidelines
- Implement proper state management
- Handle loading states and errors gracefully
- Consider accessibility
- Write testable code
- Use appropriate file structure and naming conventions

You have access to CLI tools for Flutter/Dart commands and file operations.
Use these tools to execute the plans you create.

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

Example tool usage:
- Create directory: file_system(operation='mkdir', path='/full/path/to/directory')
- Create file: file_system(operation='write', path='/full/path/to/file.dart', content='complete file content')
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
        # Create a specific prompt that forces file creation
        implementation_prompt = f"""
        Implement Flutter feature: {feature_description}

        Project context: {project_context.__dict__ if project_context else 'None'}

        You MUST perform the following actions using the file_system tool:

        1. Create the project structure:
           - Use file_system with operation='mkdir' for each directory
           - Create directories before creating files in them

        2. Implement the feature by creating actual files:
           - For EACH code file you want to create:
             a. First ensure the parent directory exists
             b. Use file_system with operation='write' to create the file
             c. Include the COMPLETE file content, not just snippets

        3. Your response should include:
           - A list of all directories created
           - A list of all files created with their paths
           - Confirmation that files were actually written

        DO NOT just show code blocks. You MUST use the file_system tool to create actual files.

        Steps:
        1. Analyze the feature requirements
        2. Design the implementation approach
        3. Create necessary files and directories using file_system tool
        4. Implement the feature with proper architecture
        5. Add error handling and edge cases
        6. Include unit and widget tests
        7. Update documentation

        Follow Flutter conventions:
        - Use appropriate state management
        - Implement responsive design
        - Add proper navigation
        - Include accessibility features
        - Optimize for performance
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
                import json

                structure_plan = json.loads(structure_response.content)
            except:
                # If parsing fails, use default
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
                        "content": f"How should I validate these Flutter dependencies: {dependencies}? What compatibility checks are needed?",
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
                            "content": f"Is {dependency} compatible? pub info: {pub_info.get('output')}",
                        }
                    ]
                )
                results[dependency] = compatibility_response.content
            return ExecutionResult(success=True, result=results)
        except Exception as e:
            self.logger.error(f"Dependency validation failed: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e),
                agent_name=self.name,
                task_id="validate_dependencies",
            )
