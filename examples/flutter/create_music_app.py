"""
Example: LLM creates a complete Flutter music app with zero hardcoded logic.

This example demonstrates how FlutterSwarm uses LLMs for ALL Flutter
development decisions - no templates, no hardcoded widgets, pure LLM generation.
"""
import asyncio
import logging
import os
import traceback
from typing import Dict, Any

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import MultiAgenticSwarm as the core SDK
import multiagenticswarm as mas

# Import FlutterSwarm implementation
from implementations.flutterswarm import FlutterSwarm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def create_music_app():
    """
    Create a complete music app using ONLY LLM knowledge.
    The LLM will decide everything about Flutter implementation.
    """

    print("🚀 Creating Flutter Music App with LLM-Powered Development")
    print("=" * 60)

    # Setup project directory
    project_path = "./music_app"
    os.makedirs(project_path, exist_ok=True)

    # Initialize MAS system
    system = mas.System()

    # Create FlutterSwarm - all Flutter knowledge from LLMs
    flutter_swarm = FlutterSwarm(
        project_path=project_path,
        system=system,
        llm_provider="anthropic",
        llm_model="claude-3-opus-20240229",
        temperature=0.7,
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    print(f"📁 Project location: {project_path}")
    print(f"🤖 Using LLM: claude-3-opus-20240229")
    print()

    # App requirements - LLM will figure out everything
    app_description = """
    A beautiful and performant music streaming app that allows users to:
    - Discover new music and browse curated playlists.
    - Search for tracks, artists, and albums.
    - Create and manage personal playlists.
    - Download music for offline playback.
    - Enjoy high-quality audio streaming.
    - View lyrics in real-time.
    - Get personalized recommendations.
    """

    features = [
        "User authentication (email/password, social login)",
        "Music streaming from a remote source (mocked API)",
        "Search functionality for tracks, artists, and albums",
        "Playlist creation, modification, and deletion",
        "Offline music download and playback",
        "Real-time synchronized lyrics display",
        "Personalized music recommendations based on listening history",
        "Audio playback controls (play, pause, skip, seek)",
        "Now Playing screen with album art",
        "Support for background audio playback",
        "Dark mode and light mode themes",
    ]

    design_requirements = {
        "style": "Sleek, modern, and immersive UI",
        "color_scheme": "Dark-themed with vibrant accent colors",
        "typography": "Clean and legible fonts",
        "animations": "Smooth transitions and micro-interactions",
        "responsiveness": "Optimized for various screen sizes on iOS and Android",
        "accessibility": "High contrast and screen reader support",
    }

    performance_requirements = {
        "startup_time": "< 2 seconds",
        "track_loading": "< 1 second for streaming",
        "ui_performance": "60 FPS for all animations and scrolling",
        "offline_database": "Efficient querying for downloaded music",
        "battery_usage": "Optimized for long listening sessions",
    }

    print("📋 App Requirements:")
    print(f"   Description: {app_description[:100]}...")
    print(f"   Features: {len(features)} features")
    print(f"   Platforms: iOS, Android")
    print()

    # Create the app - LLM makes ALL decisions
    print("🎯 Creating app with LLM-driven development...")

    try:
        result = await flutter_swarm.create_app(
            app_description=app_description,
            features=features,
            platforms=["ios", "android"],
            design_requirements=design_requirements,
            performance_requirements=performance_requirements
        )

        if result.success:
            print("✅ App created successfully!")
            print()
            print("📊 Creation Results:")
            print(f"   Created files: {len(result.created_files) if hasattr(result, 'created_files') else 'Unknown'}")
            print(f"   Project path: {project_path}")
            print()

            # Show some created files
            print("📄 Created Files (sample):")
            if hasattr(result, 'created_files') and result.created_files:
                for file_path in result.created_files[:5]:
                    print(f"   - {file_path}")
            else:
                print("   - Files created in project directory")

        else:
            print(f"❌ App creation failed: {result.error}")
            print(f"   Details: {result.details}")

    except Exception as e:
        print(f"❌ Error creating app: {str(e)}")
        traceback.print_exc()

    # Run the app
    print("\n▶️ Running the app...")
    try:
        process = await asyncio.create_subprocess_shell(
            "flutter run",
            cwd=project_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            print("✅ App is running successfully.")
            print(stdout.decode())
        else:
            print("❌ App failed to run.")
            print(stderr.decode())
    except FileNotFoundError:
        print("❌ 'flutter' command not found. Please ensure Flutter SDK is installed and in your PATH.")
    except Exception as e:
        print(f"❌ Error running app: {str(e)}")


async def main():
    """
    Main example demonstrating LLM-powered Flutter development.
    """

    print("🌟 FlutterSwarm: LLM-Powered Flutter Development")
    print("=" * 60)
    print()
    print("This example demonstrates how FlutterSwarm uses LLMs for")
    print("ALL Flutter development decisions:")
    print()
    print("✨ Key Features:")
    print("   • No hardcoded Flutter patterns or widgets")
    print("   • LLM chooses architecture and state management")
    print("   • LLM designs UI and implements features")
    print("   • LLM creates tests and debugging solutions")
    print("   • Tools are just CLI interfaces")
    print("   • Adapts to any Flutter project structure")
    print()
    print("🎯 The LLM makes decisions about:")
    print("   • Widget selection and composition")
    print("   • State management patterns")
    print("   • Navigation and routing")
    print("   • UI/UX design and theming")
    print("   • Performance optimizations")
    print("   • Testing strategies")
    print("   • Error handling approaches")
    print()

    # Run the example
    await create_music_app()

    print("\n" + "="*60)
    print("🎉 FlutterSwarm Example Complete!")
    print("="*60)
    print()
    print("Key Takeaways:")
    print("• LLM generated complete Flutter music app with zero hardcoded logic")
    print("• All architectural decisions came from LLM knowledge")
    print("• UI design and implementation by LLM analysis")
    print("• Comprehensive testing strategy created by LLM")
    print("• Fully adaptable to any Flutter project requirements")
    print()
    print("This demonstrates true LLM-powered development where the")
    print("LLM acts as an expert Flutter developer, not just a code generator!")

if __name__ == "__main__":
    # Ensure you have ANTHROPIC_API_KEY set in your environment
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY environment variable not set.")
        print("   Please set it to your Anthropic API key.")
    else:
        asyncio.run(create_music_app())
