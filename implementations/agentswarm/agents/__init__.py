"""
Abstract agent interfaces for AgentSwarm implementations.
"""

from .developer import AbstractDeveloperAgent
from .tester import AbstractTesterAgent
from .architect import AbstractArchitectAgent
from .debugger import AbstractDebuggerAgent
from .reviewer import AbstractReviewerAgent

__all__ = [
    'AbstractDeveloperAgent',
    'AbstractTesterAgent',
    'AbstractArchitectAgent',
    'AbstractDebuggerAgent',
    'AbstractReviewerAgent'
]
