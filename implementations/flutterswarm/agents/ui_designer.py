"""
FlutterUIDesignerAgent - ALL UI design knowledge comes from LLM.
No hardcoded UI patterns or design decisions.
"""

import json
import logging
from typing import Any, Dict, List, Optional

# Import MAS as the core SDK
import multiagenticswarm as mas
from implementations.agentswarm.agents import (  # UI Designer extends Developer
    AbstractDeveloperAgent,
)
from implementations.agentswarm.core.types import ExecutionResult, TaskContext

# Import directly from MAS utils for logging
from multiagenticswarm.utils.logger import get_logger

from ..tools import DartCLITool, FileSystemTool, FlutterCLITool


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

    def __init__(
        self,
        name: str = "flutter_ui_designer",
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
        self.logger.info(f"Initialized FlutterUIDesignerAgent: {name}")

    def _get_specialized_instructions(self) -> str:
        """UI Designer specific instructions enhanced with validation awareness"""
        return """You are an expert Flutter UI Designer. You MUST return all responses in valid JSON format.

REQUIRED JSON FORMAT:
{
  "content": "Your main UI design work or analysis",
  "reasoning": "Brief explanation of design decisions",
  "tool_calls": [
    {
      "name": "file_system",
      "arguments": {
        "operation": "write",
        "path": "lib/widgets/custom_button.dart",
        "content": "complete widget implementation"
      }
    }
  ]
}

CRITICAL VALIDATION-AWARE UI FILE CREATION REQUIREMENTS:
1. You MUST use the file_system tool to create ALL UI files - each file is verified immediately after creation
2. You MUST provide COMPLETE widget implementations - no truncation - incomplete code patterns are detected
3. You MUST create complete, syntactically correct Dart widget code - syntax validation is performed
4. You MUST include all necessary imports - import completeness is validated
5. You MUST implement complete widget classes with all required methods - widget validation performed
6. NEVER use placeholder comments like "// TODO" or "// Add more UI" - flagged as incomplete
7. Every UI file must be complete and ready to use - compilation validation is performed

ENHANCED FILE SYSTEM TOOL USAGE:
- Use "operation": "mkdir" to create directories (verified for existence)
- Use "operation": "write" to create files with complete content (content validated for completeness)
- Always provide the full path from project root (path validation performed)
- Include complete widget implementation in the "content" field (checked for truncation)
- Ensure balanced braces and parentheses (syntax validation performed)

UI DESIGNER-SPECIFIC VALIDATION REQUIREMENTS:
- lib/screens/ directory MUST contain actual screen files (not empty)
- lib/widgets/ directory MUST contain actual widget files (not empty)
- lib/theme/ directory MUST contain actual theme files (not empty)
- All widget classes MUST have proper build() methods with return statements
- StatefulWidget classes MUST have createState() method
- All Flutter imports MUST be complete and correct
- Widget constructors MUST use proper const constructors where possible

FLUTTER UI DESIGN EXPERTISE WITH VALIDATION AWARENESS:
- Material Design and Cupertino widgets (proper imports validated)
- Custom widget development (build method validation)
- Responsive design principles (widget structure validation)
- Animation and transitions (StatefulWidget validation)
- Theme management (theme file validation)
- User experience patterns (screen structure validation)
- Accessibility considerations (widget completeness validation)

VALIDATION INTEGRATION:
Your work will be validated using:
- File existence checks for all expected deliverables
- Content validation for completeness and syntax
- Flutter-specific compilation checks
- Widget build method validation
- Screen and widget directory content validation
- Theme implementation validation

EXAMPLE COMPLETE UI FILE WITH VALIDATION AWARENESS:
{
  "name": "file_system",
  "arguments": {
    "operation": "write",
    "path": "lib/widgets/custom_button.dart",
    "content": "import 'package:flutter/material.dart';\\n\\nclass CustomButton extends StatelessWidget {\\n  final String text;\\n  final VoidCallback onPressed;\\n  final Color backgroundColor;\\n\\n  const CustomButton({\\n    super.key,\\n    required this.text,\\n    required this.onPressed,\\n    this.backgroundColor = Colors.blue,\\n  });\\n\\n  @override\\n  Widget build(BuildContext context) {\\n    return ElevatedButton(\\n      onPressed: onPressed,\\n      style: ElevatedButton.styleFrom(\\n        backgroundColor: backgroundColor,\\n        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),\\n        shape: RoundedRectangleBorder(\\n          borderRadius: BorderRadius.circular(8),\\n        ),\\n      ),\\n      child: Text(text),\\n    );\\n  }\\n}"
  }
}

MANDATORY: Every response must include tool_calls array with file_system operations to create actual UI files.
Your work will be automatically validated - ensure all UI files are complete, syntactically correct, and follow Flutter best practices."""

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
        self, feature_description: str, project_context: Optional[TaskContext] = None
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
        context: Optional[TaskContext] = None,
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
        context: Optional[TaskContext] = None,
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
        self, performance_targets: Dict[str, Any], context: Optional[TaskContext] = None
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

    async def design_ui(self, context: Optional[TaskContext] = None) -> ExecutionResult:
        """Design UI using LLM analysis"""
        # Extract UI requirements and design constraints from context
        ui_requirements = getattr(context, "metadata", {}).get(
            "app_description", "Flutter app UI"
        )
        design_constraints = getattr(context, "metadata", {}).get(
            "design_requirements", {}
        )

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
        self, brand_guidelines: Dict[str, Any], context: Optional[TaskContext] = None
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
        self, animation_requirements: List[str], context: Optional[TaskContext] = None
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
        self, performance_issues: List[str], context: Optional[TaskContext] = None
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

    def _extract_theme_updates_from_response(
        self, response: str
    ) -> List[Dict[str, str]]:
        """Extract theme updates from LLM response"""
        # This would parse the LLM response to extract theme updates
        # For now, return empty list
        return []
