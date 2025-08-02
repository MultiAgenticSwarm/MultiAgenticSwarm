"""
Flutter UI Agent - Specialized agent for UI/UX development.
"""

from typing import Dict, Any
from multiagenticswarm.core.collaborative_system import UniversalAgent
from multiagenticswarm.utils.logger import get_logger

logger = get_logger(__name__)


class FlutterUIAgent(UniversalAgent):
    """
    Specialized agent for Flutter UI/UX development.

    Focuses on:
    - Material Design 3 implementation
    - Responsive widget design
    - Navigation and routing
    - User experience optimization
    """

    def __init__(self, progress_board=None):
        super().__init__(
            name="Flutter_UI_Agent",
            description="Specializes in Flutter UI development, Material Design 3, and user experience",
            system_prompt="""You are an expert Flutter UI developer working in a collaborative team. Your role:

PRIMARY RESPONSIBILITIES:
- Create beautiful, responsive user interfaces using Flutter
- Implement Material Design 3 components and consistent theming
- Build reusable widgets and maintainable screen layouts
- Handle app navigation, routing, and user flow
- Ensure excellent user experience and accessibility

COLLABORATION GUIDELINES:
- Share UI component interfaces early with the team
- Coordinate with Audio Agent on player controls integration
- Work with Data Agent on state management and data binding
- Provide UI feedback and suggestions to other agents
- Request help when audio or data integration is needed

TECHNICAL FOCUS:
- Material Design 3 theming and components
- Responsive design for different screen sizes
- Smooth animations and transitions
- Clean, maintainable widget architecture
- Proper state management integration

COLLABORATION TOOLS AVAILABLE:
- post_update(): Share progress and status
- share_interface(): Share UI component interfaces
- share_code_snippet(): Share UI code examples
- request_help(): Ask for integration help
- coordinate_with_team(): Coordinate development
- report_progress(): Track UI development progress

Always read the collaboration prompt first to understand the project context and your role.
Prioritize user experience and collaborate actively with your teammates.""",
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
            progress_board=progress_board
        )

        # UI-specific capabilities
        self.ui_specializations = [
            "Material Design 3",
            "Widget Architecture",
            "Navigation Systems",
            "Responsive Design",
            "Animations",
            "Accessibility",
            "Theming"
        ]

        logger.info("FlutterUIAgent initialized with UI specializations")

    async def create_screen_layout(self, screen_name: str, components: list) -> dict:
        """Create a Flutter screen layout using LLM reasoning."""
        await self.report_progress(
            task=f"Creating {screen_name}",
            percentage=20,
            details=f"Analyzing requirements and generating {screen_name} layout"
        )

        # Use LLM to generate screen layout
        prompt = f"""
        I need to create a {screen_name} screen for a Flutter music streaming app.

        Components to include: {', '.join(components)}

        Requirements:
        1. Follow Material Design 3 principles
        2. Create responsive layout for different screen sizes
        3. Include proper navigation and app bar
        4. Integrate with audio service provider
        5. Include proper state management
        6. Add accessibility features
        7. Use modern Flutter widgets and best practices

        Generate complete Dart code for the {screen_name} screen with all necessary imports.
        Make it production-ready with proper error handling and documentation.
        """

        response = await self.execute_llm_task(prompt)
        screen_code = response.get('content', '')

        await self.share_code_snippet(
            snippet=screen_code,
            description=f"AI-generated {screen_name} screen with Material Design 3",
            language="dart",
            file_path=f"lib/screens/{screen_name.lower()}_screen.dart"
        )

        # Generate interface information
        interface_prompt = f"""
        Based on the {screen_name} screen I just created, list the main public methods
        and properties that other components need to interact with.
        """

        interface_response = await self.execute_llm_task(interface_prompt)
        interface_methods = interface_response.get('content', '').split('\n')

        await self.share_code_interface(
            interface_name=f"{screen_name}Interface",
            methods=interface_methods,
            description=f"Interface for {screen_name} screen and its actions"
        )

        await self.report_progress(
            task=f"Creating {screen_name}",
            percentage=100,
            details=f"{screen_name} screen generated and shared with team"
        )

        return {
            "screen_name": screen_name,
            "components": components,
            "interface_shared": True,
            "status": "generated"
        }

    async def implement_material_design_theme(self) -> dict:
        """Implement Material Design 3 theming using LLM with collaboration context."""
        await self.report_progress("Material Design Theme", 0, "Reading collaboration prompt and project context")

        # Get collaboration context
        collaboration_context = await self._get_collaboration_context()

        prompt = f"""
Based on the collaboration prompt and project requirements, create a Material Design 3 theme for a Flutter music app.

COLLABORATION CONTEXT:
{collaboration_context}

TASK: Create a comprehensive Material Design 3 theme that includes:
1. Use Material Design 3 (useMaterial3: true)
2. Create both light and dark themes suitable for a music streaming app
3. Use a music-themed color scheme (deep purple, blues, or music-inspired colors)
4. Customize app bar, cards, buttons, and navigation components for music app
5. Include proper typography scales for track titles, artist names, etc.
6. Add custom theme extensions for music player components
7. Ensure accessibility compliance
8. Consider the collaboration with Audio and Data agents for consistent styling

Generate complete, production-ready Dart code with both ThemeData objects and any custom theme extensions.
The code should be ready to use in a Flutter app without modification.
"""

        await self.report_progress("Material Design Theme", 30, "Generating Material Design 3 theme code with LLM...")

        try:
            # Make actual LLM call
            response = await self._call_llm(prompt)
            theme_code = response.get("content", "")

            if not response.get("success", False):
                raise Exception(response.get("error", "LLM call failed"))

            # Create theme file
            await self._create_flutter_file("lib/utils/theme.dart", theme_code, "AI-generated Material Design 3 theme")

            await self.report_progress("Material Design Theme", 100, "Material Design 3 theme implementation completed")

            # Share interface with team
            await self.share_interface(
                interface_name="AppTheme",
                methods=["getTheme()", "getDarkTheme()", "getColorScheme()"],
                description="Material Design 3 theme interface for consistent app styling across all components"
            )

            return {
                "status": "completed",
                "material_design_version": 3,
                "theme_file": "lib/utils/theme.dart",
                "features": ["light_theme", "dark_theme", "custom_colors", "typography", "music_components"],
                "shared_interface": "AppTheme",
                "collaboration_aware": True
            }

        except Exception as e:
            await self.report_progress("Material Design Theme", 0, f"Error generating theme: {str(e)}")
            logger.error(f"Theme generation failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def create_navigation_system(self) -> dict:
        """Create app navigation system using LLM with collaboration context."""
        await self.report_progress("Navigation System", 0, "Reading collaboration context for navigation requirements")

        # Get collaboration context
        collaboration_context = await self._get_collaboration_context()

        prompt = f"""
Based on the collaboration context, create a comprehensive navigation system for a Flutter music streaming app.

COLLABORATION CONTEXT:
{collaboration_context}

TASK: Create a navigation system that coordinates well with other agents' work:

NAVIGATION REQUIREMENTS:
1. Use GoRouter or standard Navigator 2.0 for modern routing
2. Define routes for: Home, Player, Playlist, Search, Settings, Library
3. Include bottom navigation bar for main sections
4. Add proper route transitions and animations
5. Handle deep linking and route parameters for music tracks/playlists
6. Include route guards for protected sections
7. Support both push and replacement navigation patterns
8. Consider audio player overlay that persists across screens (coordinate with Audio Agent)
9. Integrate with state management for navigation state (coordinate with Data Agent)

Generate complete, production-ready Dart code for the navigation system.
Include router configuration, bottom navigation bar, and route definitions.
Ensure it works seamlessly with the overall app architecture.
"""

        await self.report_progress("Navigation System", 40, "Generating navigation system code with LLM...")

        try:
            # Make actual LLM call
            response = await self._call_llm(prompt)
            navigation_code = response.get("content", "")

            if not response.get("success", False):
                raise Exception(response.get("error", "LLM call failed"))

            # Create navigation file
            await self._create_flutter_file("lib/utils/app_router.dart", navigation_code, "AI-generated navigation system with GoRouter")

            await self.report_progress("Navigation System", 100, "Navigation system implementation completed")

            # Share interface with team
            await self.share_interface(
                interface_name="NavigationService",
                methods=["goToHome()", "goToPlayer(track)", "goToPlaylist(id)", "goToSearch()", "pushReplacement()"],
                description="Navigation service for app routing and screen transitions"
            )

            return {
                "status": "completed",
                "navigation_system": "generated",
                "router_type": "modern",
                "file_path": "lib/utils/app_router.dart",
                "features": ["bottom_navigation", "deep_linking", "route_guards", "transitions"],
                "collaboration_aware": True
            }

        except Exception as e:
            await self.report_progress("Navigation System", 0, f"Error generating navigation: {str(e)}")
            logger.error(f"Navigation generation failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def execute_llm_task(self, prompt: str) -> Dict[str, Any]:
        """Execute an LLM task and return the response."""
        try:
            # Add collaboration context to the prompt
            context_prompt = f"""
            {self.collaboration_prompt or ""}

            Task: {prompt}

            As the Flutter UI Agent, provide a complete, production-ready solution.
            Focus on beautiful, accessible UI design and seamless integration with the broader music app.
            Follow Material Design 3 principles and Flutter best practices.

            Respond with clean, well-documented Dart/Flutter code that is ready to use.
            """

            # Use the agent's execute method which handles LLM calls properly
            response = await self.execute(context_prompt)

            return {"content": response, "success": True}

        except Exception as e:
            logger.error(f"LLM task execution failed: {e}")
            return {"content": f"Error: {str(e)}", "success": False}
            logger.error(f"Error executing LLM task: {e}")
            return {"content": f"Error generating content: {e}", "usage": None}

    async def _get_collaboration_context(self) -> str:
        """Get collaboration context from progress board and prompt."""
        context_parts = []

        # Get collaboration prompt
        if self.collaboration_prompt:
            context_parts.append(f"COLLABORATION PROMPT:\n{self.collaboration_prompt}")

        # Get recent team updates
        if self.progress_board:
            recent_updates = self.progress_board.get_recent_activity(hours=24)
            if recent_updates.get("recent_updates"):
                context_parts.append("RECENT TEAM ACTIVITY:")
                for update in recent_updates["recent_updates"][-5:]:  # Last 5 updates
                    context_parts.append(f"- {update.get('agent', 'Unknown')}: {update.get('message', '')}")

        return "\n".join(context_parts) if context_parts else "No collaboration context available"

    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """Make an actual LLM call to generate code."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]

        try:
            # Use the agent's LLM provider to make the call
            response = await self.llm_provider.execute(messages)
            return {"content": response.content, "success": True}
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return {"content": "", "success": False, "error": str(e)}

    async def _create_flutter_file(self, file_path: str, content: str, description: str) -> None:
        """Create a Flutter file with the generated content."""
        import os
        from pathlib import Path

        # Ensure we're in the right workspace
        workspace_path = Path("./flutter_music_app_workspace")
        full_path = workspace_path / file_path

        # Create directories if they don't exist
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Created Flutter file: {full_path}")

        # Report to progress board
        if self.progress_board:
            self.progress_board.share_code_snippet(
                agent_name=self.name,
                snippet=content[:500] + "..." if len(content) > 500 else content,
                description=description,
                language="dart",
                file_path=file_path
            )

def create_flutter_ui_agent(progress_board=None):
    """Factory function to create Flutter UI Agent."""
    return FlutterUIAgent(progress_board=progress_board)
