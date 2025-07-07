#!/usr/bin/env python3
"""
Simple Flutter Music App Creator with guaranteed logging.
This version ensures logs are created no matter what.
"""

import asyncio
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

# Set up basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create log directory
project_root = Path(__file__).parent.parent.parent
log_dir = os.path.join(project_root, "logs")
os.makedirs(log_dir, exist_ok=True)

# Import MultiAgenticSwarm for proper logging
sys.path.insert(0, str(project_root))
try:
    import multiagenticswarm as mas
    from multiagenticswarm.logging import setup_logging

    # Setup comprehensive logging
    log_config = setup_logging(
        verbose=True, log_directory=log_dir, enable_json_logs=True
    )

    print(f"🔍 Comprehensive logging initialized")
    print(f"📁 Log directory: {log_config.get('log_directory', 'None')}")

    # Import the logger directly from utils
    from multiagenticswarm.utils.logger import get_logger

    logger = get_logger("flutterswarm_demo")
    logger.info(
        "Starting FlutterSwarm music app creation test", {"script_path": __file__}
    )
except ImportError as e:
    print(f"Failed to initialize MultiAgenticSwarm logging: {e}")
    sys.exit(1)

# Add project root to Python path
sys.path.insert(0, str(project_root))


async def create_simple_music_app():
    """Create a simple music app with Flutter using FlutterSwarm"""

    # Import FlutterSwarm - log any errors
    try:
        from implementations.flutterswarm import FlutterSwarm

        logger.info("FlutterSwarm imported successfully")
    except Exception as e:
        logger.error(
            f"Failed to import FlutterSwarm: {e}", {"traceback": traceback.format_exc()}
        )
        print(f"✗ Failed to import FlutterSwarm: {e}")
        return False

    # Set up app parameters
    app_name = "simple_flutter_demo"
    project_path = os.path.join(project_root, app_name)
    os.makedirs(project_path, exist_ok=True)

    logger.info(f"Created project directory: {project_path}")

    # Initialize FlutterSwarm
    try:
        # Log initialization attempt
        logger.info(
            "Initializing FlutterSwarm",
            {"project_path": project_path, "app_name": app_name},
        )

        # Create the FlutterSwarm instance
        flutter_swarm = FlutterSwarm(
            project_path=project_path,
            llm_provider="openai",  # Change as needed
            llm_model="gpt-4",  # Change as needed
            temperature=0.7,
        )

        logger.info("FlutterSwarm initialized successfully")
        print("✓ FlutterSwarm initialized")

    except Exception as e:
        logger.error(
            f"Failed to initialize FlutterSwarm: {e}",
            {"traceback": traceback.format_exc()},
        )
        print(f"✗ Failed to initialize FlutterSwarm: {e}")
        return False

    # Define a simple app description
    app_description = """
    Create a minimal music player app with:
    1. Play/pause button
    2. Song title display
    3. Simple progress bar
    """

    # Log the app description
    logger.info("App description defined", {"description": app_description})

    # Create the app
    try:
        logger.info("Starting app creation")
        print("🚀 Creating music app...")

        # Track start time
        start_time = datetime.now()

        # Create the app
        result = await flutter_swarm.create_app(
            app_description=app_description,
            features=["play_button", "title_display", "progress_bar"],
            platforms=["android", "ios"],
            design_requirements={"minimalist": True},
        )

        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()

        # Log result
        logger.info(
            "App creation completed",
            {
                "success": getattr(result, "success", False),
                "duration_seconds": duration,
                "output": getattr(result, "output", {}),
                "error": getattr(result, "error_message", None),
            },
        )

        print(f"✓ App creation completed in {duration:.2f} seconds")
        return True

    except Exception as e:
        logger.error(f"App creation failed: {e}", {"traceback": traceback.format_exc()})
        print(f"✗ App creation failed: {e}")
        return False


async def main():
    """Main entry point"""
    print(f"Starting FlutterSwarm logging test at {datetime.now().isoformat()}")

    try:
        success = await create_simple_music_app()

        if success:
            print("✅ Test completed successfully")
            logger.info("Test completed successfully")
        else:
            print("❌ Test failed")
            logger.error("Test failed")

        # Get logging config to show log files
        from multiagenticswarm.logging import get_config

        config = get_config()

        if config and "log_directory" in config:
            log_dir = config["log_directory"]
            print(f"\nLog files are stored in: {log_dir}")
            log_files = [
                f
                for f in os.listdir(log_dir)
                if os.path.isfile(os.path.join(log_dir, f))
            ]
            print(f"Found {len(log_files)} log files:")
            for i, file in enumerate(
                sorted(
                    log_files,
                    key=lambda x: os.path.getmtime(os.path.join(log_dir, x)),
                    reverse=True,
                )[:5]
            ):
                print(
                    f"  {i+1}. {file} ({os.path.getsize(os.path.join(log_dir, file))} bytes)"
                )

        return success
    except Exception as e:
        print(f"Unhandled exception: {e}")
        logger.critical(
            f"Unhandled exception: {e}", {"traceback": traceback.format_exc()}
        )
        return False


if __name__ == "__main__":
    asyncio.run(main())
