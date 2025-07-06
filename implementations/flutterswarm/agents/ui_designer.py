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

class FlutterUIDesignerAgent(AbstractDeveloperAgent):
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

    def __init__(self, name: str = "flutter_ui_designer", working_directory: str = ".", flutter_cli=None, dart_cli=None, file_system=None, **kwargs):
        self.working_directory = working_directory

        # Use shared tool instances if provided
        self.flutter_cli = flutter_cli if flutter_cli is not None else FlutterCLITool(working_directory)
        self.dart_cli = dart_cli if dart_cli is not None else DartCLITool(working_directory)
        self.file_system = file_system if file_system is not None else FileSystemTool(working_directory)

        # Initialize with proper MAS integration
        super().__init__(
            name=name,
            system=kwargs.get('system'),
            llm_provider=kwargs.get('llm_provider', 'openai'),
            llm_model=kwargs.get('llm_model', 'gpt-4'),
            **{k: v for k, v in kwargs.items() if k not in ['system', 'llm_provider', 'llm_model']}
        )

        self.logger = mas.get_logger(f"flutterswarm.{name}")
        self.logger.info(f"Initialized FlutterUIDesignerAgent: {name}")

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

    async def generate_code(
        self,
        requirements: str,
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Generate UI code based on requirements"""
        task = f"""
        Generate Flutter UI code for: {requirements}

        Focus on:
        1. Beautiful and intuitive user interface
        2. Material Design 3 principles
        3. Responsive design patterns
        4. Accessibility features
        5. Smooth animations and transitions
        6. Consistent theming
        7. Performance optimization

        Create:
        - Custom widgets as needed
        - Proper layout structures
        - Theme configuration
        - Animation implementations
        - Accessibility features
        - Platform adaptations
        """

        return await self.execute(task, context)

    async def implement_feature(
        self,
        feature_description: str,
        project_context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Implement UI feature using LLM reasoning"""
        task = f"""
        Implement Flutter UI feature: {feature_description}

        Project context: {project_context.__dict__ if project_context else 'None'}

        Design approach:
        1. Analyze UI requirements
        2. Create design mockups (described)
        3. Implement responsive layouts
        4. Add smooth animations
        5. Ensure accessibility
        6. Optimize performance
        7. Create reusable components

        Consider:
        - Material Design guidelines
        - Platform-specific adaptations
        - Different screen sizes
        - Dark mode support
        - Accessibility requirements
        """

        return await self.execute(task, project_context)

    async def refactor_code(
        self,
        code_path: str,
        refactoring_goals: List[str],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Refactor UI code using LLM analysis"""
        task = f"""
        Refactor Flutter UI code at: {code_path}

        Refactoring goals: {refactoring_goals}

        UI refactoring focus:
        1. Improve widget composition
        2. Enhance performance
        3. Better responsive design
        4. Cleaner theming
        5. Improved accessibility
        6. Better animations
        7. More maintainable code

        Apply:
        - Widget extraction and reuse
        - Performance optimizations
        - Better state management
        - Improved layouts
        - Enhanced theming
        """

        return await self.execute(task, context)

    async def debug_issue(
        self,
        issue_description: str,
        error_logs: Optional[List[str]] = None,
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Debug UI issues using LLM analysis"""
        task = f"""
        Debug Flutter UI issue: {issue_description}

        Error logs: {error_logs or 'None provided'}

        UI debugging focus:
        1. Widget tree analysis
        2. Layout issues
        3. Performance problems
        4. Animation glitches
        5. Theming inconsistencies
        6. Accessibility problems
        7. Platform-specific issues

        Provide:
        - Root cause analysis
        - Step-by-step fixes
        - Prevention strategies
        - Performance improvements
        - Testing recommendations
        """

        return await self.execute(task, context)

    async def optimize_performance(
        self,
        performance_targets: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Optimize UI performance using LLM analysis"""
        task = f"""
        Optimize Flutter UI performance for: {performance_targets}

        UI optimization areas:
        1. Widget build optimization
        2. Animation performance
        3. Layout efficiency
        4. Memory usage reduction
        5. Image loading optimization
        6. Scrolling performance
        7. Custom painter optimization

        Strategies:
        - Const constructors usage
        - Widget caching
        - Efficient layouts
        - Animation optimization
        - Asset optimization
        - Memory management
        """

        return await self.execute(task, context)

    async def design_ui(
        self,
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Design UI using LLM analysis"""
        # Extract UI requirements and design constraints from context
        ui_requirements = getattr(context, 'metadata', {}).get('app_description', 'Flutter app UI')
        design_constraints = getattr(context, 'metadata', {}).get('design_requirements', {})

        task = f"""
        Design Flutter UI for: {ui_requirements}

        Design constraints: {design_constraints}

        Create:
        1. UI/UX design specification
        2. Widget hierarchy design
        3. Layout structure
        4. Color and typography scheme
        5. Animation specifications
        6. Responsive design strategy
        7. Accessibility considerations

        Focus on:
        - User experience excellence
        - Visual hierarchy
        - Consistency and patterns
        - Performance considerations
        - Platform guidelines
        """

        return await self.execute(task, context)

    async def create_theme(
        self,
        brand_guidelines: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Create theme based on brand guidelines"""
        task = f"""
        Create Flutter theme from brand guidelines: {brand_guidelines}

        Generate:
        1. Complete ThemeData configuration
        2. Color scheme (light and dark)
        3. Typography system
        4. Component themes
        5. Custom widget themes
        6. Animation themes
        7. Platform adaptations

        Ensure:
        - Brand consistency
        - Accessibility compliance
        - Performance optimization
        - Maintainability
        - Extensibility
        """

        return await self.execute(task, context)

    async def create_animations(
        self,
        animation_requirements: List[str],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Create animations based on requirements"""
        task = f"""
        Create Flutter animations for: {animation_requirements}

        Implement:
        1. Custom animation controllers
        2. Smooth transitions
        3. Micro-interactions
        4. Page transitions
        5. Loading animations
        6. Gesture-based animations
        7. Performance-optimized animations

        Focus on:
        - Smooth 60fps performance
        - Natural motion curves
        - Accessibility considerations
        - Battery efficiency
        - Memory optimization
        """

        return await self.execute(task, context)

    async def optimize_ui_performance(
        self,
        performance_issues: List[str],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Optimize UI performance for specific issues"""
        task = f"""
        Optimize Flutter UI performance for issues: {performance_issues}

        Address:
        1. Rendering bottlenecks
        2. Widget rebuild optimization
        3. Memory leaks
        4. Animation performance
        5. Layout efficiency
        6. Asset optimization
        7. Platform-specific optimizations

        Provide:
        - Specific optimizations
        - Performance measurements
        - Best practices
        - Monitoring strategies
        - Long-term maintenance
        """

        return await self.execute(task, context)

    # Helper methods
    def _extract_ui_files_from_response(self, response: str) -> List[Dict[str, str]]:
        """Extract UI files from LLM response"""
        # This would parse the LLM response to extract UI files
        # For now, return empty list
        return []

    def _extract_theme_updates_from_response(self, response: str) -> List[Dict[str, str]]:
        """Extract theme updates from LLM response"""
        # This would parse the LLM response to extract theme updates
        # For now, return empty list
        return []
