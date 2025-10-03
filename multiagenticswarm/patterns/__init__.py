"""
Collaboration Patterns Library

Provides reusable, composable patterns for multi-agent collaboration.
"""

from .base import (
    CollaborationPattern,
    PatternMetadata,
    PatternType,
    GraphTopology,
    PatternRegistry,
)
from .supervisor import SupervisorPattern
from .parallel import ParallelPattern
from .sequential import SequentialPattern
from .consensus import ConsensusPattern
from .competitive import CompetitivePattern
from .composite import CompositePattern

# Auto-register patterns
PatternRegistry.register("supervisor", SupervisorPattern)
PatternRegistry.register("parallel", ParallelPattern)
PatternRegistry.register("sequential", SequentialPattern)
PatternRegistry.register("consensus", ConsensusPattern)
PatternRegistry.register("competitive", CompetitivePattern)

__all__ = [
    "CollaborationPattern",
    "PatternMetadata",
    "PatternType",
    "GraphTopology",
    "PatternRegistry",
    "SupervisorPattern",
    "ParallelPattern",
    "SequentialPattern",
    "ConsensusPattern",
    "CompetitivePattern",
    "CompositePattern",
]
