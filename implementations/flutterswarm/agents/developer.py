"""
FlutterDeveloperAgent - ALL Flutter knowledge comes from LLM.
No hardcoded Flutter patterns, widgets, or logic.
"""

import logging
from typing import Dict, Any, List, Optional

# Import from implementations
from implementations.agentswarm.agents import AbstractDeveloperAgent
from implementations.agentswarm.core.types import TaskContext, ExecutionResult, AgentRole

# Import tools
from ..tools import FlutterCLITool, DartCLITool, FileSystemTool

# Import MAS as the core SDK
import multiagenticswarm as mas


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

    def __init__(self, name: str = "flutter_developer", working_directory: str = ".", **kwargs):
        self.working_directory = working_directory

        # Initialize with proper MAS integration
        super().__init__(
            name=name,
            working_directory=working_directory,
            **kwargs
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
"""

    def _get_tools(self) -> List[Dict[str, Any]]:
        """Get Flutter development tools - tools come from the system"""
        return [
            {
                "name": "flutter_cli",
                "description": "Execute Flutter CLI commands for project creation, building, running, and testing",
                "scope": "global"
            },
            {
                "name": "dart_cli",
                "description": "Execute Dart CLI commands for package management, analysis, and formatting",
                "scope": "global"
            },
            {
                "name": "file_system",
                "description": "File system operations for reading, writing, and managing project files",
                "scope": "global"
            }
        ]

    async def implement_feature(self, feature_description: str, context: Optional[TaskContext] = None) -> ExecutionResult:
        """Implement a Flutter feature using LLM knowledge"""

        prompt = f"""
        Implement the following Flutter feature:
        {feature_description}

        Working directory: {self.working_directory}
        Context: {context.__dict__ if context else 'No specific context'}

        Steps to follow:
        1. Analyze the feature requirements
        2. Plan the implementation approach
        3. Create necessary files and directories
        4. Implement the feature using appropriate Flutter patterns
        5. Test the implementation
        6. Provide a summary of what was implemented

        Use your Flutter expertise to make all technical decisions.
        """

        return await self.execute(prompt, context)

    async def create_widget(self, widget_description: str, context: Optional[TaskContext] = None) -> ExecutionResult:
        """Create a custom Flutter widget"""

        prompt = f"""
        Create a custom Flutter widget:
        {widget_description}

        Requirements:
        1. Use appropriate widget type (StatelessWidget or StatefulWidget)
        2. Follow Flutter widget composition patterns
        3. Include proper documentation
        4. Handle edge cases and errors
        5. Consider performance implications
        6. Make it reusable and configurable

        Implement the widget in the appropriate file location.
        """

        return await self.execute(prompt, context)

    async def setup_project_structure(self, project_type: str, context: Optional[TaskContext] = None) -> ExecutionResult:
        """Setup Flutter project structure"""

        prompt = f"""
        Setup a Flutter project structure for: {project_type}

        Working directory: {self.working_directory}

        Tasks:
        1. Create appropriate folder structure
        2. Setup pubspec.yaml with necessary dependencies
        3. Create main entry point
        4. Setup routing structure
        5. Create basic theme configuration
        6. Setup development environment files
        7. Create example screens/widgets for the project type

        Use Flutter best practices for project organization.
        """

        return await self.execute(prompt, context)

    async def optimize_performance(self, target_area: str, context: Optional[TaskContext] = None) -> ExecutionResult:
        """Optimize Flutter app performance"""

        prompt = f"""
        Optimize Flutter app performance in: {target_area}

        Areas to analyze and optimize:
        1. Widget rebuild optimization
        2. Memory usage optimization
        3. Build time optimization
        4. Runtime performance
        5. Bundle size optimization
        6. Asset optimization

        Provide specific recommendations and implement the optimizations.
        """

        return await self.execute(prompt, context)

    async def implement_state_management(self, pattern: str, context: Optional[TaskContext] = None) -> ExecutionResult:
        """Implement state management pattern"""

        prompt = f"""
        Implement {pattern} state management pattern in Flutter.

        Tasks:
        1. Setup the state management architecture
        2. Create necessary models and state classes
        3. Implement state management logic
        4. Create example usage in widgets
        5. Setup dependency injection if needed
        6. Add proper error handling
        7. Document the implementation

        Follow best practices for the chosen pattern.
        """

        return await self.execute(prompt, context)

    async def create_responsive_ui(self, design_specs: str, context: Optional[TaskContext] = None) -> ExecutionResult:
        """Create responsive UI for multiple screen sizes"""

        prompt = f"""
        Create responsive Flutter UI based on: {design_specs}

        Requirements:
        1. Support mobile, tablet, and desktop layouts
        2. Use appropriate responsive design patterns
        3. Implement adaptive widgets for different platforms
        4. Handle orientation changes
        5. Optimize for accessibility
        6. Use appropriate breakpoints
        7. Implement smooth animations and transitions

        Create production-ready responsive UI implementation.
        """

        return await self.execute(prompt, context)

    async def integrate_platform_features(self, platform_features: List[str], context: Optional[TaskContext] = None) -> ExecutionResult:
        """Integrate platform-specific features"""

        prompt = f"""
        Integrate the following platform features: {', '.join(platform_features)}

        Tasks:
        1. Identify required packages and dependencies
        2. Setup platform-specific configurations
        3. Implement feature integration code
        4. Handle platform differences (iOS/Android)
        5. Add proper permission handling
        6. Implement error handling and fallbacks
        7. Test integration on different platforms

        Ensure robust cross-platform implementation.
        """

        return await self.execute(prompt, context)
