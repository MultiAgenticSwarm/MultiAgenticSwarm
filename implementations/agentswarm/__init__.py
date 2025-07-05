"""
AgentSwarm - Abstract base classes for all swarm implementations.

This package provides reusable abstractions that any domain-specific
swarm can implement. All classes use MultiAgenticSwarm as their
foundational SDK.
"""

from .core.base import BaseAgent, BaseSwarm
from .core.types import AgentRole, TaskContext, ExecutionResult
from .core.patterns import CollaborationPattern, WorkflowPattern

from .agents.developer import AbstractDeveloperAgent
from .agents.tester import AbstractTesterAgent
from .agents.architect import AbstractArchitectAgent
from .agents.debugger import AbstractDebuggerAgent
from .agents.reviewer import AbstractReviewerAgent

__all__ = [
    # Core components
    'BaseAgent',
    'BaseSwarm',
    'AgentRole',
    'TaskContext',
    'ExecutionResult',
    'CollaborationPattern',
    'WorkflowPattern',
    # Abstract agents
    'AbstractDeveloperAgent',
    'AbstractTesterAgent',
    'AbstractArchitectAgent',
    'AbstractDebuggerAgent',
    'AbstractReviewerAgent'
]
