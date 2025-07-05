"""
FlutterSwarm - LLM-powered Flutter development using MultiAgenticSwarm SDK.

ALL Flutter knowledge and decisions come from LLMs.
No hardcoded Flutter logic - only CLI tool interfaces.
"""

from .swarm import FlutterSwarm
from .agents import (
    FlutterDeveloperAgent,
    FlutterTesterAgent,
    FlutterUIDesignerAgent,
    FlutterArchitectAgent
)
from .tools import (
    FlutterCLITool,
    DartCLITool,
    FileSystemTool
)

__all__ = [
    'FlutterSwarm',
    'FlutterDeveloperAgent',
    'FlutterTesterAgent',
    'FlutterUIDesignerAgent',
    'FlutterArchitectAgent',
    'FlutterCLITool',
    'DartCLITool',
    'FileSystemTool'
]
