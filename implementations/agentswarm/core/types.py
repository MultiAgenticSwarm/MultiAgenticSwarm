"""
Core types and patterns for AgentSwarm implementations.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

class AgentRole(Enum):
    """Standard agent roles across all swarm implementations"""
    DEVELOPER = "developer"
    TESTER = "tester"
    ARCHITECT = "architect"
    DEBUGGER = "debugger"
    REVIEWER = "reviewer"
    DESIGNER = "designer"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"

@dataclass
class TaskContext:
    """Context information for task execution"""
    project_path: str
    project_structure: Dict[str, Any] = field(default_factory=dict)
    requirements: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    target_platforms: List[str] = field(default_factory=list)
    existing_files: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutionResult:
    """Result of agent task execution"""
    success: bool
    agent_name: str
    task_id: str
    output: Dict[str, Any] = field(default_factory=dict)
    created_files: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    commands_executed: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    next_steps: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class CollaborationPattern(ABC):
    """Base class for agent collaboration patterns"""

    @abstractmethod
    async def execute(self, agents: List[Any], task: Dict[str, Any]) -> ExecutionResult:
        """Execute the collaboration pattern"""
        pass

class WorkflowPattern(ABC):
    """Base class for workflow patterns"""

    @abstractmethod
    async def run(self, context: TaskContext) -> List[ExecutionResult]:
        """Run the workflow pattern"""
        pass
