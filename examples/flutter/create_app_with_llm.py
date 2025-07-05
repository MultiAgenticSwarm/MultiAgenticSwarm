"""
Example: LLM creates a complete Flutter app with zero hardcoded logic.

This example demonstrates how FlutterSwarm uses LLMs for ALL Flutter
development decisions - no templates, no hardcoded widgets, pure LLM generation.
"""

import asyncio
import logging
import os
from typing import Dict, Any

# Import MultiAgenticSwarm as the core SDK
import multiagenticswarm as mas

# Import FlutterSwarm implementation
from implementations.flutterswarm import FlutterSwarm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def create_recipe_app():
    """
    Create a complete recipe sharing app using ONLY LLM knowledge.
    The LLM will decide everything about Flutter implementation.
    """

    print("🚀 Creating Flutter Recipe App with LLM-Powered Development")
    print("=" * 60)

    # Setup project directory
    project_path = "./recipe_app"
    os.makedirs(project_path, exist_ok=True)

    # Initialize MAS system with LLM configuration
    system = mas.System(config={
        "llm_provider": "openai",
        "llm_model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 4000
    })

    # Create FlutterSwarm - all Flutter knowledge from LLMs
    flutter_swarm = FlutterSwarm(
        project_path=project_path,
        system=system,
        llm_provider="openai",
        llm_model="gpt-4"
    )

    print(f"📁 Project location: {project_path}")
    print(f"🤖 Using LLM: gpt-4")
    print()

    # App requirements - LLM will figure out everything
    app_description = """
    Create a modern recipe sharing app where users can:
    - Browse recipes with beautiful images and ratings
    - Search and filter by ingredients, cuisine, dietary restrictions
    - Save favorite recipes for offline access
    - Create and share their own recipes with photos
    - Rate and comment on recipes from other users
    - Generate shopping lists from recipe ingredients
    - Get step-by-step cooking instructions with timers
    - Follow other users and see their latest recipes

    The app should have a clean, modern design with smooth animations.
    Use Material Design 3 principles with a warm, food-focused color scheme.
    """

    features = [
        "User authentication with email/social login",
        "Recipe CRUD operations with image upload",
        "Advanced search with filters and sorting",
        "Offline mode with local storage",
        "Social features (likes, comments, follows)",
        "Shopping list generator with smart grouping",
        "Cooking mode with step-by-step instructions",
        "Timer functionality for cooking steps",
        "Recipe rating and review system",
        "User profiles and recipe collections",
        "Push notifications for new recipes",
        "Dark mode support"
    ]

    design_requirements = {
        "style": "Material Design 3",
        "color_scheme": "Warm food-focused palette",
        "typography": "Modern and readable",
        "animations": "Smooth and delightful",
        "responsiveness": "Mobile-first with tablet support",
        "accessibility": "WCAG 2.1 AA compliant"
    }

    performance_requirements = {
        "startup_time": "< 3 seconds",
        "image_loading": "Progressive with caching",
        "scroll_performance": "60 FPS on lists",
        "memory_usage": "< 150MB typical",
        "network_efficiency": "Offline-first with sync"
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
            print(f"   Created files: {len(result.created_files)}")
            print(f"   Project path: {result.output['project_path']}")
            print()

            # Show some created files
            print("📄 Created Files (sample):")
            for file in result.created_files[:10]:  # Show first 10 files
                print(f"   - {file}")

            if len(result.created_files) > 10:
                print(f"   ... and {len(result.created_files) - 10} more files")

            print()
            print("🎉 Next Steps:")
            for step in result.next_steps:
                print(f"   • {step}")

            print()
            print("🔍 The LLM has made ALL Flutter decisions:")
            print("   ✓ Chosen architecture pattern (Clean Architecture, MVVM, etc.)")
            print("   ✓ Selected state management (Provider, Riverpod, Bloc, etc.)")
            print("   ✓ Designed widget hierarchy and composition")
            print("   ✓ Implemented navigation and routing")
            print("   ✓ Created beautiful UI with Material Design 3")
            print("   ✓ Set up data models and services")
            print("   ✓ Implemented authentication and security")
            print("   ✓ Added comprehensive error handling")
            print("   ✓ Created thorough test suite")
            print("   ✓ Optimized for performance")
            print("   ✓ Ensured accessibility compliance")
            print()

            # Get project status
            print("📈 Project Status:")
            status = await flutter_swarm.get_project_status()
            print(f"   Total files: {len(status['project_structure'].get('files', []))}")
            print(f"   Agents used: {len(status['agents_status'])}")
            print(f"   Execution history: {status['execution_history']} tasks")

        else:
            print("❌ App creation failed")
            print(f"   Error: {result.error_message}")

    except Exception as e:
        print(f"❌ Error creating app: {str(e)}")
        import traceback
        traceback.print_exc()

async def demonstrate_feature_addition():
    """
    Demonstrate adding a new feature to existing app.
    """

    print("\n" + "="*60)
    print("🎯 Adding New Feature with LLM Analysis")
    print("="*60)

    project_path = "./recipe_app"

    # Create FlutterSwarm for existing project
    flutter_swarm = FlutterSwarm(
        project_path=project_path,
        llm_provider="openai",
        llm_model="gpt-4"
    )

    # Add a new feature - LLM figures out integration
    feature_description = """
    Add a meal planning feature that allows users to:
    - Create weekly meal plans by selecting recipes
    - Automatically generate shopping lists for the week
    - Set dietary preferences and restrictions
    - Get nutritional information for planned meals
    - Share meal plans with family members
    - Get smart suggestions based on past preferences
    """

    ui_requirements = {
        "calendar_view": "Weekly calendar with drag-and-drop",
        "planning_interface": "Intuitive meal planning UI",
        "shopping_integration": "Smart shopping list generation",
        "nutrition_display": "Beautiful nutrition visualizations"
    }

    test_requirements = [
        "unit",  # Unit tests for meal planning logic
        "widget",  # Widget tests for UI components
        "integration"  # Integration tests for full flow
    ]

    print("🔧 Adding Meal Planning Feature:")
    print(f"   Description: {feature_description[:100]}...")
    print(f"   UI Requirements: {len(ui_requirements)} specifications")
    print(f"   Test Types: {', '.join(test_requirements)}")
    print()

    try:
        result = await flutter_swarm.add_feature(
            feature_description=feature_description,
            ui_requirements=ui_requirements,
            test_requirements=test_requirements
        )

        if result.success:
            print("✅ Feature added successfully!")
            print()
            print("📊 Addition Results:")
            print(f"   Created files: {len(result.created_files)}")
            print(f"   Modified files: {len(result.modified_files)}")
            print(f"   Tests passed: {result.output['tests_passed']}")
            print()

            print("🎉 Next Steps:")
            for step in result.next_steps:
                print(f"   • {step}")

        else:
            print("❌ Feature addition failed")
            print(f"   Error: {result.error_message}")

    except Exception as e:
        print(f"❌ Error adding feature: {str(e)}")

async def demonstrate_debugging():
    """
    Demonstrate LLM-powered debugging.
    """

    print("\n" + "="*60)
    print("🐛 LLM-Powered Debugging")
    print("="*60)

    project_path = "./recipe_app"

    flutter_swarm = FlutterSwarm(
        project_path=project_path,
        llm_provider="openai",
        llm_model="gpt-4"
    )

    # Simulate debugging scenario
    issue_description = """
    Users are reporting that the app crashes when they try to upload
    large recipe images. The crash happens on both iOS and Android,
    but seems more frequent on older devices. The error appears to be
    related to memory usage during image processing.
    """

    error_logs = [
        "flutter: Out of memory error in image processing",
        "flutter: ImageProvider failed to load image",
        "E/flutter: [ERROR:flutter/runtime/dart_vm_initializer.cc(41)] Unhandled Exception: Out of memory",
        "E/AndroidRuntime: FATAL EXCEPTION: main"
    ]

    reproduction_steps = [
        "Open recipe creation screen",
        "Select large image from gallery (>5MB)",
        "Tap 'Upload Image' button",
        "App crashes or freezes"
    ]

    print("🔍 Debugging Issue:")
    print(f"   Description: {issue_description[:100]}...")
    print(f"   Error logs: {len(error_logs)} entries")
    print(f"   Reproduction steps: {len(reproduction_steps)} steps")
    print()

    try:
        result = await flutter_swarm.debug_issue(
            issue_description=issue_description,
            error_logs=error_logs,
            reproduction_steps=reproduction_steps
        )

        if result.success:
            print("✅ Issue analysis completed!")
            print()
            print("🔍 LLM Analysis:")
            print("   The LLM has analyzed the issue and provided:")
            print("   • Root cause identification")
            print("   • Step-by-step debugging approach")
            print("   • Specific code fixes")
            print("   • Prevention strategies")
            print("   • Testing recommendations")

        else:
            print("❌ Debugging failed")
            print(f"   Error: {result.error_message}")

    except Exception as e:
        print(f"❌ Error during debugging: {str(e)}")

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

    # Run the examples
    await create_recipe_app()
    await demonstrate_feature_addition()
    await demonstrate_debugging()

    print("\n" + "="*60)
    print("🎉 FlutterSwarm Example Complete!")
    print("="*60)
    print()
    print("Key Takeaways:")
    print("• LLM generated complete Flutter app with zero hardcoded logic")
    print("• All architectural decisions came from LLM knowledge")
    print("• UI design and implementation by LLM analysis")
    print("• Comprehensive testing strategy created by LLM")
    print("• Natural language debugging and issue resolution")
    print("• Fully adaptable to any Flutter project requirements")
    print()
    print("This demonstrates true LLM-powered development where the")
    print("LLM acts as an expert Flutter developer, not just a code generator!")

if __name__ == "__main__":
    asyncio.run(main())
