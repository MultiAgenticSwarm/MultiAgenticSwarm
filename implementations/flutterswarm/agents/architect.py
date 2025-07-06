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
