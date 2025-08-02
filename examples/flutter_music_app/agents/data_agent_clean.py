"""
Flutter Data Agent - Specialized agent for data models and state management.
"""

from typing import Dict, Any
from multiagenticswarm.core.collaborative_system import UniversalAgent
from multiagenticswarm.utils.logger import get_logger

logger = get_logger(__name__)


class FlutterDataAgent(UniversalAgent):
    """
    Specialized agent for Flutter data models and state management.

    Focuses on:
    - Data model design and implementation
    - State management solutions
    - Data persistence and storage
    - API integration and data services
    """

    def __init__(self, progress_board=None):
        super().__init__(
            name="Flutter_Data_Agent",
            description="Handles data models, state management, and app architecture",
            system_prompt="""You are an expert in Flutter data architecture working in a collaborative team. Your role:

PRIMARY RESPONSIBILITIES:
- Design and implement comprehensive data models
- Create efficient state management solutions
- Handle data persistence, storage, and synchronization
- Build API integration layers and data services
- Manage app configuration, settings, and user preferences

COLLABORATION GUIDELINES:
- Share data model interfaces early with all agents
- Coordinate with UI Agent on state management integration
- Work with Audio Agent on audio-related data structures
- Provide data architecture guidance and best practices
- Request help when complex integrations are needed

TECHNICAL FOCUS:
- Clean data model design (Track, Playlist, User, etc.)
- State management (Provider, Riverpod, Bloc, etc.)
- Local storage and data persistence (Hive, SQLite, etc.)
- API integration and data synchronization
- App configuration and user settings management

COLLABORATION TOOLS AVAILABLE:
- post_update(): Share data development progress
- share_interface(): Share data model interfaces
- share_code_snippet(): Share data implementation code
- request_help(): Ask for UI/audio integration help
- coordinate_with_team(): Coordinate data architecture
- report_progress(): Track data development progress

Always read the collaboration prompt first to understand the project context and your role.
Prioritize data integrity, performance, and maintainable architecture.

When tasked with creating Flutter data components, analyze the requirements and generate appropriate Dart code.
Focus on creating production-ready, well-documented code that follows Flutter best practices.""",
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
            progress_board=progress_board
        )

        # Data-specific capabilities
        self.data_specializations = [
            "Data Modeling",
            "State Management",
            "Data Persistence",
            "API Integration",
            "Configuration Management",
            "User Preferences",
            "Data Synchronization"
        ]

        logger.info("FlutterDataAgent initialized with data specializations")

    async def create_data_models(self) -> dict:
        """Create core data models for the music app using LLM reasoning."""
        await self.report_progress(
            task="Data Models Creation",
            percentage=20,
            details="Analyzing requirements and generating core data models"
        )

        # Use LLM to generate Track model
        track_prompt = """
        Create a comprehensive Track data model for a Flutter music streaming app.

        Requirements:
        1. Include all essential track properties (id, title, artist, album, url, etc.)
        2. Add music-specific fields (duration, artwork, genre, release date)
        3. Include user-specific fields (isLiked, playCount, lastPlayed)
        4. Add offline/download capabilities (isDownloaded, localPath)
        5. Use JSON serialization with json_annotation
        6. Include copyWith method for immutable updates
        7. Proper equals, hashCode, and toString methods
        8. Add validation and error handling

        Generate complete Dart code with all imports and proper documentation.
        """

        track_response = await self.execute_llm_task(track_prompt)
        track_code = track_response.get('content', '')

        await self.share_code_snippet(
            snippet=track_code,
            description="AI-generated Track data model with comprehensive music properties",
            language="dart",
            file_path="lib/models/track.dart"
        )

        # Use LLM to generate Playlist model
        playlist_prompt = """
        Create a comprehensive Playlist data model for a Flutter music streaming app.

        Requirements:
        1. Reference the Track model I just created
        2. Include playlist metadata (name, description, image, creation date)
        3. Support track management (add, remove, reorder)
        4. Include sharing and privacy settings
        5. Add playlist statistics (total duration, track count)
        6. Use JSON serialization
        7. Include proper copyWith and utility methods
        8. Support different playlist types (user-created, system, favorites)

        Generate complete Dart code with all necessary methods.
        """

        playlist_response = await self.execute_llm_task(playlist_prompt)
        playlist_code = playlist_response.get('content', '')

        await self.share_code_snippet(
            snippet=playlist_code,
            description="AI-generated Playlist data model with track management",
            language="dart",
            file_path="lib/models/playlist.dart"
        )

        # Use LLM to generate User model
        user_prompt = """
        Create a User data model for a Flutter music streaming app.

        Requirements:
        1. User authentication fields (id, email, username)
        2. Profile information (name, avatar, bio)
        3. Music preferences and settings
        4. Subscription/premium status
        5. User statistics (total listening time, favorite genres)
        6. Social features (followers, following, public playlists)
        7. JSON serialization support
        8. Privacy and settings management

        Generate complete Dart code with proper validation.
        """

        user_response = await self.execute_llm_task(user_prompt)
        user_code = user_response.get('content', '')

        await self.share_code_snippet(
            snippet=user_code,
            description="AI-generated User data model with profile and preferences",
            language="dart",
            file_path="lib/models/user.dart"
        )

        # Generate interfaces for the models
        interface_prompt = """
        Based on the Track, Playlist, and User models I just created,
        list the main methods and properties that other parts of the app
        will use to interact with these models.
        """

        interface_response = await self.execute_llm_task(interface_prompt)

        await self.share_code_interface(
            interface_name="DataModels",
            methods=interface_response.get('content', '').split('\n'),
            description="Core data model interfaces for app-wide usage"
        )

        await self.report_progress(
            task="Data Models Creation",
            percentage=75,
            details="Core data models generated: Track, Playlist, User"
        )

        return {"models_created": ["Track", "Playlist", "User"], "status": "generated"}

    async def create_state_management(self) -> dict:
        """Create state management solution using LLM reasoning."""
        prompt = """
        Create a comprehensive state management solution for a Flutter music streaming app using Provider.

        Requirements:
        1. AudioProvider for music playback state
        2. PlaylistProvider for playlist management
        3. UserProvider for user data and preferences
        4. LibraryProvider for user's music library
        5. SearchProvider for search functionality
        6. DownloadProvider for offline music management
        7. SettingsProvider for app configuration

        For each provider:
        - Use ChangeNotifier pattern
        - Include proper state updates with notifyListeners()
        - Add loading states and error handling
        - Include async operations for API calls
        - Add local storage integration

        Generate complete Dart code for all providers with proper documentation.
        """

        response = await self.execute_llm_task(prompt)
        providers_code = response.get('content', '')

        await self.share_code_snippet(
            snippet=providers_code,
            description="AI-generated Provider-based state management system",
            language="dart",
            file_path="lib/providers/app_providers.dart"
        )

        return {"state_management": "Provider", "providers_count": 7, "status": "generated"}

    async def create_data_services(self) -> dict:
        """Create data services and API integration using LLM reasoning."""
        prompt = """
        Create comprehensive data services for a Flutter music streaming app.

        Services needed:
        1. MusicApiService - Main API integration for music data
        2. UserService - User authentication and profile management
        3. PlaylistService - Playlist CRUD operations
        4. SearchService - Music search functionality
        5. DownloadService - Offline music management
        6. CacheService - Data caching and optimization
        7. SyncService - Data synchronization between local and remote

        For each service:
        - Use Dio for HTTP requests
        - Include proper error handling and retry logic
        - Add request/response interceptors
        - Include offline support where appropriate
        - Add proper logging and debugging
        - Use repository pattern for data access

        Generate complete Dart code with proper abstraction and documentation.
        """

        response = await self.execute_llm_task(prompt)
        services_code = response.get('content', '')

        await self.share_code_snippet(
            snippet=services_code,
            description="AI-generated data services with API integration and caching",
            language="dart",
            file_path="lib/services/data_services.dart"
        )

        return {"services_created": 7, "api_integration": "complete", "status": "generated"}

    async def create_local_storage(self) -> dict:
        """Create local storage and persistence layer using LLM reasoning."""
        prompt = """
        Create a comprehensive local storage system for a Flutter music streaming app.

        Requirements:
        1. Use Hive for fast local storage
        2. Create adapters for Track, Playlist, User models
        3. Implement DatabaseService for CRUD operations
        4. Add cache management for API responses
        5. Include offline data synchronization
        6. Add data migration and versioning
        7. Include data export/import functionality
        8. Add storage optimization and cleanup

        Features to implement:
        - User preferences and settings storage
        - Downloaded music metadata storage
        - Playlist caching for offline access
        - Search history and recent tracks
        - User statistics and analytics data

        Generate complete Dart code with proper initialization and error handling.
        """

        response = await self.execute_llm_task(prompt)
        storage_code = response.get('content', '')

        await self.share_code_snippet(
            snippet=storage_code,
            description="AI-generated local storage system with Hive and caching",
            language="dart",
            file_path="lib/services/storage_service.dart"
        )

        return {"storage_system": "Hive", "offline_support": True, "status": "generated"}

    async def execute_llm_task(self, prompt: str) -> Dict[str, Any]:
        """Execute an LLM task and return the response."""
        try:
            # Add collaboration context to the prompt
            context_prompt = f"""
            {self.collaboration_prompt or ""}

            Task: {prompt}

            As the Flutter Data Agent, provide a complete, production-ready solution.
            Focus on data integrity, performance, and maintainable architecture.
            Ensure compatibility with the audio and UI components being developed by other agents.
            """

            # Make the actual LLM call through the agent's provider
            self.add_to_memory("user", context_prompt)

            # Use the agent's LLM provider to generate response
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend([{"role": m["role"], "content": m["content"]} for m in self.memory])

            response = await self.llm_provider.execute(messages)

            # Store response in memory
            self.add_to_memory("assistant", response.content)

            return {"content": response.content, "usage": response.usage}

        except Exception as e:
            logger.error(f"Error executing LLM task: {e}")
            return {"content": f"Error generating content: {e}", "usage": None}


def create_flutter_data_agent(progress_board=None) -> FlutterDataAgent:
    """Create a Flutter Data Agent instance."""
    return FlutterDataAgent(progress_board=progress_board)
