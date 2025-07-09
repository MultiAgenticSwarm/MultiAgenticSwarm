"""
FlutterArchitectAgent - ALL architectural knowledge comes from LLM.
No hardcoded architectural patterns or decisions.
"""

import json
import logging
from typing import Any, Dict, List, Optional

# Import MAS as the core SDK
import multiagenticswarm as mas
from implementations.agentswarm.agents import AbstractArchitectAgent
from implementations.agentswarm.core.types import ExecutionResult, TaskContext

# Import directly from MAS utils for logging
from multiagenticswarm.utils.logger import get_logger

from ..tools import DartCLITool, FileSystemTool, FlutterCLITool


class FlutterArchitectAgent(AbstractArchitectAgent):
    """
    Flutter architect agent - ALL architectural knowledge comes from LLM.
    No hardcoded architectural patterns - all knowledge comes from LLM.
    """

    def __init__(
        self,
        name: str = "flutter_architect",
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
        self.logger.info(f"Initialized FlutterArchitectAgent: {name}")

    def _get_specialized_instructions(self) -> str:
        """Flutter architecture specific instructions"""
        return """You are an expert Flutter architect. You MUST return all responses in valid JSON format.

REQUIRED JSON FORMAT:
{
  "content": "Your main architecture analysis or design",
  "reasoning": "Brief explanation of architectural decisions",
  "tool_calls": [
    {
      "name": "file_system",
      "arguments": {
        "operation": "write",
        "path": "lib/core/architecture/base_repository.dart",
        "content": "complete architecture file content"
      }
    }
  ]
}

CRITICAL INSTRUCTIONS:
1. You MUST use the file_system tool to create ALL files
2. You MUST provide the complete file content in your tool calls
3. You MUST create all required directories using mkdir operations
4. You MUST implement pubspec.yaml with proper dependencies
5. Do NOT just describe files, actually CREATE them with file_system tool
6. NEVER return partial or truncated file content
7. ALWAYS include complete, syntactically correct Dart code
8. Use file_system tool for EVERY file and directory you create

FILE CREATION REQUIREMENTS:
- Use "operation": "mkdir" to create directories
- Use "operation": "write" to create files
- Always provide complete file content in the "content" field
- Never use placeholder comments like "// TODO" or "// Add more code"
- Include proper imports and complete implementations

FLUTTER ARCHITECTURE EXPERTISE:
- Clean Architecture and MVVM patterns
- State management (Provider, Riverpod, BLoC)
- Repository pattern and dependency injection
- Feature-based project organization
- Scalable modular architecture
- Multi-platform considerations
- Data layer and navigation architecture

EXAMPLE TOOL CALL:
{
  "name": "file_system",
  "arguments": {
    "operation": "write",
    "path": "lib/main.dart",
    "content": "import 'package:flutter/material.dart';\n\nvoid main() {\n  runApp(MyApp());\n}\n\nclass MyApp extends StatelessWidget {\n  @override\n  Widget build(BuildContext context) {\n    return MaterialApp(\n      title: 'Flutter Demo',\n      theme: ThemeData(\n        primarySwatch: Colors.blue,\n      ),\n      home: MyHomePage(title: 'Flutter Demo Home Page'),\n    );\n  }\n}"
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

    async def analyze_requirements(
        self,
        requirements: str,
        constraints: List[str],
        context: Optional[TaskContext] = None,
    ) -> ExecutionResult:
        """Analyze requirements and identify architectural needs"""
        task = f"""
        Analyze Flutter application requirements: {requirements}

        Constraints: {constraints}

        Provide:
        1. Requirements breakdown and categorization
        2. Architectural implications
        3. Technical challenges identification
        4. Scalability considerations
        5. Performance requirements
        6. Security considerations
        7. Platform-specific needs

        Consider Flutter-specific aspects:
        - Widget architecture needs
        - State management requirements
        - Platform adaptations
        - Performance considerations
        - Testing strategy implications
        """

        return await self.execute(task, context)

    async def design_architecture(
        self,
        requirements_analysis: Dict[str, Any],
        context: Optional[TaskContext] = None,
    ) -> ExecutionResult:
        """Design system architecture using LLM analysis"""
        task = f"""
        Design Flutter application architecture based on: {requirements_analysis}

        Create:
        1. Overall system architecture
        2. Application structure and organization
        3. Data flow design
        4. State management strategy
        5. Navigation architecture
        6. API integration approach
        7. Testing strategy
        8. Platform-specific considerations

        Focus on:
        - Flutter best practices
        - SOLID principles
        - Maintainability and scalability
        - Performance optimization
        - Code organization
        - Separation of concerns
        """

        return await self.execute(task, context)

    async def choose_technology_stack(
        self,
        requirements: Dict[str, Any],
        constraints: List[str],
        context: Optional[TaskContext] = None,
    ) -> ExecutionResult:
        """Choose appropriate technology stack"""
        task = f"""
        Choose Flutter technology stack for: {requirements}

        Constraints: {constraints}

        Recommend:
        1. State management solution (Provider, Riverpod, Bloc, etc.)
        2. Navigation approach (Navigator 2.0, go_router, etc.)
        3. HTTP client and API integration
        4. Local storage solutions
        5. Testing frameworks and tools
        6. CI/CD tools and processes
        7. Performance monitoring tools
        8. Platform-specific integrations

        Consider:
        - Project complexity and scale
        - Team expertise and preferences
        - Performance requirements
        - Maintenance and long-term support
        - Community support and ecosystem
        """

        return await self.execute(task, context)

    async def define_interfaces(
        self,
        architecture: Dict[str, Any],
        context: Optional[TaskContext] = None,
    ) -> ExecutionResult:
        """Define component interfaces and APIs"""
        task = f"""
        Define Flutter application interfaces for: {architecture}

        Create:
        1. Widget interfaces and contracts
        2. Service layer interfaces
        3. Repository interfaces
        4. API contracts and models
        5. State management interfaces
        6. Platform channel interfaces
        7. Navigation interfaces
        8. Testing interfaces

        Ensure:
        - Clear separation of concerns
        - Testability and mockability
        - Type safety with Dart
        - Consistent patterns
        - Documentation completeness
        - Error handling strategies
        """

        return await self.execute(task, context)

    async def create_technical_specification(
        self,
        architecture: Dict[str, Any],
        context: Optional[TaskContext] = None,
    ) -> ExecutionResult:
        """Create detailed technical specification"""
        task = f"""
        Create Flutter technical specification for: {architecture}

        Include:
        1. Architecture overview and diagrams
        2. Component specifications
        3. Data models and schemas
        4. API specifications
        5. State management flow
        6. Navigation structure
        7. Testing strategy
        8. Performance requirements
        9. Security considerations
        10. Deployment strategy

        Format as:
        - Clear documentation
        - Implementation guidelines
        - Code examples
        - Best practices
        - Review criteria
        """

        return await self.execute(task, context)

    async def review_architecture(
        self,
        architecture: Dict[str, Any],
        review_criteria: List[str],
        context: Optional[TaskContext] = None,
    ) -> ExecutionResult:
        """Review and validate architecture"""
        task = f"""
        Review Flutter architecture: {architecture}

        Review criteria: {review_criteria}

        Evaluate:
        1. Architecture consistency and coherence
        2. Performance implications
        3. Scalability potential
        4. Maintainability factors
        5. Security considerations
        6. Testing approach
        7. Platform compatibility
        8. Code organization

        Provide:
        - Strengths and weaknesses
        - Risk assessment
        - Improvement recommendations
        - Implementation guidance
        - Alternative approaches
        """

        return await self.execute(task, context)

    async def verify_flutter_environment(self, context: TaskContext) -> ExecutionResult:
        """Agent uses LLM knowledge to determine Flutter environment requirements and verify them."""
        self.logger.info("Verifying Flutter environment...")
        try:
            # LLM decides what checks are needed (simulate with prompt)
            verification_plan_response = await self.llm_provider.generate_response(
                "What steps are needed to verify a Flutter development environment is properly set up?"
            )
            verification_plan = (
                verification_plan_response.structured_content
                if hasattr(verification_plan_response, "structured_content")
                else self._safe_json_parse(verification_plan_response.content)
            )

            # Execute verification steps using tools
            flutter_version = await self.flutter_cli.execute("--version")
            doctor_status = await self.flutter_cli.execute("doctor")
            # Analyze results (LLM-driven)
            analysis_response = await self.llm_provider.generate_response(
                f"Analyze Flutter version: {flutter_version.get('output')} and doctor: {doctor_status.get('output')}. "
                "What issues exist and what should be fixed?"
            )
            analysis = (
                analysis_response.structured_content
                if hasattr(analysis_response, "structured_content")
                else self._safe_json_parse(analysis_response.content)
            )
            return ExecutionResult(
                success=True,
                result={
                    "flutter_version": flutter_version.get("output"),
                    "doctor_status": doctor_status.get("output"),
                    "analysis": analysis,
                },
            )
        except Exception as e:
            self.logger.error(f"Flutter environment verification failed: {e}")
            return ExecutionResult(success=False, error=str(e))

    async def create_project_foundation(
        self,
        project_name: str,
        requirements: Dict[str, Any],
        context: Optional[TaskContext] = None,
    ) -> ExecutionResult:
        """Create the foundational project structure and architecture setup"""
        task = f"""
        Create complete Flutter project foundation for: {project_name}

        Requirements: {requirements}

        MANDATORY ARCHITECT RESPONSIBILITIES:
        1. Create complete directory structure (lib/, test/, docs/, etc.)
        2. Create comprehensive pubspec.yaml with ALL necessary dependencies
        3. Create main.dart with proper app initialization
        4. Create app.dart for application-level configuration
        5. Set up navigation architecture (router.dart)
        6. Create base classes and abstract interfaces
        7. Set up dependency injection architecture
        8. Create constants and configuration files
        9. Set up theme and styling architecture
        10. Create error handling and logging setup
        11. Set up testing infrastructure
        12. Create documentation structure

        ARCHITECTURAL DEPENDENCIES TO INCLUDE:
        - State management (provider, riverpod, bloc, etc.)
        - Navigation (go_router, etc.)
        - HTTP client (dio, http, etc.)
        - Local storage (shared_preferences, hive, etc.)
        - Dependency injection (get_it, provider, etc.)
        - Development tools (flutter_test, mockito, etc.)
        - Code generation (json_annotation, build_runner, etc.)

        FOUNDATION FILES TO CREATE:
        - pubspec.yaml (comprehensive dependencies)
        - main.dart (app entry point)
        - lib/app.dart (application configuration)
        - lib/core/router.dart (navigation setup)
        - lib/core/dependency_injection.dart (DI container)
        - lib/core/constants.dart (app constants)
        - lib/core/theme.dart (theme configuration)
        - lib/core/error_handler.dart (error handling)
        - lib/core/logger.dart (logging setup)
        - Base classes for screens, widgets, services
        - Testing setup files

        CRITICAL REQUIREMENTS:
        - Use file_system tool to create ALL files and directories
        - Provide COMPLETE file content, not snippets
        - Ensure all files compile successfully
        - Create proper import structure
        - Follow Flutter/Dart conventions
        - Set up proper architectural patterns
        - Include comprehensive error handling
        - Create testable architecture
        """

        return await self.execute(task, context)

    async def create_base_classes(
        self,
        architecture_design: Dict[str, Any],
        context: Optional[TaskContext] = None,
    ) -> ExecutionResult:
        """Create base classes and abstract interfaces for the architecture"""
        task = f"""
        Create base classes and abstract interfaces for Flutter architecture: {architecture_design}

        MANDATORY BASE CLASSES TO CREATE:
        1. Base Screen/Page classes
        2. Base Widget classes
        3. Base Service interfaces
        4. Base Repository interfaces
        5. Base Model classes
        6. Base State Management classes
        7. Base API client interfaces
        8. Base Error classes
        9. Base Logger interfaces
        10. Base Configuration classes

        SPECIFIC BASE FILES TO CREATE:
        - lib/core/base/base_screen.dart (base screen class)
        - lib/core/base/base_widget.dart (base widget class)
        - lib/core/base/base_service.dart (base service interface)
        - lib/core/base/base_repository.dart (base repository interface)
        - lib/core/base/base_model.dart (base model class)
        - lib/core/base/base_state.dart (base state management)
        - lib/core/base/base_api_client.dart (base API client)
        - lib/core/base/base_error.dart (base error classes)
        - lib/core/base/base_logger.dart (base logger interface)
        - lib/core/base/base_config.dart (base configuration)

        ARCHITECTURAL PATTERNS TO IMPLEMENT:
        - Repository pattern interfaces
        - Service layer interfaces
        - Factory pattern for object creation
        - Observer pattern for state management
        - Strategy pattern for different implementations
        - Singleton pattern for shared resources
        - Dependency injection interfaces

        CRITICAL REQUIREMENTS:
        - Use file_system tool to create ALL files
        - Create lib/core/base/ directory structure
        - Provide COMPLETE file content with proper abstractions
        - Include comprehensive documentation
        - Follow SOLID principles
        - Create testable interfaces
        - Include proper error handling
        - Use Dart best practices (abstract classes, mixins, etc.)
        """

        return await self.execute(task, context)

    def _safe_json_parse(self, content: str) -> dict:
        """Safely parse JSON content using the enhanced parser."""
        try:
            # First try standard JSON parsing
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from the content
            try:
                import re

                json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))

                # Try to find JSON object in the text
                json_match = re.search(r"({.*})", content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))

                self.logger.warning(f"Could not extract JSON from content")
                return {"content": content, "tool_calls": []}
            except Exception as e:
                self.logger.warning(f"Failed to parse JSON content: {e}")
                return {"content": content, "tool_calls": []}

    # Helper methods
    def _extract_architecture_files_from_response(
        self, response: str
    ) -> List[Dict[str, str]]:
        """Extract architecture files from LLM response"""
        files = []

        lines = response.split("\n")
        current_file = None
        current_content = []

        for line in lines:
            if line.strip().startswith("ARCH_FILE:") or line.strip().startswith("doc/"):
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
