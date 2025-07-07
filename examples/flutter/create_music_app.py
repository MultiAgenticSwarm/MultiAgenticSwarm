#!/usr/bin/env python3
"""
Basic Music App Creator using FlutterSwarm
This is a test script to verify FlutterSwarm functionality.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import dotenv

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("flutterswarm_music_app")

# Load environment variables from .env file
dotenv.load_dotenv()
# Ensure the script is run from the project root
# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Explicitly set up logging directory for FlutterSwarm
log_dir = os.path.join(project_root, "logs")
os.makedirs(log_dir, exist_ok=True)

# Import MultiAgenticSwarm for logging setup
try:
    import multiagenticswarm as mas
    from multiagenticswarm.logging import setup_logging
    from multiagenticswarm.utils.logger import get_logger

    # Setup comprehensive logging with verbose mode and specific log directory
    log_config = setup_logging(
        verbose=True, log_directory=log_dir, enable_json_logs=True
    )
    print(f"✓ Comprehensive logging initialized:")
    print(json.dumps(log_config, indent=2))

    # Use direct import of get_logger for comprehensive logging
    logger = get_logger("flutterswarm_music_app")
    logger.info("Starting music app creation with FlutterSwarm")
except ImportError as e:
    print(f"✗ Failed to initialize MultiAgenticSwarm: {e}")
    sys.exit(1)

# Make sure logs directory exists and is writable
if not os.path.exists(log_dir):
    print(f"Creating logs directory: {log_dir}")
    os.makedirs(log_dir, exist_ok=True)

print(f"Logs will be stored in: {log_dir}")

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

    # Initialize FlutterSwarm with explicit logging configuration
    try:
        # Create a detailed log file for this specific run
        app_log_file = os.path.join(
            log_dir,
            f"flutter_music_app_creation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        )
        with open(app_log_file, "w") as f:
            f.write(f"=== Flutter Music App Creation Log ===\n")
            f.write(f"Started at: {datetime.now().isoformat()}\n")
            f.write(f"Project path: {project_path}\n")
            f.write(f"App name: {app_name}\n\n")

        print(f"✓ Created detailed log file: {app_log_file}")

        # Function to append to the log file
        def log_to_file(message):
            with open(app_log_file, "a") as f:
                timestamp = datetime.now().isoformat()
                f.write(f"[{timestamp}] {message}\n")

        # Log initialization
        log_to_file("Initializing FlutterSwarm...")

        # Initialize FlutterSwarm
        flutter_swarm = FlutterSwarm(
            project_path=project_path,
            llm_provider="anthropic",  # Change to your preferred provider
            llm_model="claude-3-5-sonnet-20240620",  # Use a valid and current model
            temperature=0.7,
            enable_comprehensive_logging=True,
            verbose_logging=True,
            log_directory=log_dir,
        )

        log_to_file("FlutterSwarm initialized successfully")
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
        "minimalist_design",
    ]

    design_requirements = {
        "style": "Material Design",
        "theme": "dark",
        "responsive": True,
        "minimalist": True,
    }

    # Create the app
    try:
        print("🚀 Starting app creation...")

        # Log the app creation request
        log_to_file("Starting app creation with the following parameters:")
        log_to_file(f"App description: {app_description}")
        log_to_file(f"Features: {features}")
        log_to_file(f"Platforms: [android, ios]")
        log_to_file(f"Design requirements: {design_requirements}")

        # Start capturing all output
        import io
        import sys

        original_stdout = sys.stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output

        # Create the app
        result = await flutter_swarm.create_app(
            app_description=app_description,
            features=features,
            platforms=["android", "ios"],
            design_requirements=design_requirements,
            performance_requirements={"startup_time": "fast", "memory_usage": "low"},
        )

        # Restore stdout and get captured output
        sys.stdout = original_stdout
        output = captured_output.getvalue()

        # Log the captured output
        log_to_file("Captured output during app creation:")
        log_to_file(output)

        # Print the output to console
        print(output)

        if result.success:
            print("✓ App creation completed successfully!")
            print(f"Execution time: {result.execution_time:.2f}s")

            # Log successful completion
            log_to_file(
                f"App creation completed successfully in {result.execution_time:.2f}s"
            )

            # Display and log results from each agent
            if isinstance(result.output, dict):
                for agent_name, agent_output in result.output.items():
                    print(f"✓ {agent_name.title()} completed")
                    log_to_file(f"Agent '{agent_name}' completed successfully")

                    # Log detailed agent output
                    try:
                        import json

                        log_to_file(
                            f"Output from {agent_name}: {json.dumps(agent_output, indent=2)}"
                        )
                    except:
                        log_to_file(f"Output from {agent_name}: {str(agent_output)}")

            # Display and log file creation info
            metadata = result.metadata or {}
            created_files = metadata.get("created_files", [])
            modified_files = metadata.get("modified_files", [])

            if created_files:
                print(f"✓ Created {len(created_files)} files")
                log_to_file(f"Created {len(created_files)} files:")
                for file in created_files:
                    log_to_file(f"  - {file}")

            if modified_files:
                print(f"✓ Modified {len(modified_files)} files")
                log_to_file(f"Modified {len(modified_files)} files:")
                for file in modified_files:
                    log_to_file(f"  - {file}")

            # Final log entry
            log_to_file("=== App creation completed successfully ===")

            return True
        else:
            error_msg = f"App creation failed: {result.error_message}"
            print(f"✗ {error_msg}")

            # Log failure
            log_to_file(f"ERROR: {error_msg}")
            if hasattr(result, "traceback"):
                log_to_file(f"Traceback: {result.traceback}")

            log_to_file("=== App creation failed ===")
            return False

    except Exception as e:
        print(f"✗ App creation error: {e}")

        # Log the exception
        log_to_file(f"CRITICAL ERROR: App creation exception: {e}")

        # Log traceback for debugging
        import traceback

        tb = traceback.format_exc()
        log_to_file(f"Traceback:\n{tb}")

        # Final error entry
        log_to_file("=== App creation failed with exception ===")

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

    llm_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
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
