"""
FlutterArchitectAgent - ALL architectural knowledge comes from LLM.
No hardcoded architectural patterns or decisions.
"""

from typing import Dict, Any, List, Optional
import logging

from implementations.agentswarm.agents import AbstractArchitectAgent
from implementations.agentswarm.core.types import TaskContext, ExecutionResult
from ..tools import FlutterCLITool, DartCLITool, FileSystemTool

# Import MAS as the core SDK
import multiagenticswarm as mas

class FlutterArchitectAgent(AbstractArchitectAgent):
    """
    Flutter architect agent - ALL architectural knowledge comes from LLM.
    No hardcoded architectural patterns - all knowledge comes from LLM.
    """

    def __init__(self, name: str = "flutter_architect", working_directory: str = ".", **kwargs):
        self.working_directory = working_directory

        # Initialize tools first
        self.flutter_cli = FlutterCLITool(working_directory)
        self.dart_cli = DartCLITool(working_directory)
        self.file_system = FileSystemTool(working_directory)

        # Initialize with proper MAS integration
        super().__init__(
            name=name,
            system=kwargs.get('system'),
            llm_provider=kwargs.get('llm_provider', 'openai'),
            llm_model=kwargs.get('llm_model', 'gpt-4'),
            **{k: v for k, v in kwargs.items() if k not in ['system', 'llm_provider', 'llm_model']}
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
"""

    def _get_tools(self) -> List[Dict[str, Any]]:
        """Get tools for this agent"""
        return [
            {
                "name": "flutter_cli",
                "func": self.flutter_cli.execute,
                "description": "Execute Flutter CLI commands",
                "scope": "local"
            },
            {
                "name": "dart_cli",
                "func": self.dart_cli.execute,
                "description": "Execute Dart CLI commands",
                "scope": "local"
            },
            {
                "name": "file_system",
                "func": self.file_system.execute,
                "description": "Execute file system operations (read, write, list, mkdir, etc.)",
                "scope": "local"
            }
        ]

    async def analyze_requirements(
        self,
        requirements: str,
        constraints: List[str],
        context: Optional[TaskContext] = None
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
        context: Optional[TaskContext] = None
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
        context: Optional[TaskContext] = None
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
        context: Optional[TaskContext] = None
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
        context: Optional[TaskContext] = None
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
        context: Optional[TaskContext] = None
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

    # Helper methods
    def _extract_architecture_files_from_response(self, response: str) -> List[Dict[str, str]]:
        """Extract architecture files from LLM response"""
        files = []

        lines = response.split('\n')
        current_file = None
        current_content = []

        for line in lines:
            if line.strip().startswith('ARCH_FILE:') or line.strip().startswith('doc/'):
                if current_file:
                    files.append({
                        'path': current_file,
                        'content': '\n'.join(current_content)
                    })

                current_file = line.split(':', 1)[1].strip() if ':' in line else line.strip()
                current_content = []
            elif current_file and line.strip():
                current_content.append(line)

        if current_file:
            files.append({
                'path': current_file,
                'content': '\n'.join(current_content)
            })

        return files
