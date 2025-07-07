#!/usr/bin/env python3
"""
Debug test for FlutterSwarm
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from implementations.agentswarm.core.types import TaskContext
from implementations.flutterswarm import FlutterSwarm


async def test_simple_architect():
    """Test just the architect agent"""

    # Configuration
    project_path = os.path.join(os.getcwd(), "test_debug_app")
    os.makedirs(project_path, exist_ok=True)

    # Initialize FlutterSwarm
    flutter_swarm = FlutterSwarm(
        project_path=project_path,
        llm_provider="anthropic",
        llm_model="claude-3-5-sonnet-20240620",
        temperature=0.7,
    )

    # Test just the architect
    requirements_analysis = {
        "app_description": "Simple music player with play/pause button",
        "features": ["play_button", "pause_button"],
        "platforms": ["android"],
        "design_requirements": {},
        "performance_requirements": {},
    }

    architect_context = TaskContext(
        project_path=project_path, metadata=requirements_analysis
    )

    print("Testing architect...")
    architect_result = await flutter_swarm.architect.design_architecture(
        requirements_analysis=requirements_analysis, context=architect_context
    )

    print(f"Architect success: {architect_result.success}")
    print(f"Architect output type: {type(architect_result.output)}")
    print(
        f"Architect output (first 200 chars): {str(architect_result.output)[:200]}..."
    )

    # Test extraction like the swarm does
    output_text = ""
    if hasattr(architect_result, "output"):
        if isinstance(architect_result.output, dict):
            # Look for common response keys
            for key in ["content", "response", "output", "message"]:
                if key in architect_result.output:
                    output_text = str(architect_result.output[key])
                    print(f"Found content in key '{key}': {output_text[:200]}...")
                    break
            if not output_text:
                output_text = str(architect_result.output)
        else:
            output_text = str(architect_result.output)

    # Test code parsing
    print(f"Extracted output contains 'python': {'python' in output_text.lower()}")
    print(f"Extracted output contains '```': {'```' in output_text}")

    # Show the full dict keys
    if isinstance(architect_result.output, dict):
        print(f"Dict keys: {list(architect_result.output.keys())}")

    return architect_result.success


if __name__ == "__main__":
    success = asyncio.run(test_simple_architect())
    sys.exit(0 if success else 1)
