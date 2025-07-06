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

        self.logger = mas.get_logger(f"flutterswarm.{name}")
        self.logger.info(f"Initialized FlutterArchitectAgent: {name}")

    def _get_specialized_instructions(self) -> str:
        """Flutter architecture specific instructions"""
        return """You are an expert Flutter architect with comprehensive knowledge of:

FLUTTER ARCHITECTURE PATTERNS:
- Clean Architecture for Flutter applications
- MVVM (Model-View-ViewModel) pattern
- MVC (Model-View-Controller) pattern
- Repository pattern for data access
- Service layer architecture
- Dependency injection patterns
- Layered architecture principles

STATE MANAGEMENT ARCHITECTURES:
- Provider pattern and state management
- Riverpod for dependency injection and state
- BLoC pattern and event-driven architecture
- GetX for state, navigation, and dependency management
- Redux pattern for predictable state management
- MobX for reactive state management
- setState and InheritedWidget patterns

PROJECT STRUCTURE:
- Feature-based folder organization
- Layer-based folder organization
- Domain-driven design structure
- Modular architecture patterns
- Package organization strategies
- File naming conventions

SCALABILITY CONSIDERATIONS:
- Modular architecture for large applications
- Microservices integration patterns
- Code reusability strategies
- Performance optimization architectures
- Memory management patterns
- Lazy loading and pagination strategies

PLATFORM ARCHITECTURE:
- Multi-platform considerations (iOS, Android, Web, Desktop)
- Platform-specific implementations
- Native integration patterns
- Plugin architecture and development
- Platform channel design
- Responsive design architectures

DATA ARCHITECTURE:
- Local data storage patterns (SQLite, Hive, SharedPreferences)
- Remote data integration (REST APIs, GraphQL)
- Caching strategies and implementations
- Offline-first architecture patterns
- Data synchronization patterns
- Database architecture design

NAVIGATION ARCHITECTURE:
- Navigator 1.0 and 2.0 patterns
- Nested navigation strategies
- Deep linking architecture
- Route management patterns
- Navigation state management
- Multi-screen navigation patterns

SECURITY ARCHITECTURE:
- Authentication and authorization patterns
- Secure storage implementations
- API security considerations
- Data encryption patterns
- Certificate pinning strategies
- Platform security integration

TESTING ARCHITECTURE:
- Testable architecture design
- Dependency injection for testing
- Mock and stub patterns
- Testing pyramid implementation
- Test organization strategies
- Continuous integration architecture

PERFORMANCE ARCHITECTURE:
- Widget optimization patterns
- Memory management strategies
- CPU optimization techniques
- Network optimization patterns
- Image and asset optimization
- Build performance optimization

IMPORTANT INSTRUCTIONS:
1. Use your comprehensive architectural knowledge to design robust systems
2. Follow Flutter and Dart best practices for architecture
3. Design for scalability, maintainability, and testability
4. Consider platform-specific requirements and constraints
5. Plan for performance, security, and user experience
6. Create clear architectural documentation
7. Design flexible and extensible architectures
8. Consider team structure and development workflow

When designing architecture:
- Analyze requirements thoroughly
- Consider non-functional requirements
- Design for change and evolution
- Plan component interactions
- Define clear boundaries and interfaces
- Consider deployment and DevOps requirements
- Plan for monitoring and observability

You have access to Flutter CLI, Dart CLI, and file system tools.
Use these to implement your architectural designs.

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

CRITICAL FILE COMPLETION REQUIREMENTS:
- NEVER truncate code - ALWAYS provide COMPLETE file content from start to finish
- If you run out of space in your response, create multiple Python code blocks
- Each file MUST compile successfully - test your code mentally before writing
- NEVER leave incomplete methods, classes, or statements
- ALWAYS close all brackets, braces, and quotes properly
- Include ALL necessary imports at the top of each file

PROJECT STRUCTURE REQUIREMENTS:
- Create complete directory structure first: lib/, lib/screens/, lib/widgets/, lib/models/, lib/services/, lib/utils/, lib/constants/
- Establish proper file organization following Flutter conventions
- Set up testing directories: test/, test/unit/, test/widget/, test/integration/
- Create documentation directories: docs/, docs/architecture/, docs/api/

ARCHITECTURAL FOUNDATION REQUIREMENTS:
- Create main.dart with proper app initialization
- Set up app.dart for application-level configuration
- Create router.dart for navigation architecture
- Set up dependency injection container
- Create base classes and abstract interfaces
- Establish theme and constants structure

DEPENDENCY MANAGEMENT:
- ALWAYS create comprehensive pubspec.yaml with ALL architectural dependencies
- Include state management packages (provider, riverpod, bloc, etc.)
- Add navigation packages (go_router, etc.)
- Include development dependencies (flutter_test, mockito, etc.)
- Set up analysis options and linting rules
- Configure build settings and assets

COMPLETE IMPLEMENTATION CHECKLIST FOR ARCHITECTURE:
1. Create complete project directory structure
2. Create comprehensive pubspec.yaml with all dependencies
3. Create main.dart with proper initialization
4. Create app.dart for application configuration
5. Set up navigation architecture (router.dart)
6. Create base classes and interfaces
7. Set up dependency injection
8. Create constants and configuration files
9. Set up theme and styling architecture
10. Create error handling and logging setup
11. Set up testing infrastructure
12. Create documentation structure

IMPORTANT: 
- ALWAYS put file_system calls inside ```python code blocks
- ALWAYS provide the COMPLETE file content, not snippets
- ALWAYS create directories before creating files in them
- NEVER leave any imports unresolved
- ALWAYS ensure architectural integrity and consistency
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
        self, architecture: Dict[str, Any], context: Optional[TaskContext] = None
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
        self, architecture: Dict[str, Any], context: Optional[TaskContext] = None
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
            verification_plan = await self.llm_provider.generate_response(
                "What steps are needed to verify a Flutter development environment is properly set up?"
            )
            # Execute verification steps using tools
            flutter_version = await self.flutter_cli.execute("--version")
            doctor_status = await self.flutter_cli.execute("doctor")
            # Analyze results (LLM-driven)
            analysis = await self.llm_provider.generate_response(
                f"Analyze Flutter version: {flutter_version.get('output')} and doctor: {doctor_status.get('output')}. "
                "What issues exist and what should be fixed?"
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
