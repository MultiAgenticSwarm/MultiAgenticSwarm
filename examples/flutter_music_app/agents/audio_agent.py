"""
Flutter Audio Agent - Specialized agent for audio features and music playback.
"""

from typing import Dict, Any
from multiagenticswarm.core.collaborative_system import UniversalAgent
from multiagenticswarm.utils.logger import get_logger

logger = get_logger(__name__)


class FlutterAudioAgent(UniversalAgent):
    """
    Specialized agent for Flutter audio features and music playback.

    Focuses on:
    - Audio playback and controls
    - Music streaming services
    - Offline playback support
    - Audio state management
    """

    def __init__(self, progress_board=None):
        super().__init__(
            name="Flutter_Audio_Agent",
            description="Expert in audio features, music playback, and streaming services",
            system_prompt="""You are an expert in Flutter audio development working in a collaborative team. Your role:

PRIMARY RESPONSIBILITIES:
- Implement robust audio playback and control systems
- Create music streaming and offline playback services
- Handle audio state management and player controls
- Build performance-optimized audio features
- Integrate with audio plugins and external music services

COLLABORATION GUIDELINES:
- Share audio service interfaces with UI and Data agents
- Coordinate with UI Agent on player control components
- Work with Data Agent on audio-related data models
- Provide audio expertise and troubleshooting help
- Request help when UI integration challenges arise

TECHNICAL FOCUS:
- Audio playback libraries and plugins (just_audio, audioplayers)
- Streaming service integration
- Offline music caching and playback
- Audio state management and notifications
- Performance optimization for smooth playback

COLLABORATION TOOLS AVAILABLE:
- post_update(): Share audio development progress
- share_interface(): Share audio service interfaces
- share_code_snippet(): Share audio implementation code
- request_help(): Ask for UI/data integration help
- coordinate_with_team(): Coordinate audio features
- report_progress(): Track audio development progress

Always read the collaboration prompt first to understand the project context and your role.
Prioritize audio quality and smooth user experience.

When tasked with creating Flutter audio components, analyze the requirements and generate appropriate Dart code.
Focus on creating production-ready, well-documented code that follows Flutter best practices.""",
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
            progress_board=progress_board
        )

        # Audio-specific capabilities
        self.audio_specializations = [
            "Audio Playback",
            "Streaming Services",
            "Offline Playback",
            "Audio Controls",
            "State Management",
            "Performance Optimization",
            "Plugin Integration"
        ]

        logger.info("FlutterAudioAgent initialized with audio specializations")

    async def create_audio_service(self) -> dict:
        """Create the core audio service using LLM with collaboration context."""
        await self.report_progress(
            task="Audio Service Development",
            percentage=25,
            details="Reading collaboration context and generating core audio service"
        )

        # Get collaboration context
        collaboration_context = await self._get_collaboration_context()

        # Use LLM to generate audio service code
        prompt = f"""
Based on the collaboration context, create a comprehensive Flutter audio service for a music streaming app.

COLLABORATION CONTEXT:
{collaboration_context}

TASK: Create a robust audio service that integrates well with UI and Data components:

AUDIO SERVICE REQUIREMENTS:
1. Audio playback controls (play, pause, stop, seek, volume)
2. Playlist management (next, previous, shuffle, repeat modes)
3. State management with proper notifications to UI components
4. Integration with just_audio or audioplayers plugin
5. Streaming URL support for online music
6. Local file playback for offline mode
7. Proper error handling and recovery
8. Progress tracking and position updates
9. Audio session management for background playback
10. Integration points for UI controls (coordinate with UI Agent)
11. Data model integration for tracks and playlists (coordinate with Data Agent)

Generate complete, production-ready Dart code for the audio service.
Include proper error handling, state management, and clean interfaces for team integration.
The service should be the core foundation for all audio functionality in the app.
"""

        await self.report_progress(
            task="Audio Service Development",
            percentage=60,
            details="Generating audio service code with LLM..."
        )

        try:
            # Make actual LLM call
            response = await self._call_llm(prompt)
            audio_code = response.get("content", "")

            if not response.get("success", False):
                raise Exception(response.get("error", "LLM call failed"))

            # Create audio service file
            await self._create_flutter_file("lib/services/audio_service.dart", audio_code, "AI-generated core audio service")

            await self.report_progress(
                task="Audio Service Development",
                percentage=100,
                details="Core audio service completed and ready for integration"
            )

            # Share interface with team
            await self.share_interface(
                interface_name="AudioService",
                methods=["play(track)", "pause()", "stop()", "seek(position)", "next()", "previous()", "setPlaylist(tracks)"],
                description="Core audio playback service interface for team integration"
            )

            return {
                "status": "completed",
                "audio_service": "generated",
                "file_path": "lib/services/audio_service.dart",
                "features": ["playback_controls", "playlist_management", "state_notifications", "streaming_support"],
                "collaboration_aware": True
            }

        except Exception as e:
            await self.report_progress("Audio Service Development", 0, f"Error generating audio service: {str(e)}")
            logger.error(f"Audio service generation failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def create_streaming_service(self) -> dict:
        """Create music streaming service using LLM reasoning."""
        prompt = """
        Create a Flutter streaming service class that handles:

        1. Music search functionality
        2. Featured tracks retrieval
        3. Stream URL resolution
        4. Track downloading for offline mode
        5. HTTP requests using Dio
        6. Proper error handling and offline fallbacks

        Generate complete Dart code with imports and documentation.
        Make it compatible with a Track model that has id, title, artist, url fields.
        """

        response = await self.execute_llm_task(prompt)
        streaming_code = response.get('content', '')

        await self.share_code_snippet(
            snippet=streaming_code,
            description="AI-generated music streaming service with search and download capabilities",
            language="dart",
            file_path="lib/services/streaming_service.dart"
        )

        return {"streaming_service": "generated", "features": ["search", "download", "streaming"]}

    async def create_player_controls_widget(self) -> dict:
        """Create player controls widget for UI integration using LLM reasoning."""
        # Coordinate with UI agent first
        await self.coordinate_with_team(
            message="Generating player controls widget for UI integration",
            coordination_type="integration",
            target_agents=["Flutter_UI_Agent"]
        )

        prompt = """
        Create a Flutter player controls widget that integrates with an AudioService provider.

        Requirements:
        1. Play/pause button with loading state
        2. Skip previous/next buttons
        3. Seek bar with time display
        4. Modern Material Design 3 styling
        5. Proper Consumer/Provider integration
        6. Responsive design
        7. Accessibility support

        Generate complete Dart code with proper imports and documentation.
        Make it reusable and customizable.
        """

        response = await self.execute_llm_task(prompt)
        controls_code = response.get('content', '')

        await self.share_code_snippet(
            snippet=controls_code,
            description="AI-generated player controls widget with Material Design 3 styling",
            language="dart",
            file_path="lib/widgets/player_controls.dart"
        )

        # Generate interface information
        interface_prompt = """
        Based on the PlayerControls widget I created, list the key properties and methods
        that the UI team needs to know about for integration.
        """

        interface_response = await self.execute_llm_task(interface_prompt)

        await self.share_code_interface(
            interface_name="PlayerControlsWidget",
            methods=interface_response.get('content', '').split('\n'),
            description="Player controls widget interface for UI integration"
        )

        await self.report_progress(
            task="Player Controls Widget",
            percentage=100,
            details="Player controls widget generated and ready for UI integration"
        )

        return {"widget": "PlayerControls", "ui_integration": "ready"}

    async def execute_llm_task(self, prompt: str) -> Dict[str, Any]:
        """Execute an LLM task and return the response."""
        try:
            # Add collaboration context to the prompt
            context_prompt = f"""
            {self.collaboration_prompt or ""}

            Task: {prompt}

            As the Flutter Audio Agent, provide a complete, production-ready audio solution.
            Focus on robust audio playback, streaming capabilities, and seamless integration.
            Follow Flutter audio best practices and use appropriate audio plugins.

            Respond with clean, well-documented Dart/Flutter code that is ready to use.
            """

            # Use the agent's execute method which handles LLM calls properly
            response = await self.execute(context_prompt)

            return {"content": response, "success": True}

        except Exception as e:
            logger.error(f"Audio LLM task execution failed: {e}")
            return {"content": f"Error generating content: {e}", "success": False}

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

def create_flutter_audio_agent(progress_board=None):
    """Factory function to create Flutter Audio Agent."""
    return FlutterAudioAgent(progress_board=progress_board)
