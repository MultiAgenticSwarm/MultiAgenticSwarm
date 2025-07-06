#!/usr/bin/env python3
"""
Basic Music App Creator using FlutterSwarm
This is a test script to verify FlutterSwarm functionality.
"""

import os
import asyncio
import sys
from pathlib import Path

import dotenv
# Load environment variables from .env file
dotenv.load_dotenv()
# Ensure the script is run from the project root
# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from implementations.flutterswarm import FlutterSwarm
    print("✓ FlutterSwarm imported successfully")
except ImportError as e:
    print(f"✗ Failed to import FlutterSwarm: {e}")
    sys.exit(1)


async def create_basic_music_app():
    """Create a very basic music app with minimal features"""

    # Configuration
    app_name = "basic_music_player"
    project_path = os.path.join(os.getcwd(), app_name)

    print(f"Creating basic music app: {app_name}")
    print(f"Output directory: {project_path}")

    # Ensure output directory exists
    os.makedirs(project_path, exist_ok=True)
    print(f"✓ Output directory created/verified: {project_path}")

    # Initialize FlutterSwarm
    try:
        flutter_swarm = FlutterSwarm(
            project_path=project_path,
            llm_provider="anthropic",  # Change to your preferred provider
            llm_model="claude-3-5-sonnet-20241022",  # Use a suitable model
            temperature=0.7
        )
        print("✓ FlutterSwarm initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize FlutterSwarm: {e}")
        return False

    # Validate environment
    try:
        env_valid = await flutter_swarm.validate_environment()
        if not env_valid:
            print("✗ Flutter environment validation failed")
            return False
        print("✓ Flutter environment validated")
    except Exception as e:
        print(f"✗ Environment validation error: {e}")
        return False

    # Define the music app requirements
    app_description = """
    Create a very basic music player app with these minimal features:

    1. Simple UI with a play/pause button
    2. A song title display
    3. A basic progress bar (can be non-functional for now)
    4. A volume control slider
    5. Skip previous/next buttons
    6. Clean, minimalist Material Design

    The app doesn't need to actually play music - just the UI components.
    Focus on a clean, simple interface that demonstrates basic Flutter widgets.
    """

    features = [
        "play_pause_button",
        "song_title_display",
        "progress_bar_ui",
        "volume_slider",
        "skip_buttons",
        "minimalist_design"
    ]

    design_requirements = {
        "style": "Material Design",
        "theme": "dark",
        "responsive": True,
        "minimalist": True
    }

    # Create the app
    try:
        print("🚀 Starting app creation...")
        result = await flutter_swarm.create_app(
            app_description=app_description,
            features=features,
            platforms=["android", "ios"],
            design_requirements=design_requirements,
            performance_requirements={"startup_time": "fast", "memory_usage": "low"}
        )

        if result.success:
            print("✓ App creation completed successfully!")
            print(f"Output: {result.output}")
            return True
        else:
            print(f"✗ App creation failed: {result.error}")
            return False

    except Exception as e:
        print(f"✗ App creation error: {e}")
        return False


async def test_flutterswarm_basic():
    """Test basic FlutterSwarm functionality"""

    print("=" * 60)
    print("🎵 Basic Music App Creator - FlutterSwarm Test")
    print("=" * 60)

    # Check if we can import the required modules
    try:
        import multiagenticswarm as mas
        print("✓ MultiAgenticSwarm SDK available")
    except ImportError as e:
        print(f"✗ MultiAgenticSwarm SDK not available: {e}")
        return False

    # Test environment variables
    import os
    llm_key = os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
    if not llm_key:
        print("⚠️  Warning: No LLM API key found in environment variables")
        print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY for full functionality")
    else:
        print("✓ LLM API key found")

    # Create the app
    success = await create_basic_music_app()

    if success:
        print("\n" + "=" * 60)
        print("✅ FlutterSwarm test completed successfully!")
        print("✅ Basic music app created")
        print("=" * 60)

        # Provide next steps
        print("\n🎯 Next steps:")
        print("1. Navigate to the output directory")
        print("2. Run 'flutter pub get' to install dependencies")
        print("3. Run 'flutter run' to test the app")
        print("4. Check the generated code quality")

        return True
    else:
        print("\n" + "=" * 60)
        print("❌ FlutterSwarm test failed!")
        print("❌ Check the error messages above")
        print("=" * 60)
        return False


def main():
    """Main entry point"""
    try:
        # Run the async test
        success = asyncio.run(test_flutterswarm_basic())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
