"""
FlutterSwarm - LLM-powered Flutter development using MultiAgenticSwarm SDK.

ALL Flutter knowledge and decisions come from LLMs.
No hardcoded Flutter logic - only CLI tool interfaces.
"""

# Import required MultiAgenticSwarm module
import multiagenticswarm as mas
from multiagenticswarm.logging import setup_logging
from multiagenticswarm.utils.logger import MultiAgenticSwarmLogger, get_logger

# Initialize logger using MAS logging
logger = get_logger("flutterswarm")
logger.info("FlutterSwarm module initialized")

from .agents import (
    FlutterArchitectAgent,
    FlutterDeveloperAgent,
    FlutterTesterAgent,
    FlutterUIDesignerAgent,
)
from .swarm import FlutterSwarm
from .tools import DartCLITool, FileSystemTool, FlutterCLITool

__all__ = [
    "FlutterSwarm",
    "FlutterDeveloperAgent",
    "FlutterTesterAgent",
    "FlutterUIDesignerAgent",
    "FlutterArchitectAgent",
    "FlutterCLITool",
    "DartCLITool",
    "FileSystemTool",
]
