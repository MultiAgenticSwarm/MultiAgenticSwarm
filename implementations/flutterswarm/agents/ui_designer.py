"""
FlutterUIDesignerAgent - ALL UI design knowledge comes from LLM.
No hardcoded UI patterns or design decisions.
"""

from typing import Dict, Any, List, Optional
import logging

from implementations.agentswarm.agents import AbstractDeveloperAgent  # UI Designer extends Developer
from implementations.agentswarm.core.types import TaskContext, ExecutionResult
from ..tools import FlutterCLITool, DartCLITool, FileSystemTool

# Import MAS as the core SDK
import multiagenticswarm as mas
from multiagenticswarm.core.agent import Agent

class FlutterUIDesignerAgent(AbstractDeveloperAgent, Agent):
    """
    Flutter UI Designer agent - ALL UI design knowledge comes from LLM.
    No hardcoded UI patterns, themes, or design decisions.

    This agent specializes in:
    - UI/UX design and layout
    - Material Design and Cupertino implementation
    - Custom widget creation
    - Animation and transitions
    - Responsive design
    - Accessibility
    - Theming and styling
    """

    def __init__(self, name: str = "flutter_ui_designer", working_directory: str = ".", **kwargs):
        self.working_directory = working_directory
        super().__init__(name=name, **kwargs)

        # Initialize tools
        self.flutter_cli = FlutterCLITool(working_directory)
        self.dart_cli = DartCLITool(working_directory)
        self.file_system = FileSystemTool(working_directory)

        self.logger = logging.getLogger(f"flutterswarm.{name}")

    def _get_specialized_instructions(self) -> str:
        """UI Designer specific instructions"""
        return """You are an expert Flutter UI Designer with comprehensive knowledge of:

UI DESIGN PRINCIPLES:
- Material Design 3 guidelines and implementation
- Cupertino design for iOS applications
- Brand identity integration
- Color theory and typography
- Spacing and layout principles
- User experience best practices
- Interaction design patterns

FLUTTER UI IMPLEMENTATION:
- Widget composition and custom widgets
- Responsive and adaptive layouts
- Theming and styling
- Animation and motion design
- Custom painting and graphics
- Asset management and integration
- Localization and internationalization

ADVANCED UI TECHNIQUES:
- Complex widget trees and composition
- Custom UI components and reusable widgets
- Gesture handling and input systems
- Custom scrolling behaviors
- Hero animations and transitions
- Staggered animations and choreography
- Custom painters and rendering

ACCESSIBILITY:
- Screen reader compatibility
- Color contrast guidelines
- Focus management
- Semantic labels and descriptions
- Text scaling
- Alternative input methods
- Accessibility testing

RESPONSIVE DESIGN:
- Layout adaptation for different screen sizes
- Orientation changes
- Adaptive and responsive widgets
- Flexible layouts
- MediaQuery and LayoutBuilder usage
- Breakpoint systems
- Device-specific optimizations

PLATFORM ADAPTABILITY:
- Platform-aware design
- Material/Cupertino adaptive components
- Desktop, web, and mobile considerations
- Different navigation patterns by platform
- Platform-specific gestures and interactions
- Target platform constraints

PROTOTYPING AND ITERATION:
- Rapid prototyping techniques
- UI testing and validation
- User feedback integration
- Design system implementation
- Component libraries
- Design documentation
- Design-to-code workflow

IMPORTANT INSTRUCTIONS:
1. Use your comprehensive UI design knowledge to create beautiful, functional interfaces
2. Follow platform-appropriate design guidelines (Material, Cupertino)
3. Create reusable, maintainable UI components
4. Ensure accessibility compliance
5. Design for different screen sizes and orientations
6. Consider performance implications of your designs
7. Document design patterns and component usage

When designing Flutter UIs:
- Start with user needs and workflows
- Create consistent visual language
- Use the right widgets for the right purposes
- Design for edge cases (empty states, errors, loading)
- Consider internationalization requirements
- Optimize for different devices and platforms
- Create delightful interactions and animations

You have access to Flutter CLI, Dart CLI, and file system tools.
Use these to implement your UI designs.
"""

    def _get_tools(self) -> List[Any]:
        """Get tools for UI design"""
        return [
            mas.Tool(
                name="flutter_cli",
                description="Execute Flutter CLI commands",
                function=self.flutter_cli.execute
            ),
            mas.Tool(
                name="dart_cli",
                description="Execute Dart CLI commands",
                function=self.dart_cli.execute
            ),
            mas.Tool(
                name="file_system",
                description="File system operations",
                function=self.file_system._execute_wrapper
            )
        ]

    async def design_ui(
        self,
        ui_requirements: str,
        design_constraints: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Design complete UI using LLM knowledge.
        """

        # Get current project context
        project_structure = await self.file_system.list_directory(
            path=self.working_directory,
            recursive=True
        )

        # Read current theme if exists
        theme_files = []
        for file in project_structure.get('files', []):
            if 'theme' in file.lower() or 'style' in file.lower():
                theme_content = await self.file_system.read_file(file)
                if theme_content.get('success'):
                    theme_files.append({
                        'path': file,
                        'content': theme_content['content']
                    })

        design_prompt = f"""
Design a complete Flutter UI for these requirements:
{ui_requirements}

Design constraints:
{design_constraints}

Current project context:
- Project structure: {project_structure.get('files', []) if project_structure.get('success') else 'New project'}
- Existing themes: {theme_files if theme_files else 'None'}
- Target platforms: {context.target_platforms if context else ['iOS', 'Android']}

Create a comprehensive UI design:

1. UI_ANALYSIS: Analyze requirements and identify UI components needed
2. DESIGN_SYSTEM: Define colors, typography, spacing, and overall design system
3. WIDGET_HIERARCHY: Plan widget structure and composition
4. RESPONSIVE_STRATEGY: Plan responsive design approach
5. ANIMATION_PLAN: Plan animations and transitions
6. ACCESSIBILITY_CONSIDERATIONS: Plan accessibility features
7. IMPLEMENTATION: Complete Flutter UI implementation

Provide:
- Complete widget implementations
- Theme and styling code
- Animation implementations
- Responsive design code
- Accessibility features
- File structure for UI components

Base all design decisions on:
- Material Design 3 principles (for Android)
- Cupertino design patterns (for iOS)
- Best UI/UX practices
- Flutter widget best practices
- Performance considerations
- Accessibility guidelines

Generate production-ready, beautiful UI code.
"""

        # Get LLM design
        design_result = await self.execute(design_prompt, context)

        if not design_result.success:
            return design_result

        # Extract and implement the design
        llm_response = design_result.output

        # Extract UI components from response
        ui_files = self._extract_ui_files_from_response(llm_response)
        theme_updates = self._extract_theme_updates_from_response(llm_response)

        created_files = []

        # Create UI component files
        for file_info in ui_files:
            result = await self.file_system.write_file(
                path=file_info['path'],
                content=file_info['content'],
                create_dirs=True
            )

            if result.get('success'):
                created_files.append(file_info['path'])
                self.logger.info(f"Created UI file: {file_info['path']}")

        # Update theme files
        for theme_update in theme_updates:
            result = await self.file_system.write_file(
                path=theme_update['path'],
                content=theme_update['content'],
                create_dirs=True
            )

            if result.get('success'):
                created_files.append(theme_update['path'])
                self.logger.info(f"Updated theme file: {theme_update['path']}")

        return ExecutionResult(
            success=True,
            agent_name=self.name,
            task_id=f"design_ui_{len(self.execution_history)}",
            output={
                'design_analysis': llm_response,
                'created_files': created_files,
                'ui_components': ui_files,
                'theme_updates': theme_updates
            },
            created_files=created_files,
            next_steps=[
                "Review the UI design implementation",
                "Test UI on different screen sizes",
                "Verify accessibility features",
                "Test animations and transitions",
                "Validate design consistency"
            ]
        )

    async def create_theme(
        self,
        brand_guidelines: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Create a comprehensive Flutter theme.
        """

        theme_prompt = f"""
Create a comprehensive Flutter theme based on these brand guidelines:
{brand_guidelines}

Project context: {context.__dict__ if context else 'None'}

Create:
1. THEME_ANALYSIS: Analyze brand guidelines and define theme strategy
2. COLOR_SCHEME: Define primary, secondary, and accent colors
3. TYPOGRAPHY: Define text styles and font hierarchy
4. COMPONENT_THEMES: Define themes for all Flutter components
5. DARK_THEME: Create dark mode variant
6. THEME_IMPLEMENTATION: Complete Flutter theme code

Provide:
- Complete ThemeData implementation
- Color scheme definitions
- Typography themes
- Component-specific themes
- Dark mode support
- Theme switching functionality

Base the theme on:
- Material Design 3 color system
- Brand guidelines and identity
- Accessibility requirements
- Platform conventions
- User experience best practices

Generate production-ready theme code.
"""

        return await self.execute(theme_prompt, context)

    async def create_animations(
        self,
        animation_requirements: List[str],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Create Flutter animations using LLM knowledge.
        """

        animation_prompt = f"""
Create Flutter animations for these requirements:
{animation_requirements}

Project context: {context.__dict__ if context else 'None'}

Create:
1. ANIMATION_ANALYSIS: Analyze requirements and plan animation approach
2. ANIMATION_STRATEGY: Choose appropriate animation techniques
3. PERFORMANCE_CONSIDERATIONS: Plan for smooth, performant animations
4. IMPLEMENTATION: Complete animation code

Provide:
- Animation controller implementations
- Tween and curve definitions
- Custom animation widgets
- Performance optimizations
- Usage examples

Use appropriate Flutter animation techniques:
- Implicit animations for simple cases
- Explicit animations for complex scenarios
- Hero animations for navigation
- Custom animations for unique effects
- Optimized animations for performance

Generate smooth, beautiful animations.
"""

        return await self.execute(animation_prompt, context)

    async def optimize_ui_performance(
        self,
        performance_issues: List[str],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Optimize UI performance using LLM analysis.
        """

        optimization_prompt = f"""
Optimize Flutter UI performance for these issues:
{performance_issues}

Project context: {context.__dict__ if context else 'None'}

Analyze and optimize:
1. PERFORMANCE_ANALYSIS: Identify performance bottlenecks
2. OPTIMIZATION_STRATEGY: Plan optimization approach
3. WIDGET_OPTIMIZATIONS: Optimize widget usage
4. RENDERING_OPTIMIZATIONS: Optimize rendering performance
5. MEMORY_OPTIMIZATIONS: Optimize memory usage

Apply Flutter UI performance best practices:
- Const constructors for immutable widgets
- RepaintBoundary for expensive widgets
- ListView.builder for large lists
- Image optimization and caching
- Animation performance optimization
- Widget tree optimization
- Memory leak prevention

Provide specific optimization recommendations and code changes.
"""

        return await self.execute(optimization_prompt, context)

    # Helper methods
    def _extract_ui_files_from_response(self, response: str) -> List[Dict[str, str]]:
        """Extract UI files from LLM response"""
        # Similar to the developer agent's file extraction
        files = []

        lines = response.split('\n')
        current_file = None
        current_content = []

        for line in lines:
            if line.strip().startswith('UI_FILE:') or line.strip().startswith('WIDGET:'):
                if current_file:
                    files.append({
                        'path': current_file,
                        'content': '\n'.join(current_content)
                    })

                current_file = line.split(':', 1)[1].strip()
                current_content = []
            elif current_file and line.strip():
                current_content.append(line)

        if current_file:
            files.append({
                'path': current_file,
                'content': '\n'.join(current_content)
            })

        return files

    def _extract_theme_updates_from_response(self, response: str) -> List[Dict[str, str]]:
        """Extract theme updates from LLM response"""
        # Similar extraction for theme files
        themes = []

        lines = response.split('\n')
        current_theme = None
        current_content = []

        for line in lines:
            if line.strip().startswith('THEME:') or line.strip().startswith('STYLE:'):
                if current_theme:
                    themes.append({
                        'path': current_theme,
                        'content': '\n'.join(current_content)
                    })

                current_theme = line.split(':', 1)[1].strip()
                current_content = []
            elif current_theme and line.strip():
                current_content.append(line)

        if current_theme:
            themes.append({
                'path': current_theme,
                'content': '\n'.join(current_content)
            })

        return themes
